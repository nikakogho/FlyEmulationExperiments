"""Actual FlyGym 3D eye geometry, explicit spectra, no neural/body stepping."""
import os
os.environ.setdefault('NUMBA_NUM_THREADS', '2')
import json
import argparse
import sys
from pathlib import Path
import numpy as np
from flygym import Fly, SingleFlySimulation
from flygym.vision import Retina
from light_garden import arena_for_lights
ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
from flyplasticity.retinal_bridge import RetinalBridge
from flyplasticity.spectral import SpectralRetina, narrowband, render_spectral_eyes, fisheye_channels


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('--out', default='results/spectral_scene')
    out = ROOT/parser.parse_args().out
    if out.exists() and any(out.iterdir()):
        raise FileExistsError('Choose a new --out directory to preserve prior evidence')
    out.mkdir(exist_ok=True)
    eye = Retina()
    centers = np.array(json.loads((ROOT/'results/visual_learning_path/flyvis_receptor_centers.json').read_text()))
    retina = SpectralRetina(RetinalBridge(eye.ommatidia_id_map, centers), seed=101)
    w = retina.receptors.wavelength_nm
    # Equal photon radiance, finite bandwidth, spectra independent of human display.
    spectra = {str(c): narrowband(w, c) for c in (365, 450, 525)}
    background = np.ones_like(w)*.02/(w[-1]-w[0])
    arena, _ = arena_for_lights(False)
    fly = Fly(enable_vision=True, render_raw_vision=True, spawn_pos=(0, 0, .2))
    sim = SingleFlySimulation(fly=fly, cameras=[], arena=arena, timestep=.0001)
    saved = {}
    try:
        sim.reset(seed=101)
        # Match FlyGym's own eye rendering exclusions, restoring exact RGBA.
        hidden = [f'{fly.name}/{g}' for g in fly._geoms_to_hide]
        rgba = [sim.physics.named.model.geom_rgba[g].copy() for g in hidden]
        for g in hidden: sim.physics.named.model.geom_rgba[g, 3] = 0
        geometries = {i: background for i in range(sim.physics.model.ngeom)}
        cue_ids = [sim.physics.model.name2id(f'light_cue_{i}', 'geom') for i in (0, 1)]
        cameras = [f'{fly.name}/{side}Eye_cam' for side in ('L', 'R')]
        for cue in ('365', '450', '525', 'background'):
            for i in cue_ids: geometries[i] = background if cue == 'background' else spectra[cue]
            image = render_spectral_eyes(sim.physics, cameras, eye.ommatidia_id_map.shape,
                                        geometries, background, retina.receptors)
            corrected = np.array([fisheye_channels(im, eye.zoom, eye.distortion_coefficient) for im in image])
            actual, potential = retina.sample_excitation(corrected)
            saved[cue] = actual
            saved[cue+'_potential'] = potential
        # Spatial transport regression against the installed renderer, independent of spectra.
        marker = np.random.default_rng(13).integers(0, 256, (*eye.ommatidia_id_map.shape, 3), dtype=np.uint8)
        np.testing.assert_array_equal(fisheye_channels(marker, eye.zoom, eye.distortion_coefficient), eye.correct_fisheye(marker))
        # Human RGB materials are irrelevant to the sensor; mutate them and rerender.
        original = sim.physics.model.geom_rgba.copy()
        sim.physics.model.geom_rgba[:, :3] = np.random.default_rng(3).random((sim.physics.model.ngeom, 3))
        repeated = render_spectral_eyes(sim.physics, cameras, eye.ommatidia_id_map.shape,
                                        geometries, background, retina.receptors)
        np.testing.assert_array_equal(repeated, image)
        sim.physics.model.geom_rgba[:] = original
        for g, color in zip(hidden, rgba): sim.physics.named.model.geom_rgba[g] = color
    finally:
        sim.close()
    contrasts = {c: float(np.max(np.abs(saved[c]-saved['background']))) for c in spectra}
    differences = {a+'_'+b: float(np.max(np.abs(saved[a]-saved[b]))) for a, b in [('365','450'),('450','525'),('365','525')]}
    assert min(contrasts.values()) > .01, 'Cues not visible in actual 3D eyes'
    assert min(differences.values()) > .01, 'Spectral cues alias'
    np.savez_compressed(out/'retinal_inputs.npz', **saved, pale=retina.pale, wavelength_nm=w)
    checks = dict(passed=True, actual_3d_eye_render=True, physics_steps=0, neural_simulation=False,
        no_rgb_dependency=True, fisheye_matches_flygym=True, receptors_per_eye=len(retina.bridge.counts),
        actual_channels=['R1_6', 'R7', 'R8'], pale_counts=retina.pale.sum(axis=1).tolist(),
        cue_background_max_difference=contrasts, pairwise_max_difference=differences,
        limitation='Explicit uniform surface radiance, empirical ERG response filters, assumed mosaic; no full phototransduction model.')
    (out/'checks.json').write_text(json.dumps(checks, indent=2))
    print(json.dumps(checks, indent=2))


if __name__ == '__main__': main()

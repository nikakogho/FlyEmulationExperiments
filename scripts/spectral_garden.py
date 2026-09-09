"""Reward-free embodied transfer of the stationary spectral memory.

This tests the existing motor readout, not spontaneous acquisition from food.
"""
import argparse
import json
from pathlib import Path
import sys
import numpy as np
from flygym.vision import Retina
from light_garden import episode
from spectral_brain import SpectralBrain
ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
from flyplasticity.retinal_bridge import RetinalBridge
from flyplasticity.spectral import SpectralRetina, narrowband, render_spectral_eyes, fisheye_channels
from flyplasticity.spectral_learning import receptor_features


class SceneSensor:
    description = 'Explicit photon spectra -> empirical Rh1/Rh3/Rh4/Rh5/Rh6 filters -> assumed R7/R8 mosaic -> fixed five-channel pooling; no RGB input'

    def __init__(self):
        self.eye = Retina()
        centers = np.array(json.loads((ROOT/'results/visual_learning_path/flyvis_receptor_centers.json').read_text()))
        self.retina = SpectralRetina(RetinalBridge(self.eye.ommatidia_id_map, centers), seed=101)
        w = self.retina.receptors.wavelength_nm
        self.spectra = [narrowband(w, 450), narrowband(w, 525)]
        self.background = np.ones_like(w)*.02/(w[-1]-w[0])
        self.baseline = np.load(ROOT/'results/spectral_scene/retinal_inputs.npz')['background']

    def __call__(self, sim, fly, order):
        spectra = {i:self.background for i in range(sim.physics.model.ngeom)}
        for location, color in enumerate(order):
            spectra[sim.physics.model.name2id(f'light_cue_{location}', 'geom')] = self.spectra[color]
        # Same camera exclusions as native FlyGym vision; restore exact values.
        hidden = [f'{fly.name}/{g}' for g in fly._geoms_to_hide]
        colors = [sim.physics.named.model.geom_rgba[g].copy() for g in hidden]
        try:
            for g in hidden: sim.physics.named.model.geom_rgba[g, 3] = 0
            image = render_spectral_eyes(sim.physics, [f'{fly.name}/{s}Eye_cam' for s in ('L','R')],
                self.eye.ommatidia_id_map.shape, spectra, self.background, self.retina.receptors)
        finally:
            for g, color in zip(hidden, colors): sim.physics.named.model.geom_rgba[g] = color
        image = np.array([fisheye_channels(im, self.eye.zoom, self.eye.distortion_coefficient) for im in image])
        actual, _ = self.retina.sample_excitation(image)
        return receptor_features(actual, self.baseline, self.retina.pale)


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument('--out', default='results/spectral_garden')
    ap.add_argument('--seeds', nargs='+', type=int, default=[201,202,203])
    ap.add_argument('--resume', action='store_true')
    args = ap.parse_args()
    out = ROOT/args.out
    out.mkdir(exist_ok=args.resume)
    protocol = dict(seeds=args.seeds, steps=24, decision_dt_s=.1, physics_dt_s=.0001,
        conditions=['paired','delayed','frozen'], positions_swapped=[False,True],
        acquisition='Saved stationary blue 450 nm conditioning weights from spectral_memory',
        blue_cue_index=0, green_cue_index=1, reward_during_body_test=False, learning_during_body_test=False,
        motor_readout='Unchanged fixed normalized hemispheric MBON difference plus matched random exploration',
        metric='Mean over decisions of distance to green minus distance to blue (mm); positive favors blue.',
        success='After averaging swapped positions, paired score exceeds BOTH controls for every fixed seed.',
        limitation='Exploratory transfer; not spontaneous acquisition in the body or improved plasticity. Three seeds give a pilot, not robust statistical validation.')
    if args.resume:
        original = json.loads((out/'protocol.json').read_text())
        if not set(args.seeds).issubset(original['seeds']):
            raise ValueError('Resume seeds must belong to original protocol')
        for key in protocol:
            if key != 'seeds' and protocol[key] != original[key]:
                raise ValueError(f'Resume protocol mismatch: {key}')
    else:
        (out/'protocol.json').write_text(json.dumps(protocol, indent=2))
    rows = []
    for seed in args.seeds:
        brain = SpectralBrain(seed)
        np.testing.assert_array_equal(brain.initial, np.load(ROOT/f'results/spectral_memory/initial_{seed}.npy'))
        for condition in protocol['conditions']:
            weights = np.load(ROOT/f'results/spectral_memory/weights_{seed}_{condition}.npy')
            for swap in (False, True):
                brain.reset(weights)
                path = out/f'{seed}_{condition}_swap{int(swap)}'
                if args.resume and path.with_suffix('.json').exists():
                    result = json.loads(path.with_suffix('.json').read_text())
                    if (not result.get('completed') or len(result['rows']) != 24 or result.get('seed') != seed
                        or result.get('swapped') != swap or result.get('learning') or result.get('food_present')
                        or result.get('physics_dt') != .0001 or result.get('sensory_interface') != SceneSensor.description):
                        raise ValueError(f'Cannot resume incompatible episode {path}')
                else:
                    result = episode(brain, seed, 0., 24, swap, False, False,
                        path, .0001, vision_sensor=SceneSensor())
                np.testing.assert_array_equal(brain.weights(), weights)
                distances = np.array([r['cue_distances'] for r in result['rows']])
                row = dict(seed=seed, condition=condition, swapped=swap,
                    blue_approach_score_mm=float(np.mean(distances[:,1]-distances[:,0])),
                    final_xyz=result['rows'][-1]['xyz'], runtime_sec=result['runtime_sec'])
                rows.append(row)
                print(json.dumps(row), flush=True)
        del brain
    effects = []
    for seed in args.seeds:
        means = {c:float(np.mean([r['blue_approach_score_mm'] for r in rows if r['seed']==seed and r['condition']==c]))
                 for c in protocol['conditions']}
        effects.append(dict(seed=seed, scores_mm=means,
            paired_beats_both_controls=bool(means['paired'] > max(means['delayed'],means['frozen']))))
    result = dict(completed=True, episodes=len(rows), effects=effects, rows=rows,
        pilot_gate_passed=all(e['paired_beats_both_controls'] for e in effects),
        improved_plasticity_demonstrated=False, biological_pathway_validated=False)
    name = 'checks.json' if args.seeds == [201,202,203] else 'checks_seed_'+'_'.join(map(str,args.seeds))+'.json'
    (out/name).write_text(json.dumps(result, indent=2))
    print(json.dumps({k:v for k,v in result.items() if k!='rows'}), flush=True)


if __name__ == '__main__': main()

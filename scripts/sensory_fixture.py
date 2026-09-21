"""Pinned FlyGym scene and optical sampling; never imports a connectome runner."""
import os
os.environ.setdefault('NUMBA_NUM_THREADS', '2')
os.environ.setdefault('OMP_NUM_THREADS', '2')
from pathlib import Path
import sys, json
import numpy as np
from flygym import Fly
from flygym.vision import Retina
from flygym.arena import FlatTerrain
ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
from flyplasticity.standing import StandingController
from flyplasticity.spectral import SpectralRetina, narrowband, render_spectral_eyes, fisheye_channels
from flyplasticity.retinal_bridge import RetinalBridge


class SensoryArena(FlatTerrain):
    odor_dimensions = 1

    def __init__(self):
        super().__init__(size=(40, 25))
        self.materials = {'ground': 'floor_dark'}
        self.source = np.array([9., 3., 1.])
        # sensor_ names opt out of FlyGym's implicit floor-contact pairs.
        # Masks AND the compiled pair inventory are verified before any steps.
        for ix in range(-3, 12):
            for iy in range(-5, 6):
                if (ix+iy) % 2:
                    continue
                self.add_visual(f'sensor_tile_{ix}_{iy}', 'box',
                    (2*ix, 2*iy, .0002), (1., 1., .0001), (.48, .54, .45, 1), 'floor_light')
        for name, pos, color, band in [
            ('uv', (3, -5, 2), (.55, .35, .72, 1), 'uv'),
            ('blue', (9, 5, 2), (.20, .53, .72, 1), 'blue'),
            ('green', (16, -4, 2), (.43, .62, .32, 1), 'green')]:
            self.add_visual('sensor_card_'+name, 'box', pos, (.2, .8, 2), color, band)
        self.add_visual('sensor_odor_marker', 'sphere', self.source, (.25,),
                        (.87, .65, .25, 1), 'marker')
        self.add_visual('sensor_calibration_probe', 'sphere', (0, 0, 100), (.08,),
                        (1, 1, 1, 1), 'background', group=5)

    def add_visual(self, name, kind, position, size, rgba, material, group=0):
        self.root_element.worldbody.add('geom', name=name, type=kind, pos=position,
            size=size, rgba=rgba, group=group, contype=0, conaffinity=0)
        self.materials[name] = material

    def get_olfaction(self, positions):
        p = np.asarray(positions)
        return np.exp(-np.sum((p-self.source)**2, axis=1)/(2*4.**2))[None, :]


def make_fixture():
    eye = Retina()
    centers = np.array(json.loads((ROOT/'results/visual_learning_path/flyvis_receptor_centers.json').read_text()))
    retina = SpectralRetina(RetinalBridge(eye.ommatidia_id_map, centers), seed=101)
    arena = SensoryArena()
    fly = Fly(enable_adhesion=True, enable_olfaction=True, enable_vision=False,
        spawn_pos=(0, 0, .2),
        contact_sensor_placements=[f'{leg}{segment}' for leg in ('LF', 'LM', 'LH', 'RF', 'RM', 'RH')
            for segment in ('Tibia', 'Tarsus1', 'Tarsus2', 'Tarsus3', 'Tarsus4', 'Tarsus5')])
    # Install the same pinned eye cameras, but do not run FlyGym's RGB pipeline.
    fly._configure_eyes()
    sim = StandingController(fly=fly, arena=arena, cameras=[], timestep=.0001, seed=101)
    obs, _ = sim.reset(seed=101)
    w = retina.receptors.wavelength_nm
    uniform = np.ones_like(w)/(w[-1]-w[0])
    spectra = dict(background=.08*uniform, floor_dark=.035*uniform, floor_light=.07*uniform,
        body=.04*uniform, marker=.09*uniform)
    for name, wavelength in [('uv', 365), ('blue', 450), ('green', 525)]:
        spectra[name] = .05*uniform+narrowband(w, wavelength, total_photons=.15)
    mapping, names = {}, {}
    for i in range(sim.physics.model.ngeom):
        name = sim.physics.model.id2name(i, 'geom')
        material = arena.materials.get(name)
        if material is None:
            if not name or not name.startswith(fly.name+'/'):
                raise ValueError('Unspecified spectral surface: '+str(name))
            material = 'body'
        mapping[i], names[str(i)] = spectra[material], dict(geometry=name, material=material)
    return arena, fly, sim, obs, eye, retina, spectra, mapping, names


def sample_eyes(sim, fly, eye, retina, spectra, mapping):
    ids = [sim.physics.model.name2id(f'{fly.name}/{g}', 'geom') for g in fly._geoms_to_hide]
    original = sim.physics.model.geom_rgba[ids].copy()
    try:
        sim.physics.model.geom_rgba[ids, 3] = 0
        raw = render_spectral_eyes(sim.physics,
            [f'{fly.name}/{side}Eye_cam' for side in ('L', 'R')],
            eye.ommatidia_id_map.shape, mapping, spectra['background'], retina.receptors)
        corrected = np.array([fisheye_channels(im, eye.zoom, eye.distortion_coefficient) for im in raw])
        return retina.sample_excitation(corrected)
    finally:
        sim.physics.model.geom_rgba[ids] = original


def visual_contact_check(sim):
    m = sim.physics.model
    visual = [i for i in range(m.ngeom) if str(m.id2name(i, 'geom')).startswith('sensor_')]
    if not visual:
        raise ValueError('No fixture visuals')
    if np.any(m.geom_contype[visual]) or np.any(m.geom_conaffinity[visual]):
        raise ValueError('Visual has collision mask')
    if np.isin(m.pair_geom1, visual).any() or np.isin(m.pair_geom2, visual).any():
        raise ValueError('Visual included in explicit contact pair')
    return set(visual)

"""Reusable 3D apparatus for mechanical and guarded neural preference assays."""
import os
os.environ.setdefault('NUMBA_NUM_THREADS','2');os.environ.setdefault('OMP_NUM_THREADS','2')
from pathlib import Path
import sys
import numpy as np
ROOT=Path(__file__).resolve().parents[1];sys.path.insert(0,str(ROOT))
from flygym import Fly
from flygym.arena import OdorArena
from flyplasticity.standing import StandingController
from flyplasticity.hybrid_navigation import PreferenceField
from flyplasticity.visual_markers import noncolliding_odor_markers


class PreferenceArena(OdorArena):
    def __init__(self,swapped=False):
        self.field=PreferenceField([[6,3,1],[6,-3,1]],swapped);self.enabled=False
        colors=[(.15,.65,.85,1),(.95,.65,.15,1)]
        super().__init__(odor_source=self.field.sources,peak_odor_intensity=np.eye(2),
            marker_colors=colors[::-1] if swapped else colors,marker_size=.3)
        noncolliding_odor_markers(self)

    def get_olfaction(self,antennae_pos):
        return self.field.sample(antennae_pos) if self.enabled else np.zeros((2,4))


def make_fixture(heading=.6,swapped=False):
    arena=PreferenceArena(swapped)
    fly=Fly(enable_adhesion=True,enable_olfaction=True,spawn_pos=(0,0,.2),spawn_orientation=(0,0,heading),
        contact_sensor_placements=[f'{l}{s}' for l in ['LF','LM','LH','RF','RM','RH']
            for s in ['Tibia','Tarsus1','Tarsus2','Tarsus3','Tarsus4','Tarsus5']])
    sim=StandingController(fly=fly,arena=arena,cameras=[],timestep=.0001,seed=101)
    obs,_=sim.reset(seed=101)
    for k in range(3000):obs=advance(sim,[0.,0.],1)
    return arena,fly,sim,obs


def advance(sim,u,steps=50):
    for j in range(steps):
        obs,_,ended,truncated,_=sim.step(u)
        if ended or truncated or not np.isfinite(sim.physics.get_state()).all():raise RuntimeError('Invalid physical state')
    return obs


def observe(arena,fly,sim,obs):
    sites=np.asarray(sim.physics.bind(fly._antennae_sensors).sensordata).reshape(4,3)
    orientation=obs['fly_orientation']
    if np.linalg.norm(orientation[:2])<1e-6:raise RuntimeError('Undefined planar heading')
    heading=float(np.arctan2(orientation[1],orientation[0]))
    scent=arena.get_olfaction(sites);center=sites[2:].mean(axis=0)
    gradients=arena.field.gradients(center) if arena.enabled else np.zeros((2,3))
    wind=arena.field.wind(center) if arena.enabled else np.zeros(2)
    return dict(xyz=obs['fly'][0].tolist(),heading=heading,odor=scent.tolist(),
        gradients=gradients.tolist(),wind=wind.tolist(),sensor_positions_mm=sites.tolist(),
        speed_mm_s=float(np.linalg.norm(obs['fly'][1,:2])))


def save_tapes(out,rows,frames):
    import json
    (out/'telemetry.json').write_text('[\n'+',\n'.join(json.dumps(r,separators=(',',':')) for r in rows)+'\n]')
    if frames:np.savez_compressed(out/'replay.npz',time_s=[r[0] for r in frames],qpos=[r[1] for r in frames],qvel=[r[2] for r in frames],act=[r[3] for r in frames])


def frame(t,sim):return (t,sim.physics.data.qpos.copy(),sim.physics.data.qvel.copy(),sim.physics.data.act.copy())

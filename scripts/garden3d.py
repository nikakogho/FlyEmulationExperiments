"""A physical terraced 3D garden for the connectome-derived walking fly.

Odor fields are analytic 3D Gaussians, not fluid dynamics. Controller only
receives antenna concentrations via brain outputs, never source coordinates.
Both conditions run the same fixed duration. Source distances are evaluation only.
"""
import argparse
import importlib.util
import json
from pathlib import Path
import numpy as np
import brian2 as br
from flygym import Fly, Camera
from flygym.arena import FlatTerrain
from flygym.examples.locomotion import HybridTurningController

ROOT = Path(__file__).resolve().parents[1]
SOURCES = np.array([[17., 7., 1.5], [20., -8., 1.5]])


def concentration(point):
    return np.exp(-.5*np.sum(((SOURCES-point)/np.array([10., 10., 5.]))**2, axis=1))


def camera_axes(position, target):
    z = np.asarray(position,dtype=float)-np.asarray(target,dtype=float)
    z /= np.linalg.norm(z)
    x = np.cross([0., 0., 1.], z)
    x /= np.linalg.norm(x)
    return np.r_[x, np.cross(z, x)]


def make_arena():
    arena = FlatTerrain()
    world = arena.root_element.worldbody
    # A terraced soil bed, with 80-micron risers that the reflex controller
    # must physically negotiate. Unit lengths follow flygym's millimetres.
    for k in range(4):
        height = .08*(k+1)
        world.add('geom', name=f'terrace_{k}', type='box',
                  pos=(8.+k*2, 0, height/2), size=(1, 13, height/2),
                  rgba=(.30+.025*k, .38+.02*k, .20, 1), friction=(1, .005, .0001))
    world.add('geom', name='upper_bed', type='box', pos=(21, 0, .16),
              size=(6, 13, .16), rgba=(.39,.44,.24,1))
    # Collidable stones with unequal elevations; not visual-only markers.
    for k, (x,y,z,r) in enumerate([(5,-5,.18,1.1),(10,-4,.25,.85),
                                   (13,1,.25,.75),(22,3,.35,1.3),(25,-5,.3,.9)]):
        world.add('geom', name=f'rock_{k}', type='ellipsoid', pos=(x,y,z),
                  size=(r,r*.75,z+.08), rgba=(.38,.42,.43,1), friction=(1,.005,.0001))
    # Low enclosure, well outside the initial path.
    for k, (pos,size) in enumerate([((12,-14,.08),(17,.25,.08)),((12,14,.08),(17,.25,.08)),
                                     ((29,0,.08),(.25,14,.08)),((-5,0,.08),(.25,14,.08))]):
        world.add('geom', name=f'border_{k}', type='box', pos=pos, size=size, rgba=(.23,.19,.14,1))
    for k, (src,color) in enumerate(zip(SOURCES,[(.94,.57,.12,1),(.28,.58,.80,1)])):
        world.add('geom', name=f'odor_pedestal_{k}', type='cylinder',
                  pos=(src[0],src[1],.52), size=(.8,.2), rgba=(.5,.3,.14,1),contype=0,conaffinity=0)
        world.add('geom', name=f'odor_bead_{k}', type='sphere', pos=src,
                  size=(.72,), rgba=color,contype=0,conaffinity=0)
    return arena


def rollout(brain, which, out, steps):
    brain.net.restore('before_rollouts', restore_random_state=True)
    brain.prev = np.array(brain.spk.count[:], dtype=np.int64)
    brain.set_weights(which)
    arena = make_arena()
    fly = Fly(enable_adhesion=True, spawn_pos=(0,0,.2),
              contact_sensor_placements=[f'{leg}{seg}' for leg in ['LF','LM','LH','RF','RM','RH']
                                          for seg in ['Tibia','Tarsus1','Tarsus2','Tarsus3','Tarsus4','Tarsus5']])
    pos = (23., -29., 28.)
    camera = Camera(attachment_point=arena.root_element.worldbody,
                    camera_name='garden_view',
                    camera_parameters={'mode':'fixed','pos':pos,'xyaxes':camera_axes(pos,(12,0,0)), 'fovy':48},
                    play_speed=.5, window_size=(960,720))
    sim = HybridTurningController(fly=fly, cameras=[camera], timestep=1e-4, seed=0, arena=arena)
    obs,_ = sim.reset(0)
    rows=[]
    import imageio.v3 as iio
    iio.imwrite(out/f'{which}_start.png',sim.render()[0])
    for decision in range(steps):
        xyz = np.array(obs['fly'][0], dtype=float)
        forward = np.array(obs['fly_orientation'], dtype=float)
        forward /= max(np.linalg.norm(forward),1e-9)
        lateral = np.cross([0.,0.,1.],forward)
        lateral /= max(np.linalg.norm(lateral),1e-9)
        left = concentration(xyz+1.5*forward+1.2*lateral)
        right = concentration(xyz+1.5*forward-1.2*lateral)
        vl,vr = brain.valence(*left),brain.valence(*right)
        total=vl+vr
        delta=float(np.clip(1.2*(vl-vr)/max(total,200),-.32,.32))
        action=np.array([1+delta,1-delta]) if total>=80 else np.array([.55,.55])
        for _ in range(1500):
            obs,_,_,_,_=sim.step(action)
            sim.render()
        after=np.array(obs['fly'][0],dtype=float)
        if not np.isfinite(after).all():
            raise RuntimeError('Non-finite body position')
        row=dict(decision=decision, time_s=(decision+1)*.15, xyz=after.tolist(),
                 antenna_left=left.tolist(), antenna_right=right.tolist(), mbon_left=vl,mbon_right=vr,
                 motor_drive=action.tolist(), source_distances_3d_mm=np.linalg.norm(SOURCES-after,axis=1).tolist())
        rows.append(row)
        print(which,decision,np.round(after,2),flush=True)
    camera.save_video(out/f'{which}.mp4')
    iio.imwrite(out/f'{which}_end.png',sim.physics.render(width=960,height=720,camera_id=camera.camera_id))
    (out/f'{which}.json').write_text(json.dumps(rows,indent=2))
    sim.close()
    return dict(final_xyz=rows[-1]['xyz'], final_distances=rows[-1]['source_distances_3d_mm'],
                min_distances=np.min([r['source_distances_3d_mm'] for r in rows],axis=0).tolist(),
                body_height_range=[min(r['xyz'][2] for r in rows),max(r['xyz'][2] for r in rows)])


def main():
    ap=argparse.ArgumentParser()
    ap.add_argument('--out',default='results/garden3d')
    ap.add_argument('--steps',type=int,default=24)
    args=ap.parse_args()
    if args.steps<1: ap.error('--steps must be positive')
    br.prefs.codegen.target='numpy'
    path=ROOT/'upstream/fly-api/experiments/navigation/nav_demo.py'
    spec=importlib.util.spec_from_file_location('nav',path)
    nav=importlib.util.module_from_spec(spec); spec.loader.exec_module(nav)
    nav.ANN=str(ROOT/'data/annotations.tsv')
    brain=nav.Brain(str(ROOT/'upstream/Drosophila_brain_model'))
    brain.train()
    brain.net.store('before_rollouts')
    out=Path(args.out); out.mkdir(parents=True,exist_ok=True)
    (out/'config.json').write_text(json.dumps(dict(steps=args.steps,decision_sec=.15,seed=0,
        sources=SOURCES.tolist(),odor_sigma=[10,10,5],learning='upstream episodic LTD',
        notes='Ground walking in physical 3D geometry; analytic odor field; no coordinate-based stopping'),indent=2))
    summary={which:rollout(brain,which,out,args.steps) for which in ['naive','trained']}
    (out/'summary.json').write_text(json.dumps(summary,indent=2))
    print(json.dumps(summary,indent=2))


if __name__=='__main__': main()

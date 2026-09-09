"""Exploratory light-cue conditioning in the physical FlyGym garden.

Learner gets only eye pixels (via features) and a local taste proxy. Evaluator
alone knows rewarded cue identity. Fixed reset schedule, no target-seeking code.
"""
import os
os.environ.setdefault('NUMBA_NUM_THREADS','2')
os.environ.setdefault('OMP_NUM_THREADS','2')
import argparse
import json
import sys
from pathlib import Path
from time import perf_counter
import numpy as np
import imageio.v3 as iio
from flygym import Fly,Camera
from flygym.examples.locomotion import HybridTurningController
from garden3d import make_arena,camera_axes
from light_brain import LightBrain,ROOT
sys.path.insert(0,str(ROOT))
from flyplasticity.light_task import visual_features,motor_output

LIGHT_POS=np.array([[9.,5.,2.2],[9.,-5.,2.2]])
CONTACT_RADIUS=2.5


def arena_for_lights(swapped):
    arena=make_arena()
    # Revision 2: flat physical floor. Terraces/rocks caused BADQACC even at
    # 0.1 ms; remove them before evaluating learning, for every condition.
    for geom in list(arena.root_element.find_all('geom')):
        if geom.name and geom.name.startswith(('terrace_', 'rock_', 'border_', 'upper_bed', 'odor_')):
            geom.remove()
    # Neutralize old odor markers and colored ground to avoid a color-label confound.
    for geom in arena.root_element.find_all('geom'):
        if geom.rgba is not None:
            gray=float(np.mean(geom.rgba[:3])); geom.rgba=(gray,gray,gray,1.)
    order=[1,0] if swapped else [0,1]
    for location,color in enumerate(order):
        rgb=[(.05,1.,.05,1.),(.05,.05,1.,1.)][color]
        mat=arena.root_element.asset.add('material',name=f'cue_material_{location}',rgba=rgb,emission=1)
        arena.root_element.worldbody.add('geom',name=f'light_cue_{location}',type='sphere',
            pos=LIGHT_POS[location],size=(1.5,),material=mat,contype=0,conaffinity=0)
    return arena,order


def episode(brain,seed,heading,steps,swapped,food,learn,path,physics_dt,video=False,yoked=None,motor_probe=None,vision_sensor=None):
    arena,order=arena_for_lights(swapped)
    fly=Fly(enable_adhesion=True,spawn_pos=(0,0,.2),spawn_orientation=(0,0,heading),
        enable_vision=True,render_raw_vision=True,vision_refresh_rate=10,
        contact_sensor_placements=[f'{leg}{seg}' for leg in ['LF','LM','LH','RF','RM','RH']
                                  for seg in ['Tibia','Tarsus1','Tarsus2','Tarsus3','Tarsus4','Tarsus5']])
    camera=Camera(attachment_point=arena.root_element.worldbody,camera_name='light_garden',
        camera_parameters={'mode':'fixed','pos':(14,-23,24),'xyaxes':camera_axes((14,-23,24),(8,0,0)),'fovy':48},
        play_speed=.5,window_size=(800,600)) if video else None
    sim=HybridTurningController(fly=fly,cameras=[camera] if camera else [],timestep=physics_dt,seed=seed,arena=arena)
    rows=[]; start=perf_counter(); rng=np.random.default_rng(seed); walk=0.
    path.parent.mkdir(parents=True,exist_ok=True)
    try:
        obs,info=sim.reset(seed)
        if video:
            iio.imwrite(str(path)+'_start.png',sim.render()[0])
            iio.imwrite(str(path)+'_eyes.png',np.concatenate(info['raw_vision'],axis=1).astype(np.uint8))
        for decision in range(steps):
            xyz=np.array(obs['fly'][0],dtype=float)
            features=(visual_features(info['raw_vision']) if vision_sensor is None
                      else vision_sensor(sim,fly,order))
            # A local contact-volume approximation, not a distance-shaped reward.
            contact=bool(food and xyz[2]<2.5 and np.linalg.norm(xyz[:2]-LIGHT_POS[order.index(0),:2])<=CONTACT_RADIUS)
            taste=float(yoked[decision]) if yoked is not None else float(contact)
            if brain is None:
                rates=np.zeros(2); spikes={}
            else:
                rates,spikes=brain.step(features,taste,learn)
            walk=.8*walk+rng.normal(0,.055)
            action=motor_output(rates,walk)
            if motor_probe is not None:
                if brain is not None: raise ValueError('Motor probes are body-only checks')
                action=np.array([1+motor_probe,1-motor_probe])
            for _ in range(round(.1/physics_dt)):
                obs,_,terminated,truncated,info=sim.step(action)
                if video: sim.render()
                if terminated or truncated: raise RuntimeError('Body simulation terminated')
            after=np.array(obs['fly'][0],dtype=float)
            if not np.isfinite(after).all() or after[2]>5 or after[2]<-.5:
                raise RuntimeError(f'Invalid body state: {after.tolist()}')
            distances=np.linalg.norm(after[:2]-LIGHT_POS[:,:2],axis=1)
            cue_distances=[float(distances[order.index(c)]) for c in (0,1)]
            row=dict(decision=decision,xyz=after.tolist(),features=features.tolist(),taste=taste,
                physical_food_contact=contact,mbon_rates=rates.tolist(),action=action.tolist(),
                cue_distances=cue_distances,**spikes)
            rows.append(row)
        if video:
            camera.save_video(str(path)+'.mp4')
            iio.imwrite(str(path)+'_end.png',sim.physics.render(width=800,height=600,camera_id=camera.camera_id))
        result=dict(completed=True,steps=steps,seed=seed,heading=heading,swapped=swapped,
            food_present=food,learning=learn,physics_dt=physics_dt,arena_revision=2,
            runtime_sec=perf_counter()-start,rows=rows)
        if vision_sensor is not None:
            result['sensory_interface']=vision_sensor.description
    except Exception as exc:
        result=dict(completed=False,error=repr(exc),seed=seed,swapped=swapped,rows=rows)
        Path(str(path)+'.json').write_text(json.dumps(result,indent=2))
        raise
    finally:
        sim.close()
    Path(str(path)+'.json').write_text(json.dumps(result,indent=2))
    return result


def main():
    ap=argparse.ArgumentParser()
    ap.add_argument('--seed',type=int,default=0)
    ap.add_argument('--out',default='results/light_garden')
    ap.add_argument('--preflight',action='store_true')
    ap.add_argument('--condition',choices=('all','plastic','frozen','yoked'),default='all')
    ap.add_argument('--physics-dt',type=float,default=.0001)
    args=ap.parse_args(); out=Path(args.out); out.mkdir(parents=True,exist_ok=True)
    if args.preflight:
        for index,probe in enumerate((-.3,0.,.3)):
            r=episode(None,101+index,0.,24,False,False,False,out/f'preflight_{probe}',args.physics_dt,True,motor_probe=probe)
            print(json.dumps({k:v for k,v in r.items() if k!='rows'}),flush=True)
        return
    brain=LightBrain(args.seed)
    np.save(out/f'seed{args.seed}_initial_weights.npy',brain.initial)
    (out/f'brain_{args.seed}.json').write_text(json.dumps(brain.metadata,indent=2))
    # Acquisition side counterbalanced by seed; test swaps positions explicitly.
    training_swap=bool(args.seed%2)
    headings=(-.35,0.,.35)
    exposures=[]
    if args.condition=='yoked':
        for ep in range(3):
            acquisition=json.loads((out/f'seed{args.seed}_plastic_train{ep}.json').read_text())
            if not acquisition.get('completed') or len(acquisition['rows'])!=24 or acquisition.get('arena_revision')!=2:
                raise RuntimeError('Shifted reward requires complete revision-2 acquisition tapes')
            exposures.append([row['taste'] for row in acquisition['rows']])
    conditions=('plastic','frozen','yoked') if args.condition=='all' else (args.condition,)
    for condition in conditions:
        brain.reset()
        for ep,heading in enumerate(headings):
            tape=None
            if condition=='yoked': tape=np.roll(np.array(exposures[ep]),12)
            r=episode(brain,args.seed*100+ep,heading,24,training_swap,condition!='yoked',condition!='frozen',
                out/f'seed{args.seed}_{condition}_train{ep}',args.physics_dt,
                video=(args.seed==0 and condition=='plastic' and ep==0),yoked=tape)
            if condition=='plastic': exposures.append([x['taste'] for x in r['rows']])
            print(f'seed {args.seed} {condition} training {ep}: contacts={sum(x["physical_food_contact"] for x in r["rows"])}',flush=True)
        learned=brain.weights()
        np.save(out/f'seed{args.seed}_{condition}_weights.npy',learned)
        for swap in (False,True):
            brain.reset(learned)
            r=episode(brain,args.seed*100+90,0.,24,swap,False,False,
                out/f'seed{args.seed}_{condition}_test_swap{int(swap)}',args.physics_dt,
                video=(args.seed==0 and condition in ('plastic','frozen')))
            print(f'seed {args.seed} {condition} test swap={swap}: final={r["rows"][-1]["xyz"]}',flush=True)
    np.save(out/f'seed{args.seed}_initial_weights.npy',brain.initial)


if __name__=='__main__': main()

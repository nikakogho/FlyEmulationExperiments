"""Short mechanical rest/walk/rest probe; no connectome or learning model."""
import os
os.environ.setdefault('NUMBA_NUM_THREADS','2')
os.environ.setdefault('OMP_NUM_THREADS','2')
import argparse
import json
import sys
from pathlib import Path
import numpy as np
from flygym import Fly
from flygym.arena import FlatTerrain
from flygym.examples.locomotion import HybridTurningController
ROOT=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT))
from flyplasticity.standing import StandingController
from flyplasticity.sensory import SensoryStream,from_flygym,rest_capable_drive


def main():
    parser=argparse.ArgumentParser()
    parser.add_argument('--seed',type=int,default=101)
    parser.add_argument('--out',required=True)
    args=parser.parse_args()
    out=ROOT/args.out
    out.mkdir(parents=True,exist_ok=False)
    fly=Fly(enable_adhesion=True,spawn_pos=(0,0,.2),enable_vision=True,
            render_raw_vision=True,vision_refresh_rate=50,
            contact_sensor_placements=[f'{leg}{seg}' for leg in ['LF','LM','LH','RF','RM','RH']
                                      for seg in ['Tibia','Tarsus1','Tarsus2','Tarsus3','Tarsus4','Tarsus5']])
    sim=StandingController(fly=fly,arena=FlatTerrain(),cameras=[],timestep=.0001,seed=args.seed)
    stream=SensoryStream(); rows=[]; rgb=[]; angles=[]; velocities=[]; loads=[]
    outcome=dict(completed=False,brain_simulated=False,seed=args.seed,controller="explicit neutral standing",
                 protocol='rest 0-.3 s, activity .6 from .3-.7 s, rest .7-1.4 s',
                 rest_gate='last .3 s XY displacement <= .2 mm and median speed <= .5 mm/s',
                 limitation='Mechanical capability, not a neural decision to rest or a welfare assay')
    try:
        obs,info=sim.reset(seed=args.seed)
        for step in range(14000):
            t=sim.curr_time
            activity=.6 if .3<=t<.7 else 0.
            command=rest_capable_drive(activity,0)
            obs,_,terminated,truncated,info=sim.step(command)
            if terminated or truncated: raise RuntimeError('Unexpected physical termination')
            if (step+1)%200: continue
            # Actual acquisition timestamp exposed by the inspected FlyGym source.
            frame=from_flygym(stream,time_s=sim.curr_time,vision_time_s=fly._last_vision_update_time,
                              observation=obs,raw_vision=info['raw_vision'],previous_motor_command=command)
            xyz=np.asarray(obs['fly'][0],dtype=float)
            if not np.isfinite(xyz).all() or not -.5<xyz[2]<5:
                raise RuntimeError('Invalid physical body state')
            # Position/speed are evaluator-only; from_flygym excludes them.
            rows.append(dict(time_s=frame.time_s,vision_time_s=frame.vision_time_s,
                             vision_fresh=frame.vision_fresh,command=command.tolist(),xyz=xyz.tolist(),
                             speed_mm_s=float(np.linalg.norm(obs['fly'][1,:2]))))
            rgb.append(np.asarray(info['raw_vision'],dtype=np.uint8))
            angles.append(frame.joint_angles_rad); velocities.append(frame.joint_velocities_rad_s)
            loads.append(frame.contact_load_native_units)
        settled=[row for row in rows if row['time_s']>=1.1-1e-8]
        displacement=float(np.linalg.norm(np.array(settled[-1]['xyz'])[:2]-np.array(settled[0]['xyz'])[:2]))
        speed=float(np.median([row['speed_mm_s'] for row in settled]))
        outcome.update(completed=True,passed=displacement<=.2 and speed<=.5,
                       settled_displacement_mm=displacement,settled_median_speed_mm_s=speed,
                       samples=len(rows),joint_count=len(angles[0]),contact_sensor_count=len(loads[0]))
    except Exception as exc:
        outcome['error']=repr(exc)
        raise
    finally:
        sim.close()
        outcome['rows']=rows
        (out/'body_rest_checks.json').write_text(json.dumps(outcome,indent=2))
        if rows:
            np.savez_compressed(out/'body_sensor_recording.npz',eye_rgb=np.array(rgb),
                                joint_angles_rad=np.array(angles),joint_velocities_rad_s=np.array(velocities),
                                contact_load_native_units=np.array(loads),
                                time_s=np.array([r['time_s'] for r in rows]),
                                vision_time_s=np.array([r['vision_time_s'] for r in rows]),
                                motor_commands=np.array([r['command'] for r in rows]))
    print(json.dumps({k:v for k,v in outcome.items() if k!='rows'},indent=2))
    if not outcome.get('passed'): raise SystemExit(1)


if __name__=='__main__': main()

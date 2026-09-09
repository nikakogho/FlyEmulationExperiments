"""Record an actual 3D mechanical fly and export passive replay. No brain runs."""
import os
os.environ.setdefault('NUMBA_NUM_THREADS','2');os.environ.setdefault('OMP_NUM_THREADS','2')
from pathlib import Path
import sys,json,time,gzip
ROOT=Path(__file__).resolve().parents[1];sys.path.insert(0,str(ROOT))
import numpy as np
from flygym import Fly
from flygym.arena import FlatTerrain
from flyplasticity.standing import StandingController
from flyplasticity.welfare import Guard,Limits,Sample


def scripted_drive(t):
    """Fixed mechanical assay; has no sensor, cue, position or reward arguments."""
    if t<.3 or t>=2.:return np.zeros(2)
    if t<1.:return np.array([.7,.7])
    if t<1.5:return np.array([.8,.5])
    return np.array([.65,.65])


def main():
    import argparse
    ap=argparse.ArgumentParser(description=__doc__);ap.add_argument('--out',default='results/delivery_arena');args=ap.parse_args()
    out=ROOT/args.out;out.mkdir(exist_ok=False)
    arena=FlatTerrain()
    world=arena.root_element.worldbody
    for index,(x,y,color) in enumerate([(8,4,(.2,.5,.9,1)),(8,-4,(.3,.8,.4,1))]):
        world.add('geom',name=f'visual_marker_{index}',type='cylinder',pos=(x,y,.4),size=(.6,.4),rgba=color,contype=0,conaffinity=0)
    fly=Fly(enable_adhesion=True,spawn_pos=(0,0,.2),
            contact_sensor_placements=[f'{leg}{seg}' for leg in ['LF','LM','LH','RF','RM','RH'] for seg in ['Tibia','Tarsus1','Tarsus2','Tarsus3','Tarsus4','Tarsus5']])
    sim=StandingController(fly=fly,arena=arena,cameras=[],timestep=.0001,seed=101)
    guard=Guard(Limits(2.80001,.000101,1.3,.1))
    states=[];rows=[];wall=time.perf_counter()
    try:
        obs,_=sim.reset(seed=101)
        sim.physics.model.save_binary(str(out/'scene.mjb'))
        for step in range(28000):
            t=step*.0001;command=scripted_drive(t)
            finite=bool(np.isfinite(np.r_[sim.physics.data.qpos,sim.physics.data.qvel]).all())
            # This is a mechanical controller with no modeled neurons/valence.
            sample=Sample(t,float(max(command)),finite,True,False,False)
            obs,_,terminated,truncated,_=guard.advance(sample,lambda:sim.step(command))
            if terminated or truncated:raise RuntimeError('Physics terminated')
            if step%100==0:
                states.append((sim.curr_time,sim.physics.data.qpos.copy(),sim.physics.data.qvel.copy(),sim.physics.data.act.copy()))
                rows.append(dict(time_s=sim.curr_time,xyz=np.asarray(obs['fly'][0]).tolist(),speed_mm_s=float(np.linalg.norm(obs['fly'][1,:2])),command=command.tolist(),
                                 joint_angles_rad=np.asarray(obs['joints'][0]).tolist(),contact_forces=np.asarray(obs['contact_forces']).tolist()))
            if step%5000==0:print(f'Mechanical arena {t:.1f}/2.8 s',flush=True)
        end=[r for r in rows if r['time_s']>2.5]
        report=dict(completed=True,neural_steps=0,learning_demonstrated=False,control='fixed scripted engineering gait',
                    physics_steps=28000,recorded_frames=len(states),duration_s=sim.curr_time,
                    final_rest_displacement_mm=float(np.linalg.norm(np.array(end[-1]['xyz'])[:2]-np.array(end[0]['xyz'])[:2])),
                    final_rest_median_speed_mm_s=float(np.median([r['speed_mm_s'] for r in end])),
                    max_distance_from_start_mm=float(max(np.linalg.norm(np.array(r['xyz'])[:2]-np.array(rows[0]['xyz'])[:2]) for r in rows)),
                    wall_seconds=time.perf_counter()-wall,mechanical_guard_only=True)
        report['rest_pass']=report['final_rest_displacement_mm']<=.2 and report['final_rest_median_speed_mm_s']<=.5
        before=sim.curr_time
        try:guard.advance(Sample(2.8,0.,False,True,False,False),lambda:sim.step([0.,0.]))
        except RuntimeError:pass
        report['fault_prevents_next_step']=guard.stopped and sim.curr_time==before
        (out/'report.json').write_text(json.dumps(report,indent=2));print(json.dumps(report,indent=2))
    finally:
        (out/'telemetry.json').write_text(json.dumps(rows))
        with gzip.open(out/'guard_events.full.json.gz','wt',encoding='utf8') as stream:json.dump(guard.events,stream)
        (out/'guard_events.json').write_text(json.dumps(dict(observations=len(guard.events),
            first=guard.events[0],last=guard.events[-1],
            non_continue_events=[e for e in guard.events if e['status']!='CONTINUE']),indent=2))
        if states:np.savez_compressed(out/'replay.npz',time_s=[s[0] for s in states],qpos=[s[1] for s in states],qvel=[s[2] for s in states],act=[s[3] for s in states])
        sim.close()


if __name__=='__main__':main()

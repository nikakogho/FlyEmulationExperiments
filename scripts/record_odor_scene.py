"""Mechanical 3D odor-interface audit; no brain construction or neural steps."""
import os
os.environ.setdefault('NUMBA_NUM_THREADS','2');os.environ.setdefault('OMP_NUM_THREADS','2')
from pathlib import Path
import sys,json,time
ROOT=Path(__file__).resolve().parents[1];sys.path.insert(0,str(ROOT))
import numpy as np
from flygym import Fly
from flyplasticity.standing import StandingController
from flyplasticity.odor_scene import make_arena,SENSOR_NAMES
from flyplasticity.welfare import Guard,Limits,Sample
from deliver_arena import scripted_drive

def main():
    import argparse
    ap=argparse.ArgumentParser(description=__doc__);ap.add_argument('--out',default='results/odor_scene_v2');args=ap.parse_args()
    out=ROOT/args.out;out.mkdir(exist_ok=False)
    arena,field=make_arena()
    fly=Fly(enable_adhesion=True,enable_olfaction=True,spawn_pos=(0,0,.2),
            contact_sensor_placements=[f'{l}{s}' for l in ['LF','LM','LH','RF','RM','RH']
                                      for s in ['Tibia','Tarsus1','Tarsus2','Tarsus3','Tarsus4','Tarsus5']])
    names=tuple(fly.config['olfaction']['sensor_positions'])
    if names!=SENSOR_NAMES:raise ValueError('Sensor ordering changed')
    sim=StandingController(fly=fly,arena=arena,cameras=[],timestep=.0001,seed=101)
    guard=Guard(Limits(2.80001,.000101,1.3,.1));frames=[];rows=[];start=time.perf_counter()
    try:
        obs,_=sim.reset(seed=101);sim.physics.model.save_binary(str(out/'scene.mjb'))
        for k in range(28000):
            t=k*.0001;command=scripted_drive(t)
            sample=Sample(t,float(max(command)),bool(np.isfinite(sim.physics.get_state()).all()),True,False,False)
            obs,_,terminated,truncated,_=guard.advance(sample,lambda:sim.step(command))
            if terminated or truncated:raise RuntimeError('Physics ended early')
            if k%100==0:
                p=np.asarray(sim.physics.bind(fly._antennae_sensors).sensordata).reshape(4,3)
                expected=field.sample(p);actual=np.asarray(obs['odor_intensity'])
                if not np.allclose(expected,actual,atol=1e-7,rtol=0):raise RuntimeError('Odor geometry mismatch')
                heading=np.asarray(obs['fly_orientation'][:2]);heading=heading/np.linalg.norm(heading)
                lateral=np.array([-heading[1],heading[0]])
                legacy=np.array([obs['fly'][0,:2]+1.5*heading+1.2*lateral,
                                 obs['fly'][0,:2]+1.5*heading-1.2*lateral])
                rows.append(dict(time_s=sim.curr_time,xyz=obs['fly'][0].tolist(),command=command.tolist(),
                                 sensor_positions_mm=p.tolist(),odor=actual.tolist(),
                                 old_proxy_position_rmse_mm=float(np.sqrt(np.mean((legacy-p[2:,:2])**2))),
                                 field_error=float(np.max(np.abs(expected-actual))),speed_mm_s=float(np.linalg.norm(obs['fly'][1,:2]))))
                frames.append((sim.curr_time,sim.physics.data.qpos.copy(),sim.physics.data.qvel.copy(),sim.physics.data.act.copy()))
            if k%7000==0:print(f'Odor-scene mechanical test {t:.1f}/2.8 s',flush=True)
        rest=[r for r in rows if r['time_s']>2.5]
        report=dict(completed=True,neural_steps=0,learning_demonstrated=False,control='fixed mechanical script',
                    frames=len(frames),physics_steps=28000,max_field_error=max(r['field_error'] for r in rows),
                    median_old_proxy_position_rmse_mm=float(np.median([r['old_proxy_position_rmse_mm'] for r in rows])),
                    median_actual_antenna_separation_mm=float(np.median([np.linalg.norm(np.array(r['sensor_positions_mm'])[2]-np.array(r['sensor_positions_mm'])[3]) for r in rows])),
                    rest_median_speed_mm_s=float(np.median([r['speed_mm_s'] for r in rest])),
                    sources_mm=field.sources.tolist(),sensor_names=names,wall_seconds=time.perf_counter()-start,
                    limitation='Gaussian field and mesh sensor sites are engineering approximations, not calibrated odor physiology')
        report['passed']=report['max_field_error']<1e-7 and report['rest_median_speed_mm_s']<.5
        (out/'report.json').write_text(json.dumps(report,indent=2));print(json.dumps(report,indent=2))
    finally:
        (out/'telemetry.json').write_text('[\n'+',\n'.join(json.dumps(r) for r in rows)+'\n]')
        if frames:np.savez_compressed(out/'replay.npz',time_s=[r[0] for r in frames],qpos=[r[1] for r in frames],qvel=[r[2] for r in frames],act=[r[3] for r in frames])
        sim.close()

if __name__=='__main__':main()

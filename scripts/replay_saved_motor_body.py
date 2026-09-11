"""Mechanical diagnostic driven by archived commands. No neural simulation."""
import os
os.environ.setdefault('NUMBA_NUM_THREADS','2');os.environ.setdefault('OMP_NUM_THREADS','2')
from pathlib import Path
import sys,json,hashlib
import numpy as np
ROOT=Path(__file__).resolve().parents[1];sys.path.insert(0,str(ROOT))
from flygym import Fly
from flyplasticity.standing import StandingController


def run(arm,cue,out):
    out.mkdir(exist_ok=False)
    source=ROOT/f'results/saved_motor_readout_v1/seed311_A_{arm}.json'
    tape=[r for r in json.loads(source.read_text()) if r['phase']=='post_'+cue]
    if len(tape)!=50:raise ValueError('Expected exactly 250ms archived probe')
    commands=np.array([r['command'] for r in tape])
    if not np.isfinite(commands).all() or np.any(commands<0) or np.any(commands>1):raise ValueError('Invalid command tape')
    fly=Fly(enable_adhesion=True,spawn_pos=(0,0,.2),contact_sensor_placements=[f'{l}{s}'
        for l in ['LF','LM','LH','RF','RM','RH']
        for s in ['Tibia','Tarsus1','Tarsus2','Tarsus3','Tarsus4','Tarsus5']])
    sim=StandingController(fly=fly,cameras=[],timestep=.0001,seed=101)
    obs,_=sim.reset(seed=101);frames=[];rows=[];error=None
    try:
        for k in range(3000):
            obs,_,ended,truncated,_=sim.step([0.,0.])
            if ended or truncated or not np.isfinite(sim.physics.get_state()).all():raise RuntimeError('Mechanical settling failed')
        sim.physics.model.save_binary(str(out/'scene.mjb'))
        for k in range(151):
            u=commands[k] if k<50 else np.zeros(2)
            rows.append(dict(time_s=k*.005,xyz=obs['fly'][0].tolist(),
                speed_mm_s=float(np.linalg.norm(obs['fly'][1,:2])),command=u.tolist()))
            frames.append((k*.005,sim.physics.data.qpos.copy(),sim.physics.data.qvel.copy(),sim.physics.data.act.copy()))
            if k==150:break
            for j in range(50):
                obs,_,ended,truncated,_=sim.step(u)
                if ended or truncated or not np.isfinite(sim.physics.get_state()).all():raise RuntimeError('Mechanical physics failed')
    except (ValueError,RuntimeError) as exc:error=str(exc)
    finally:
        sim.close()
        if frames:np.savez_compressed(out/'replay.npz',time_s=[r[0] for r in frames],qpos=[r[1] for r in frames],qvel=[r[2] for r in frames],act=[r[3] for r in frames])
        report=dict(status='completed' if error is None else 'failed',error=error,arm=arm,cue=cue,
            body_run=False,archived_command_playback=True,new_neural_steps=0,
            source=str(source.relative_to(ROOT)),source_sha256=hashlib.sha256(source.read_bytes()).hexdigest(),
            scope='Mechanical playback of stationary neural archive; no live brain, learning, or sensory feedback',
            mean_probe_speed_mm_s=float(np.mean([r['speed_mm_s'] for r in rows if 0<r['time_s']<=.25])) if rows else None,
            probe_displacement_mm=float(np.linalg.norm(np.array(rows[50]['xyz'])[:2]-np.array(rows[0]['xyz'])[:2])) if len(rows)>50 else None,
            final_speed_mm_s=rows[-1]['speed_mm_s'] if rows else None,
            final_rest_pass=bool(len(rows)==151 and rows[-1]['speed_mm_s']<.5))
        (out/'report.json').write_text(json.dumps(report,indent=2))
        (out/'telemetry.json').write_text('[\n'+',\n'.join(json.dumps(r,separators=(',',':')) for r in rows)+'\n]')
        print(json.dumps(report),flush=True)
    return report


def main():
    out=ROOT/'results/saved_motor_body_v1';out.mkdir(exist_ok=False);reports={}
    for cue in ('A','B'):
        for arm in ('paired','unpaired','frozen'):
            report=run(arm,cue,out/f'{cue}_{arm}');reports[f'{cue}_{arm}']=report
            if report['status']!='completed':break
        if report['status']!='completed':break
    result=dict(new_neural_steps=0,reports=reports,
        mechanical_checks_passed=len(reports)==6 and all(r['status']=='completed' and r['final_rest_pass'] for r in reports.values()),
        learned_navigation_demonstrated=False,closed_loop_learning_demonstrated=False)
    if len(reports)==6:
        v={k:r['mean_probe_speed_mm_s'] for k,r in reports.items()}
        result['descriptive_speed_changes']={cue:{arm:1-v[f'{cue}_paired']/v[f'{cue}_{arm}']
            for arm in ('unpaired','frozen')} for cue in ('A','B')}
    (out/'assessment.json').write_text(json.dumps(result,indent=2))

if __name__=='__main__':main()

"""Controlled 3D neural-to-speed coupling. Not a navigation controller."""
import os
os.environ.setdefault('NUMBA_NUM_THREADS','2');os.environ.setdefault('OMP_NUM_THREADS','2')
from pathlib import Path
import sys,json,hashlib
ROOT=Path(__file__).resolve().parents[1];sys.path.insert(0,str(ROOT))
import numpy as np,brian2 as br
from flygym import Fly
from flygym.arena import OdorArena
from flyplasticity.odor_scene import OdorField
from flyplasticity.standing import StandingController
from flyplasticity.neural_speed import NeuralSpeed
from flyplasticity.behavior_monitor import BehaviorMonitor
from flyplasticity.learning_preflight import FixedPathwayAudit,NeuralPreflightGuard
from controlled_association import build
from olfactory_interface import transport_for

def run(arm,cue,out):
    out.mkdir(exist_ok=False);sources=np.array([[6.,0.,1.]])
    peaks=np.array([[1.,0.]]) if cue=='A' else np.array([[0.,1.]])
    field=OdorField(sources,peaks)
    arena=OdorArena(odor_source=sources,peak_odor_intensity=peaks,diffuse_func=lambda d:np.exp(-d*d/72.),
                    marker_colors=[(.15,.65,.85,1) if cue=='A' else (.95,.65,.15,1)],marker_size=.4)
    for geom in arena.root_element.find_all('geom'):
        if 'odor_source_marker' in str(getattr(geom.parent,'name','')):geom.contype=0;geom.conaffinity=0
    fly=Fly(enable_adhesion=True,enable_olfaction=True,spawn_pos=(0,0,.2),
            contact_sensor_placements=[f'{l}{s}' for l in ['LF','LM','LH','RF','RM','RH']
                                      for s in ['Tibia','Tarsus1','Tarsus2','Tarsus3','Tarsus4','Tarsus5']])
    sim=StandingController(fly=fly,arena=arena,cameras=[],timestep=.0001,seed=101)
    obs,_=sim.reset(seed=101)
    for k in range(3000):
        obs,_,ended,truncated,_=sim.step([0.,0.])
        if ended or truncated or not np.isfinite(sim.physics.get_state()).all():raise RuntimeError('Mechanical setup failure before neural construction')
    physical_origin=sim.curr_time
    brain,pre,post,w,*rest=build(311);output=rest[3]
    checkpoint=ROOT/f'results/association_validation_v1/seed311_A/{arm}/network_state.pkl'
    brain.net.restore('terminal',filename=str(checkpoint),restore_random_state=True)
    neural_origin=float(brain.net.t/br.second);w=np.array(brain.syn.w[:])
    bridge,drive_idx,anatomy=transport_for(brain)
    audit=FixedPathwayAudit(len(brain.neu),brain.g['ppl1'],pre,post,w,modulatory_sources=())
    guard=NeuralPreflightGuard(len(brain.neu),brain.g['ppl1'],duration_s=2.,pathways=audit)
    behavior=BehaviorMonitor();motor=NeuralSpeed(len(output))
    previous=np.array(brain.spk.count[:]);rows=[];frames=[];error=None;status='running'
    sim.physics.model.save_binary(str(out/'scene.mjb'))
    metadata=dict(arm=arm,cue=cue,checkpoint=str(checkpoint.relative_to(ROOT)),
                  checkpoint_sha256=hashlib.sha256(checkpoint.read_bytes()).hexdigest(),
                  protocol_sha256=hashlib.sha256((ROOT/'research/embodied_speed_protocol.md').read_bytes()).hexdigest(),
                  neural_origin=neural_origin,physical_origin=physical_origin,unknown_side_inputs=bridge.unknown_sides,
                  controller='Fixed scalar MBON-to-equal-gait command, no direction or coordinates',learning_in_body=False)
    (out/'metadata.json').write_text(json.dumps(metadata,indent=2))
    try:
        for k in range(401):
            t=k*.005
            if abs(float(brain.net.t/br.second)-neural_origin-t)>1e-8 or abs(sim.curr_time-physical_origin-t)>1e-8:
                raise RuntimeError('Coupled clocks disagree')
            p=np.asarray(sim.physics.bind(fly._antennae_sensors).sensordata).reshape(4,3)
            scent=field.sample(p)
            if not np.allclose(scent,obs['odor_intensity'],atol=1e-7,rtol=0):raise RuntimeError('Sensory geometry mismatch')
            enabled=50<=k<240;delivered=scent if enabled else np.zeros((2,4))
            rates=np.zeros(len(brain.tgt));rates[drive_idx]=bridge.rates(delivered,t,t)
            brain.pg.rates=rates*br.Hz
            counts=np.array(brain.spk.count[:]);delta=counts-previous;previous=counts
            row=guard.inspect(t,delta,np.array(brain.neu.v[:]),np.array(brain.neu.g[:]),np.array(brain.pg.rates[:]/br.Hz),[0.],
                              pre=np.array(brain.syn.i[:]),post=np.array(brain.syn.j[:]),weights=np.array(brain.syn.w[:]),modulatory_sources=())
            command=motor.step(delta[output])
            if k<70 or k>=240:command=np.zeros(2)
            row.update(mbon01_spikes=int(delta[output].sum()),filtered_output_hz=motor.rate_hz)
            # Physical motion at t resulted from the previous command, not the new one.
            prior=rows[-1]['command'] if rows else [0.,0.]
            body=dict(time_s=t,xyz=obs['fly'][0].tolist(),speed_mm_s=float(np.linalg.norm(obs['fly'][1,:2])),
                      command=command.tolist(),odor=delivered.tolist(),sensor_positions_mm=p.tolist(),
                      filtered_output_hz=motor.rate_hz,mbon01_spikes=int(delta[output].sum()))
            rows.append(body)
            frames.append((t,sim.physics.data.qpos.copy(),sim.physics.data.qvel.copy(),sim.physics.data.act.copy()))
            behavior.observe(t,body['xyz'],prior,delivered,stimulus_enabled=enabled)
            if k==400:
                if any(r['total_spikes'] for r in guard.rows[-10:]) or body['speed_mm_s']>=.5:raise RuntimeError('Final recovery failed')
                break
            brain.net.run(.005*br.second,namespace={})
            for sub in range(50):
                obs,_,ended,truncated,_=sim.step(command)
                if ended or truncated or not np.isfinite(sim.physics.get_state()).all():raise RuntimeError('Physics failed')
            if k%100==0:print(f'{cue}/{arm}: {t:.2f}s',flush=True)
        status='completed'
    except (RuntimeError,ValueError) as exc:
        status='stopped';error=str(exc)
        if not guard.guard.stopped:guard.guard._stop('embodied_execution_stop',float(brain.net.t/br.second)-neural_origin)
    finally:
        brain.net.store('terminal',filename=str(out/'network_state.pkl'))
        if frames:np.savez_compressed(out/'replay.npz',time_s=[r[0] for r in frames],qpos=[r[1] for r in frames],qvel=[r[2] for r in frames],act=[r[3] for r in frames])
        window=[r['speed_mm_s'] for r in rows if .65<=r['time_s']<=1.15]
        report=dict(status=status,error=error,completed=status=='completed',arm=arm,cue=cue,
                    neural_time_s=float(brain.net.t/br.second)-neural_origin,body_time_s=sim.curr_time-physical_origin,
                    median_probe_speed_mm_s=float(np.median(window)) if window else None,
                    weights_unchanged=bool(np.array_equal(w,np.array(brain.syn.w[:]))),
                    stopped=guard.guard.stopped or behavior.stopped,behavior_stop=behavior.reason,
                    sources_mm=sources.tolist(),body_run=True,learning_demonstrated=False,
                    scope='Conditioned slowing test, not navigation; learning occurred in prior stationary assay',
                    subjective_welfare='not established')
        for name,obj in [('report',report),('telemetry',rows),('neural_telemetry',guard.rows),('guard_events',guard.guard.events)]:
            (out/(name+'.json')).write_text(json.dumps(obj,separators=(',',':')))
        sim.close();print(json.dumps(report,indent=2),flush=True)
    return report

def main():
    if not json.loads((ROOT/'results/association_validation_v1/assessment.json').read_text())['passed']:
        raise SystemExit('Independent learning validation required')
    out=ROOT/'results/embodied_speed_v1';out.mkdir(exist_ok=False);reports={};stopped=False
    for cue in ('A','B'):
        for arm in ('paired','unpaired','frozen'):
            report=run(arm,cue,out/f'{cue}_{arm}');reports[f'{cue}_{arm}']=report
            if report['status']!='completed':stopped=True;break
        if stopped:break
    result=dict(passed=False,reports=reports,welfare_or_execution_stop=stopped)
    if not stopped:
        v={k:r['median_probe_speed_mm_s'] for k,r in reports.items()}
        if min(v.values())>0:
            a=1-v['A_paired']/v['A_frozen'];b=1-v['B_paired']/v['B_frozen']
            criteria=dict(paired_A_vs_frozen=a>=.05,paired_A_vs_unpaired=1-v['A_paired']/v['A_unpaired']>=.05,
                          cue_specific_slowing=a-b>=.05)
            result.update(passed=all(criteria.values()),criteria=criteria,A_slowing=a,B_slowing=b)
    (out/'assessment.json').write_text(json.dumps(result,indent=2));print(json.dumps(result,indent=2))

if __name__=='__main__':main()

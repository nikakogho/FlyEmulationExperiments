"""Frozen, bounded live preference cohort. Every hard stop cancels the cohort."""
import os
os.environ.setdefault('NUMBA_NUM_THREADS','2');os.environ.setdefault('OMP_NUM_THREADS','2')
from pathlib import Path
import sys,json,hashlib,pickle
ROOT=Path(__file__).resolve().parents[1];sys.path.insert(0,str(ROOT))
import numpy as np,brian2 as br
from controlled_association import build,run_arm
from olfactory_interface import transport_for
from hybrid_fixture import make_fixture,advance,observe,save_tapes,frame
from flyplasticity.hybrid_navigation import HybridNavigation
from flyplasticity.behavior_review import ReviewedBehaviorMonitor
from flyplasticity.learning_preflight import FixedPathwayAudit,NeuralPreflightGuard
from flyplasticity.preference_evaluation import preference,assess
from flyplasticity.checkpoint_identity import input_group_name,equivalent

CASES=((315,'A',False,.6),(315,'B',False,.6),(316,'A',True,-.6),(316,'B',True,-.6))
PROTOCOL='research/hybrid_preference_protocol.md'
MANIFEST='results/hybrid_preference_admission_v2.json'
SOURCES=[PROTOCOL,'scripts/run_hybrid_preference.py','scripts/controlled_association.py',
    'scripts/hybrid_fixture.py','scripts/olfactory_interface.py','flyplasticity/hybrid_navigation.py',
    'flyplasticity/behavior_review.py','flyplasticity/visual_markers.py','flyplasticity/preference_evaluation.py',
    'flyplasticity/association.py','flyplasticity/learning_preflight.py','flyplasticity/odor_scene.py',
    'flyplasticity/standing.py','flyplasticity/compartment_plasticity.py','flyplasticity/light_task.py','flyplasticity/welfare.py',
    'flyplasticity/checkpoint_identity.py','research/hybrid_checkpoint_amendment.md']


def verify_manifest():
    manifest=json.loads((ROOT/MANIFEST).read_text())
    for path,digest in manifest['source_sha256'].items():
        if hashlib.sha256((ROOT/path).read_bytes()).hexdigest()!=digest:raise ValueError('Frozen source changed: '+path)
    if not json.loads((ROOT/'results/hybrid_mechanics_v2/assessment.json').read_text())['passed']:
        raise ValueError('Final mechanical qualification required')
    return manifest


def probe(checkpoint,out,seed,reinforced,swapped,heading,label):
    out.mkdir(exist_ok=False);arena,fly,sim,obs=make_fixture(heading,swapped);physical_origin=sim.curr_time
    state=pickle.loads(checkpoint.read_bytes())
    brain,pre,post,_,*rest=build(seed,input_group_name=input_group_name(state));output=rest[3]
    brain.net.restore('terminal',filename=str(checkpoint),restore_random_state=True)
    origin=float(brain.net.t/br.second);weights=np.array(brain.syn.w[:])
    bridge,drive_idx,_=transport_for(brain)
    paths=FixedPathwayAudit(len(brain.neu),brain.g['ppl1'],pre,post,weights,modulatory_sources=())
    guard=NeuralPreflightGuard(len(brain.neu),brain.g['ppl1'],duration_s=3.,pathways=paths)
    monitor=ReviewedBehaviorMonitor();motor=HybridNavigation();previous=np.array(brain.spk.count[:])
    prior=[0.,0.];rows=[];frames=[];error=None;recovery=False;status='running'
    sim.physics.model.save_binary(str(out/'scene.mjb'))
    (out/'metadata.json').write_text(json.dumps(dict(checkpoint=str(checkpoint.relative_to(ROOT)),
        checkpoint_sha256=hashlib.sha256(checkpoint.read_bytes()).hexdigest(),neural_origin=origin,
        physical_origin=physical_origin,seed=seed,reinforced=reinforced,label=label,
        source_manifest=MANIFEST,unknown_side_ORNs=bridge.unknown_sides,
        learning_during_retrieval=False),indent=2))
    try:
        for k in range(601):
            t=k*.005
            if abs(float(brain.net.t/br.second)-origin-t)>1e-8 or abs(sim.curr_time-physical_origin-t)>1e-8:
                raise RuntimeError('Coupled clocks disagree')
            arena.enabled=50<=k<450;body=observe(arena,fly,sim,obs)
            rates=np.zeros(len(brain.tgt));rates[drive_idx]=bridge.rates(body['odor'],t,t);brain.pg.rates=rates*br.Hz
            actual=np.array(brain.pg.rates[:]/br.Hz)
            if not np.array_equal(rates,actual):raise RuntimeError('Delivered sensory drive mismatch')
            counts=np.array(brain.spk.count[:]);delta=counts-previous;previous=counts
            nrow=guard.inspect(t,delta,np.array(brain.neu.v[:]),np.array(brain.neu.g[:]),actual,[0.],
                pre=np.array(brain.syn.i[:]),post=np.array(brain.syn.j[:]),weights=np.array(brain.syn.w[:]),modulatory_sources=())
            load=float(np.asarray(body['odor'])[:,2:].mean(axis=1).sum())
            u=motor.step(delta[output],body['heading'],body['wind'],load)
            if not arena.enabled:u=np.zeros(2)
            nrow.update(mbon01_spikes=int(delta[output].sum()),filtered_mbon_hz=motor.rate_hz)
            body.update(time_s=t,command=u.tolist(),stimulus_enabled=arena.enabled,mbon01_spikes=int(delta[output].sum()),filtered_mbon_hz=motor.rate_hz)
            rows.append(body);frames.append(frame(t,sim))
            body['behavior']=monitor.observe(t,body['xyz'],body['heading'],prior,body['odor'],body['gradients'],stimulus_enabled=arena.enabled)
            if k==600:
                recovery=not any(r['total_spikes'] for r in guard.rows[-10:]) and body['speed_mm_s']<.5
                if not recovery:raise RuntimeError('Final recovery failed')
                break
            brain.net.run(.005*br.second,namespace={});obs=advance(sim,u);prior=u
            if k%200==0:print(f'{out.parent.name}/{label}: {t:.2f}s',flush=True)
        status='completed'
    except (RuntimeError,ValueError) as exc:
        status='stopped';error=str(exc)
        if rows:rows[-1]['behavior']=monitor.last_result
        if not guard.guard.stopped:guard.guard._stop('hybrid_execution_stop',float(brain.net.t/br.second)-origin)
    finally:
        brain.net.store('terminal',filename=str(out/'network_state.pkl'));sim.close();save_tapes(out,rows,frames)
        outcome=None
        if status=='completed':
            try:outcome=preference(rows,reinforced)
            except ValueError:pass
        report=dict(status=status,completed=status=='completed',error=error,recovery_pass=bool(recovery),
            label=label,body_run=True,hybrid_preference=True,weights_unchanged=bool(np.array_equal(weights,np.array(brain.syn.w[:]))),
            neural_time_s=float(brain.net.t/br.second)-origin,body_time_s=sim.curr_time-physical_origin,
            sources_mm=arena.field.sources.tolist(),reinforced=reinforced,swapped=swapped,preference=outcome,
            displacement_mm=float(np.linalg.norm(np.array(rows[-1]['xyz'])[:2]-np.array(rows[0]['xyz'])[:2])) if rows else 0,
            subjective_welfare='unassessed',scope='Live olfactory-memory/engineering-navigation hybrid; no learning during retrieval')
        for name,obj in [('report',report),('neural_telemetry',guard.rows),('guard_events',guard.guard.events)]:
            text='[\n'+',\n'.join(json.dumps(r,separators=(',',':')) for r in obj)+'\n]' if isinstance(obj,list) else json.dumps(obj,indent=2)
            (out/(name+'.json')).write_text(text)
        print(json.dumps(report),flush=True)
    return report


def main():
    import argparse
    ap=argparse.ArgumentParser();ap.add_argument('--freeze',action='store_true');ap.add_argument('--resume-bookkeeping',action='store_true');args=ap.parse_args()
    if args.freeze:
        p=ROOT/MANIFEST
        if p.exists():raise ValueError('Admission already frozen')
        p.write_text(json.dumps(dict(protocol=PROTOCOL,cases=CASES,max_neural_seconds=96,
            source_sha256={s:hashlib.sha256((ROOT/s).read_bytes()).hexdigest() for s in SOURCES}),indent=2));return
    verify_manifest();out=ROOT/'results/hybrid_preference_v1';cases=[];stop=False
    if args.resume_bookkeeping:
        old=json.loads((out/'assessment.json').read_text());error=json.loads((out/'execution_error.json').read_text())
        if (error['error']!="ValueError('Shared baseline checkpoint differs across arms')" or len(old['cases'])!=1
            or old['cases'][0]['probes'] or set(old['cases'][0]['training'])!={'paired','unpaired','frozen'}
            or not all(r['status']=='completed' and r['recovery_pass'] for r in old['cases'][0]['training'].values())):
            raise ValueError('Only the reviewed between-run bookkeeping interruption may resume')
        first=out/'seed315_A'
        for arm in ('paired','unpaired','frozen'):
            events=json.loads((first/f'train_{arm}/guard_events.json').read_text())
            if any(e.get('status')=='STOP' for e in events):raise ValueError('A neural guard fired; resumption forbidden')
        archive=out/'checkpoint_interruption.json'
        if archive.exists():raise ValueError('Bookkeeping resumption was already attempted')
        archive.write_text(json.dumps(dict(assessment=old,error=error),indent=2));cases=old['cases']
    else:out.mkdir(exist_ok=False)
    try:
        for seed,cue,swapped,heading in CASES:
            p=out/f'seed{seed}_{cue}'
            existing=[c for c in cases if c['seed']==seed and c['reinforced']==cue]
            if existing:case=existing[0]
            else:
                p.mkdir();case=dict(seed=seed,reinforced=cue,training={},probes={});cases.append(case)
            for arm in ('paired','unpaired','frozen'):
                if arm in case['training']:continue
                verify_manifest();case['training'][arm]=run_arm(arm,p/f'train_{arm}',seed,cue,PROTOCOL,save_pre_state=True)
                if case['training'][arm]['status']!='completed':stop=True;break
            if stop:break
            states=[pickle.loads((p/f'train_{arm}/pre_state.pkl').read_bytes()) for arm in ('paired','unpaired','frozen')]
            if not all(equivalent(states[0],state) for state in states[1:]):raise ValueError('Actual baseline neural state differs across arms')
            for label in ('pre','paired','unpaired','frozen'):
                verify_manifest();checkpoint=p/('train_paired/pre_state.pkl' if label=='pre' else f'train_{label}/network_state.pkl')
                case['probes'][label]=probe(checkpoint,p/label,seed,cue,swapped,heading,label)
                if case['probes'][label]['status']!='completed':stop=True;break
            (p/'assessment.json').write_text(json.dumps(case,indent=2))
            if stop:break
    except Exception as exc:
        stop=True;(out/'execution_error.json').write_text(json.dumps(dict(error=repr(exc)),indent=2));raise
    finally:
        result=assess(cases);result.update(cases=cases,welfare_or_execution_stop=stop,
            conditional_rule_comparison_allowed=result['passed'] and not stop,
            bookkeeping_interruption_preserved=(out/'checkpoint_interruption.json').exists())
        (out/'assessment.json').write_text(json.dumps(result,indent=2));print(json.dumps({k:v for k,v in result.items() if k!='cases'}),flush=True)

if __name__=='__main__':main()

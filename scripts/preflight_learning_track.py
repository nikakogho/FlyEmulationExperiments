"""One guarded, continuous olfactory exposure. Never calls legacy train/reset."""
from pathlib import Path
import sys,json,importlib.util,hashlib
ROOT=Path(__file__).resolve().parents[1];sys.path.insert(0,str(ROOT))
import numpy as np,pandas as pd,brian2 as br
from flyplasticity.learning_preflight import NeuralPreflightGuard, FixedPathwayAudit


def main():
    import argparse
    ap=argparse.ArgumentParser(description=__doc__)
    ap.add_argument('--out',default='results/learning_track_preflight_v2')
    ap.add_argument('--audit-only',action='store_true',help='Inspect old saved counts; zero neural steps')
    args=ap.parse_args()
    out=ROOT/args.out;out.mkdir(exist_ok=False)
    br.prefs.codegen.target='numpy'
    path=ROOT/'upstream/fly-api/experiments/navigation/nav_demo.py'
    reviewed={
        path:'22e83d60e8d6b2ca0e40e14bf69ba511e491a28bab89a0a6160eb36b539a38dc',
        ROOT/'upstream/fly-api/experiments/learning/model_ext.py':'ad7b85da4411c91e3a3f556e5fcdd648d87c2e481a60f5e826248f5054467932',
        ROOT/'upstream/Drosophila_brain_model/model.py':'b879a8a286f367165e3effa6d47562cac289333c977be7716ccb646067326cce'}
    for source,expected in reviewed.items():
        if hashlib.sha256(source.read_bytes()).hexdigest()!=expected:
            raise ValueError('Unreviewed source changes: '+str(source))
    spec=importlib.util.spec_from_file_location('guarded_nav',path);nav=importlib.util.module_from_spec(spec);spec.loader.exec_module(nav)
    nav.ANN=str(ROOT/'data/annotations.tsv')
    sys.path.insert(0,str(ROOT/'upstream/fly-api/experiments/learning'))
    import model_ext
    original=model_ext.build_subnet;mapping={}
    def capture(*a,**kw):
        result=original(*a,**kw);mapping.update(result[-1]);return result
    model_ext.build_subnet=capture
    try:brain=nav.Brain(str(ROOT/'upstream/Drosophila_brain_model'),seed=310)
    finally:model_ext.build_subnet=original
    ann=pd.read_csv(ROOT/'data/annotations.tsv',sep='\t',low_memory=False).set_index('root_id')
    comp=pd.read_csv(ROOT/'upstream/Drosophila_brain_model/Completeness_783.csv',index_col=0)
    local={new:(str(comp.index[old]),ann.loc[comp.index[old]]) for old,new in mapping.items() if comp.index[old] in ann.index}
    output=np.array([i for i,(_,row) in local.items() if row.cell_type=='MBON01'],dtype=int)
    pam=np.array([i for i,(_,row) in local.items() if row.cell_type=='PAM01'],dtype=int)
    pre=np.array(brain.syn.i[:]);post=np.array(brain.syn.j[:]);weights=np.array(brain.syn.w[:])
    if not np.isfinite(weights).all():raise ValueError('Nonfinite initial synaptic weights')
    plastic=np.flatnonzero(np.isin(pre,brain.g['kc'])&np.isin(post,output)&(weights>0))
    if not len(output) or not len(pam) or not len(plastic):raise ValueError('Missing named learning interface')
    metadata=dict(neurons=len(brain.neu),synapses=len(weights),output_root_ids=[local[i][0] for i in output],
                  pam_root_ids=[local[i][0] for i in pam],candidate_plastic_edges=len(plastic),
                  named_output='MBON01',modulator='PAM01',learning_enabled=False,body_instantiated=False,
                  source_nav_sha256=hashlib.sha256(path.read_bytes()).hexdigest(),
                  protocol_sha256=hashlib.sha256((ROOT/'research/learning_track_protocol_v2.md').read_bytes()).hexdigest(),
                  reviewed_sources={str(p.relative_to(ROOT)):h for p,h in reviewed.items()})
    (out/'metadata.json').write_text(json.dumps(metadata,indent=2))
    routes=FixedPathwayAudit(len(brain.neu),brain.g['ppl1'],pre,post,weights,modulatory_sources=())
    if args.audit_only:
        old=ROOT/'results/learning_track_preflight'
        saved=np.load(old/'terminal_state.npz')
        old_report=json.loads((old/'report.json').read_text())
        if not old_report['all_synaptic_weights_unchanged']:
            raise ValueError('Historical weights cannot be inferred')
        report=dict(neural_steps=0,old_total_ppl1_spikes=int(saved['counts'][brain.g['ppl1']].sum()),
                    old_spikes_with_enabled_route=routes.inspect(saved['counts'],pre,post,weights,()),
                    ppl1_outgoing_edges=int(np.isin(pre,brain.g['ppl1']).sum()),
                    enabled_ppl1_sources=routes.watched_enabled.tolist(),extra_modulation_routes=[],
                    basis='Reconstructed runtime weights and unchanged-weight historical report; not exact state replay',
                    subjective_welfare='not established')
        (out/'audit.json').write_text(json.dumps(report,indent=2));print(json.dumps(report,indent=2));return
    guard=NeuralPreflightGuard(len(brain.neu),brain.g['ppl1'],pathways=routes)
    previous=np.zeros(len(brain.neu),dtype=np.int64)
    rows=[];status='running';blocks=0
    try:
        for block in range(201):
            t=block*.005;rates=np.zeros(len(brain.tgt))
            if .25<=t<.5:
                for i in brain.A:rates[brain.pos[i]]=500.
            counts=np.array(brain.spk.count[:],dtype=np.int64);delta=counts-previous;previous=counts
            if abs(float(brain.net.t/br.second)-t)>1e-9:raise RuntimeError('Neural clock mismatch')
            brain.pg.rates=rates*br.Hz
            actual_rates=np.array(brain.pg.rates[:]/br.Hz)
            reward_rates=actual_rates[[brain.pos[i] for i in pam]]
            row=guard.inspect(t,delta,np.array(brain.neu.v[:]),np.array(brain.neu.g[:]),actual_rates,reward_rates,
                              pre=np.array(brain.syn.i[:]),post=np.array(brain.syn.j[:]),
                              weights=np.array(brain.syn.w[:]),modulatory_sources=())
            row['mbon01_spikes']=int(delta[output].sum());rows.append(row)
            if block==200:break
            brain.net.run(.005*br.second,namespace={});blocks+=1
        status='completed'
    except RuntimeError as exc:status='stopped';error=str(exc)
    finally:
        # Includes Brian2 pending queues and RNG state; no restore or extra steps.
        brain.net.store('terminal',filename=str(out/'network_state.pkl'))
        np.savez_compressed(out/'terminal_state.npz',v=np.array(brain.neu.v[:]),g=np.array(brain.neu.g[:]),counts=np.array(brain.spk.count[:]))
        report=dict(status=status,neural_blocks=blocks,neural_time_s=float(brain.net.t/br.second),
                    all_synaptic_weights_unchanged=bool(np.array_equal(weights,np.array(brain.syn.w[:]))),
                    stopped=guard.guard.stopped,no_automatic_retry=True,learning_run=False,body_run=False,
                    recovery_screen_pass=bool(status=='completed' and guard.rows[-1]['total_spikes']==0),
                    accepted_observation_mbon01_spikes=sum(r.get('mbon01_spikes',0) for r in rows),
                    output_response_spikes=int(np.array(brain.spk.count[:])[output].sum()),
                    error=locals().get('error'),subjective_welfare='not established')
        (out/'report.json').write_text(json.dumps(report,indent=2));(out/'telemetry.json').write_text(json.dumps(guard.rows,indent=2))
        (out/'guard_events.json').write_text(json.dumps(guard.guard.events,indent=2));print(json.dumps(report,indent=2))
    if status!='completed':raise SystemExit(1)


if __name__=='__main__':main()

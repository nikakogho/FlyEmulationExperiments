"""One predeclared three-arm stationary pilot; stop aborts remaining arms."""
from pathlib import Path
import sys,json,hashlib,importlib.util
ROOT=Path(__file__).resolve().parents[1];sys.path.insert(0,str(ROOT))
import numpy as np,pandas as pd,brian2 as br
from flyplasticity.association import GammaEligibilityLTD,PlasticPathwayAudit,schedule,comparison,output_compartments
from flyplasticity.learning_preflight import NeuralPreflightGuard


def build(seed=310,*,input_group_name=None):
    # Reuse the exact source versions approved and recorded in the v2 preflight.
    provenance=json.loads((ROOT/'results/learning_track_preflight_v2/metadata.json').read_text())
    for path,expected in provenance['reviewed_sources'].items():
        if hashlib.sha256((ROOT/path).read_bytes()).hexdigest()!=expected:
            raise ValueError('Upstream source changed: '+path)
    br.start_scope();br.prefs.codegen.target='numpy'
    path=ROOT/'upstream/fly-api/experiments/navigation/nav_demo.py'
    spec=importlib.util.spec_from_file_location('association_nav',path)
    nav=importlib.util.module_from_spec(spec);spec.loader.exec_module(nav)
    original_poisson=br.PoissonGroup
    if input_group_name is not None:
        import re
        if not re.fullmatch(r'poissongroup(?:_\d+)?',input_group_name):raise ValueError('Unrecognized checkpoint input group')
        def named_inputs(*args,**kwargs):
            return original_poisson(*args,**kwargs,name=input_group_name)
        br.PoissonGroup=named_inputs
    nav.ANN=str(ROOT/'data/annotations.tsv')
    sys.path.insert(0,str(ROOT/'upstream/fly-api/experiments/learning'))
    import model_ext
    original=model_ext.build_subnet;mapping={}
    def capture(*a,**kw):
        result=original(*a,**kw);mapping.update(result[-1]);return result
    model_ext.build_subnet=capture
    try:brain=nav.Brain(str(ROOT/'upstream/Drosophila_brain_model'),seed=seed)
    finally:
        model_ext.build_subnet=original
        br.PoissonGroup=original_poisson
    ann=pd.read_csv(ROOT/'data/annotations.tsv',sep='\t',low_memory=False).set_index('root_id')
    comp=pd.read_csv(ROOT/'upstream/Drosophila_brain_model/Completeness_783.csv',index_col=0)
    local={new:ann.loc[comp.index[old]] for old,new in mapping.items()}
    roots={new:str(comp.index[old]) for old,new in mapping.items()}
    output=np.array([i for i,r in local.items() if r.cell_type=='MBON01'],dtype=int)
    pam=np.array([i for i,r in local.items() if r.cell_type=='PAM01'],dtype=int)
    gamma=np.array([i for i,r in local.items() if str(r.cell_type).startswith('KCg-')],dtype=int)
    pre=np.array(brain.syn.i[:]);post=np.array(brain.syn.j[:]);w=np.array(brain.syn.w[:])
    input_sides=output_compartments(pre,post,{i:local[i].side for i in gamma},output)
    positions=[];compartments=[];groups={}
    for label,side in enumerate(('left','right')):
        k=[i for i in gamma if local[i].side==side]
        o=[i for i in output if input_sides[i]==side]
        groups[label]=[i for i in pam if local[i].side==side]
        p=np.flatnonzero(np.isin(pre,k)&np.isin(post,o)&(w>0))
        if not len(p) or not groups[label]:raise ValueError('Missing hemisphere interface')
        positions.extend(p.tolist());compartments.extend([label]*len(p))
    positions=np.array(positions,dtype=int)
    metadata=dict(neurons=len(brain.neu),synapses=len(w),seed=seed,
                  output_root_ids=[roots[i] for i in output],
                  pam_groups={k:[roots[i] for i in v] for k,v in groups.items()},
                  plastic_edges=len(positions),plastic_edges_by_hemisphere={k:compartments.count(k) for k in groups},
                  plastic_source_types=sorted({local[i].cell_type for i in pre[positions]}),
                  output_input_hemispheres={roots[i]:dict(annotation_side=local[i].side,
                                                         gamma_input_side=input_sides[i]) for i in output},
                  pam_side_mapping='Coarse annotation-side assignment; precise bilateral release fields unvalidated',
                  reviewed_sources=provenance['reviewed_sources'])
    return brain,pre,post,w,positions,compartments,groups,output,pam,gamma,metadata


def run_arm(arm,out,seed=310,reinforced='A',protocol='research/association_protocol.md',save_pre_state=False):
    out.mkdir(exist_ok=False)
    brain,pre,post,initial,pos,comps,groups,output,pam,gamma,metadata=build(seed)
    paths=PlasticPathwayAudit(len(brain.neu),brain.g['ppl1'],pre,post,initial,
                             modulatory_sources=pam,plastic_positions=pos,gamma_kcs=gamma,output_neurons=output)
    rule=GammaEligibilityLTD(pre[pos],comps,groups,len(brain.neu),initial[pos])
    guard=NeuralPreflightGuard(len(brain.neu),brain.g['ppl1'],duration_s=4.,pathways=paths)
    previous=np.zeros(len(brain.neu),dtype=np.int64)
    reward_idx=np.array([brain.pos[i] for i in pam]);rows=[];status='running';error=None
    snapshots={'initial':initial[pos].copy()};probe_counts={p:0 for p in ('pre_A','pre_B','post_A','post_B')}
    probe_kc={p:np.zeros(len(brain.neu),dtype=np.int64) for p in probe_counts}
    metadata.update(arm=arm,reinforced=reinforced,learning_enabled=arm!='frozen',additional_modulation_sources='PAM01, hemisphere local',
                    protocol_sha256=hashlib.sha256((ROOT/protocol).read_bytes()).hexdigest(),
                    runner_sha256=hashlib.sha256(Path(__file__).read_bytes()).hexdigest(),
                    rule_sha256=hashlib.sha256((ROOT/'flyplasticity/association.py').read_bytes()).hexdigest())
    (out/'metadata.json').write_text(json.dumps(metadata,indent=2))
    try:
        for block in range(801):
            t=block*.005
            if abs(float(brain.net.t/br.second)-t)>1e-9:raise RuntimeError('Neural clock mismatch')
            cue,reward,phase=schedule(block,arm,reinforced)
            rates=np.zeros(len(brain.tgt))
            if cue:
                rates[[brain.pos[i] for i in getattr(brain,cue)]]=500.
            rates[reward_idx]=reward
            brain.pg.rates=rates*br.Hz
            actual=np.array(brain.pg.rates[:]/br.Hz)
            if not np.array_equal(actual,rates):raise RuntimeError('External drive differs from protocol')
            counts=np.array(brain.spk.count[:],dtype=np.int64);delta=counts-previous;previous=counts
            current=np.array(brain.syn.w[:])
            row=guard.inspect(t,delta,np.array(brain.neu.v[:]),np.array(brain.neu.g[:]),actual,actual[reward_idx],
                              pre=np.array(brain.syn.i[:]),post=np.array(brain.syn.j[:]),weights=current,
                              modulatory_sources=pam,expected_reward_rates=np.full(len(pam),reward))
            observed_phase=schedule(block-1,arm,reinforced)[2] if block else 'initial'
            row.update(observed_phase=observed_phase,next_phase=phase,mbon01_spikes=int(delta[output].sum()),
                       pam01_spikes=int(delta[pam].sum()))
            rows.append(row)
            if observed_phase in probe_counts:
                probe_counts[observed_phase]+=row['mbon01_spikes'];probe_kc[observed_phase]+=delta
            # Predeclared quiet windows: assess BEFORE the next stimulus, never extend.
            if block in (150,250,390,550,650,800):
                if any(r['total_spikes'] for r in rows[-10:]):
                    guard.guard._stop('failed_recovery_screen',t);raise RuntimeError('Failed recovery screen')
            if block==250 and save_pre_state:
                # Snapshot a validated quiet boundary. It is usable for a
                # prospectively declared probe only after this arm completes.
                brain.net.store('terminal',filename=str(out/'pre_state.pkl'))
            if block in (250,550,800):snapshots[str(block)]=current[pos].copy()
            proposed=rule.step(delta,current[pos],frozen=arm=='frozen')
            paths.authorize_update(current,proposed)
            brain.syn.w[pos]=proposed*br.volt
            row['minimum_weight_fraction']=float((proposed/initial[pos]).min())
            row['mean_weight_fraction']=float((proposed/initial[pos]).mean())
            if block==800:break
            brain.net.run(.005*br.second,namespace={})
            if block%200==0:print(f'{arm}: {t:.3f} s',flush=True)
        status='completed'
    except (RuntimeError,ValueError) as exc:
        status='stopped';error=str(exc)
        if not guard.guard.stopped:guard.guard._stop('execution_or_update_error',float(brain.net.t/br.second))
    finally:
        final=np.array(brain.syn.w[:]);mask=np.ones(len(final),dtype=bool);mask[pos]=False
        brain.net.store('terminal',filename=str(out/'network_state.pkl'))
        np.savez_compressed(out/'learning_arrays.npz',**snapshots,final=final[pos],plastic_positions=pos,
                            plastic_pre=pre[pos],plastic_post=post[pos],**probe_kc)
        report=dict(arm=arm,status=status,error=error,neural_time_s=float(brain.net.t/br.second),
                    recovery_pass=bool(status=='completed' and not any(r['total_spikes'] for r in rows[-10:])),
                    probe_spikes=probe_counts,changed_edges=int(np.count_nonzero(initial!=final)),
                    nonplastic_weights_unchanged=bool(np.array_equal(initial[mask],final[mask])),
                    min_weight_fraction=float((final[pos]/initial[pos]).min()),
                    mean_weight_fraction=float((final[pos]/initial[pos]).mean()),
                    total_ppl1_spikes=sum(r['ppl1_spikes'] for r in guard.rows),
                    total_ppl1_spikes_with_enabled_route=sum(r['ppl1_spikes_with_enabled_route'] for r in guard.rows),
                    body_run=False,no_automatic_retry=True,subjective_welfare='not established')
        for name,obj in [('report',report),('telemetry',guard.rows),('guard_events',guard.guard.events)]:
            text=('[\n'+',\n'.join(json.dumps(r,separators=(',',':')) for r in obj)+'\n]') if isinstance(obj,list) else json.dumps(obj,indent=2)
            (out/(name+'.json')).write_text(text)
        print(json.dumps(report,indent=2),flush=True)
    return report


def main():
    import argparse
    ap=argparse.ArgumentParser(description=__doc__)
    ap.add_argument('--out',default='results/controlled_association_v1')
    ap.add_argument('--audit-only',action='store_true');args=ap.parse_args()
    out=ROOT/args.out;out.mkdir(exist_ok=False)
    if args.audit_only:
        b,pre,post,w,pos,comps,groups,output,pam,gamma,meta=build()
        PlasticPathwayAudit(len(b.neu),b.g['ppl1'],pre,post,w,modulatory_sources=pam,
                            plastic_positions=pos,gamma_kcs=gamma,output_neurons=output)
        meta['neural_steps']=0
        (out/'audit.json').write_text(json.dumps(meta,indent=2));print(json.dumps(meta,indent=2));return
    reports={}
    # Predeclared independent controls; a welfare/execution stop cancels the rest.
    for arm in ('paired','unpaired','frozen'):
        reports[arm]=run_arm(arm,out/arm)
        if reports[arm]['status']!='completed':break
    result=comparison(reports);result['arms_executed']=list(reports)
    (out/'comparison.json').write_text(json.dumps(result,indent=2));print(json.dumps(result,indent=2))
    if not result['passed']:raise SystemExit(1)


if __name__=='__main__':main()

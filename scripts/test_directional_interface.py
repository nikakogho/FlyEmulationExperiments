"""Bounded sensory laterality assay; fixed naive circuit and no plasticity."""
from pathlib import Path
import sys,json,hashlib
ROOT=Path(__file__).resolve().parents[1];sys.path.insert(0,str(ROOT))
import numpy as np,brian2 as br
from controlled_association import build
from olfactory_interface import transport_for
from flyplasticity.learning_preflight import FixedPathwayAudit,NeuralPreflightGuard

def run(cue,side,out):
    out.mkdir(exist_ok=False)
    brain,pre,post,w,pos,comps,groups,output,pam,gamma,meta=build(311)
    bridge,drive_idx,anatomy=transport_for(brain)
    roots=meta['output_root_ids']
    # Output order is always physical INPUT hemisphere, not annotation/soma side.
    output=np.array(sorted(output,key=lambda i:meta['output_input_hemispheres'][roots[list(output).index(i)]]['gamma_input_side']))
    audit=FixedPathwayAudit(len(brain.neu),brain.g['ppl1'],pre,post,w,modulatory_sources=())
    guard=NeuralPreflightGuard(len(brain.neu),brain.g['ppl1'],pathways=audit)
    previous=np.zeros(len(brain.neu),dtype=int);responses=np.zeros(2,dtype=int);error=None;status='running'
    meta['protocol_sha256']=hashlib.sha256((ROOT/'research/directional_protocol.md').read_bytes()).hexdigest()
    try:
        for block in range(201):
            t=block*.005;c=np.zeros((2,4))
            if abs(float(brain.net.t/br.second)-t)>1e-9:raise RuntimeError('Neural clock mismatch')
            if 50<=block<100:
                if side=='left':c[cue,[0,2]]=1
                elif side=='right':c[cue,[1,3]]=1
                else:c[cue,:]=.5
            rates=np.zeros(len(brain.tgt));rates[drive_idx]=bridge.rates(c,t,t)
            brain.pg.rates=rates*br.Hz
            if not np.array_equal(np.array(brain.pg.rates[:]/br.Hz),rates):raise RuntimeError('Input transport mismatch')
            counts=np.array(brain.spk.count[:]);delta=counts-previous;previous=counts
            row=guard.inspect(t,delta,np.array(brain.neu.v[:]),np.array(brain.neu.g[:]),np.array(brain.pg.rates[:]/br.Hz),[0.],
                              pre=np.array(brain.syn.i[:]),post=np.array(brain.syn.j[:]),weights=np.array(brain.syn.w[:]),modulatory_sources=())
            if 50<block<=100:responses+=delta[output]
            row['output_spikes_by_input_side']=delta[output].tolist()
            if block==200:
                if any(r['total_spikes'] for r in guard.rows[-10:]):
                    guard.guard._stop('failed_recovery_screen',t);raise RuntimeError('Failed recovery')
                break
            brain.net.run(.005*br.second,namespace={})
        status='completed'
    except (RuntimeError,ValueError) as exc:status='stopped';error=str(exc)
    finally:
        brain.net.store('terminal',filename=str(out/'network_state.pkl'))
        report=dict(status=status,error=error,cue=cue,side=side,output_spikes=responses.tolist(),
                    neural_time_s=float(brain.net.t/br.second),unknown_side_inputs=bridge.unknown_sides,
                    weights_unchanged=bool(np.array_equal(w,np.array(brain.syn.w[:]))),subjective_welfare='not established')
        (out/'report.json').write_text(json.dumps(report,indent=2))
        (out/'telemetry.json').write_text('[\n'+',\n'.join(json.dumps(r,separators=(',',':')) for r in guard.rows)+'\n]')
        (out/'interface.json').write_text(json.dumps(dict(metadata=meta,inputs=anatomy),separators=(',',':')))
        print(json.dumps(report),flush=True)
    return report

def main():
    validation=json.loads((ROOT/'results/association_validation_v1/assessment.json').read_text())
    if not validation['passed']:raise SystemExit('Learning validation has not passed; no new neural exposure')
    out=ROOT/'results/directional_interface_v1';out.mkdir(exist_ok=False);reports=[]
    for cue in (0,1):
        for side in ('center','left','right'):
            report=run(cue,side,out/f'{cue}_{side}');reports.append(report)
            if report['status']!='completed':
                (out/'assessment.json').write_text(json.dumps(dict(passed=False,reason='stopped',reports=reports),indent=2));return
    scores={};passed=True
    for cue in (0,1):
        rows={r['side']:r for r in reports if r['cue']==cue};center=np.asarray(rows['center']['output_spikes'])
        if np.any(center<5):passed=False;scores[cue]=dict(reason='insufficient_center_response');continue
        values={}
        for side in ('left','right'):
            x=np.asarray(rows[side]['output_spikes'])/center
            values[side]=float((x[0]-x[1])/max(x.sum(),1e-12))
        scores[cue]=values;passed=passed and values['left']>.10 and values['right']<-.10
    (out/'assessment.json').write_text(json.dumps(dict(passed=bool(passed),scores=scores,reports=reports),indent=2))
    print('Direction gate',passed,scores)

if __name__=='__main__':main()

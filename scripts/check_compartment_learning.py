"""Synthetic spike-tape diagnostic, not a simulated animal or behavioral score."""
import argparse
import json
import sys
from pathlib import Path
import numpy as np
ROOT=Path(__file__).resolve().parents[1];sys.path.insert(0,str(ROOT))
from flyplasticity.compartment_plasticity import CompartmentEligibilityLTD
from flyplasticity.light_task import LocalEligibilityLTD
parser=argparse.ArgumentParser()
parser.add_argument('--out',default='results/compartment_learning')
parser.add_argument('--matched-drive',action='store_true')
args=parser.parse_args()
out=ROOT/args.out;out.mkdir(exist_ok=True)
pre=np.array([0,1,0,1]);comp=np.array([0,0,1,1]);groups={0:[2],1:[3]}

def run(kind,condition):
    local=kind=='local'
    rule=CompartmentEligibilityLTD(pre,comp,groups,4,eta=2. if args.matched_drive else 4.) if local else LocalEligibilityLTD(pre,[2,3],4)
    w=np.ones(4);trace=[]
    for step in range(400):
        counts=np.zeros(4)
        # Same KC represents cue A on two output branches. Only compartment 0's DAN fires.
        if step<50 and step%2==0:counts[0]=1
        reward=(step<50 if condition!='unpaired' else 150<=step<200)
        if reward and step%2==0:counts[2]=1
        old=w.copy()
        if local:w=rule.step(counts,w,learn=condition!='frozen')
        else:
            proposed=rule.step(counts,w)
            if condition!='frozen':w=proposed
        trace.append(w.copy())
    retained=w.copy()
    # Frozen readout: cue A and unrelated cue B activate different fixture KCs.
    response_A=w[[0,2]].copy();response_B=w[[1,3]].copy()
    return dict(kind=kind,condition=condition,weights=w.tolist(),cue_A_readout=response_A.tolist(),
                cue_B_readout=response_B.tolist(),retained_after_quiet_s=3.5),np.array(trace)

rows=[];traces={}
for kind in ('pooled','local'):
    for condition in ('paired','unpaired','frozen'):
        row,trace=run(kind,condition);rows.append(row);traces[kind+'_'+condition]=trace
get=lambda k,c:next(r for r in rows if r['kind']==k and r['condition']==c)
local=np.array(get('local','paired')['weights']);pooled=np.array(get('pooled','paired')['weights'])
assert local[0]<.9 and np.array_equal(local[1:],np.ones(3))
assert pooled[2]<.9, 'Original pooled rule should expose cross-compartment update'
assert np.allclose(get('local','unpaired')['weights'],1,atol=.001)
assert np.array_equal(get('local','frozen')['weights'],np.ones(4))
result=dict(passed=True,neural_or_body_simulation=False,rows=rows,
            analytically_matched_dopamine_drive=args.matched_drive,
            improvement_demonstrated='Eliminates cross-compartment updates in a labeled synthetic fixture',
            limitation='Fixture compartments are supplied, not inferred from the connectome. No biological accuracy or behavioral gain established.')
(out/'checks.json').write_text(json.dumps(result,indent=2));np.savez_compressed(out/'traces.npz',**traces)
print(json.dumps(result,indent=2))

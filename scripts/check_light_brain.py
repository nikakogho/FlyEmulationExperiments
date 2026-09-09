"""Reserved seed 101: neural-interface positive and frozen controls, no body."""
import json
from pathlib import Path
import numpy as np
from light_brain import LightBrain,ROOT

def main():
    brain=LightBrain(101)
    initial_all=np.array(brain.b.syn.w[:])
    results=[]
    for name,taste,learn in [('frozen',True,False),('paired',True,True),('no_external_reward',False,True)]:
        brain.reset()
        counts=[]
        for _ in range(5):
            rates,spikes=brain.step(np.array([[1.,0.],[1.,0.]]),taste,learn)
            counts.append(spikes)
        weights=brain.weights()
        fraction=float(weights.sum()/brain.initial.sum())
        if not learn: np.testing.assert_array_equal(weights,brain.initial)
        if name=='paired':
            assert fraction<1., 'Positive control did not modify eligible synapses'
            assert sum(s['pam_spikes'] for s in counts)>0
            assert sum(s['kc_spikes'] for s in counts)>0
        other=np.ones(len(initial_all),dtype=bool); other[brain.plastic]=False
        np.testing.assert_array_equal(np.array(brain.b.syn.w[:])[other],initial_all[other])
        results.append(dict(condition=name,weight_fraction=fraction,spike_counts=counts))
    brain.reset(); before=brain.weights()
    brain.step(np.ones((2,2)),True,False)
    np.testing.assert_array_equal(brain.weights(),before)
    out=ROOT/'results/light_brain_checks.json'
    out.write_text(json.dumps(dict(passed=True,seed=101,metadata=brain.metadata,conditions=results),indent=2))
    print(json.dumps(dict(passed=True,conditions=[{k:v for k,v in r.items() if k!='spike_counts'} for r in results]),indent=2))

if __name__=='__main__': main()

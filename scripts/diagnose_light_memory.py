"""Reserved-seed cue-response diagnostic; not an embodied learning score.

No parameters are selected using this result. Compare retained weight changes
under identical fresh neural state and identical test Poisson streams.
"""
import json
import numpy as np
from light_brain import LightBrain, ROOT
from flyplasticity.light_task import motor_output


def main():
    brain=LightBrain(101)
    rows=[]
    for condition,taste,learn in [('frozen',1,False),('paired',1,True),('no_external_reward',0,True)]:
        brain.reset()
        for _ in range(5):
            brain.step(np.array([[1.,0.],[1.,0.]]),taste,learn)
        weights=brain.weights()
        responses=[]
        for color in (0,1):
            for eye in (0,1):
                brain.reset(weights)
                features=np.zeros((2,2)); features[eye,color]=1.
                rates=[]
                for _ in range(5):
                    output,_=brain.step(features,0,False)
                    rates.append(output)
                mean_rates=np.mean(rates,axis=0)
                responses.append(dict(color=['green','blue'][color],eye=['left','right'][eye],
                                      mean_mbon_hz=mean_rates.tolist(),
                                      action_from_mean_rates=motor_output(mean_rates,0).tolist()))
                np.testing.assert_array_equal(brain.weights(),weights)
        rows.append(dict(condition=condition,responses=responses,
                         retained_weight_fraction=float(weights.sum()/brain.initial.sum())))
    result=dict(seed=101,training='0.5 s bilateral green; paired external PAM input 60 Hz',
                testing='0.5 s each color and eye separately, fresh state, no food or updates',rows=rows,
                limitation='Synthetic isolated-cue diagnostic; mixed MBON activity is not a behavioral valence measure')
    (ROOT/'results/light_memory_diagnostic.json').write_text(json.dumps(result,indent=2))
    print(json.dumps(result,indent=2))


if __name__=='__main__': main()

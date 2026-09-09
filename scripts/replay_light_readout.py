"""Post-hoc diagnostic: does retained memory change actions for identical vision?

Replay frozen-control test eye features, never re-optimize parameters. This is
an open-loop neural counterfactual, not a new embodied success measurement.
"""
import json
import numpy as np
from light_brain import LightBrain, ROOT
from flyplasticity.light_task import motor_output


def main():
    out=ROOT/'results/light_garden'
    rows=[]
    for seed in (0,1,2):
        brain=LightBrain(seed)
        learned=np.load(out/f'seed{seed}_plastic_weights.npy')
        for swap in (0,1):
            trace=json.loads((out/f'seed{seed}_frozen_test_swap{swap}.json').read_text())
            if not trace['completed']: raise RuntimeError('Counterfactual requires a complete frozen test')
            actions=[]; rates=[]
            for weights in (brain.initial,learned):
                brain.reset(weights)
                rng=np.random.default_rng(seed*100+90); walk=0.
                condition_actions=[]; condition_rates=[]
                for row in trace['rows']:
                    output,_=brain.step(np.array(row['features']),0,False)
                    walk=.8*walk+rng.normal(0,.055)
                    condition_actions.append(motor_output(output,walk))
                    condition_rates.append(output)
                np.testing.assert_array_equal(brain.weights(),weights)
                actions.append(np.array(condition_actions)); rates.append(np.array(condition_rates))
            difference=np.abs(actions[1]-actions[0])
            rows.append(dict(seed=seed,swapped=bool(swap),
                             fraction_decisions_with_changed_action=float((difference.max(axis=1)>1e-9).mean()),
                             mean_absolute_action_change=float(difference.mean()),
                             max_absolute_action_change=float(difference.max()),
                             initial_actions=actions[0].tolist(),learned_actions=actions[1].tolist()))
    result=dict(design='Post-hoc controlled replay of the frozen test visual features for all seeds/layouts',
                random_stream='Fresh paired neural RNG streams; not a recreation of RNG use during body construction',
                limitation='Open-loop diagnostic, not an additional behavioral trial or an estimate of navigation benefit',
                rows=rows)
    (ROOT/'results/light_readout_replay.json').write_text(json.dumps(result,indent=2))
    print(json.dumps([{k:v for k,v in r.items() if not k.endswith('actions')} for r in rows],indent=2))


if __name__=='__main__': main()

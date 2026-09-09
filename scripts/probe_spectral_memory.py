"""Predeclared stationary 3D-derived cue-memory probe; no behavior claim.

Blue is paired with a synthetic taste input. Same cue and reward exposure in
delayed controls, but a one-second gap; test inputs contain no reward.
"""
import argparse
import json
from pathlib import Path
import sys
import time
import numpy as np
ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
from flyplasticity.spectral_learning import receptor_features
from spectral_brain import SpectralBrain


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument('--out', default='results/spectral_memory')
    ap.add_argument('--seeds', nargs='+', type=int, default=[201, 202, 203])
    ap.add_argument('--train-nm', choices=['365', '450', '525'], default='450')
    args = ap.parse_args()
    out = ROOT/args.out
    out.mkdir(exist_ok=False)
    data = np.load(ROOT/'results/spectral_scene/retinal_inputs.npz')
    features = {c: receptor_features(data[c], data['background'], data['pale']) for c in ('365', '450', '525')}
    protocol = dict(seeds=args.seeds, paired_cue_nm=int(args.train_nm), gain=30, drive_hz=250,
        cue_steps=5, delayed_gap_steps=10, reward_steps=5, total_steps=20, test_steps=3, dt_s=.1,
        channels=['Rh1', 'Rh3', 'Rh4', 'Rh5', 'Rh6'], features={k:v.tolist() for k,v in features.items()},
        conditions=['paired', 'delayed', 'frozen'],
        success='Paired-minus-control reduction in reward-free mean MBON response is larger for the trained cue than BOTH untrained cues, for every fixed seed. This absolute-response screen alone does not exclude broad generalization.',
        interpretation='Exploratory neural memory with a synthetic sensory and reward adapter; no locomotion, full-pathway fidelity or improved plasticity claim.')
    (out/'protocol.json').write_text(json.dumps(protocol, indent=2))
    print(json.dumps(protocol), flush=True)
    rows = []
    start = time.perf_counter()
    for seed in args.seeds:
        brain = SpectralBrain(seed)
        (out/f'brain_{seed}.json').write_text(json.dumps(brain.metadata, indent=2))
        np.save(out/f'initial_{seed}.npy', brain.initial)
        all_initial = np.array(brain.b.syn.w[:])
        nonplastic = np.ones(len(all_initial), dtype=bool)
        nonplastic[brain.plastic] = False
        for condition in protocol['conditions']:
            brain.reset()
            spike_totals = dict(kc_spikes=0, pam_spikes=0, mbon_spikes=0)
            for t in range(20):
                stimulus = features[args.train_nm] if t < 5 else np.zeros((2, 5))
                reward = t < 5 if condition != 'delayed' else 15 <= t < 20
                _, spikes = brain.step(stimulus, reward, condition != 'frozen')
                for key, value in spikes.items(): spike_totals[key] += value
            learned = brain.weights()
            np.testing.assert_array_equal(np.array(brain.b.syn.w[:])[nonplastic], all_initial[nonplastic])
            if condition == 'frozen': np.testing.assert_array_equal(learned, brain.initial)
            np.save(out/f'weights_{seed}_{condition}.npy', learned)
            tests = {}
            for cue, stimulus in features.items():
                brain.reset(learned)
                responses = [brain.step(stimulus, 0., False)[0] for _ in range(3)]
                np.testing.assert_array_equal(brain.weights(), learned)
                tests[cue] = float(np.mean(responses))
            row = dict(seed=seed, condition=condition, weight_fraction=float(learned.sum()/brain.initial.sum()),
                       reward_free_mbon_hz=tests, acquisition_spikes=spike_totals)
            rows.append(row)
            (out/f'{seed}_{condition}.json').write_text(json.dumps(row, indent=2))
            print(json.dumps(row), flush=True)
        del brain
    effects = []
    for seed in args.seeds:
        lookup = {r['condition']:r['reward_free_mbon_hz'] for r in rows if r['seed']==seed}
        for control in ('delayed', 'frozen'):
            reduction = {cue:lookup[control][cue]-lookup['paired'][cue] for cue in features}
            effects.append(dict(seed=seed, control=control, reduction_hz=reduction,
                trained_specific=bool(reduction[args.train_nm] > max([0]+[v for c,v in reduction.items() if c != args.train_nm]))))
    result = dict(completed=True, memory_specificity_gate_passed=all(e['trained_specific'] for e in effects),
        full_biological_integration=False, embodied_learning_demonstrated=False,
        runtime_sec=time.perf_counter()-start, effects=effects, rows=rows)
    (out/'checks.json').write_text(json.dumps(result, indent=2))
    print(json.dumps({k:v for k,v in result.items() if k != 'rows'}), flush=True)


if __name__ == '__main__': main()

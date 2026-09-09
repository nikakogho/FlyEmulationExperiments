"""Exploratory online temporal LTD in Daniel's real connectome subcircuit.

NOT a validated fly plasticity model. Adds an exponentially decaying KC
eligibility trace and a pooled PAM activity trace; retains global PAM gating,
upstream circuit edits, and gain 20. No odor label/reward flag reaches the rule.
All conditions/parameters are fixed before running. No navigation optimization.
"""
import argparse
import importlib.util
import json
from pathlib import Path
import sys
import numpy as np
import brian2 as br

ROOT = Path(__file__).resolve().parents[1]


class TemporalLTD:
    def __init__(self, n_neurons, pre, pam, dt=0.01, tau_e=0.1, tau_d=0.05, eta=4.0):
        self.pre, self.pam = pre, pam
        self.dt, self.tau_e, self.tau_d, self.eta = dt, tau_e, tau_d, eta
        self.e = np.zeros(n_neurons)
        self.d = 0.0

    def step(self, spike_counts, weights):
        self.e *= np.exp(-self.dt / self.tau_e)
        self.e[spike_counts > 0] = 1.0
        rate = spike_counts[self.pam].mean() / self.dt
        # Threshold suppresses very low spontaneous PAM activity; a free parameter.
        drive = rate / 60.0 if rate >= 1.0 else 0.0
        decay = np.exp(-self.dt / self.tau_d)
        self.d = decay * self.d + (1 - decay) * drive
        return weights * np.exp(-self.eta * self.dt * self.e[self.pre] * self.d)


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument('--out', default='results/temporal_pilot')
    ap.add_argument('--seed', type=int, default=0)
    ap.add_argument('--dt', type=float, default=0.01)
    args = ap.parse_args()
    br.prefs.codegen.target = 'numpy'
    path = ROOT / 'upstream/fly-api/experiments/navigation/nav_demo.py'
    spec = importlib.util.spec_from_file_location('nav', path)
    nav = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(nav)
    nav.ANN = str(ROOT / 'data/annotations.tsv')
    brain = nav.Brain(str(ROOT / 'upstream/Drosophila_brain_model'), seed=args.seed)
    brain.net.store('initial')
    out = Path(args.out)
    out.mkdir(parents=True, exist_ok=True)
    config = dict(seed=args.seed, dt=args.dt, tau_e=0.1, tau_d=0.05, eta_per_sec=4.0,
                  gain=20, pairs=3, episode_sec=2.5,
                  limitation='Pooled PAMs, no compartment mapping or LTP; hypothesis pilot only')
    (out / 'config.json').write_text(json.dumps(config, indent=2))
    rows = []
    for condition, onset, blocked in [('paired', 0.0, False), ('forward_gap_100ms', 0.6, False),
                                     ('forward_gap_1000ms', 1.5, False), ('no_dopamine', 0.0, True),
                                     ('plasticity_off', 0.0, False)]:
        brain.net.restore('initial', restore_random_state=True)
        brain.prev[:] = 0
        pre_a, pre_b = brain.valence(1, 0, 500), brain.valence(0, 1, 500)
        rule = TemporalLTD(len(brain.neu), brain.plastic_pre, brain.g['pam'], dt=args.dt)
        last = np.array(brain.spk.count[:], dtype=np.int64)
        def update():
            nonlocal last
            counts = np.array(brain.spk.count[:], dtype=np.int64)
            weights = np.array(brain.syn.w[brain.plastic_pos])
            new = rule.step(counts - last, weights)
            last = counts
            if condition != 'plasticity_off':
                brain.syn.w[brain.plastic_pos] = new * br.volt
        operation = br.NetworkOperation(update, dt=args.dt * br.second, when='end')
        brain.net.add(operation)
        # Events schedule sensory / optogenetic input; the learner sees spikes only.
        for pairing in range(3):
            boundaries = sorted(set([0.0, 0.5, onset, onset + 0.5, 2.5]))
            for start, end in zip(boundaries, boundaries[1:]):
                rates = np.zeros(len(brain.tgt))
                if start < 0.5:
                    for idx in brain.A:
                        rates[brain.pos[idx]] = 500.0
                if onset <= start < onset + 0.5 and not blocked:
                    for idx in brain.g['pam']:
                        rates[brain.pos[idx]] = 60.0
                brain.pg.rates = rates * br.Hz
                brain.net.run((end - start) * br.second)
        brain.net.remove(operation)
        brain.prev = np.array(brain.spk.count[:], dtype=np.int64)
        post_a, post_b = brain.valence(1, 0, 500), brain.valence(0, 1, 500)
        weights = np.array(brain.syn.w[brain.plastic_pos])
        row = dict(condition=condition, pre_A=pre_a, post_A=post_a, pre_B=pre_b, post_B=post_b,
                   suppression_A=1-post_a/max(pre_a, 1), suppression_B=1-post_b/max(pre_b, 1),
                   weight_fraction=float(weights.sum()/brain.w_naive.sum()))
        np.savez_compressed(out / f'{condition}_weights.npz', weights=weights,
                            synapse_indices=brain.plastic_pos)
        rows.append(row)
        (out / 'summary.json').write_text(json.dumps(rows, indent=2))
        print(json.dumps(row), flush=True)


if __name__ == '__main__':
    main()

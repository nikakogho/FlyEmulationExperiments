"""Evaluate every predeclared body episode, without selecting trajectories."""
import json
from pathlib import Path
import numpy as np
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt

ROOT = Path(__file__).resolve().parents[1]
folder = ROOT/'results/spectral_garden'
protocol = json.loads((folder/'protocol.json').read_text())
rows, effects = [], []
fig, axs = plt.subplots(3, 2, figsize=(10, 10), layout='constrained', sharex=True, sharey=True)
colors = {'paired':'#147c42', 'delayed':'#c17c12', 'frozen':'#747474'}
for i, seed in enumerate(protocol['seeds']):
    for condition in protocol['conditions']:
        for swap in (False, True):
            r = json.loads((folder/f'{seed}_{condition}_swap{int(swap)}.json').read_text())
            if not r['completed'] or len(r['rows']) != protocol['steps']:
                raise ValueError('Incomplete predeclared cohort')
            xyz = np.array([v['xyz'] for v in r['rows']])
            distance = np.array([v['cue_distances'] for v in r['rows']])
            features = np.array([v['features'] for v in r['rows']])
            assert np.isfinite(xyz).all() and np.isfinite(features).all()
            assert all(v['taste'] == 0 and not v['physical_food_contact'] for v in r['rows'])
            rows.append(dict(seed=seed, condition=condition, swapped=swap,
                blue_approach_score_mm=float(np.mean(distance[:,1]-distance[:,0])),
                entered_blue_radius=bool(np.any(distance[:,0] <= 2.5)),
                entered_green_radius=bool(np.any(distance[:,1] <= 2.5)),
                final_blue_distance_mm=float(distance[-1,0]),
                max_feature=float(features.max()), fraction_features_at_one=float(np.mean(features >= 1))))
            axs[i,int(swap)].plot(xyz[:,0], xyz[:,1], label=condition, color=colors[condition],
                                  lw=2 if condition=='paired' else 1.2, ls='-' if condition=='paired' else '--')
    lookup = {c:float(np.mean([r['blue_approach_score_mm'] for r in rows if r['seed']==seed and r['condition']==c]))
              for c in protocol['conditions']}
    effects.append(dict(seed=seed, scores_mm=lookup,
        paired_minus_delayed_mm=lookup['paired']-lookup['delayed'],
        paired_minus_frozen_mm=lookup['paired']-lookup['frozen'],
        paired_beats_both_controls=bool(lookup['paired'] > max(lookup['delayed'],lookup['frozen'])),
        paired_absolute_blue_preference=bool(lookup['paired'] > 0)))
    for j in range(2):
        ax = axs[i,j]
        ax.scatter([9,9], [5,-5], c=['#357ce0','#69ad35'] if j==0 else ['#69ad35','#357ce0'], s=140)
        ax.scatter(0,0,c='black',marker='x')
        ax.set(title=f'Seed {seed}; positions '+('swapped' if j else 'original'),
               xlabel='x (mm)', ylabel='y (mm)', aspect='equal', xlim=(-1,36), ylim=(-20,20))
        ax.grid(alpha=.15)
axs[0,0].legend(fontsize=8)
fig.suptitle('Reward-free spectral-memory transfer: every trajectory\nBlue / green dots are 450 / 525 nm cue locations')
fig.savefig(folder/'trajectories.png', dpi=150)
plt.close(fig)
summary = {c:dict(mean_score_mm=float(np.mean([e['scores_mm'][c] for e in effects])),
    episodes_entering_blue=sum(r['entered_blue_radius'] for r in rows if r['condition']==c),
    episodes_entering_green=sum(r['entered_green_radius'] for r in rows if r['condition']==c)) for c in protocol['conditions']}
result = dict(completed=True, episodes=len(rows), protocol=protocol, effects=effects, summary=summary, rows=rows,
    relative_pilot_gate_passed=all(e['paired_beats_both_controls'] for e in effects),
    consistent_absolute_blue_preference=all(e['paired_absolute_blue_preference'] for e in effects),
    improved_plasticity_demonstrated=False, biological_pathway_validated=False,
    note='Relative improvement can reduce an existing green bias without producing an absolute blue preference. Proximity is measured in xy as in the original pilot.')
(folder/'analysis.json').write_text(json.dumps(result, indent=2))
print(json.dumps({k:v for k,v in result.items() if k not in ('rows','protocol')}, indent=2))

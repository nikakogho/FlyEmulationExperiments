import json
from pathlib import Path
import numpy as np
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt

ROOT = Path(__file__).resolve().parents[1]
results = ROOT/'results'
summary = {}
for name in ['baseline_s0', 'baseline_s1', 'baseline_s2', 'baseline_gain1']:
    path = results/name/'episodes.jsonl'
    if not path.exists():
        continue
    rows = [json.loads(line) for line in path.read_text().splitlines()]
    values = {}
    for odor in ['A', 'B']:
        pre = np.mean([r['mbon_spk'] for r in rows if r['episode'].startswith('pre_'+odor)])
        post = np.mean([r['mbon_spk'] for r in rows if r['episode'].startswith('post_'+odor)])
        values[odor] = {'pre': float(pre), 'post': float(post), 'suppression_pct': float(100*(1-post/pre))}
    summary[name] = values
for name in ['navigation', 'temporal_pilot', 'temporal_pilot_dt5ms']:
    path = results/name/'summary.json'
    if path.exists():
        summary[name] = json.loads(path.read_text())
(results/'summary.json').write_text(json.dumps(summary, indent=2))

fig, ax = plt.subplots(1, 2, figsize=(11, 4.5), layout='constrained')
names = ['baseline_s0', 'baseline_s1', 'baseline_s2']
x = np.arange(3)
for delta, odor, color in [(-0.18, 'A', '#cb8428'), (0.18, 'B', '#546b80')]:
    ax[0].bar(x+delta, [summary[n][odor]['suppression_pct'] for n in names], width=.36, label=f'Odor {odor}', color=color)
ax[0].set(xticks=x, xticklabels=['Seed 0', 'Seed 1', 'Seed 2'], ylabel='MBON response suppression (%)', title="Reproduced conditioning (gain 20)")
ax[0].legend()
rows = summary['temporal_pilot']
ax[1].bar(np.arange(5), [r['suppression_A']*100 for r in rows], color=['#cb8428','#627f66','#627f66','#546b80','#546b80'])
ax[1].set(xticks=np.arange(5), xticklabels=['Paired','100 ms\ngap','1 s\ngap','No DA\ndrive','Plasticity\noff'], ylabel='Odor A suppression (%)', title='Temporal pilot: one seed, uncalibrated rule')
for a in ax:
    a.spines[['top','right']].set_visible(False)
fig.savefig(results/'comparison.png', dpi=160)
print(json.dumps(summary, indent=2))

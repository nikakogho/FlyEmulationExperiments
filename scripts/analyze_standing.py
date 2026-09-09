"""Summarize the fixed three-seed mechanical standing probe."""
import hashlib
import json
from pathlib import Path
import numpy as np
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt

ROOT = Path(__file__).resolve().parents[1]
out = ROOT/'results/standing_summary'
out.mkdir(exist_ok=True)
summary = {'brain_simulated': False, 'seeds': [], 'limits':
           'Three short flat-floor mechanical trials; not a welfare or learning test.'}
fig, ax = plt.subplots(figsize=(9, 4))
for seed in (101, 102, 103):
    path = ROOT/f'results/standing_v2_seed{seed}/body_rest_checks.json'
    d = json.loads(path.read_text())
    rows = d.pop('rows')
    d['walking_median_speed_mm_s'] = float(np.median(
        [r['speed_mm_s'] for r in rows if .32 < r['time_s'] < .7]))
    d['final_height_mm'] = rows[-1]['xyz'][2]
    d['max_image_age_s'] = max(r['time_s']-r['vision_time_s'] for r in rows)
    summary['seeds'].append(d)
    ax.plot([r['time_s'] for r in rows], [r['speed_mm_s'] for r in rows], label=f'Seed {seed}')
ax.axvspan(.3, .7, color='green', alpha=.08, label='Walk command')
ax.axvspan(1.1, 1.4, color='blue', alpha=.06, label='Rest evaluation')
ax.axhline(.5, color='black', linestyle=':', label='Median rest-speed limit')
ax.set(xlabel='Simulation time (s)', ylabel='Instantaneous XY speed (mm/s)',
       title='Explicit standing: mechanical body only')
ax.legend(fontsize=8, ncol=2)
fig.tight_layout()
fig.savefig(out/'speed_traces.png', dpi=160)
plt.close(fig)
summary['passed'] = all(s['completed'] and s['passed'] for s in summary['seeds'])
summary['source_sha256'] = {p: hashlib.sha256((ROOT/p).read_bytes()).hexdigest()
                           for p in ['flyplasticity/standing.py', 'scripts/check_explicit_standing.py',
                                     'scripts/analyze_standing.py', 'tests/test_standing.py']}
(out/'checks.json').write_text(json.dumps(summary, indent=2))
print(json.dumps(summary, indent=2))
if not summary['passed']:
    raise SystemExit(1)

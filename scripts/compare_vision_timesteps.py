"""Apply frozen numerical-convergence criteria; preserve qualitative failures."""
import json
from pathlib import Path
import numpy as np
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt

ROOT=Path(__file__).resolve().parents[1]
coarse=json.loads((ROOT/'results/vision_calibration_v1/checks.json').read_text())
fine=json.loads((ROOT/'results/vision_calibration_dt2500us/checks.json').read_text())
rows=[]
for a,b in zip(coarse['metrics'],fine['metrics']):
    assert a['cell']==b['cell']
    rows.append(dict(cell=a['cell'],direction_index_change=abs(a['direction_index']-b['direction_index']),
                     relative_peak_change=abs(a['preferred_peak']-b['preferred_peak'])/max(b['preferred_peak'],1e-12)))
numeric_pass=all(r['direction_index_change']<=.05 and r['relative_peak_change']<=.1 for r in rows)
out=ROOT/'results/vision_comparison';out.mkdir(exist_ok=True)
result=dict(passed=bool(numeric_pass and coarse['passed'] and fine['passed']),
            numerical_tolerance_pass=bool(numeric_pass),coarse_qualitative_pass=coarse['passed'],
            fine_qualitative_pass=fine['passed'],rows=rows)
(out/'checks.json').write_text(json.dumps(result,indent=2))
fig,ax=plt.subplots(figsize=(10,4))
x=np.arange(8)
ax.bar(x-.18,[m['expected_polarity_peak'] for m in fine['metrics']],width=.36,label='Expected polarity')
ax.bar(x+.18,[m['other_polarity_peak'] for m in fine['metrics']],width=.36,label='Other polarity')
ax.set_xticks(x,[m['cell'] for m in fine['metrics']])
ax.set(ylabel='Peak positive activity change (model units)',title='400 Hz: expected versus other contrast polarity')
ax.legend();fig.tight_layout();fig.savefig(out/'polarity_check.png',dpi=150)
print(json.dumps(result,indent=2))
if not result['passed']:raise SystemExit(1)

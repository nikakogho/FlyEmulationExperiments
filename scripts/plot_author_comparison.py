"""Show all ten author-listed checkpoints; retain every polarity mismatch."""
import json
from pathlib import Path
import numpy as np
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
ROOT=Path(__file__).resolve().parents[1]
out=ROOT/'results/author_ensemble'
d=json.loads((out/'checks.json').read_text())
assert d['complete']
names=list(d['summary'])
fig,ax=plt.subplots(figsize=(10,4.5))
for i,name in enumerate(names):
    y=np.array([r['fri'][name] for r in d['rows']])
    ax.scatter(i+np.linspace(-.15,.15,len(y)),y,color='steelblue',s=25)
    ax.scatter(i-.15,y[0],color='red',marker='x',s=65,zorder=3,
               label='Default checkpoint 000' if i==0 else None)
    ax.plot([i-.2,i+.2],[np.median(y)]*2,color='black',linewidth=2)
ax.axhline(0,color='gray',linestyle=':')
ax.set_xticks(range(len(names)),names)
ax.set(ylabel='Authors’ flash-response index (FRI)',
       title='Same ten models as authors’ Fig. 2 notebook; disk radius 6')
ax.text(.01,.98,'Positive = ON preference; negative = OFF preference',transform=ax.transAxes,va='top',fontsize=9)
ax.legend(loc='lower left');fig.tight_layout()
fig.savefig(out/'polarity_ensemble.png',dpi=160)

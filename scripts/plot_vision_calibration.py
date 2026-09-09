"""Plot every subtype's preferred/null responses without selecting successes."""
import argparse
import json
from pathlib import Path
import numpy as np
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt

parser=argparse.ArgumentParser()
parser.add_argument('directory')
args=parser.parse_args()
out=Path(args.directory)
d=json.loads((out/'checks.json').read_text())
r=np.load(out/'responses.npz')
fig,axes=plt.subplots(2,4,figsize=(13,6),sharex=True)
time=np.arange(r['traces'].shape[1])*d['dt']-1
for k,(ax,m) in enumerate(zip(axes.flat,d['metrics'])):
    polarity=int(m['cell'].startswith('T4'))
    for angle,label in [(m['preferred_angle'],'Preferred'),((m['preferred_angle']+180)%360,'Opposite')]:
        i=next(i for i,s in enumerate(d['stimuli']) if s['angle']==angle and s['intensity']==polarity)
        trace=r['traces'][i,:,k]
        baseline=trace[int(1/d['dt'])-int(.1/d['dt']):int(1/d['dt'])].mean()
        ax.plot(time,trace-baseline,label=label)
    ax.set_title(f"{m['cell']}: index {m['direction_index']:.2f}")
    ax.axvline(0,color='gray',linestyle=':')
    ax.set_xlabel('Time from edge onset (s)')
    ax.set_ylabel('Change in model activity')
axes[0,0].legend()
fig.suptitle('Published visual model: fixed-checkpoint offline probe')
fig.tight_layout()
fig.savefig(out/'motion_responses.png',dpi=150)

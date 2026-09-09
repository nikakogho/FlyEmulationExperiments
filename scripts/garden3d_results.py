"""Produce a labelled comparison video and trajectory plot after garden3d.py."""
import argparse
import json
from pathlib import Path
import cv2
import imageio.v2 as imageio
import numpy as np
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt

ap=argparse.ArgumentParser()
ap.add_argument('--out',default='results/garden3d')
args=ap.parse_args()
out=Path(args.out)
caps=[cv2.VideoCapture(str(out/f'{n}.mp4')) for n in ['naive','trained']]
counts=[int(c.get(cv2.CAP_PROP_FRAME_COUNT)) for c in caps]
if min(counts)<=0 or counts[0]!=counts[1]:
    raise RuntimeError(f'Expected two complete matched-duration videos: {counts}')
fps=caps[0].get(cv2.CAP_PROP_FPS)
with imageio.get_writer(out/'comparison.mp4',fps=fps) as writer:
    for _ in range(counts[0]):
        frames=[]
        for cap,label in zip(caps,['NAIVE','CONDITIONED']):
            ok,bgr=cap.read()
            if not ok: raise RuntimeError('Video decode failed')
            frame=cv2.resize(bgr,(640,480))
            cv2.rectangle(frame,(0,0),(640,42),(27,33,27),-1)
            cv2.putText(frame,label,(16,29),cv2.FONT_HERSHEY_SIMPLEX,.7,(245,245,245),2,cv2.LINE_AA)
            frames.append(cv2.cvtColor(frame,cv2.COLOR_BGR2RGB))
        writer.append_data(np.concatenate(frames,axis=1))
for cap in caps: cap.release()
fig,ax=plt.subplots(1,2,figsize=(10,4),layout='constrained')
for name,color in [('naive','#536f89'),('trained','#be791e')]:
    rows=json.loads((out/f'{name}.json').read_text())
    xyz=np.array([r['xyz'] for r in rows]); t=[r['time_s'] for r in rows]
    ax[0].plot(xyz[:,0],xyz[:,1],'.-',label=name,color=color)
    ax[1].plot(t,xyz[:,2],label=name,color=color)
sources=np.array(json.loads((out/'config.json').read_text())['sources'])
ax[0].scatter(sources[:,0],sources[:,1],c=['#be791e','#268cbc'],marker='*',s=180)
ax[0].set(xlabel='x (mm)',ylabel='y (mm)',title='Paths in the terraced garden',aspect='equal')
ax[1].set(xlabel='Time (s)',ylabel='Body height (mm)',title='Physical elevation during walking')
for a in ax: a.legend(); a.spines[['top','right']].set_visible(False)
fig.savefig(out/'trajectories.png',dpi=150)
print('Decoded and combined',counts[0],'frames per condition at',fps,'fps')

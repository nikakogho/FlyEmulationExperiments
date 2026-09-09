"""Show every final test trajectory and the preselected seed-0 3D videos."""
import json
from pathlib import Path
import numpy as np
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
import imageio.v2 as iio
import cv2

ROOT=Path(__file__).resolve().parents[1]
OUT=ROOT/'results/light_garden'
COLORS={'plastic':'#982bc0','frozen':'#525b68','yoked':'#d08a16'}


def plot_trajectories():
    fig,axes=plt.subplots(2,3,figsize=(13,8),layout='constrained')
    for seed in (0,1,2):
        for swap in (0,1):
            ax=axes[swap,seed]
            for condition,color in COLORS.items():
                data=json.loads((OUT/f'seed{seed}_{condition}_test_swap{swap}.json').read_text())
                if not data['completed']: raise RuntimeError('Cannot present a failed test as complete')
                xyz=np.array([[0,0,.2]]+[r['xyz'] for r in data['rows']])
                ax.plot(xyz[:,0],xyz[:,1],color=color,label=condition,
                        lw=2.5 if condition=='plastic' else 1.5,
                        linestyle='--' if condition=='yoked' else '-')
                ax.scatter(*xyz[-1,:2],color=color,s=12)
            for location,y in enumerate((5,-5)):
                color=['limegreen','blue'][location^swap]
                ax.scatter(9,y,color=color,s=45,zorder=5)
                ax.add_patch(plt.Circle((9,y),3,fill=False,edgecolor=color,linestyle=':',alpha=.5))
            ax.scatter(0,0,marker='x',color='black',s=30)
            ax.set_title(f'Seed {seed} | '+('swapped lights' if swap else 'original lights'))
            ax.set_aspect('equal',adjustable='datalim'); ax.set_xlabel('X (mm)'); ax.set_ylabel('Y (mm)')
            ax.grid(alpha=.15)
    axes[0,0].legend(fontsize=8)
    fig.suptitle('All food-free test paths; dotted circles are evaluation zones, not food')
    fig.savefig(OUT/'test_trajectories.png',dpi=150)
    plt.close(fig)


def comparison_video():
    panels=[(condition,swap) for condition in ('plastic','frozen') for swap in (0,1)]
    movies=[list(iio.mimread(OUT/f'seed0_{c}_test_swap{s}.mp4')) for c,s in panels]
    lengths=[len(frames) for frames in movies]
    if len(set(lengths))!=1: raise RuntimeError(f'Mismatched video lengths: {lengths}')
    with iio.get_writer(OUT/'seed0_comparison.mp4',fps=30) as writer:
        for frame_index in range(lengths[0]):
            tiles=[]
            for frames,(condition,swap) in zip(movies,panels):
                tile=np.full((512,640,3),248,dtype=np.uint8)
                tile[32:]=cv2.resize(frames[frame_index],(640,480))
                label=f'{condition.upper()} | '+('swapped lights' if swap else 'original lights')+' | food absent'
                cv2.putText(tile,label,(10,22),cv2.FONT_HERSHEY_SIMPLEX,.52,(25,25,25),1,cv2.LINE_AA)
                tiles.append(tile)
            writer.append_data(np.concatenate([np.concatenate(tiles[:2],axis=1),np.concatenate(tiles[2:],axis=1)],axis=0))
    metadata=dict(preselection='seed 0, both food-free test layouts, plastic and frozen',
                  frames_per_source=lengths,fps=30,playback_speed=.5,
                  note='Full fixed-camera clips; trajectories retain positions even when the fly leaves the camera view')
    (OUT/'media_checks.json').write_text(json.dumps(metadata,indent=2))
    print(json.dumps(metadata,indent=2))


if __name__=='__main__':
    plot_trajectories()
    comparison_video()

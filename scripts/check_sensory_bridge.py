"""Offline sensor checks using a stored eye image; no brain simulation."""
import json
import sys
from pathlib import Path
import numpy as np
import imageio.v3 as iio
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
ROOT=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT))
from flyplasticity.sensory import SensoryStream
from flyplasticity.light_task import visual_features


def main():
    path=ROOT/'results/light_flat_preflight/preflight_0.0_eyes.png'
    stored=iio.imread(path)
    eyes=np.stack(np.split(stored,2,axis=1))
    # Remove color while retaining the stored scene's spatial structure.
    gray=np.repeat(eyes.mean(axis=-1,keepdims=True),3,axis=-1)
    shifted=np.roll(gray,1,axis=2)
    common=dict(joint_angles_rad=np.zeros(2),joint_velocities_rad_s=np.zeros(2),
                contact_forces=np.zeros((2,3)),previous_motor_command=np.zeros(2))
    stream=SensoryStream()
    first=stream.update(time_s=0,vision_time_s=0,eye_rgb=gray,**common)
    second=stream.update(time_s=.02,vision_time_s=.02,eye_rgb=shifted,**common)
    old=visual_features(gray)
    assert np.array_equal(old,np.zeros((2,2)))
    assert first.luminance.std()>.01
    assert np.any(second.temporal_contrast_per_s!=0)
    out=ROOT/'results/sensory_bridge'; out.mkdir(parents=True,exist_ok=True)
    fig,axes=plt.subplots(1,3,figsize=(12,3.5),layout='constrained')
    axes[0].imshow(eyes[0]); axes[0].set_title('Stored left-eye image')
    axes[1].imshow(first.luminance[0],cmap='gray',vmin=0,vmax=1)
    axes[1].set_title('Preserved spatial grayscale')
    scale=float(np.max(np.abs(second.temporal_contrast_per_s)))
    axes[2].imshow(second.temporal_contrast_per_s[0],cmap='coolwarm',vmin=-scale,vmax=scale)
    axes[2].set_title('Temporal change: synthetic 1 px shift')
    for ax in axes: ax.axis('off')
    fig.savefig(out/'sensory_comparison.png',dpi=150)
    checks=dict(passed=True,source=str(path),eye_shape=list(eyes.shape),
                old_gray_features=old.tolist(),retained_grayscale_std=float(first.luminance.std()),
                shifted_nonzero_temporal_pixels=int(np.count_nonzero(second.temporal_contrast_per_s)),
                brain_simulated=False,
                limitation='A synthetic image shift tests temporal transport, not biological motion tuning or calibrated optic flow')
    (out/'offline_checks.json').write_text(json.dumps(checks,indent=2))
    print(json.dumps(checks,indent=2))


if __name__=='__main__': main()

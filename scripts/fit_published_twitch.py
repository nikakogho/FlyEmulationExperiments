"""Digitize Figure 4B's trial bundle and fit a descriptive pulse, offline only.

The median of visible stroke pixels is NOT an across-trial median or raw data.
This approximation cannot validate neural recruitment or freely moving mechanics.
"""
from pathlib import Path
import sys,json,hashlib
ROOT=Path(__file__).resolve().parents[1];sys.path.insert(0,str(ROOT))
import numpy as np
from PIL import Image
from flyplasticity.figure_twitch import fit_twitch,twitch


def main():
    import argparse
    ap=argparse.ArgumentParser(description=__doc__);ap.add_argument('--out',default='results/published_twitch');args=ap.parse_args()
    source=ROOT/'data/motor_physiology/figure4.jpg'
    out=ROOT/args.out;out.mkdir(exist_ok=False)
    im=np.asarray(Image.open(source)).astype(float)
    if im.shape[:2]!=(1784,1530): raise ValueError('Unexpected source figure dimensions')
    # From scale bars: x=606 spike alignment, 51 px /20 ms; y=494 baseline,
    # 42 px /5 um. Sample at original video spacing, not every image column.
    # Exclude t=0 because its vertical alignment line contaminates digitization.
    ts=np.arange(1000/170,121,1000/170)
    variants=[];central=None
    for threshold in (160,180,200):
        for baseline in (493,494,495):
            values=[]
            for t in ts:
                x=int(round(606+t*51/20));roi=im[425:510,x-2:x+3]
                gray=roi.mean(2);mask=(np.ptp(roi,axis=2)<12)&(gray>70)&(gray<threshold)
                yy=np.where(mask)[0]+425
                if not len(yy): raise ValueError('No visible trace pixels')
                values.append((baseline-float(np.median(yy)))*5/42)
            fit=fit_twitch(ts,values);fit.update(threshold=threshold,baseline_pixel=baseline)
            variants.append(fit)
            if threshold==180 and baseline==494: central=(values,fit)
    values,fit=central
    report=dict(status='figure_derived_descriptive_fit_not_raw_recording_calibration',
                source_url='https://iiif.elifesciences.org/lax/56754%2Felife-56754-fig4-v2.tif/full/full/0/default.jpg',
                sha256=hashlib.sha256(source.read_bytes()).hexdigest(),panel='4B top: one-spike intermediate example',
                fit=fit,variant_ranges={k:[min(v[k] for v in variants),max(v[k] for v in variants)] for k in ('amplitude_um','time_to_peak_ms','rmse_um')},
                variants=variants,time_ms=ts.tolist(),digitized_displacement_um=values,
                scale=dict(spike_x=606,time_bar_pixels=51,time_bar_ms=20,
                           baseline_y=494,displacement_bar_pixels=42,displacement_bar_um=5,
                           original_video_fps=170),
                neural_steps=0,raw_recording_fit=False,independent_physiology_validation=False,
                embodied_use_enabled=False,
                limitations=['Visible stroke-pixel median is not an average/median over identified trials',
                             'Three-parameter gamma pulse is a descriptive engineering model',
                             'Sensitivity ranges cover threshold/baseline choices only, not biological confidence intervals',
                             'Probe displacement in this experimental load is not unloaded joint angle',
                             'Fitted delay includes probe and sampling effects, not axonal conduction delay',
                             'No somatic spike threshold, synaptic efficacy or motor learning inferred'])
    (out/'report.json').write_text(json.dumps(report,indent=2))
    import matplotlib;matplotlib.use('Agg')
    import matplotlib.pyplot as plt
    dense=np.linspace(0,120,600);fig,ax=plt.subplots(figsize=(7,4))
    for v in variants: ax.plot(dense,twitch(dense,v['amplitude_um'],v['tau_ms'],v['delay_ms']),color='gray',alpha=.2)
    ax.plot(ts,values,'o',label='Digitized visible-trace bundle')
    ax.plot(dense,twitch(dense,fit['amplitude_um'],fit['tau_ms'],fit['delay_ms']),label='Descriptive fit')
    ax.set(xlabel='Time after spike alignment (ms)',ylabel='Probe displacement (um)',title='Intermediate flexor: published-figure approximation')
    ax.legend();fig.tight_layout();fig.savefig(out/'fit.png',dpi=160);plt.close(fig)
    print(json.dumps(fit,indent=2))


if __name__=='__main__':main()

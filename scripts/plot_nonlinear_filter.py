"""Plot saved comparisons only; no fitting or simulation."""
import argparse
import json
from pathlib import Path
import numpy as np
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument('--path', default='results/nonlinear_filter_v2')
    args = ap.parse_args()
    path = Path(args.path)
    r = json.loads((path/'report.json').read_text())
    a = np.load(path/'predictions.npz', allow_pickle=False)
    fig, axes = plt.subplots(3, 2, figsize=(15, 9), layout='constrained')
    for col, field in enumerate(('new_background_evaluation', 'old_background_regression')):
        bg = r[field]['background']
        for ax, c in zip(axes[:, col], r[field]['conditions']):
            key = f"dc{bg}_hz{c['bandwidth_hz']}"
            t = np.arange(81, 2001)
            ax.plot(t, a[key+'_target'], color='#252525', lw=1.2, label='Recorded mean')
            ax.plot(t, a[key+'_identity'], color='#df9b47', lw=1, label='Linear')
            ax.plot(t, a[key+'_nonlinear'], color='#087e8b', lw=1.1, label='Nonlinear')
            ax.set(title=f"{c['bandwidth_hz']} Hz: error / SD {c['metrics']['identity']['normalized_rmse']:.3f} → {c['metrics']['nonlinear']['normalized_rmse']:.3f}",
                   xlabel='Published time (ms)', ylabel='Relative voltage (mV)', xlim=(81, 2000))
            ax.grid(alpha=.15)
        axes[0, col].legend(ncol=3, fontsize=8, loc='lower right')
    fig.suptitle('Offline nonlinear response fit: mixed improvement, overall gate FAILED\n'
                 'Left: reserved brighter background (BG1.5)    |    Right: previous background regression check (BG0.5)', fontsize=14)
    fig.savefig(path/'comparison.png', dpi=150)
    plt.close(fig)


if __name__ == '__main__': main()

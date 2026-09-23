"""Plot saved held-out predictions; never fits a model."""
import argparse
import json
from pathlib import Path
import numpy as np
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument('--path', default='results/causal_filter_v1')
    args = ap.parse_args()
    path = Path(args.path)
    report = json.loads((path/'report.json').read_text())
    protocol = json.loads((path/'frozen_protocol.json').read_text())
    data = np.load(path/'predictions.npz', allow_pickle=False)
    fig, axes = plt.subplots(4, 1, figsize=(12, 10), layout='constrained')
    for ax, check in zip(axes, report['same_cell_test']):
        hz = check['bandwidth_hz']
        target = data[f'hz{hz}_target']
        t = (np.arange(len(target))+protocol['max_lag_samples']+1)*protocol['dt_ms']
        ax.plot(t, data[f'hz{hz}_baseline'], color='#adb5bd', lw=1, label='Current-input control')
        ax.plot(t, target, color='#252525', lw=1.4, label='Measured mean of 20 trials')
        ax.plot(t, data[f'hz{hz}_prediction'], color='#087e8b', lw=1.3, label='Causal filter prediction')
        ax.set(title=f"Held-out {hz} Hz stimulus | RMSE / waveform SD = {check['fir']['normalized_rmse']:.3f}",
               ylabel='Relative voltage (mV)', xlabel='Published time (ms)', xlim=(81, 2000))
        ax.grid(alpha=.15)
    axes[0].legend(loc='upper right', ncol=3, fontsize=8)
    weights = report['model']['weights_current_to_lag80']
    axes[3].plot(np.arange(len(weights))*protocol['dt_ms'], weights, color='#087e8b')
    axes[3].axhline(0, color='gray', lw=.7)
    axes[3].set(xlabel='Past-input lag (ms)', ylabel='Fitted weight',
                title='81-coefficient causal filter fitted on 20 and 50 Hz stimuli only')
    axes[3].grid(alpha=.15)
    fig.suptitle('Offline R1-R6 response benchmark: overall acceptance gate FAILED\n'
                 'Better than controls; 100 and 200 Hz errors exceed the frozen 0.35 target', fontsize=14)
    fig.savefig(path/'comparison.png', dpi=160)
    plt.close(fig)


if __name__ == '__main__':
    main()

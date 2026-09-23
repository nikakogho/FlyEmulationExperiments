"""Plot an audited numerical archive using the project plotting environment."""
from pathlib import Path
import argparse, json
import numpy as np


def main():
    ap = argparse.ArgumentParser(); ap.add_argument('--path', required=True); args=ap.parse_args()
    out=Path(args.path)
    report=json.loads((out/'audit.json').read_text()); rows=report['measurements']
    with np.load(out/'voltage_trials.npz') as z: arrays={k:z[k] for k in z.files}
    import sys
    sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
    from flyplasticity.temporal_sampling import sampling_error
    import matplotlib
    matplotlib.use('Agg')
    import matplotlib.pyplot as plt
    fig, axes = plt.subplots(1, 2, figsize=(12, 4), constrained_layout=True)
    # Prespecified example: brightest background, 100 Hz input bandwidth.
    y = arrays['bg4_hz100'].mean(axis=1)
    _, coarse = sampling_error(y, 10)
    axes[0].plot(np.arange(1, 501), y[:500], label='Published mean, 1 ms')
    axes[0].plot(np.arange(1, 501), coarse[:500], label='10 ms samples, interpolated', alpha=.8)
    axes[0].set(xlabel='Time (ms)', ylabel='Voltage response (mV)', title='Same measured response, different sampling')
    axes[0].legend(fontsize=8)
    for number in range(4):
        entries = rows[number*5:number*5+5]
        axes[1].plot([r['bandwidth_hz'] for r in entries],
            [r['mean_voltage_sampling']['100']['normalized_rmse'] for r in entries], 'o-', label=f'BG {[0,.5,1,1.5][number]}')
    axes[1].set(xlabel='Published input bandwidth (Hz)', ylabel='RMSE / response temporal SD', title='Waveform distortion at 100 Hz acquisition')
    axes[1].legend(fontsize=8)
    fig.savefig(out/'sampling.png', dpi=150)


if __name__ == '__main__': main()

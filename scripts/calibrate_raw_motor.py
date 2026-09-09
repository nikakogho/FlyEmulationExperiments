"""Verify two public recording archives and fit offline passive/probe responses."""
from pathlib import Path
import sys, json, hashlib, zipfile, argparse
ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
import numpy as np
from scipy.io import loadmat
from flyplasticity.raw_motor_calibration import aligned_probe, passive_pulse, fit_probe_trials
from flyplasticity.figure_twitch import twitch

ARCHIVES = {
    '180222_F1_C1': ('CurrentStep2T', 98, 126, 199758273,
                    'c904f419a52f7993f4146e578a760168178b0dc9ea61c19e9708f2adc99a6e33', 585425),
    '180405_F3_C1': ('EpiFlash2T', 42, 125, 450813051,
                    '9c685045d6f74823c9ceec22e8cd51df11dea80ab68fb58a040f6bbddeafd51e', 585433),
}


def verify_archive(path, size, digest):
    if path.stat().st_size != size:
        raise ValueError('Incomplete archive: ' + str(path))
    with path.open('rb') as stream:
        actual = hashlib.file_digest(stream, 'sha256').hexdigest()
    if actual != digest:
        raise ValueError('Archive checksum mismatch: ' + str(path))
    return actual


def evaluate(traces, fit):
    parameters = [fit[k] for k in ('amplitude_um', 'tau_ms', 'delay_ms')]
    mse = [float(np.mean((twitch(t, *parameters)-y)**2)) for t, y in traces]
    null = [float(np.mean(y*y)) for _, y in traces]
    return {'rmse_um': float(np.sqrt(np.mean(mse))),
            'zero_response_rmse_um': float(np.sqrt(np.mean(null))),
            'mse_reduction_vs_zero_fraction': float(1-np.mean(mse)/np.mean(null)),
            'per_trial_rmse_um': np.sqrt(mse).tolist()}


def main():
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument('--recordings', default='data/motor_physiology/recordings')
    ap.add_argument('--out', default='results/raw_motor_calibration')
    args = ap.parse_args(); out = ROOT / args.out; out.mkdir(exist_ok=False)
    report = {'status': 'offline_raw_recording_calibration', 'neural_steps': 0,
              'embodied_use_enabled': False, 'cells': {},
              'dataset_doi': '10.5061/dryad.76hdr7stb', 'dataset_version': 105831,
              'analysis_commit': 'c68159f1f7a4ecc957c708ae8411fd2550482f63',
              'timing_helper_commit': 'd9f18ffa3b2a13c7c8434450191e08be436d6d08',
              'um_per_pixel': float(np.sqrt(1.03)),
              'scale_basis': 'Paper states 1.03 square micrometres per pixel; square root gives linear pitch.',
              'split': 'Chronological first two thirds train, final third evaluation, separately per assay. Exploratory, not preregistered.',
              'limitations': [
                  'Fit predicts loaded probe displacement conditional on one observed spike, not neuron recruitment or unloaded joint torque.',
                  'Whole-cell and optogenetic assays analyzed separately; not interchangeable cross-animal validation.',
                  '180405 acquisition genotype conflicts with curated author dataset label; intermediate class follows published analysis table, not acquisition field.',
                  'Evaluation trials excluded from numerical fitting, but exploratory inspection occurred; not a confirmatory blinded validation.',
                  'Small-sample intervals resample trials within a cell; not population or between-animal confidence.',
                  'Frame end timestamps follow author code; exposure integration and tracking introduce timing uncertainty.',
                  'No raw video re-tracking; archived spike annotations and probe tracking are inherited.',
                  'No functional-equivalent suffering assessment from offline data analysis.']}
    plot_data = {}
    for cell, (protocol, lo, hi, size, expected, file_id) in ARCHIVES.items():
        path = ROOT / args.recordings / (cell + '.zip')
        digest = verify_archive(path, size, expected)
        rows, singles, traces, frame_audits = [], [], [], []
        with zipfile.ZipFile(path) as z:
            genotype = loadmat(z.open('Acquisition_' + cell + '.mat'), simplify_cells=True)['acqStruct']['flygenotype']
            for number in range(lo, hi+1):
                name = f'{protocol}_Raw_{cell}_{number}.mat'
                with z.open(name) as stream:
                    d = loadmat(stream, simplify_cells=True)
                row = {'trial': number, 'excluded_by_author': bool(d.get('excluded', False))}
                if row['excluded_by_author']:
                    rows.append(row); continue
                row['spike_count'] = int(np.atleast_1d(d.get('spikes', [])).size)
                row['sample_rate_hz'] = float(d['params']['sampratein'])
                row['passive'] = passive_pulse(d['current_1'], d['voltage_1'], row['sample_rate_hz'])
                t = np.arange(len(d['voltage_1'])) / row['sample_rate_hz'] - d['params']['preDurInSec']
                baseline = (t > -.05) & (t < -.01)
                row['prestimulus_voltage_mv_ljp_corrected'] = float(np.mean(d['voltage_1'][baseline])-13)
                row['prestimulus_measured_current_pa'] = float(np.mean(d['current_1'][baseline]))
                if row['spike_count'] == 1:
                    tt, yy, audit = aligned_probe(d)
                    singles.append(number); traces.append((tt, yy)); frame_audits.append(dict(trial=number, **audit))
                rows.append(row)
        accepted = [r for r in rows if not r['excluded_by_author']]
        cut = len(accepted) * 2 // 3
        train, test = accepted[:cut], accepted[cut:]
        x = np.array([r['passive']['delta_current_pa'] for r in train])
        y = np.array([r['passive']['delta_voltage_mv'] for r in train])
        resistance = float(1000 * np.dot(x, y) / np.dot(x, x))
        tx = np.array([r['passive']['delta_current_pa'] for r in test])
        ty = np.array([r['passive']['delta_voltage_mv'] for r in test])
        passive = {'fitted_resistance_mohm': resistance,
                   'train_trials': [r['trial'] for r in train], 'evaluation_trials': [r['trial'] for r in test],
                   'evaluation_voltage_rmse_mv': float(np.sqrt(np.mean((tx*resistance/1000-ty)**2))),
                   'published_300mohm_reference_rmse_mv': float(np.sqrt(np.mean((tx*.3-ty)**2))),
                   'zero_response_rmse_mv': float(np.sqrt(np.mean(ty**2))),
                   'recording_mean_resistance_mohm': float(np.mean([r['passive']['resistance_mohm'] for r in accepted])),
                   'recording_median_resistance_mohm': float(np.median([r['passive']['resistance_mohm'] for r in accepted])),
                   'prestimulus_voltage_mv_ljp_corrected_median': float(np.median([r['prestimulus_voltage_mv_ljp_corrected'] for r in accepted])),
                   'voltage_note': 'Pre-stimulus recording voltage, not necessarily unheld resting potential; -13mV post hoc correction.'}
        cut = len(traces) * 2 // 3
        fit = fit_probe_trials(traces[:cut])
        rng = np.random.default_rng(56754)
        boot = [fit_probe_trials([traces[i] for i in rng.integers(0, cut, cut)]) for _ in range(200)]
        ci = {k: np.percentile([b[k] for b in boot], [2.5, 97.5]).tolist()
              for k in ['amplitude_um', 'time_to_peak_ms']}
        evaluation = evaluate(traces[cut:], fit)
        figure_report = ROOT / 'results/published_twitch/report.json'
        if figure_report.exists():
            figure_fit = json.loads(figure_report.read_text())['fit']
            evaluation['previous_figure_fit_rmse_um'] = evaluate(traces[cut:], figure_fit)['rmse_um']
            evaluation['previous_figure_report_sha256'] = hashlib.sha256(figure_report.read_bytes()).hexdigest()
        differences = []
        params = [fit[k] for k in ('amplitude_um', 'tau_ms', 'delay_ms')]
        for tt, yy in traces[cut:]:
            differences.append(float(np.mean(yy**2)-np.mean((twitch(tt, *params)-yy)**2)))
        improvement_ci = np.percentile([np.mean(rng.choice(differences, len(differences))) for _ in range(1000)], [2.5, 97.5]).tolist()
        probe = {'fit': fit, 'train_trials': singles[:cut], 'evaluation_trials': singles[cut:],
                 'train': evaluate(traces[:cut], fit), 'evaluation': evaluation,
                 'bootstrap_training_trial_95_percentile': ci,
                 'evaluation_mse_improvement_um2_bootstrap_95_percentile': improvement_ci,
                 'beats_zero_on_evaluation_point_estimate': evaluation['mse_reduction_vs_zero_fraction'] > 0,
                 'frame_alignment_audit': frame_audits,
                 'traces': [dict(trial=n, time_ms=tt.tolist(), displacement_um=yy.tolist())
                            for n, (tt, yy) in zip(singles, traces)]}
        # Sensitivity only: conversion of pixels scales amplitude linearly.
        probe['scale_sensitivity_amplitude_um'] = {
            str(s): fit['amplitude_um'] * s / np.sqrt(1.03) for s in [1., np.sqrt(1.03), 1.03]}
        report['cells'][cell] = {'archive_sha256': digest, 'archive_size': size,
                               'download_url': f'https://datadryad.org/downloads/file_stream/{file_id}',
                               'protocol': protocol, 'acquisition_genotype_verbatim': genotype,
                               'curated_author_class': 'intermediate / 22A08',
                               'genotype_metadata_conflict': cell == '180405_F3_C1',
                               'trial_audit': rows, 'passive': passive, 'single_spike_probe': probe}
        plot_data[cell] = (traces, cut, fit)
    (out / 'report.json').write_text(json.dumps(report, indent=2, allow_nan=False))
    import matplotlib
    matplotlib.use('Agg')
    import matplotlib.pyplot as plt
    fig, axes = plt.subplots(2, 2, figsize=(11, 7), sharex=True)
    for row, (cell, (traces, cut, fit)) in enumerate(plot_data.items()):
        for col, (label, group) in enumerate([('Training', traces[:cut]), ('Evaluation', traces[cut:])]):
            ax = axes[row, col]
            for tt, yy in group: ax.plot(tt, yy, alpha=.45, lw=.8)
            dense = np.linspace(-20, 120, 300)
            ax.plot(dense, twitch(dense, *[fit[k] for k in ('amplitude_um', 'tau_ms', 'delay_ms')]), 'k', lw=2, label='Training-fit prediction')
            ax.axhline(0, color='gray', ls=':', lw=1)
            ax.set_title(f'{cell}: {label}, n={len(group)}')
            ax.set_ylabel('Probe displacement (um)'); ax.set_xlabel('Time from recorded spike (ms)')
    axes[0, 0].legend(fontsize=8)
    fig.suptitle('Raw recordings: fixed single-spike probe model, separate assays')
    fig.tight_layout(); fig.savefig(out / 'fit.png', dpi=150); plt.close(fig)
    print(json.dumps({k: {'resistance_mohm': v['passive']['fitted_resistance_mohm'],
                         'probe_fit': v['single_spike_probe']['fit'],
                         'probe_evaluation': v['single_spike_probe']['evaluation']}
                      for k, v in report['cells'].items()}, indent=2))


if __name__ == '__main__':
    main()

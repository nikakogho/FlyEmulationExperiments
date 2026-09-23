"""Independently check saved predictions using convolution, not design matrices."""
import argparse
import hashlib
import json
from pathlib import Path
import numpy as np


def digest(path):
    return hashlib.sha256(Path(path).read_bytes()).hexdigest()


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument('--path', default='results/causal_filter_v1')
    ap.add_argument('--data', default='results/origin_audit_v1')
    args = ap.parse_args()
    root = Path(__file__).resolve().parents[1]
    path, source = root/args.path, root/args.data
    r = json.loads((path/'report.json').read_text())
    p = json.loads((path/'frozen_protocol.json').read_text())
    if digest(path/'frozen_protocol.json') != r['protocol_sha256']:
        raise ValueError('Protocol hash mismatch')
    if digest(source/'paired_recordings.npz') != r['data_sha256']:
        raise ValueError('Data hash mismatch')
    if digest(source/'audit.json') != r['audit_sha256']:
        raise ValueError('Audit hash mismatch')
    if digest(path/'predictions.npz') != r['predictions_sha256']:
        raise ValueError('Prediction hash mismatch')
    for name, sha in r['code_sha256'].items():
        if digest(root/name) != sha:
            raise ValueError('Benchmark source changed since run')
    if set(p['training_bandwidths_hz']) & set(p['test_bandwidths_hz']):
        raise ValueError('Training/test condition overlap')
    if p['development_fit_raw_slice'][1] >= p['development_validation_raw_slice'][0]:
        raise ValueError('Development block overlap')
    if p['transfer_columns'] != ['n2', 'n3', 'n4', 'n5', 'n6', 'n7']:
        raise ValueError('Duplicate cell included or unsupported population mapping')
    data = np.load(source/'paired_recordings.npz', allow_pickle=False)
    saved = np.load(path/'predictions.npz', allow_pickle=False)
    w, intercept = np.asarray(r['model']['weights_current_to_lag80']), r['model']['intercept_mV']
    lag, bg = p['max_lag_samples'], p['background_origin_index']
    if len(w) != lag+1 or p['dt_ms'] != 1 or bg != 1:
        raise ValueError('Unsupported filter clock/background')
    errors, passed, transfer_errors = [], [], []
    for check in r['same_cell_test']:
        hz = check['bandwidth_hz']
        key = f'dc{bg}_hz{hz}'
        x = data[key+'_stimulus']
        pred = np.convolve(x, w, mode='full')[lag:len(x)]+intercept
        target = data[key+'_trials'].mean(axis=1)[lag:]
        errors.append(float(np.max(abs(pred-saved[f'hz{hz}_prediction']))))
        np.testing.assert_allclose(pred, saved[f'hz{hz}_prediction'], rtol=0, atol=1e-10)
        np.testing.assert_array_equal(target, saved[f'hz{hz}_target'])
        nrmse = float(np.linalg.norm(target-pred) / np.linalg.norm(target-target.mean()))
        np.testing.assert_allclose(nrmse, check['fir']['normalized_rmse'], rtol=0, atol=1e-12)
        a = p['acceptance']
        # Recompute baseline error ratios from arrays rather than trusting summary fields.
        base_ratio = np.linalg.norm(target-pred)/np.linalg.norm(target-saved[f'hz{hz}_baseline'])
        shift_ratio = np.linalg.norm(target-pred)/np.linalg.norm(target-saved[f'hz{hz}_shifted'])
        gate = bool(nrmse <= a['same_cell_each_test_nrmse_max']
            and base_ratio <= a['same_cell_each_rmse_ratio_to_current_input_max']
            and shift_ratio <= a['same_cell_each_rmse_ratio_to_shifted_training_max'])
        if gate != check['passes']:
            raise ValueError('Condition gate inconsistent with measured errors')
        passed.append(gate)
        population = data[key+'_population'][lag:, 1:]
        np.testing.assert_array_equal(population, saved[f'hz{hz}_population'])
        for y in population.T:
            transfer_errors.append(float(np.linalg.norm(y-pred)/np.linalg.norm(y-y.mean())))
    median = float(np.median(transfer_errors))
    np.testing.assert_allclose(median, r['transfer_median_nrmse'], rtol=0, atol=1e-12)
    same, transfer = all(passed), median <= p['acceptance']['transfer_median_nrmse_max']
    if (same != r['same_cell_gate'] or transfer != r['transfer_gate']
            or r['status'] != ('passed' if same and transfer else 'failed')):
        raise ValueError('Overall gate inconsistent')
    result = dict(status='passed', meaning='Saved numerical evidence is internally consistent; model acceptance remains '+r['status'],
        max_convolution_disagreement_mV=max(errors),
        script_sha256=digest(Path(__file__)), report_sha256=digest(path/'report.json'))
    dst = path/'independent_check.json'
    if dst.exists():
        raise ValueError('Refusing to overwrite evidence check')
    dst.write_text(json.dumps(result, indent=2)+'\n', encoding='utf-8')
    print(json.dumps(result, indent=2))


if __name__ == '__main__':
    main()

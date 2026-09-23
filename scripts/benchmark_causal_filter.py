"""Execute the frozen offline FIR benchmark, with no neural dependencies."""
import argparse
import hashlib
import json
from pathlib import Path
import sys
import numpy as np

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
from flyplasticity.causal_filter import causal_rows, fit_ridge, prediction_error


def digest(path):
    return hashlib.sha256(Path(path).read_bytes()).hexdigest()


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument('--data', default='results/origin_audit_v1')
    ap.add_argument('--protocol', default='research/calibration/causal_filter_protocol.json')
    ap.add_argument('--out', required=True)
    args = ap.parse_args()
    protocol_path = ROOT/args.protocol
    protocol = json.loads(protocol_path.read_text())
    source_dir, out = ROOT/args.data, ROOT/args.out
    audit_path, data_path = source_dir/'audit.json', source_dir/'paired_recordings.npz'
    audit = json.loads(audit_path.read_text())
    if audit['status'] != 'passed' or digest(data_path) != audit['arrays_sha256']:
        raise ValueError('Paired recording integrity check failed')
    out.mkdir(parents=True, exist_ok=False)
    (out/'frozen_protocol.json').write_bytes(protocol_path.read_bytes())
    data = np.load(data_path, allow_pickle=False)
    lag = protocol['max_lag_samples']
    bg = protocol['background_origin_index']
    train_hz = protocol['training_bandwidths_hz']

    def records(hz):
        key = f'dc{bg}_hz{hz}'
        return data[key+'_stimulus'], data[key+'_trials'].mean(axis=1)

    def training_rows(bounds, shifted=False):
        xs, ys = [], []
        start, stop = bounds
        for hz in train_hz:
            x, y = records(hz)
            if shifted:
                x = np.roll(x, protocol['negative_control_shift_samples'])
            xs.append(causal_rows(x[start:stop], lag))
            ys.append(y[start+lag:stop])
        return np.concatenate(xs), np.concatenate(ys)

    dx, dy = training_rows(protocol['development_fit_raw_slice'])
    vx, vy = training_rows(protocol['development_validation_raw_slice'])
    development = []
    for penalty in protocol['ridge_penalties']:
        model = fit_ridge(dx, dy, penalty)
        development.append(dict(penalty=penalty, **prediction_error(vy, model.predict(vx))))
    selected = min(development, key=lambda d:d['rmse_mV'])['penalty']
    tx, ty = training_rows([0, 2000])
    model = fit_ridge(tx, ty, selected)
    baseline = fit_ridge(tx[:, :1], ty, 0.)
    sx, sy = training_rows([0, 2000], shifted=True)
    shuffled = fit_ridge(sx, sy, selected)
    checks, transfer, predictions = [], [], {}
    thresholds = protocol['acceptance']
    for hz in protocol['test_bandwidths_hz']:
        x, y = records(hz)
        rows = causal_rows(x, lag)
        target = y[lag:]
        pred = model.predict(rows)
        base_pred, shift_pred = baseline.predict(rows[:, :1]), shuffled.predict(rows)
        fitted, base, shift = [prediction_error(target, v) for v in (pred, base_pred, shift_pred)]
        ratio_base, ratio_shift = fitted['rmse_mV']/base['rmse_mV'], fitted['rmse_mV']/shift['rmse_mV']
        checks.append(dict(bandwidth_hz=hz, fir=fitted, current_input=base, shifted_training=shift,
            rmse_ratio_to_current_input=ratio_base, rmse_ratio_to_shifted_training=ratio_shift,
            passes=bool(fitted['normalized_rmse'] <= thresholds['same_cell_each_test_nrmse_max']
                and ratio_base <= thresholds['same_cell_each_rmse_ratio_to_current_input_max']
                and ratio_shift <= thresholds['same_cell_each_rmse_ratio_to_shifted_training_max'])))
        population = data[f'dc{bg}_hz{hz}_population']
        for col in protocol['transfer_columns']:
            index = int(col.removeprefix('n'))-1
            transfer.append(dict(bandwidth_hz=hz, source_column=col,
                **prediction_error(population[lag:, index], pred)))
        predictions[f'hz{hz}_target'] = target
        predictions[f'hz{hz}_prediction'] = pred
        predictions[f'hz{hz}_baseline'] = base_pred
        predictions[f'hz{hz}_shifted'] = shift_pred
        predictions[f'hz{hz}_population'] = population[lag:, 1:]
    median_transfer = float(np.median([v['normalized_rmse'] for v in transfer]))
    same_cell_pass = all(v['passes'] for v in checks)
    transfer_pass = median_transfer <= thresholds['transfer_median_nrmse_max']
    np.savez_compressed(out/'predictions.npz', **predictions)
    report = dict(status='passed' if same_cell_pass and transfer_pass else 'failed',
        same_cell_gate=same_cell_pass, transfer_gate=transfer_pass,
        protocol_sha256=digest(protocol_path), audit_sha256=digest(audit_path),
        data_sha256=digest(data_path), predictions_sha256=digest(out/'predictions.npz'),
        development=development, selected_penalty=selected,
        same_cell_test=checks, transfer=transfer, transfer_median_nrmse=median_transfer,
        model=dict(weights_current_to_lag80=model.weights.tolist(), intercept_mV=model.intercept),
        welfare='Offline matrix operations on recorded data. No neural recipient, recurrent cellular state, needs, reward, valence, body or connectome execution.',
        limitations=protocol['limitations'],
        code_sha256={p:digest(ROOT/p) for p in ['scripts/benchmark_causal_filter.py', 'flyplasticity/causal_filter.py']})
    (out/'report.json').write_text(json.dumps(report, indent=2)+'\n', encoding='utf-8')
    print(json.dumps({k:report[k] for k in ('status', 'selected_penalty', 'same_cell_gate',
                                         'transfer_gate', 'transfer_median_nrmse')}, indent=2))


if __name__ == '__main__':
    main()

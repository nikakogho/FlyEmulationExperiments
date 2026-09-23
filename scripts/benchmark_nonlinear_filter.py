"""Two-phase selection/evaluation benchmark on archived numbers only."""
import argparse
import hashlib
import json
from pathlib import Path
import sys
import numpy as np

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
from flyplasticity.causal_filter import causal_rows, fit_ridge, prediction_error
from flyplasticity.nonlinear_filter import transform_light

IDENTITY = dict(kind='identity', parameter=1.)
CODE = ['scripts/benchmark_nonlinear_filter.py', 'flyplasticity/nonlinear_filter.py',
        'flyplasticity/causal_filter.py']


def digest(path):
    return hashlib.sha256(Path(path).read_bytes()).hexdigest()


def write_json(path, value):
    with Path(path).open('x', encoding='utf-8') as f:
        json.dump(value, f, indent=2, allow_nan=False)
        f.write('\n')


def validate_protocol(p):
    # This first protocol has a deliberately narrow supported scope.
    if (p['selection_background'] != 1 or p['new_evaluation_background'] != 3
            or p['training_bandwidths'] != [20, 50]
            or p['evaluation_bandwidths'] != [100, 200, 500]
            or p['development_fit_slice'] != [0, 1200]
            or p['development_validation_slice'] != [1400, 2000]
            or p['lag_samples'] != 80 or p['dt_ms'] != 1):
        raise ValueError('Unsupported split or clock; requires a new reviewed protocol')


def training_data(data, p, bg, transform, bounds, shift=0):
    xs, ys = [], []
    start, stop = bounds
    lag = p['lag_samples']
    for hz in p['training_bandwidths']:
        key = f'dc{bg}_hz{hz}'
        x = data[key+'_stimulus']
        if shift:
            x = np.roll(x, shift)
        xs.append(causal_rows(transform_light(x[start:stop], **transform), lag))
        ys.append(data[key+'_trials'][start+lag:stop].mean(axis=1))
    return np.concatenate(xs), np.concatenate(ys)


def select(data, p):
    """Only accesses the two selection-background training conditions."""
    scores = []
    for transform in [IDENTITY]+p['nonlinear_candidates']:
        tx, ty = training_data(data, p, p['selection_background'], transform, p['development_fit_slice'])
        vx, vy = training_data(data, p, p['selection_background'], transform, p['development_validation_slice'])
        for penalty in p['penalties']:
            model = fit_ridge(tx, ty, penalty)
            scores.append(dict(transform=transform, penalty=penalty,
                **prediction_error(vy, model.predict(vx))))
    identity = min([r for r in scores if r['transform']['kind'] == 'identity'], key=lambda r:r['rmse_mV'])
    nonlinear = min([r for r in scores if r['transform']['kind'] != 'identity'], key=lambda r:r['rmse_mV'])
    ratio = nonlinear['rmse_mV']/identity['rmse_mV']
    return dict(scores=scores, identity=identity, nonlinear=nonlinear,
        development_rmse_ratio=ratio, development_gate=ratio <= p['acceptance']['development_rmse_ratio_max'])


def evaluate_background(data, p, selection, bg):
    lag = p['lag_samples']
    fitted = {}
    for name in ('identity', 'nonlinear'):
        config = selection[name]
        tx, ty = training_data(data, p, bg, config['transform'], [0, 2000])
        fitted[name] = fit_ridge(tx, ty, config['penalty'])
    tx, ty = training_data(data, p, bg, IDENTITY, [0, 2000])
    fitted['current'] = fit_ridge(tx[:, :1], ty, 0.)
    config = selection['nonlinear']
    sx, sy = training_data(data, p, bg, config['transform'], [0, 2000], p['shift_samples'])
    fitted['shifted'] = fit_ridge(sx, sy, config['penalty'])
    arrays, checks = {}, []
    for hz in p['evaluation_bandwidths']:
        key = f'dc{bg}_hz{hz}'
        x, y = data[key+'_stimulus'], data[key+'_trials'][lag:].mean(axis=1)
        identity_rows = causal_rows(x, lag)
        nonlinear_rows = causal_rows(transform_light(x, **config['transform']), lag)
        predictions = dict(identity=fitted['identity'].predict(identity_rows),
            nonlinear=fitted['nonlinear'].predict(nonlinear_rows),
            current=fitted['current'].predict(identity_rows[:, :1]),
            shifted=fitted['shifted'].predict(nonlinear_rows))
        metrics = {name:prediction_error(y, pred) for name,pred in predictions.items()}
        ratios = {name:metrics['nonlinear']['rmse_mV']/metrics[name]['rmse_mV']
                  for name in ('identity', 'current', 'shifted')}
        checks.append(dict(bandwidth_hz=hz, metrics=metrics, nonlinear_rmse_ratios=ratios))
        arrays[key+'_target'] = y
        arrays.update({key+'_'+name:pred for name,pred in predictions.items()})
    pooled_ratio = float(np.sqrt(sum(c['metrics']['nonlinear']['rmse_mV']**2 for c in checks)
                                  /sum(c['metrics']['identity']['rmse_mV']**2 for c in checks)))
    a = p['acceptance']
    gates = dict(pooled_improvement=pooled_ratio <= a['new_pooled_rmse_ratio_to_identity_max'],
        no_condition_regression=all(c['nonlinear_rmse_ratios']['identity'] <= a['new_each_rmse_ratio_to_identity_max'] for c in checks),
        absolute_accuracy=all(c['metrics']['nonlinear']['normalized_rmse'] <= a['new_each_normalized_rmse_max'] for c in checks),
        current_control=all(c['nonlinear_rmse_ratios']['current'] <= a['new_each_rmse_ratio_to_current_max'] for c in checks),
        shifted_control=all(c['nonlinear_rmse_ratios']['shifted'] <= a['new_each_rmse_ratio_to_shifted_max'] for c in checks))
    models = {name:dict(weights=model.weights.tolist(), intercept=model.intercept) for name,model in fitted.items()}
    return dict(background=bg, conditions=checks, pooled_rmse_ratio=pooled_ratio, gates=gates, models=models), arrays


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument('phase', choices=['select', 'evaluate'])
    ap.add_argument('--protocol', default='research/calibration/nonlinear_filter_protocol.json')
    ap.add_argument('--data', default='results/origin_audit_v1')
    ap.add_argument('--out', required=True)
    args = ap.parse_args()
    out = ROOT/args.out
    protocol_path = ROOT/args.protocol
    p = json.loads(protocol_path.read_text())
    validate_protocol(p)
    source = ROOT/args.data
    audit = json.loads((source/'audit.json').read_text())
    data_sha = digest(source/'paired_recordings.npz')
    if audit['status'] != 'passed' or data_sha != audit['arrays_sha256']:
        raise ValueError('Paired data failed integrity check')
    provenance = dict(protocol_sha256=digest(protocol_path), data_sha256=data_sha,
        code_sha256={name:digest(ROOT/name) for name in CODE})
    with np.load(source/'paired_recordings.npz', allow_pickle=False) as data:
        if args.phase == 'select':
            out.mkdir(parents=True, exist_ok=False)
            (out/'frozen_protocol.json').write_bytes(protocol_path.read_bytes())
            selection = select(data, p)
            write_json(out/'selection.json', dict(**selection, provenance=provenance))
            print(json.dumps({k:selection[k] for k in ('identity','nonlinear','development_rmse_ratio','development_gate')}, indent=2))
        else:
            selection = json.loads((out/'selection.json').read_text())
            if selection['provenance'] != provenance or digest(out/'frozen_protocol.json') != provenance['protocol_sha256']:
                raise ValueError('Selection, data, code or protocol changed after freeze')
            if (out/'report.json').exists() or (out/'predictions.npz').exists():
                raise ValueError('Refusing to overwrite evaluation')
            fresh, arrays = evaluate_background(data, p, selection, p['new_evaluation_background'])
            old, old_arrays = evaluate_background(data, p, selection, p['selection_background'])
            arrays.update(old_arrays)
            np.savez_compressed(out/'predictions.npz', **arrays)
            passed = selection['development_gate'] and all(fresh['gates'].values())
            report = dict(status='passed' if passed else 'failed', new_background_evaluation=fresh,
                old_background_regression=old, provenance=provenance,
                selection_sha256=digest(out/'selection.json'), predictions_sha256=digest(out/'predictions.npz'),
                claim_limits=p['claim_limits'], welfare=p['scope'])
            write_json(out/'report.json', report)
            print(json.dumps(dict(status=report['status'], fresh_gates=fresh['gates'],
                                  fresh_pooled_ratio=fresh['pooled_rmse_ratio'], old_pooled_ratio=old['pooled_rmse_ratio']), indent=2))


if __name__ == '__main__':
    main()

"""Freeze development selection, then evaluate a causal two-path recipe."""
import argparse
import json
from pathlib import Path
import sys
import numpy as np
ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
from flyplasticity.causal_filter import fit_ridge, prediction_error
from flyplasticity.two_path_filter import path_rows
from scripts.benchmark_nonlinear_filter import digest, write_json

KINDS = ('linear', 'compressed', 'combined')
CODE = ['scripts/benchmark_two_path.py', 'flyplasticity/two_path_filter.py',
        'flyplasticity/causal_filter.py', 'flyplasticity/nonlinear_filter.py',
        'scripts/benchmark_nonlinear_filter.py']


def training(data, p, bg, kind, bounds, shift=0):
    xs, ys = [], []
    start, stop = bounds
    for hz in p['training_hz']:
        key = f'dc{bg}_hz{hz}'
        x = data[key+'_stimulus']
        if shift: x = np.roll(x, shift)
        xs.append(path_rows(x[start:stop], kind, p['lag']))
        ys.append(data[key+'_trials'][start+p['lag']:stop].mean(axis=1))
    return np.concatenate(xs), np.concatenate(ys)


def select(data, p):
    scores, chosen = [], {}
    for kind in KINDS:
        x, y = training(data, p, p['selection_background'], kind, p['fit_slice'])
        vx, vy = training(data, p, p['selection_background'], kind, p['validation_slice'])
        candidates = []
        for penalty in p['penalties']:
            m = fit_ridge(x, y, penalty)
            candidates.append(dict(kind=kind, penalty=penalty, **prediction_error(vy, m.predict(vx))))
        chosen[kind] = min(candidates, key=lambda c:c['rmse_mV'])
        scores.extend(candidates)
    return dict(scores=scores, chosen=chosen,
                development_ratio=chosen['combined']['rmse_mV']/chosen['linear']['rmse_mV'])


def evaluate(data, p, selection, bg):
    models = {}
    for kind in KINDS:
        x, y = training(data, p, bg, kind, [0, 2000])
        models[kind] = fit_ridge(x, y, selection['chosen'][kind]['penalty'])
    x, y = training(data, p, bg, 'linear', [0, 2000])
    models['current'] = fit_ridge(x[:, :1], y, 0.)
    x, y = training(data, p, bg, 'combined', [0, 2000], p['shift_samples'])
    models['shifted'] = fit_ridge(x, y, selection['chosen']['combined']['penalty'])
    conditions, arrays = [], {}
    for hz in p['evaluation_hz']:
        key = f'dc{bg}_hz{hz}'
        x, y = data[key+'_stimulus'], data[key+'_trials'][p['lag']:].mean(axis=1)
        rows = {k:path_rows(x, k, p['lag']) for k in KINDS}
        rows.update(current=rows['linear'][:, :1], shifted=rows['combined'])
        predictions = {k:m.predict(rows[k]) for k,m in models.items()}
        metrics = {k:prediction_error(y, pred) for k,pred in predictions.items()}
        ratios = {k:metrics['combined']['rmse_mV']/metrics[k]['rmse_mV'] for k in models if k != 'combined'}
        conditions.append(dict(hz=hz, metrics=metrics, ratios=ratios))
        arrays[key+'_target'] = y
        arrays.update({key+'_'+k:v for k,v in predictions.items()})
    pooled = float(np.sqrt(sum(c['metrics']['combined']['rmse_mV']**2 for c in conditions)
                           /sum(c['metrics']['linear']['rmse_mV']**2 for c in conditions)))
    a = p['acceptance']
    gates = dict(pooled_improvement=pooled <= a['reserved_pooled_ratio_to_linear_max'],
        no_regression=all(c['ratios']['linear'] <= a['reserved_each_ratio_to_linear_max'] for c in conditions),
        accuracy=all(c['metrics']['combined']['normalized_rmse'] <= a['reserved_each_nrmse_max'] for c in conditions),
        current=all(c['ratios']['current'] <= a['reserved_each_ratio_to_current_max'] for c in conditions),
        shifted=all(c['ratios']['shifted'] <= a['reserved_each_ratio_to_shifted_max'] for c in conditions))
    return dict(background=bg, conditions=conditions, pooled_ratio=pooled, gates=gates,
        models={k:dict(weights=m.weights.tolist(), intercept=m.intercept) for k,m in models.items()}), arrays


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument('phase', choices=['select', 'evaluate'])
    ap.add_argument('--out', required=True)
    args = ap.parse_args()
    pp = ROOT/'research/calibration/two_path_protocol.json'
    p = json.loads(pp.read_text())
    if (p['selection_background'], p['reserved_background'], p['training_hz'], p['evaluation_hz'],
        p['lag'], p['fit_slice'], p['validation_slice']) != (1, 2, [20, 50], [100, 200, 500], 80, [0, 1200], [1400, 2000]):
        raise ValueError('Unsupported protocol split')
    source = ROOT/'results/origin_audit_v1'
    audit = json.loads((source/'audit.json').read_text())
    data_sha = digest(source/'paired_recordings.npz')
    if audit['status'] != 'passed' or data_sha != audit['arrays_sha256']: raise ValueError('Data integrity failure')
    provenance = dict(protocol_sha256=digest(pp), data_sha256=data_sha,
        code_sha256={n:digest(ROOT/n) for n in CODE})
    out = ROOT/args.out
    with np.load(source/'paired_recordings.npz', allow_pickle=False) as data:
        if args.phase == 'select':
            out.mkdir(parents=True, exist_ok=False)
            (out/'frozen_protocol.json').write_bytes(pp.read_bytes())
            s = select(data, p)
            write_json(out/'selection.json', dict(**s, provenance=provenance))
            print(json.dumps(s['chosen'], indent=2))
        else:
            s = json.loads((out/'selection.json').read_text())
            if s['provenance'] != provenance or digest(out/'frozen_protocol.json') != provenance['protocol_sha256']:
                raise ValueError('Frozen selection changed')
            if (out/'report.json').exists() or (out/'predictions.npz').exists(): raise ValueError('Refusing overwrite')
            fresh, arrays = evaluate(data, p, s, p['reserved_background'])
            regression = []
            for bg in p['regression_backgrounds']:
                r, a = evaluate(data, p, s, bg)
                regression.append(r)
                arrays.update(a)
            np.savez_compressed(out/'predictions.npz', **arrays)
            passed = s['development_ratio'] <= p['acceptance']['development_ratio_to_linear_max'] and all(fresh['gates'].values())
            report = dict(status='passed' if passed else 'failed', reserved=fresh, regression=regression,
                selection_sha256=digest(out/'selection.json'), predictions_sha256=digest(out/'predictions.npz'),
                provenance=provenance, limits=p['limits'], scope=p['scope'])
            write_json(out/'report.json', report)
            print(json.dumps(dict(status=report['status'], pooled_ratio=fresh['pooled_ratio'], gates=fresh['gates']), indent=2))


if __name__ == '__main__': main()

"""Independent convolution and explicit-transform check of saved evidence."""
import argparse
import hashlib
import json
from pathlib import Path
import numpy as np


def digest(path):
    return hashlib.sha256(Path(path).read_bytes()).hexdigest()


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument('--path', default='results/nonlinear_filter_v2')
    ap.add_argument('--data', default='results/origin_audit_v1')
    args = ap.parse_args()
    root = Path(__file__).resolve().parents[1]
    path = root/args.path
    r = json.loads((path/'report.json').read_text())
    p = json.loads((path/'frozen_protocol.json').read_text())
    s = json.loads((path/'selection.json').read_text())
    for file, expected in [(path/'frozen_protocol.json', r['provenance']['protocol_sha256']),
                           (path/'selection.json', r['selection_sha256']),
                           (path/'predictions.npz', r['predictions_sha256']),
                           (root/args.data/'paired_recordings.npz', r['provenance']['data_sha256'])]:
        if digest(file) != expected: raise ValueError('Evidence hash mismatch: '+file.name)
    for name, expected in r['provenance']['code_sha256'].items():
        if digest(root/name) != expected: raise ValueError('Source changed: '+name)
    if r['provenance'] != s['provenance']: raise ValueError('Selection provenance changed')
    expected_selection = min((c for c in s['scores'] if c['transform']['kind'] != 'identity'), key=lambda c:c['rmse_mV'])
    if s['nonlinear'] != expected_selection: raise ValueError('Selection was not best development candidate')
    expected_identity = min((c for c in s['scores'] if c['transform']['kind'] == 'identity'), key=lambda c:c['rmse_mV'])
    if s['identity'] != expected_identity: raise ValueError('Baseline selection mismatch')
    config = s['nonlinear']['transform']
    # Fail closed if this check is used for a different selected mathematical transform.
    if config != dict(kind='signed_log1p', parameter=.5):
        raise ValueError('Independent formula needs review for this transform')
    data = np.load(root/args.data/'paired_recordings.npz', allow_pickle=False)
    saved = np.load(path/'predictions.npz', allow_pickle=False)
    error, recomputed = 0., {}
    for field in ('new_background_evaluation', 'old_background_regression'):
        bg = r[field]['background']
        model_defs = r[field]['models']
        condition_metrics = []
        for condition in r[field]['conditions']:
            key = f"dc{bg}_hz{condition['bandwidth_hz']}"
            x, y = data[key+'_stimulus'], data[key+'_trials'][80:].mean(axis=1)
            np.testing.assert_array_equal(saved[key+'_target'], y)
            transformed = np.copysign(np.log(1+np.abs(x)/.5), x)
            metrics = {}
            for name, model in model_defs.items():
                signal = transformed if name in ('nonlinear', 'shifted') else x
                pred = np.convolve(signal, model['weights'], mode='full')[80:len(x)]+model['intercept']
                error = max(error, float(np.max(abs(pred-saved[key+'_'+name]))))
                np.testing.assert_allclose(pred, saved[key+'_'+name], rtol=0, atol=1e-10)
                rmse = float(np.linalg.norm(y-pred)/np.sqrt(len(y)))
                nrmse = float(np.linalg.norm(y-pred)/np.linalg.norm(y-y.mean()))
                np.testing.assert_allclose([rmse, nrmse],
                    [condition['metrics'][name]['rmse_mV'], condition['metrics'][name]['normalized_rmse']], rtol=0, atol=1e-12)
                metrics[name] = (rmse, nrmse)
            condition_metrics.append(metrics)
        a = p['acceptance']
        pooled = float(np.sqrt(sum(c['nonlinear'][0]**2 for c in condition_metrics)/sum(c['identity'][0]**2 for c in condition_metrics)))
        np.testing.assert_allclose(pooled, r[field]['pooled_rmse_ratio'], rtol=0, atol=1e-12)
        gates = dict(pooled_improvement=pooled <= a['new_pooled_rmse_ratio_to_identity_max'],
            no_condition_regression=all(c['nonlinear'][0]/c['identity'][0] <= a['new_each_rmse_ratio_to_identity_max'] for c in condition_metrics),
            absolute_accuracy=all(c['nonlinear'][1] <= a['new_each_normalized_rmse_max'] for c in condition_metrics),
            current_control=all(c['nonlinear'][0]/c['current'][0] <= a['new_each_rmse_ratio_to_current_max'] for c in condition_metrics),
            shifted_control=all(c['nonlinear'][0]/c['shifted'][0] <= a['new_each_rmse_ratio_to_shifted_max'] for c in condition_metrics))
        if gates != r[field]['gates']: raise ValueError('Gate mismatch')
        recomputed[field] = gates
    dev_gate = s['nonlinear']['rmse_mV']/s['identity']['rmse_mV'] <= p['acceptance']['development_rmse_ratio_max']
    status = 'passed' if dev_gate and all(recomputed['new_background_evaluation'].values()) else 'failed'
    if status != r['status'] or dev_gate != s['development_gate']: raise ValueError('Overall gate mismatch')
    result = dict(status='passed', model_acceptance=status, max_independent_prediction_difference_mV=error,
        report_sha256=digest(path/'report.json'), checker_sha256=digest(__file__),
        checks=['source and artifact hashes', 'development selection rule', 'explicit signed transform',
                'independent convolution', 'all condition metrics and gates'])
    with (path/'independent_check.json').open('x', encoding='utf-8') as f:
        json.dump(result, f, indent=2)
        f.write('\n')
    print(json.dumps(result, indent=2))


if __name__ == '__main__': main()

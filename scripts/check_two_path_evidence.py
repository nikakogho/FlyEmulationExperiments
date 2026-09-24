"""Independent convolution check and plot of the frozen two-path experiment."""
import argparse
import hashlib
import json
from pathlib import Path
import numpy as np


def digest(p):
    return hashlib.sha256(Path(p).read_bytes()).hexdigest()


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument('--path', default='results/two_path_v1')
    args = ap.parse_args()
    root = Path(__file__).resolve().parents[1]
    path = root/args.path
    r = json.loads((path/'report.json').read_text())
    s = json.loads((path/'selection.json').read_text())
    p = json.loads((path/'frozen_protocol.json').read_text())
    source = root/'results/origin_audit_v1/paired_recordings.npz'
    for file, sha in [(source, r['provenance']['data_sha256']),
                      (path/'selection.json', r['selection_sha256']),
                      (path/'predictions.npz', r['predictions_sha256']),
                      (path/'frozen_protocol.json', r['provenance']['protocol_sha256'])]:
        if digest(file) != sha: raise ValueError('Hash mismatch: '+str(file))
    for name, sha in r['provenance']['code_sha256'].items():
        if digest(root/name) != sha: raise ValueError('Source hash mismatch')
    if s['provenance'] != r['provenance']: raise ValueError('Selection changed')
    for kind, choice in s['chosen'].items():
        best = min((v for v in s['scores'] if v['kind'] == kind), key=lambda c:c['rmse_mV'])
        if best != choice: raise ValueError('Selection minimum mismatch')
    source_arrays = np.load(source, allow_pickle=False)
    saved = np.load(path/'predictions.npz', allow_pickle=False)
    max_error = 0.
    blocks = [r['reserved']]+r['regression']
    for block in blocks:
        conditions = []
        for c in block['conditions']:
            key = f"dc{block['background']}_hz{c['hz']}"
            x = source_arrays[key+'_stimulus']
            z = np.copysign(np.log(1+abs(x)/.5), x)
            y = source_arrays[key+'_trials'][80:].mean(axis=1)
            np.testing.assert_array_equal(y, saved[key+'_target'])
            metrics = {}
            for kind, model in block['models'].items():
                w = np.asarray(model['weights'])
                if kind in ('combined', 'shifted'):
                    if len(w) != 162: raise ValueError('Wrong combined feature count')
                    full = np.convolve(x, w[:81])+np.convolve(z, w[81:])
                else:
                    full = np.convolve(z if kind == 'compressed' else x, w)
                pred = full[80:len(x)]+model['intercept']
                max_error = max(max_error, float(np.max(abs(pred-saved[key+'_'+kind]))))
                np.testing.assert_allclose(pred, saved[key+'_'+kind], rtol=0, atol=1e-10)
                rmse = float(np.sqrt(np.mean((y-pred)**2)))
                nrmse = rmse/float(np.std(y))
                np.testing.assert_allclose([rmse,nrmse], [c['metrics'][kind]['rmse_mV'],c['metrics'][kind]['normalized_rmse']], rtol=0, atol=1e-12)
                metrics[kind] = (rmse,nrmse)
            conditions.append(metrics)
        pooled = float(np.sqrt(sum(v['combined'][0]**2 for v in conditions)/sum(v['linear'][0]**2 for v in conditions)))
        np.testing.assert_allclose(pooled, block['pooled_ratio'], rtol=0, atol=1e-12)
        a = p['acceptance']
        gates = dict(pooled_improvement=pooled <= a['reserved_pooled_ratio_to_linear_max'],
            no_regression=all(v['combined'][0]/v['linear'][0] <= a['reserved_each_ratio_to_linear_max'] for v in conditions),
            accuracy=all(v['combined'][1] <= a['reserved_each_nrmse_max'] for v in conditions),
            current=all(v['combined'][0]/v['current'][0] <= a['reserved_each_ratio_to_current_max'] for v in conditions),
            shifted=all(v['combined'][0]/v['shifted'][0] <= a['reserved_each_ratio_to_shifted_max'] for v in conditions))
        if gates != block['gates']: raise ValueError('Gate mismatch')
    dev_ratio = s['chosen']['combined']['rmse_mV']/s['chosen']['linear']['rmse_mV']
    np.testing.assert_allclose(dev_ratio, s['development_ratio'], atol=1e-12, rtol=0)
    status = 'passed' if dev_ratio <= p['acceptance']['development_ratio_to_linear_max'] and all(r['reserved']['gates'].values()) else 'failed'
    if status != r['status']: raise ValueError('Overall acceptance mismatch')
    result = dict(status='passed', model_acceptance=status, max_convolution_disagreement_mV=max_error,
        report_sha256=digest(path/'report.json'), checker_sha256=digest(__file__))
    with (path/'independent_check.json').open('x', encoding='utf-8') as f:
        json.dump(result,f,indent=2); f.write('\n')
    print(json.dumps(result,indent=2))
    import matplotlib
    matplotlib.use('Agg')
    import matplotlib.pyplot as plt
    fig, axes = plt.subplots(3,1,figsize=(12,9),layout='constrained')
    for ax,c in zip(axes,r['reserved']['conditions']):
        key = f"dc2_hz{c['hz']}"
        for name,color in [('target','#252525'),('linear','#df9b47'),('compressed','#999999'),('combined','#087e8b')]:
            ax.plot(np.arange(81,2001),saved[key+'_'+name],color=color,lw=1.1,label=name)
        ax.set(title=f"{c['hz']} Hz: linear error / SD {c['metrics']['linear']['normalized_rmse']:.3f}; combined {c['metrics']['combined']['normalized_rmse']:.3f}",
               xlabel='Published time (ms)',ylabel='Relative voltage (mV)',xlim=(81,2000))
        ax.grid(alpha=.15)
    axes[0].legend(ncol=4,fontsize=8)
    fig.suptitle('Reserved BG1 test: two-path candidate rejected\n11.2% higher pooled prediction error than linear baseline')
    fig.savefig(path/'comparison.png',dpi=150)
    plt.close(fig)


if __name__ == '__main__': main()

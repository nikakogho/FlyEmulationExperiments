"""Read published numerical voltage workbooks; quantify sampling loss.

Run with bundled Python (openpyxl, numpy). Sources stay read-only.
No stimulus-response fitting: the workbooks do not contain paired stimuli.
"""
from pathlib import Path
import argparse
import hashlib
import json
import sys
import urllib.request
import openpyxl
import numpy as np
ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
from flyplasticity.temporal_sampling import sampling_error

HASHES = [
    'cb457117a713ad69c985d687c33d96d46ec027b66718b214be379b048d084c0d',
    '9d32a2fb99166a39bac81522523a5d54e53f2cdeb4f86513c7ef3415c3e0fa9a',
    '22b4b6b0e358ceb4a719720395879cc49bea3fdda3ce592ec09b4d7fc18e6330',
    '4f0d4012f9781646516823cc5132035db2fe078978bf8306a7355caa7e029622',
]


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument('--out', required=True)
    ap.add_argument('--download', action='store_true')
    args = ap.parse_args()
    out = ROOT/args.out; out.mkdir(parents=True, exist_ok=False)
    data = ROOT/'data/receptor_calibration'; data.mkdir(parents=True, exist_ok=True)
    rows, arrays, sources = [], {}, []
    expected_header = [None, 'Time (ms)']+[f'Run{i}' for i in range(1, 21)]+['Mean', 'SD']
    for number, expected_hash in enumerate(HASHES, 1):
        name = f'elife-26117-fig1-data{number}-v1.xlsx'
        path = data/name; url = 'https://cdn.elifesciences.org/articles/26117/'+name
        if not path.exists() and args.download:
            with urllib.request.urlopen(url, timeout=60) as response:
                payload = response.read()
            if hashlib.sha256(payload).hexdigest() != expected_hash:
                raise ValueError('Downloaded source hash mismatch')
            path.write_bytes(payload)
        sha = hashlib.sha256(path.read_bytes()).hexdigest()
        if sha != expected_hash: raise ValueError('Source hash mismatch: '+name)
        sources.append(dict(file=name, url=url, sha256=sha,
            caption_background=[0., .5, 1., 1.5][number-1],
            source_doi=f'10.7554/eLife.26117.{number+4:03d}'))
        workbook = openpyxl.load_workbook(path, read_only=True, data_only=True)
        if len(workbook.worksheets) != 5: raise ValueError('Unexpected worksheet count')
        for frequency, sheet in zip([20, 50, 100, 200, 500], workbook.worksheets):
            values = list(sheet.iter_rows(values_only=True))
            if list(values[0]) != expected_header: raise ValueError('Unexpected column labels')
            a = np.array([r[1:] for r in values[1:]], dtype=float)
            if a.shape != (2000, 23) or not np.isfinite(a).all(): raise ValueError('Invalid response table')
            np.testing.assert_array_equal(a[:, 0], np.arange(1, 2001))
            trials = a[:, 1:21]; mean = trials.mean(axis=1); sd = trials.std(axis=1, ddof=1)
            mean_error = float(np.max(np.abs(mean-a[:, 21])))
            sd_error = float(np.max(np.abs(sd-a[:, 22])))
            if max(mean_error, sd_error) > 1e-5: raise ValueError('Published mean/SD do not reconcile')
            key = f'bg{number}_hz{frequency}'; arrays[key] = trials
            rates = {}
            for stride in [1, 2, 5, 10]:
                rates[str(1000//stride)] = sampling_error(mean, stride)[0]
            rows.append(dict(source=name, sheet=sheet.title, cells='B2:X2001',
                declared_background=sources[-1]['caption_background'], bandwidth_hz=frequency,
                mean_check_max_abs_mV=mean_error, sd_check_max_abs_mV=sd_error,
                original_interval_ms=1, trials=20, duration_s=2,
                mean_voltage_sampling=rates,
                split_trial_mean_rmse_mV=float(np.sqrt(np.mean((trials[:, :10].mean(axis=1)-trials[:, 10:].mean(axis=1))**2)))))
        workbook.close()
    np.savez_compressed(out/'voltage_trials.npz', **arrays)
    report = dict(status='completed', neural_steps=0, biological_cells=1, conditions=20,
        trial_traces=400, voltage_samples=800000, source=sources, measurements=rows,
        tests=dict(all_means_and_sample_sds_reconciled=True, exact_1ms_time_axes=True),
        limitations=['No paired light-input waveform columns; causal kernel fitting is blocked.',
            'Data 3 and 4 retain misleading BG05 sheet names; background comes from publisher captions, not inferred names.',
            'Repeated trials share one cell and the same stimuli; not independent biological replication.',
            'Voltage shifts are recorded response units, not calibrated absolute resting potentials.',
            'Sampling comparisons use instantaneous decimation and linear interpolation, no anti-alias filter.',
            'The published 1 kHz series cannot validate sub-millisecond biological dynamics.'])
    report['code_sha256'] = {p:hashlib.sha256((ROOT/p).read_bytes()).hexdigest() for p in
        ['scripts/audit_voltage_sampling.py', 'flyplasticity/temporal_sampling.py']}
    (out/'audit.json').write_text(json.dumps(report, indent=2)+'\n')
    print(json.dumps({k:report[k] for k in ['status', 'conditions', 'trial_traces', 'voltage_samples', 'tests']}, indent=2))


if __name__ == '__main__': main()

"""Verify Origin extraction against pinned sources and independent Excel export.

Use Python with openpyxl. Writes compact checks and ignored numerical arrays.
"""
import argparse
import gzip
import hashlib
import json
from pathlib import Path
import sys
import numpy as np
import openpyxl

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
from flyplasticity.origin_data import numeric_column, named_columns, trial_matrix
from audit_voltage_sampling import HASHES

SOURCES = [
    ('figure1', 58484, 'd869a74b541b7ff7bb6018e6dc6952c62fb81a8b1a0a1921342703e6c112a7a1',
     '291dabd46d932e790a74f82fc1669c71'),
    ('figure1_supp1', 58485, 'b5684032f04a0d96598e70479fd6650216badb95bad8e8b3c84d700113da39c2',
     'a51bd7e43b413597f50e22b8d0953008')]


def digest(path):
    return hashlib.sha256(Path(path).read_bytes()).hexdigest()


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument('--exports', default='results/origin_extraction_v1')
    ap.add_argument('--out', required=True)
    args = ap.parse_args()
    out = ROOT/args.out
    out.mkdir(parents=True, exist_ok=False)
    data = ROOT/'data/receptor_calibration'
    projects, provenance, graph_refs = [], [], []
    for name, file_id, sha, md5 in SOURCES:
        src, export = data/(name+'.opj'), ROOT/args.exports/(name+'.json.gz')
        payload = src.read_bytes()
        if hashlib.sha256(payload).hexdigest() != sha or hashlib.md5(payload).hexdigest() != md5:
            raise ValueError('Origin source integrity failure')
        with gzip.open(export, 'rt', encoding='utf-8') as f:
            project = json.load(f)
        if project['source_sha256'] != sha or project['parser_revision'] != 'f19e74517059769f9525b477ab934b6f9b1602d5':
            raise ValueError('Unexpected export provenance')
        spreads = {s['name']: s for s in project['spreads']}
        if len(spreads) != 25:
            raise ValueError('Unexpected spreadsheet count')
        refs = {(c['dataName'].removeprefix('T_'), c['xColumnName'], c['yColumnName'])
                for g in project['graphs'] for l in g['layers'] for c in l['curves']}
        projects.append(spreads)
        graph_refs.append(refs)
        provenance.append(dict(file=src.name, bytes=len(payload), sha256=sha, md5=md5,
            dryad_api=f'https://datadryad.org/api/v2/files/{file_id}',
            doi='10.5061/dryad.12751', export_sha256=digest(export),
            parser_revision=project['parser_revision']))
    arrays, rows, workbooks = {}, [], []
    for bg in range(4):
        workbook_path = data/f'elife-26117-fig1-data{bg+1}-v1.xlsx'
        if digest(workbook_path) != HASHES[bg]:
            raise ValueError('Excel source integrity failure')
        wb = openpyxl.load_workbook(workbook_path, read_only=True, data_only=True)
        workbooks.append(dict(file=workbook_path.name, sha256=HASHES[bg]))
        for hz, ws in zip([20, 50, 100, 200, 500], wb.worksheets):
            name, stim_name = f'WN{hz}HzDC{bg}', f'WNstimDC{bg}'
            key = f'dc{bg}_hz{hz}'
            trials = trial_matrix(projects[0][name])
            excel = np.asarray([r for r in ws.iter_rows(min_row=2, min_col=2, max_col=22,
                                                       values_only=True)], dtype=float)
            np.testing.assert_array_equal(excel[:, 0], np.arange(1, 2001))
            excel_error = float(np.max(abs(trials-excel[:, 1:])))
            if excel_error > 1e-8:
                raise ValueError('Origin/Excel voltage mismatch')
            stats = []
            for index, project in enumerate(projects):
                cs, sc = named_columns(project[name]), named_columns(project[stim_name])
                for axis in (cs['A'], sc['A']):
                    np.testing.assert_allclose(numeric_column(axis), np.arange(1, 2001), rtol=0, atol=1e-8)
                if (stim_name, 'A', f'{hz}Hz') not in graph_refs[index] or (name, 'A', 'mean') not in graph_refs[index]:
                    raise ValueError('Missing graph reference for stimulus or response')
                column_names = [n for n in cs if n not in ('A', 'mean', 'SD')]
                values = np.column_stack([numeric_column(cs[n]) for n in column_names])
                mean_error = float(np.max(abs(values.mean(axis=1)-numeric_column(cs['mean']))))
                sd_error = float(np.max(abs(values.std(axis=1, ddof=1)-numeric_column(cs['SD']))))
                if max(mean_error, sd_error) > 1e-8:
                    raise ValueError('Stored mean/SD mismatch')
                stats.append(dict(columns=column_names, mean_max_abs_mV=mean_error, sd_max_abs_mV=sd_error))
                stimulus = numeric_column(sc[f'{hz}Hz'])
                if index == 0:
                    arrays[key+'_stimulus'] = stimulus
                    arrays[key+'_trials'] = trials
                else:
                    np.testing.assert_array_equal(stimulus, arrays[key+'_stimulus'])
                    arrays[key+'_population'] = values
                    if values.shape[1] != [16, 7, 8, 4][bg]:
                        raise ValueError('Population count differs from figure annotations')
                    if bg == 1:
                        if column_names != [f'n{i}' for i in range(1, 8)]:
                            raise ValueError('Unexpected BG0.5 population column identities')
                        np.testing.assert_allclose(values[:, 0], trials.mean(axis=1), rtol=0, atol=1e-12)
            rows.append(dict(key=key, worksheet=name, stimulus_worksheet=stim_name,
                stimulus_column=f'{hz}Hz', time_column='A', samples=2000, dt_ms=1,
                excel_max_abs_mV=excel_error, primary=stats[0], population=stats[1],
                paired_by='worksheet condition names, common 1..2000 ms axes, figure graph references',
                source_background_units=[0, .5, 1., 1.5][bg]))
        wb.close()
    np.savez_compressed(out/'paired_recordings.npz', **arrays)
    report = dict(status='passed', source=provenance, excel_sources=workbooks, conditions=rows,
        stimulus_samples=40000, primary_voltage_samples=800000,
        population_cell_condition_traces=175,
        duplicate_excluded='BG0.5 supplement n1 equals primary mean in all five conditions',
        integrity_note='A positional comparison initially failed because Origin column order differs. Matching n1..n20 by name reconciles all samples.',
        timing_limit='Axes agree as published; instrument latency and sub-ms timing are not independently measured.',
        excluded='80,000-sample responseReps records and non-BG0.5 cell identities are not used in fitting.',
        welfare='Stored numeric data only; no neural or body model advanced.',
        arrays_sha256=digest(out/'paired_recordings.npz'),
        code_sha256={p:digest(ROOT/p) for p in ['scripts/audit_origin_receptors.py',
            'scripts/export_origin_project.py', 'flyplasticity/origin_data.py', 'scripts/origin_reader.Dockerfile']})
    (out/'audit.json').write_text(json.dumps(report, indent=2)+'\n', encoding='utf-8')
    print(json.dumps(dict(status='passed', conditions=20, voltage_samples=800000,
                         max_excel_error=max(r['excel_max_abs_mV'] for r in rows)), indent=2))


if __name__ == '__main__':
    main()

"""Validation of stored Origin numbers; never evaluate worksheet commands."""
import numpy as np

ORIGIN_MISSING = -1.23456789e-300


def numeric_column(column, count=2000):
    """Accept a finite numeric prefix and only missing-value padding after it."""
    raw = column['data']
    if len(raw) < count or any(type(v) not in (int, float) for v in raw):
        raise ValueError('Non-numeric or truncated Origin column')
    a = np.asarray(raw, dtype=float)
    if not np.isfinite(a).all() or np.any(a[:count] == ORIGIN_MISSING):
        raise ValueError('Invalid or missing observation')
    if np.any(a[count:] != ORIGIN_MISSING):
        raise ValueError('Unexpected observations beyond declared record')
    return a[:count].copy()


def named_columns(spread):
    columns = {c['name']: c for c in spread['columns']}
    if len(columns) != len(spread['columns']):
        raise ValueError('Duplicate Origin column name')
    return columns


def trial_matrix(spread, count=2000):
    columns = named_columns(spread)
    expected = {'A', 'mean', 'SD'} | {f'n{i}' for i in range(1, 21)}
    if set(columns) != expected:
        raise ValueError('Unexpected trial names')
    t = numeric_column(columns['A'], count)
    if not np.allclose(t, np.arange(1, count+1), rtol=0, atol=1e-8):
        raise ValueError('Invalid 1 ms time axis')
    return np.column_stack([numeric_column(columns[f'n{i}'], count)
                            for i in range(1, 21)])

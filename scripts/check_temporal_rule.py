"""Causal access and numerical checks; these do not validate fly biology."""
import numpy as np
from temporal_pilot import TemporalLTD


def response(gap, dt=0.01, dopamine=True):
    rule = TemporalLTD(2, np.array([0]), np.array([1]), dt=dt)
    w = np.ones(1)
    for k in range(round(2.5/dt)):
        t = k*dt
        # Deliberately constructed traces, separate from connectome experiments.
        counts = np.zeros(2)
        if t < 0.5:
            counts[0] = 1
        if dopamine and 0.5+gap <= t < 1+gap:
            counts[1] = 60*dt
        w = rule.step(counts, w)
    return w[0]


assert response(0, dopamine=False) == 1.0
assert response(0.1) < response(1.0)
assert 0 < response(0) <= 1
assert abs(response(0.1, 0.01)-response(0.1, 0.005)) < 0.02
print('PASS: zero dopamine leaves weights unchanged; delayed credit decays; bounds; dt check')

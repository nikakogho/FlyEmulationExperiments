"""Python port of Luo/Huang's released recurrent model (GPL-3.0-or-later).

Original: Junjie Luo, Cheng Huang, Mark J. Schnitzer, 2024.
Source commit: 5d7c08a9a88f923169a0c3008aca68af421e9a7f.
This port preserves the released algorithm, including bout approximations.
It is NOT an online spike rule, and fitted timing coefficients apply to +3 s.
All matrices are [presynaptic, postsynaptic]. Times are seconds, rates Hz.
"""
from dataclasses import dataclass, replace
from pathlib import Path
import numpy as np
from scipy.io import loadmat

ROOT = Path(__file__).resolve().parents[1]
UPSTREAM = ROOT / 'upstream/Luo_Huang_2024_MB_model'
BASELINE = np.array([0., 0., 0., 35.2, 9., 11.2])
MAXIMUM = BASELINE[3:] + [36.46, 8.9, 19.96]
PUNISHMENT = np.array([27.85, 0., 11.38, 0., 0., 0.])


@dataclass(frozen=True)
class Bout:
    name: str
    duration: float
    odor: tuple[float, float] = (0., 0.)
    punishment: float = 0.
    imaging: int = 0

    def __post_init__(self):
        values = [self.duration, *self.odor, self.punishment]
        if not np.isfinite(values).all() or self.duration < 0:
            raise ValueError('Bout times and inputs must be finite; duration nonnegative')
        if len(self.odor) != 2 or any(x not in (0., 1.) for x in self.odor) or sum(self.odor) > 1:
            raise ValueError('Released model supports at most one of two odors per bout')
        if self.punishment < 0 or self.imaging not in (0, 1, 2):
            raise ValueError('Invalid punishment or imaging index')


def session(name, n=1, duration=5., interval=120.):
    imaging = name in ('imaging', 'extinction')
    cycle = [Bout(name, duration, (1., 0.), float(name == 'training'), int(imaging)),
             Bout(name, interval),
             Bout(name, duration, (0., 1.), 0., 2 * int(imaging)),
             Bout(name, interval)]
    return cycle * n


def figure5c_protocol():
    """Exact schedule from plotPanel_5c_S10j_R2_CI.m, including trailing ISIs."""
    bouts = []
    for name in ('imaging', 'training', 'imaging', 'training', 'imaging'):
        bouts += session(name, 3, 30., 135.) if name == 'training' else session(name)
    for rest in (3600-250-300, 7200-250, 21*3600-250):
        bouts += [Bout('rest', rest)] + session('imaging')
    for matlab_index in (4, 16, 20, 32):
        bouts[matlab_index-1] = replace(bouts[matlab_index-1], duration=300.)
    return bouts


def fitting_protocol():
    """Schedule of saved native-MATLAB fitting figures, distinct from Fig. 5c."""
    bouts=[]
    for name in ('imaging','training','imaging','training','imaging'):
        bouts += session(name,3,30.,135.) if name=='training' else session(name)
    for rest in (3600.,7200.-250.,21*3600.-500.):
        bouts += [Bout('rest',rest)] + session('imaging')
    return bouts


def parameter_file(modules=3):
    if modules not in (2, 3):
        raise ValueError('modules must be 2 or 3')
    return UPSTREAM / f'data_and_parameters/Dx_steady_state_nonlinear_3_27-Mar-2023_{modules}modules.mat'


def load_parameters(modules=3, ensemble=False, *, path=None):
    """Expand MATLAB column-major parameter cells; retain supplied samples."""
    data = loadmat(parameter_file(modules) if path is None else path)
    vec = data['para_rand'].T if ensemble else data['para_mu'].reshape(1, -1)
    cells, cursor = [], 0
    for bounds in data['mat_lu_cell'].ravel():
        low, high = bounds[..., 0], bounds[..., 1]
        flat = np.tile(low.ravel(order='F'), (len(vec), 1))
        mask = (low != high).ravel(order='F')
        count = int(mask.sum())
        flat[:, mask] = vec[:, cursor:cursor+count]
        cells.append(np.stack([row.reshape(low.shape, order='F') for row in flat]))
        cursor += count
    if cursor != vec.shape[1] or any(not np.isfinite(c).all() for c in cells):
        raise ValueError('Incomplete or nonfinite parameter expansion')
    return cells


def steady_state(kc, punishment, weights, recurrent, iterations=10):
    """Released ten-iteration solver, vectorized across parameter samples."""
    drive = np.einsum('bo,bon->bn', kc, weights) + punishment * PUNISHMENT
    # Preserve the released initialization, which uses I-W, not I-W.T.
    x = np.linalg.solve(np.eye(6)[None] - recurrent, drive[..., None])[..., 0]
    for _ in range(iterations):
        x = drive + BASELINE + np.einsum('bi,bij->bj', x, recurrent)
        x[:, 3:] = np.clip(x[:, 3:], 0., MAXIMUM)
        x -= BASELINE
    return x


def direct_state(kc, punishment, weights, recurrent):
    """Independent DAG solve for the released topology, for numerical checks."""
    if np.any(recurrent[:, :3]) or np.any(recurrent[:, 4:, 3:]) or np.any(recurrent[:, 3, 3]):
        raise ValueError('Direct solve only supports the published feedforward MBON topology')
    drive = np.einsum('bo,bon->bn', kc, weights) + punishment * PUNISHMENT
    x = np.zeros_like(drive)
    x[:, 3] = np.clip(drive[:, 3] + BASELINE[3], 0, MAXIMUM[0]) - BASELINE[3]
    x[:, 4:] = np.clip(drive[:, 4:] + BASELINE[4:] + x[:, 3, None]*recurrent[:, 3, 4:],
                       0., MAXIMUM[1:]) - BASELINE[4:]
    x[:, :3] = drive[:, :3] + np.einsum('bi,bij->bj', x[:, 3:], recurrent[:, 3:, :3])
    return x


def decay_factor(duration, elapsed_after_training, tau):
    """Split intervals exactly at the released 3-hour decay switch."""
    early = np.clip(10800. - (elapsed_after_training-duration), 0., duration)
    late = duration - early
    return np.exp(-early / tau[:, [0, 1, 1]] - late / tau[:, [0, 2, 2]])


def run(cells, bouts, valence='attractive', *, learn=True, solver=steady_state, trace=False):
    """Run a fixed protocol. Disabling learning keeps adaptation but freezes weights.

    Outputs have shape [sample, neuron, odor, imaging session]. Per-bout
    traces are optional. They contain no world positions, targets or actions.
    """
    if valence not in ('attractive', 'repulsive'):
        raise ValueError('Unknown valence')
    columns = [0, 1, 2, 3, 4, 5] if valence == 'attractive' else [6, 7, 8, 3, 4, 5]
    initial = np.repeat(cells[0][:, :, columns], 2, axis=1)
    weights = initial.copy()
    batch = len(weights)
    delta = np.zeros((batch, 2, 3))
    odor_start = np.ones((batch, 2))
    fw0 = cells[1][:, 0, 0]
    fw_dt = cells[2][:, 0, 0]
    recurrent, tau = cells[3], cells[4][:, 0, :]
    recovery = cells[5][:, 0, 0]
    if np.any(tau <= 0) or np.any(recovery <= 0):
        raise ValueError('Time constants must be positive')
    training = [i for i, b in enumerate(bouts) if b.name == 'training']
    last_training = training[-1] if training else -1
    elapsed = 0.
    observations, pending, history = [], None, []
    for index, b in enumerate(bouts):
        odor = np.asarray(b.odor)
        # Exact released split update: recovery is applied even during odor.
        end = odor_start * np.exp(-.05*b.duration*odor)
        end = 1. - (1.-end)*np.exp(-b.duration/recovery[:, None])
        mean = (odor_start+end)/2
        odor_start = end
        kc = mean*odor
        x = solver(kc, b.punishment, weights, recurrent)
        if learn:
            endogenous = np.einsum('bo,bon->bn', kc, weights[:, :, :3])
            endogenous += np.einsum('bi,bij->bj', x[:, 3:], recurrent[:, 3:, :3])
            teaching = fw0[:, None]*endogenous + fw_dt[:, None]*PUNISHMENT[:3]*b.punishment
            delta += (b.duration/90)*kc[:, :, None]*teaching[:, None, :]
        if index > last_training:
            elapsed += b.duration
        delta *= decay_factor(b.duration, elapsed, tau)[:, None, :]
        weights = initial.copy()
        weights[:, :, 3:] += delta
        if b.imaging == 1:
            if pending is not None:
                raise ValueError('Unpaired imaging observations')
            pending = x.copy()
        elif b.imaging == 2:
            if pending is None:
                raise ValueError('Missing first imaging odor')
            observations.append(np.stack([pending, x], axis=2))
            pending = None
        if trace:
            history.append({'rates': x.copy(), 'weights': weights.copy(),
                            'kc': kc.copy(), 'odor_end': end.copy()})
    if pending is not None:
        raise ValueError('Missing second imaging odor')
    result = np.stack(observations, axis=3) if observations else np.empty((batch, 6, 2, 0))
    if not np.isfinite(result).all() or not np.isfinite(weights).all():
        raise FloatingPointError('Nonfinite neural state')
    return result, history

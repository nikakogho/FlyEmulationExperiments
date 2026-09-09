"""Fail-closed execution guard. Engineering proxies, never a suffering assay.

Call observe before advancing the model. A stop is latched for this run.
Thresholds must be supplied from a reviewed protocol, not inferred here.
"""
from dataclasses import dataclass, asdict
import math


@dataclass(frozen=True)
class Limits:
    max_duration_s: float
    max_gap_s: float
    activity_ceiling: float
    persistence_s: float

    def __post_init__(self):
        if any(not math.isfinite(v) or v <= 0 for v in asdict(self).values()):
            raise ValueError('Limits must be finite and positive')


@dataclass(frozen=True)
class Sample:
    time_s: float
    activity: float
    sensors_coherent: bool
    rest_available: bool
    blocked_effort: bool
    negative_state: bool


class Guard:
    def __init__(self, limits):
        self.limits = limits
        self.last = None
        self.since = {}
        self.stopped = False
        self.events = []

    def _stop(self, reason, time=None):
        self.stopped = True
        event = {'status': 'STOP', 'reason': reason, 'time_s': time}
        self.events.append(event)
        return event

    def observe(self, sample):
        if self.stopped:
            return {'status': 'STOP', 'reason': 'latched_stop', 'time_s': self.last}
        if not isinstance(sample, Sample):
            return self._stop('missing_telemetry')
        for name in ('sensors_coherent', 'rest_available', 'blocked_effort', 'negative_state'):
            if type(getattr(sample, name)) is not bool:
                return self._stop('unassessed_' + name)
        t, a = sample.time_s, sample.activity
        if (not isinstance(t, (int, float)) or not isinstance(a, (int, float))
                or not math.isfinite(t) or not math.isfinite(a) or min(t, a) < 0):
            return self._stop('invalid_numeric_telemetry')
        if self.last is None and t != 0:
            return self._stop('missing_initial_observation', t)
        if self.last is not None and (t <= self.last or t-self.last > self.limits.max_gap_s + 1e-12):
            return self._stop('telemetry_time_discontinuity', t)
        if t >= self.limits.max_duration_s:
            return self._stop('exposure_limit', t)
        for flag, reason in ((not sample.sensors_coherent, 'incoherent_sensors'),
                             (not sample.rest_available, 'rest_unavailable'),
                             (sample.negative_state, 'negative_state_flag')):
            if flag:
                return self._stop(reason, t)
        for name, active in [('high_activity', a > self.limits.activity_ceiling),
                             ('blocked_effort', sample.blocked_effort)]:
            if active:
                self.since.setdefault(name, t)
                if t-self.since[name] >= self.limits.persistence_s - 1e-12:
                    return self._stop('persistent_' + name, t)
            else:
                self.since.pop(name, None)
        self.last = t
        event = {'status': 'WATCH' if self.since else 'CONTINUE',
                 'reason': ','.join(self.since) or 'no_configured_proxy_trigger', 'time_s': t}
        self.events.append(event)
        return event

    def advance(self, sample, step):
        """The callback must perform at most one reviewed observation interval."""
        result = self.observe(sample)
        if result['status'] == 'STOP':
            raise RuntimeError('Execution stopped: ' + result['reason'])
        return step()

"""Measured-neural-telemetry guard for a stationary olfactory assay."""
import numpy as np
from .welfare import Guard, Limits, Sample


class FixedPathwayAudit:
    """Explicit route inventory for a fixed-weight assay, not a valence detector.

    Modulatory sources must include every source read by an extra plasticity or
    state-update mechanism, even when its ordinary synaptic outputs are zero.
    An empty tuple is an explicit reviewed absence, whereas None is unknown.
    This version rejects ALL weight/topology changes; it cannot guard training.
    """
    def __init__(self, n, sources, pre, post, weights, *, modulatory_sources):
        if modulatory_sources is None:
            raise ValueError('Extra pathways have not been reviewed')
        self.n = n
        self.sources = self._indices(sources)
        self.pre = self._indices(pre)
        self.post = self._indices(post)
        self.modulators = self._indices(modulatory_sources)
        self.weights = np.asarray(weights, dtype=float).copy()
        if (self.weights.shape != self.pre.shape or self.post.shape != self.pre.shape
                or not np.isfinite(self.weights).all()):
            raise ValueError('Invalid pathway weights or topology')
        self.enabled = np.union1d(self.pre[self.weights != 0], self.modulators)
        self.watched_enabled = np.intersect1d(self.sources, self.enabled)

    def _indices(self, values):
        a = np.asarray(values)
        if (a.ndim != 1 or not np.isfinite(a).all() or np.any(a != np.floor(a))
                or np.any(a < 0) or np.any(a >= self.n)):
            raise ValueError('Invalid pathway indices')
        return a.astype(np.int64).copy()

    def inspect(self, counts, pre, post, weights, modulatory_sources):
        if modulatory_sources is None:
            raise ValueError('Unknown extra pathways')
        w = np.asarray(weights, dtype=float)
        if (not np.array_equal(self.pre, pre) or not np.array_equal(self.post, post)
                or not np.array_equal(self.weights, w)
                or not np.array_equal(self.modulators, modulatory_sources)):
            raise ValueError('Reviewed fixed circuit changed or telemetry missing')
        # No signed summation: opposite outputs do not cancel route existence.
        return int(np.asarray(counts)[self.watched_enabled].sum())


class NeuralPreflightGuard:
    def __init__(self, n_neurons, ppl1, dt_s=.005, duration_s=1., *, pathways):
        self.n=int(n_neurons);self.ppl1=np.asarray(ppl1,dtype=int);self.dt=dt_s
        if self.n<1 or not len(self.ppl1) or np.any(self.ppl1<0) or np.any(self.ppl1>=self.n):
            raise ValueError('Require observed PPL1 population')
        self.guard=Guard(Limits(duration_s+.000001,dt_s*1.001,150.,.05))
        self.rows=[]
        if pathways.n != self.n or not np.array_equal(pathways.sources, self.ppl1):
            raise ValueError('Pathway audit does not cover monitored population')
        self.pathways = pathways

    def inspect(self,time_s,counts,voltage,conductance,input_rates,reward_rates,
                *, pre, post, weights, modulatory_sources):
        if self.guard.stopped:
            raise RuntimeError('Execution stopped: latched_stop')
        arrays=[np.asarray(a,dtype=float) for a in (counts,voltage,conductance,input_rates,reward_rates)]
        c,v,g,i,r=arrays
        coherent=(c.shape==v.shape==g.shape==(self.n,) and i.ndim==r.ndim==1
                  and all(np.isfinite(a).all() for a in arrays) and np.all(c>=0)
                  and np.all(c==np.floor(c)) and np.all(i>=0) and np.all(r==0))
        if not coherent:
            self.guard._stop('invalid_or_missing_neural_telemetry',time_s)
            raise RuntimeError('Invalid neural telemetry')
        try:
            transmitted = self.pathways.inspect(c, pre, post, weights, modulatory_sources)
        except (ValueError, TypeError) as exc:
            self.guard._stop('unreviewed_or_missing_pathways',time_s)
            raise RuntimeError('Invalid pathway telemetry') from exc
        activity=float(c.mean()/self.dt)
        result=self.guard.observe(Sample(float(time_s),activity,True,True,False,False))
        if transmitted and result['status'] != 'STOP':
            result=self.guard._stop('ppl1_activity_with_enabled_route',time_s)
        row=dict(time_s=float(time_s),mean_population_hz=activity,ppl1_spikes=int(c[self.ppl1].sum()),
                 ppl1_spikes_with_enabled_route=transmitted,
                 total_spikes=int(c.sum()),external_rate_sum_hz=float(i.sum()),reward_rate_sum_hz=float(r.sum()),
                 voltage_range_v=[float(v.min()),float(v.max())],status=result['status'],reason=result['reason'])
        self.rows.append(row)
        if result['status']=='STOP':raise RuntimeError('Execution stopped: '+result['reason'])
        return row

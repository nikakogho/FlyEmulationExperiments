"""Measured-neural-telemetry guard for a stationary olfactory assay."""
import numpy as np
from .welfare import Guard, Limits, Sample


class NeuralPreflightGuard:
    def __init__(self, n_neurons, ppl1, dt_s=.005, duration_s=1.):
        self.n=int(n_neurons);self.ppl1=np.asarray(ppl1,dtype=int);self.dt=dt_s
        if self.n<1 or not len(self.ppl1) or np.any(self.ppl1<0) or np.any(self.ppl1>=self.n):
            raise ValueError('Require observed PPL1 population')
        self.guard=Guard(Limits(duration_s+.000001,dt_s*1.001,150.,.05))
        self.rows=[]

    def inspect(self,time_s,counts,voltage,conductance,input_rates,reward_rates):
        arrays=[np.asarray(a,dtype=float) for a in (counts,voltage,conductance,input_rates,reward_rates)]
        c,v,g,i,r=arrays
        coherent=(c.shape==v.shape==g.shape==(self.n,) and i.ndim==r.ndim==1
                  and all(np.isfinite(a).all() for a in arrays) and np.all(c>=0)
                  and np.all(i>=0) and np.all(r==0))
        if not coherent:
            self.guard._stop('invalid_or_missing_neural_telemetry',time_s)
            raise RuntimeError('Invalid neural telemetry')
        activity=float(c.mean()/self.dt);negative=bool(c[self.ppl1].sum()>0)
        result=self.guard.observe(Sample(float(time_s),activity,True,True,False,negative))
        row=dict(time_s=float(time_s),mean_population_hz=activity,ppl1_spikes=int(c[self.ppl1].sum()),
                 total_spikes=int(c.sum()),external_rate_sum_hz=float(i.sum()),reward_rate_sum_hz=float(r.sum()),
                 voltage_range_v=[float(v.min()),float(v.max())],status=result['status'],reason=result['reason'])
        self.rows.append(row)
        if result['status']=='STOP':raise RuntimeError('Execution stopped: '+result['reason'])
        return row

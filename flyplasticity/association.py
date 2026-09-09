"""Bounded candidate gamma-compartment plasticity and its write-set audit.

The learning interface has only spike counts, local weights and a frozen flag.
It has no cue identity, position, success score or external reward-label input.
Parameters are engineering hypotheses, not fitted fly biochemistry.
"""
import numpy as np
from .compartment_plasticity import CompartmentEligibilityLTD
from .learning_preflight import FixedPathwayAudit


def output_compartments(pre,post,gamma_sides,outputs):
    """Infer MBON input hemisphere from actual KC edges, never soma labels."""
    result={}
    for neuron in outputs:
        sides={gamma_sides[int(i)] for i in np.asarray(pre)[np.asarray(post)==neuron]
               if int(i) in gamma_sides}
        if len(sides)!=1 or not sides.issubset({'left','right'}):
            raise ValueError('Missing or mixed gamma input compartment')
        result[int(neuron)]=sides.pop()
    return result


class PlasticPathwayAudit(FixedPathwayAudit):
    def __init__(self, n, sources, pre, post, weights, *, modulatory_sources,
                 plastic_positions, gamma_kcs, output_neurons):
        super().__init__(n,sources,pre,post,weights,modulatory_sources=modulatory_sources)
        p=np.asarray(plastic_positions)
        if (p.ndim!=1 or not len(p) or not np.issubdtype(p.dtype,np.integer)
                or np.any(p<0) or np.any(p>=len(self.weights)) or len(np.unique(p))!=len(p)):
            raise ValueError('Invalid plastic write set')
        if (not np.isin(self.pre[p],gamma_kcs).all()
                or not np.isin(self.post[p],output_neurons).all()
                or np.isin(self.pre[p],self.sources).any() or np.any(self.weights[p]<=0)):
            raise ValueError('Plasticity must use positive gamma-KC to named-output edges')
        self.positions=p.copy();self.initial=self.weights[p].copy()

    def authorize_update(self, current_weights, proposed):
        """Update the expected write set only after the actual pre-write audit.

        Any other edit, sign change, potentiation or >50% depression is rejected.
        This checks allowed writes; causal-rule tests are a separate requirement.
        """
        p=np.asarray(proposed,dtype=float)
        if (not np.array_equal(current_weights,self.weights) or p.shape!=self.initial.shape
                or not np.isfinite(p).all() or np.any(p<.5*self.initial)
                or np.any(p>self.weights[self.positions])):
            raise ValueError('Unreviewed plasticity update')
        self.weights[self.positions]=p


class GammaEligibilityLTD:
    def __init__(self,pre,compartments,pam_groups,n_neurons,initial):
        self.initial=np.asarray(initial,dtype=float).copy()
        if self.initial.shape!=np.asarray(pre).shape or not np.isfinite(self.initial).all() or np.any(self.initial<=0):
            raise ValueError('Require finite positive initial weights')
        self.n=n_neurons
        self.rule=CompartmentEligibilityLTD(pre,compartments,pam_groups,n_neurons,
                                          dt=.005,eta=4.,tau_e=.1,tau_d=.05)

    def step(self,counts,weights,*,frozen=False):
        c=np.asarray(counts,dtype=float);w=np.asarray(weights,dtype=float)
        if (c.shape!=(self.n,) or not np.isfinite(c).all() or np.any(c<0)
                or np.any(c!=np.floor(c)) or w.shape!=self.initial.shape
                or not np.isfinite(w).all() or np.any(w<.5*self.initial) or np.any(w>self.initial)):
            raise ValueError('Invalid learning telemetry')
        proposed=self.rule.step(c,w,learn=not frozen)
        return np.maximum(.5*self.initial,proposed)


def schedule(block,arm):
    """External apparatus schedule in 5-ms ticks; never passed to the LTD rule."""
    if arm not in ('paired','unpaired','frozen'):raise ValueError('Unknown control')
    cue=None;phase='quiet'
    for name,start,end,odor in [('pre_A',50,100,'A'),('pre_B',150,200,'B'),
                              ('training',250,300,'A'),('post_A',550,600,'A'),
                              ('post_B',650,700,'B')]:
        if start<=block<end:cue=odor;phase=name
    reward=(390<=block<420) if arm=='unpaired' else (270<=block<300)
    return cue,60. if reward else 0.,phase


def comparison(reports):
    """Predeclared engineering gate for one-seed pilot, not a statistical test."""
    scores={}
    for arm in ('paired','unpaired','frozen'):
        r=reports.get(arm,{})
        if r.get('status')!='completed' or not r.get('recovery_pass'):
            return dict(passed=False,reason='incomplete_or_failed_recovery',scores=scores)
        c=r['probe_spikes']
        if min(c['pre_A'],c['pre_B'])<20:
            return dict(passed=False,reason='insufficient_baseline_output',scores=scores)
        scores[arm]=(c['pre_A']-c['post_A'])/c['pre_A']-(c['pre_B']-c['post_B'])/c['pre_B']
    passed=(scores['paired']>=.15 and scores['paired']-scores['unpaired']>=.10
            and scores['paired']-scores['frozen']>=.10)
    return dict(passed=bool(passed),reason='pilot_contrast_pass' if passed else 'no_controlled_association_advantage',
                scores=scores,statistical_replication=False)

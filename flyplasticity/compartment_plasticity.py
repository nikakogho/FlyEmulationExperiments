"""Candidate compartment-local version of the existing LTD kernel.

This adds locality, not a fitted receptor model. Real applications must supply
an independently justified synapse/compartment/DAN mapping. No default map.
"""
import numpy as np
from .light_task import LocalEligibilityLTD


class CompartmentEligibilityLTD:
    def __init__(self,pre,edge_compartment,pam_groups,n_neurons,**parameters):
        self.pre=np.asarray(pre,dtype=int)
        self.compartments=np.asarray(edge_compartment,dtype=int)
        if self.pre.ndim!=1 or self.compartments.shape!=self.pre.shape or len(self.pre)==0:
            raise ValueError('Every plastic edge requires a compartment')
        if np.any(self.pre<0) or np.any(self.pre>=n_neurons):raise ValueError('Invalid presynaptic index')
        if set(self.compartments)!=set(pam_groups):raise ValueError('Missing or unused compartment mapping')
        self.n_neurons=n_neurons
        self.rules={}
        for compartment,pam in pam_groups.items():
            pam=np.asarray(pam,dtype=int)
            if pam.ndim!=1 or len(pam)==0 or np.any(pam<0) or np.any(pam>=n_neurons):
                raise ValueError('Invalid DAN group')
            indices=np.flatnonzero(self.compartments==compartment)
            self.rules[compartment]=(indices,LocalEligibilityLTD(self.pre[indices],pam,n_neurons,**parameters))

    def step(self,counts,weights,learn=True):
        counts=np.asarray(counts,dtype=float);weights=np.asarray(weights,dtype=float)
        if counts.shape!=(self.n_neurons,) or not np.isfinite(counts).all() or np.any(counts<0):
            raise ValueError('Invalid spike counts')
        if weights.shape!=self.pre.shape or not np.isfinite(weights).all() or np.any(weights<0):
            raise ValueError('This kernel supports nonnegative KC output weights only')
        result=weights.copy()
        for indices,rule in self.rules.values():
            proposed=rule.step(counts,weights[indices])
            if learn:result[indices]=proposed
        return result

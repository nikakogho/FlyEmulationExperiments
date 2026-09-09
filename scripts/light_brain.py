"""Real connectome subnet with synthetic visual-KC and taste-PAM interfaces."""
import importlib.util
import sys
from pathlib import Path
import numpy as np
import pandas as pd
import brian2 as br
ROOT=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT))
from flyplasticity.light_task import LocalEligibilityLTD


class LightBrain:
    def __init__(self,seed):
        br.prefs.codegen.target='numpy'
        path=ROOT/'upstream/fly-api/experiments/navigation/nav_demo.py'
        spec=importlib.util.spec_from_file_location('light_nav',path)
        nav=importlib.util.module_from_spec(spec); spec.loader.exec_module(nav)
        nav.ANN=str(ROOT/'data/annotations.tsv')
        # Capture the builder's anatomical ID mapping without changing upstream files.
        sys.path.insert(0,str(ROOT/'upstream/fly-api/experiments/learning'))
        import model_ext
        original=model_ext.build_subnet
        def capture(*args,**kwargs):
            result=original(*args,**kwargs); self.old2new=result[-1]; return result
        model_ext.build_subnet=capture
        try: self.b=nav.Brain(str(ROOT/'upstream/Drosophila_brain_model'),seed=seed)
        finally: model_ext.build_subnet=original
        b=self.b
        ann=pd.read_csv(ROOT/'data/annotations.tsv',sep='\t',low_memory=False).set_index('root_id')
        comp=pd.read_csv(ROOT/'upstream/Drosophila_brain_model/Completeness_783.csv',index_col=0)
        local={new:ann.loc[root] for old,new in self.old2new.items()
               if (root:=comp.index[old]) in ann.index}
        self.visual=np.array([i for i,r in local.items() if r.cell_type=='KCg-d'],dtype=int)
        if len(self.visual)<100: raise RuntimeError('Visual KC mapping incomplete')
        side_map={'left':0,'right':1}
        self.sides=np.array([side_map.get(str(local[i].side).lower(),-1) for i in self.visual])
        if np.any(self.sides<0): raise RuntimeError('Unknown visual KC laterality')
        rng=np.random.default_rng(seed)
        self.colors=np.zeros(len(self.visual),dtype=int)
        for side in (0,1):
            idx=np.flatnonzero(self.sides==side); idx=rng.permutation(idx)
            self.colors[idx[len(idx)//2:]]=1
        self.mbon=[np.array([i for i in b.g['mbon'] if str(local[i].side).lower()==s]) for s in ('left','right')]
        if min(map(len,self.mbon))==0: raise RuntimeError('Missing lateral MBON outputs')
        self.pg=br.PoissonGroup(len(self.visual),rates=0*br.Hz)
        self.drive=br.Synapses(self.pg,b.neu,on_pre='v_post += w_drv',
            namespace={'w_drv':b.p['w_syn']*b.p['f_poi']})
        self.drive.connect(i=np.arange(len(self.visual)),j=self.visual)
        b.net.add(self.pg,self.drive)
        mask=np.isin(b.plastic_pre,self.visual)
        self.plastic=b.plastic_pos[mask]
        self.pre=b.plastic_pre[mask]
        self.initial=np.array(b.syn.w[self.plastic])
        self.rule=LocalEligibilityLTD(self.pre,b.g['pam'],len(b.neu))
        self.enabled=False
        self.last=np.array(b.spk.count[:],dtype=np.int64)
        def update():
            counts=np.array(b.spk.count[:],dtype=np.int64)
            new=self.rule.step(counts-self.last,np.array(b.syn.w[self.plastic]))
            self.last=counts
            if self.enabled: b.syn.w[self.plastic]=new*br.volt
        self.operation=br.NetworkOperation(update,dt=.01*br.second,when='end')
        b.net.add(self.operation); b.net.store('light_initial')
        self.metadata=dict(neurons=len(b.neu),visual_kcs=len(self.visual),plastic_edges=len(self.plastic),
            side_counts=[int((self.sides==i).sum()) for i in (0,1)],
            adapter='random balanced green/blue selectivity within anatomical KCg-d, direct Poisson input',
            reward='local contact proxy drives PAMs at 60 Hz; no recovered taste pathway',
            readout='mean MBON spikes per hemisphere; fixed differential avoidance')

    def reset(self,weights=None):
        self.b.net.restore('light_initial',restore_random_state=True)
        self.last=np.array(self.b.spk.count[:],dtype=np.int64)
        self.rule.e[:]=0.; self.rule.d=0.
        if weights is not None: self.b.syn.w[self.plastic]=np.asarray(weights)*br.volt

    def weights(self): return np.array(self.b.syn.w[self.plastic])

    def step(self,features,taste,learn=False):
        features=np.asarray(features)
        if features.shape!=(2,2) or not np.isfinite(features).all(): raise ValueError('Bad visual input')
        self.enabled=learn
        self.pg.rates=250*np.clip(features[self.sides,self.colors],0,1)*br.Hz
        rates=np.zeros(len(self.b.tgt))
        for i in self.b.g['pam']: rates[self.b.pos[i]]=60*float(taste)
        self.b.pg.rates=rates*br.Hz
        before=np.array(self.b.spk.count[:],dtype=np.int64)
        self.b.net.run(.1*br.second,namespace={})
        counts=np.array(self.b.spk.count[:],dtype=np.int64)-before
        output=np.array([counts[idx].mean()/.1 for idx in self.mbon])
        return output,dict(kc_spikes=int(counts[self.visual].sum()),pam_spikes=int(counts[self.b.g['pam']].sum()),
                           mbon_spikes=int(counts[self.b.g['mbon']].sum()))

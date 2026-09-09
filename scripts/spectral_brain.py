"""Spectral input diagnostic using the existing connectome subnet.

Five-channel random balanced KC drive remains an engineered input adapter.
It does not claim R7/R8 -> aMe12 -> KC physiological integration.
"""
import numpy as np
import brian2 as br
from light_brain import LightBrain


class SpectralBrain(LightBrain):
    def __init__(self, seed):
        super().__init__(seed)
        rng = np.random.default_rng(seed)
        self.spectral_channels = np.zeros(len(self.visual), dtype=int)
        for side in (0, 1):
            idx = rng.permutation(np.flatnonzero(self.sides == side))
            self.spectral_channels[idx] = np.arange(len(idx)) % 5
        self.metadata['adapter'] = 'Fixed random balanced Rh1/Rh3/Rh4/Rh5/Rh6 feature selectivity within KCg-d; direct Poisson input, exploratory only'
        self.metadata['spectral_channel_counts'] = np.bincount(self.spectral_channels, minlength=5).tolist()

    def step(self, features, taste, learn=False):
        features = np.asarray(features, dtype=float)
        if features.shape != (2, 5) or not np.isfinite(features).all() or np.any(features < 0) or np.any(features > 1):
            raise ValueError('Expected five receptor features per eye in 0..1')
        self.enabled = learn
        self.pg.rates = 250*features[self.sides, self.spectral_channels]*br.Hz
        rates = np.zeros(len(self.b.tgt))
        for i in self.b.g['pam']:
            rates[self.b.pos[i]] = 60*float(taste)
        self.b.pg.rates = rates*br.Hz
        before = np.array(self.b.spk.count[:], dtype=np.int64)
        self.b.net.run(.1*br.second, namespace={})
        counts = np.array(self.b.spk.count[:], dtype=np.int64)-before
        return np.array([counts[idx].mean()/.1 for idx in self.mbon]), dict(
            kc_spikes=int(counts[self.visual].sum()), pam_spikes=int(counts[self.b.g['pam']].sum()),
            mbon_spikes=int(counts[self.b.g['mbon']].sum()))

"""Retinal geometry and legacy RGB transports.

New spectral experiments use flyplasticity.spectral. The grayscale encoder is
retained only to reproduce earlier FlyVis motion-model calibration.
"""
import numpy as np
from scipy.spatial import cKDTree


class RetinalBridge:
    def __init__(self, id_map, target_centers):
        self.ids=np.asarray(id_map,dtype=int)
        n=int(self.ids.max())
        if self.ids.ndim!=2 or self.ids.min()<0 or n<1:
            raise ValueError('Invalid ommatidium map')
        target=np.asarray(target_centers,dtype=float)
        if target.shape!=(n,2) or not np.isfinite(target).all():
            raise ValueError('Invalid target geometry')
        rows,cols=np.indices(self.ids.shape)
        counts=np.bincount(self.ids.ravel(),minlength=n+1)[1:]
        if np.any(counts==0): raise ValueError('Missing ommatidium IDs')
        self.counts=counts
        self.centers=np.stack([np.bincount(self.ids.ravel(),weights=x.ravel(),minlength=n+1)[1:]/counts
                               for x in (rows,cols)],axis=1)
        span=np.ptp(target,axis=0)
        if np.any(span==0): raise ValueError('Degenerate geometry')
        mapped=(target-target.min(axis=0))/span*np.ptp(self.centers,axis=0)+self.centers.min(axis=0)
        distance,indices=cKDTree(self.centers).query(mapped)
        if len(np.unique(indices))!=n or distance.max()>2:
            raise ValueError('Retinal lattices do not match within two image pixels')
        self.to_target=indices
        self.to_source=np.argsort(indices)
        self.max_mapping_error_pixels=float(distance.max())

    def encode(self, eye_rgb):
        image=np.asarray(eye_rgb,dtype=float)
        if image.shape!=(2,*self.ids.shape,3) or not np.isfinite(image).all() or image.min()<0 or image.max()>255:
            raise ValueError('Expected two finite RGB eye images in 0..255')
        # Engineering grayscale proxy; preserve per-receptor spatial information.
        gray=image.mean(axis=-1)/255.
        result=np.stack([np.bincount(self.ids.ravel(),weights=eye.ravel(),minlength=len(self.counts)+1)[1:]/self.counts
                         for eye in gray])
        return result[:,self.to_target]

    def encode_rgb(self, eye_rgb):
        """Preserve three display channels for a future spectral front end.

        RGB values are not fly photoreceptor activations. This method deliberately
        does not label channels as R7/R8 or feed them to the grayscale FlyVis model.
        """
        image=np.asarray(eye_rgb,dtype=float)
        if image.shape!=(2,*self.ids.shape,3) or not np.isfinite(image).all() or image.min()<0 or image.max()>255:
            raise ValueError('Expected two finite RGB eye images in 0..255')
        result=np.empty((2,len(self.counts),3))
        for eye in range(2):
            for channel in range(3):
                result[eye,:,channel]=np.bincount(self.ids.ravel(),weights=image[eye,:,:,channel].ravel(),
                    minlength=len(self.counts)+1)[1:]/self.counts/255.
        return result[:,self.to_target,:]


def sample_hold(values, acquisition_times, query_times, max_age=.03):
    """Hold actual samples at finer integrator steps; never claim new observations."""
    values=np.asarray(values);t=np.asarray(acquisition_times);q=np.asarray(query_times)
    if len(t)!=len(values) or len(t)==0 or np.any(np.diff(t)<=0) or np.any(np.diff(q)<0):
        raise ValueError('Invalid time sequence')
    if not np.isfinite(t).all() or not np.isfinite(q).all() or not np.isfinite(values).all():
        raise ValueError('Nonfinite data')
    indices=np.searchsorted(t,q,side='right')-1
    if np.any(indices<0) or np.any(q-t[indices]>max_age+1e-10):
        raise ValueError('Missing or stale sensory sample')
    return values[indices],t[indices]

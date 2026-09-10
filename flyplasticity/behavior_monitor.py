"""Observable embodied investigation proxies, not a suffering detector.

Thresholds are engineering hypotheses and require protocol-specific review.
No missing channel is substituted with a zero signal. A stop latches.
"""
from collections import deque
import numpy as np

class BehaviorMonitor:
    def __init__(self):
        self.rows=deque();self.stopped=False;self.reason=None;self.last=None

    def observe(self,t,xyz,command,odor):
        if self.stopped:raise RuntimeError('Latched behavioral stop: '+self.reason)
        p=np.asarray(xyz,dtype=float);u=np.asarray(command,dtype=float);c=np.asarray(odor,dtype=float)
        if (p.shape!=(3,) or u.shape!=(2,) or c.shape!=(2,4) or not np.isfinite(np.r_[t,p,u,c.ravel()]).all()
                or t<0 or np.any(c<0) or np.any(c>1) or np.any(u<0) or np.any(u>1)
                or self.last is None and t!=0
                or self.last is not None and (t<=self.last or t-self.last>.010001)):
            self.stopped=True;self.reason='invalid_or_stale_behavior';raise RuntimeError(self.reason)
        self.last=t;self.rows.append((t,p.copy(),u.copy(),float(c[:,2:].max())))
        while self.rows and t-self.rows[0][0]>.5+1e-10:self.rows.popleft()
        recent=[r for r in self.rows if t-r[0]<=.2+1e-10]
        span=t-recent[0][0];moving_request=all(max(r[2])>.25 for r in recent)
        displacement=float(np.linalg.norm(p[:2]-recent[0][1][:2]))
        blocked=span>=.19 and moving_request and displacement<.04
        # Sustained movement away from stronger recent stimulus, after its rise.
        fullspan=t-self.rows[0][0];stimuli=[r[3] for r in self.rows]
        peak=max(stimuli);peak_index=stimuli.index(peak)
        onset=peak-stimuli[0]>.05
        after_peak=t-self.rows[peak_index][0]
        avoidance=fullspan>=.45 and onset and after_peak>=.15 and peak-stimuli[-1]>.05 and displacement>.1
        turns=[np.sign(r[2][0]-r[2][1]) if abs(r[2][0]-r[2][1])>.1 else 0 for r in self.rows]
        turns=[s for s in turns if s]
        reversals=sum(a!=b for a,b in zip(turns,turns[1:]))
        competing=fullspan>=.45 and reversals>=6 and displacement<.1
        rest_request=span>=.19 and all(max(r[2])==0 for r in recent)
        failed_rest=rest_request and displacement>.1
        flags=dict(blocked_effort=bool(blocked),stimulus_linked_avoidance=bool(avoidance),
                   competing_actions=bool(competing),failed_rest=bool(failed_rest))
        for reason,active in flags.items():
            if active:
                self.stopped=True;self.reason=reason;raise RuntimeError('Behavioral proxy: '+reason)
        return dict(time_s=t,**flags,coverage='observable movement proxies only; subjective welfare unassessed')

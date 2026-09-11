"""Reviewed movement proxies v2. Investigation flags, not subjective-state labels.

Separate geometric stimulus departure from an observed change that directs the
body away from the local gradient. Historical BehaviorMonitor is unchanged.
"""
from collections import deque
import numpy as np


class ReviewedBehaviorMonitor:
    def __init__(self):
        self.rows=deque();self.last=None;self.stopped=False;self.reason=None;self.rest_since=None;self.last_result=None

    def stop(self,reason):
        self.stopped=True;self.reason=reason
        raise RuntimeError('Behavior review: '+reason)

    def observe(self,t,xyz,heading,command,odor,gradients,*,stimulus_enabled):
        if self.stopped:raise RuntimeError('Latched behavior stop: '+self.reason)
        try:
            p,u,c,g=map(lambda a:np.asarray(a,dtype=float),(xyz,command,odor,gradients))
            valid=(p.shape==(3,) and u.shape==(2,) and c.shape==(2,4) and g.shape==(2,3)
                and type(stimulus_enabled) is bool and np.isfinite(np.r_[t,heading,p,u,c.ravel(),g.ravel()]).all()
                and t>=0 and (self.last is not None or t==0)
                and (self.last is None or 0<t-self.last<=.010001)
                and np.all((u>=0)&(u<=1)) and np.all((c>=0)&(c<=1)))
        except (ValueError,TypeError):valid=False
        if not valid:self.stop('invalid_or_stale_behavior')
        self.last=t
        if np.max(u)==0:
            if self.rest_since is None:self.rest_since=t
        else:self.rest_since=None
        self.rows.append(dict(t=t,p=p.copy(),u=u.copy(),h=np.array([np.cos(heading),np.sin(heading)]),
            c=c[:,2:].max(axis=1),enabled=stimulus_enabled))
        while t-self.rows[0]['t']>.5+1e-10:self.rows.popleft()
        recent=[r for r in self.rows if t-r['t']<=.2+1e-10]
        span=t-recent[0]['t'];motion=p[:2]-recent[0]['p'][:2];distance=np.linalg.norm(motion)
        turn_progress=np.arccos(np.clip(np.dot(recent[0]['h'],self.rows[-1]['h']),-1,1))
        blocked=span>=.19 and all(max(r['u'])>.25 for r in recent) and distance<.04 and turn_progress<.1
        # StandingController takes 100ms to interpolate to its neutral pose.
        # Assess 200ms of motion AFTER that mechanically specified interval.
        rest_ready=self.rest_since is not None and t-self.rest_since>=.3-1e-10
        failed_rest=rest_ready and distance>.1
        signs=[np.sign(r['u'][0]-r['u'][1]) for r in self.rows if abs(r['u'][0]-r['u'][1])>.1]
        reversals=sum(a!=b for a,b in zip(signs,signs[1:]))
        competing=t-self.rows[0]['t']>=.45 and reversals>=6 and distance<.1
        departure=[False,False];withdrawal=[False,False];rapid_departure=[False,False]
        if t-self.rows[0]['t']>=.45 and all(r['enabled'] for r in self.rows):
            old=[r for r in self.rows if .3<=t-r['t']<=.5+1e-10]
            new=[r for r in self.rows if t-r['t']<=.1+1e-10]
            old_h=np.mean([r['h'] for r in old],axis=0);new_h=np.mean([r['h'] for r in new],axis=0)
            old_speed=np.linalg.norm(old[-1]['p'][:2]-old[0]['p'][:2])/(old[-1]['t']-old[0]['t'])
            new_speed=np.linalg.norm(new[-1]['p'][:2]-new[0]['p'][:2])/(new[-1]['t']-new[0]['t'])
            old_u=np.mean([r['u'].mean() for r in old]);new_u=np.mean([r['u'].mean() for r in new])
            for cue in range(2):
                levels=[r['c'][cue] for r in self.rows];peak=max(levels);idx=levels.index(peak)
                departure[cue]=bool(peak-levels[0]>.05 and peak-levels[-1]>.05
                    and t-self.rows[idx]['t']>=.15 and distance>.1)
                norm=np.linalg.norm(g[cue,:2])
                if departure[cue] and norm>1e-8:
                    direction=g[cue,:2]/norm
                    away=np.dot(new_h,direction)<-.5 and np.dot(motion,direction)<-.02
                    withdrawal[cue]=bool(away and np.dot(old_h,direction)>.5)
                    rapid_departure[cue]=bool(away and old_speed>.1 and old_u>.05
                        and new_speed>1.5*old_speed and new_u>1.5*old_u)
        flags=dict(blocked_effort=bool(blocked),failed_rest=bool(failed_rest),
            competing_actions=bool(competing),stimulus_linked_withdrawal=any(withdrawal),
            rapid_stimulus_departure=any(rapid_departure))
        result=dict(time_s=t,**flags,geometric_departure=departure,
            coverage='Observable movement and execution only; valence and subjective welfare unassessed')
        self.last_result=result
        for name,value in flags.items():
            if value:self.stop(name)
        return result

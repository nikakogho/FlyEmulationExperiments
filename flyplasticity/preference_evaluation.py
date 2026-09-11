"""Fixed descriptive preference gate; missing trials never become zeros."""
import numpy as np


def preference(rows,reinforced):
    if reinforced not in ('A','B'):raise ValueError('Unknown cue')
    active=[r for r in rows if .25<=r['time_s']<2.25]
    if len(active)!=400:raise ValueError('Incomplete preference window')
    c=np.array([np.asarray(r['odor'])[:,2:].mean(axis=1) for r in active])
    dose=c.sum(axis=0)*.005
    if not np.isfinite(dose).all() or dose.sum()<=.2:raise ValueError('Insufficient odor exposure')
    sign=1 if reinforced=='A' else -1
    return dict(index=float(sign*(dose[0]-dose[1])/dose.sum()),dose=dose.tolist(),
        dominant_A_s=float(np.sum(c[:,0]-c[:,1]>.1)*.005),
        dominant_B_s=float(np.sum(c[:,1]-c[:,0]>.1)*.005))


def assess(cases):
    if len(cases)!=4:return dict(passed=False,reason='incomplete_cohort')
    deltas={arm:[] for arm in ('paired','unpaired','frozen')};wins=0
    for c in cases:
        p=c.get('probes',{})
        if set(p)!={'pre','paired','unpaired','frozen'} or not all(r.get('completed') and r.get('recovery_pass')
            and r.get('weights_unchanged') and r.get('displacement_mm',0)>=1 and r.get('preference') is not None for r in p.values()):
            return dict(passed=False,reason='incomplete_or_uninformative_probe')
        for arm in deltas:deltas[arm].append(p[arm]['preference']['index']-p['pre']['preference']['index'])
        wins+=deltas['paired'][-1]>max(deltas['unpaired'][-1],deltas['frozen'][-1])
    means={k:float(np.mean(v)) for k,v in deltas.items()}
    checks=dict(paired_increase=means['paired']>=.05,paired_vs_unpaired=means['paired']-means['unpaired']>=.05,
        paired_vs_frozen=means['paired']-means['frozen']>=.05,positive_cases=wins>=3)
    return dict(passed=all(checks.values()),reason='preference_gate_pass' if all(checks.values()) else 'effect_margin_not_met',
        criteria=checks,deltas=deltas,means=means,positive_cases=wins,statistical_replication=False)

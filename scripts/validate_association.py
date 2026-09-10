"""Fixed independent validation cohort; no adaptive sampling or retuning."""
from pathlib import Path
import json,sys
ROOT=Path(__file__).resolve().parents[1];sys.path.insert(0,str(ROOT))
from controlled_association import run_arm
from flyplasticity.association import comparison

CASES=((311,'A'),(311,'B'),(312,'A'),(312,'B'))

def assess(cases):
    if len(cases)!=len(CASES) or any('criteria' not in r for r in cases):
        return dict(passed=False,reason='incomplete_or_unassessable_cohort')
    means={a:sum(r['scores'][a] for r in cases)/len(cases) for a in ('paired','unpaired','frozen')}
    criteria=dict(mean_selectivity_at_least_015=means['paired']>=.15,
                  mean_paired_minus_unpaired_at_least_010=means['paired']-means['unpaired']>=.10,
                  mean_paired_minus_frozen_at_least_010=means['paired']-means['frozen']>=.10,
                  advantage_in_every_case=all(r['scores']['paired']>max(r['scores']['unpaired'],r['scores']['frozen']) for r in cases))
    return dict(passed=all(criteria.values()),criteria=criteria,mean_scores=means,
                scope='Two held-out seeds, both reinforced cues; small model validation, not population inference')

def main():
    out=ROOT/'results/association_validation_v1';out.mkdir(exist_ok=False)
    cases=[];stopped=False
    for seed,cue in CASES:
        case=out/f'seed{seed}_{cue}';case.mkdir()
        reports={}
        for arm in ('paired','unpaired','frozen'):
            print(f'VALIDATION seed={seed}, reinforced={cue}, arm={arm}',flush=True)
            reports[arm]=run_arm(arm,case/arm,seed,cue,'research/validation_protocol.md')
            if reports[arm]['status']!='completed':stopped=True;break
        result=comparison(reports,cue);result.update(seed=seed,reinforced=cue)
        (case/'comparison.json').write_text(json.dumps(result,indent=2));cases.append(result)
        (out/'progress.json').write_text(json.dumps(cases,indent=2))
        if stopped:break
    summary=assess(cases);summary.update(cases=cases,welfare_or_execution_stop=stopped)
    (out/'assessment.json').write_text(json.dumps(summary,indent=2));print(json.dumps(summary,indent=2))
    if not summary['passed']:raise SystemExit(1)

if __name__=='__main__':main()

"""Replay existing spike totals through the fixed scalar decoder, never neurons.

Aggregate counts suffice because NeuralSpeed depends only on their mean. This
does not reconstruct bilateral counts, sensory feedback, or a new experiment.
"""
from pathlib import Path
import json,sys,hashlib
import numpy as np
ROOT=Path(__file__).resolve().parents[1];sys.path.insert(0,str(ROOT))
from flyplasticity.neural_speed import NeuralSpeed


def decode(rows):
    motor=NeuralSpeed(2);out=[]
    for k,r in enumerate(rows):
        if abs(r['time_s']-k*.005)>1e-9:raise ValueError('Missing or misordered archived bin')
        total=r['mbon01_spikes']
        # [total,0] is an algebraic representation of the sum, not laterality.
        u=motor.step([total,0])
        out.append(dict(time_s=r['time_s'],phase=r['observed_phase'],command=u.tolist()))
    return out


def main():
    base=ROOT/'results/association_validation_v1';out=ROOT/'results/saved_motor_readout_v1'
    out.mkdir(exist_ok=True);cases=[];provenance={}
    assessment=json.loads((base/'assessment.json').read_text())
    for case in assessment['cases']:
        name=f"seed{case['seed']}_{case['reinforced']}";arms={}
        for arm in ('paired','unpaired','frozen'):
            p=base/name/arm/'telemetry.json';rows=json.loads(p.read_text())
            report=json.loads((p.parent/'report.json').read_text())
            if report['status']!='completed':raise ValueError('Only completed source traces allowed')
            provenance[str(p.relative_to(ROOT))]=hashlib.sha256(p.read_bytes()).hexdigest()
            tape=decode(rows)
            arms[arm]={phase:float(np.mean([r['command'][0] for r in tape if r['phase']==phase]))
                       for phase in ('pre_A','pre_B','post_A','post_B')}
            (out/f'{name}_{arm}.json').write_text('[\n'+',\n'.join(json.dumps(r,separators=(',',':')) for r in tape if r['phase'] in ('post_A','post_B'))+'\n]')
        reinforced=case['reinforced'];other='B' if reinforced=='A' else 'A'
        def slowing(cue,control):return 1-arms['paired']['post_'+cue]/arms[control]['post_'+cue]
        cases.append(dict(case=name,mean_commands=arms,
            reinforced_slowing_vs_frozen=slowing(reinforced,'frozen'),
            reinforced_slowing_vs_unpaired=slowing(reinforced,'unpaired'),
            other_slowing_vs_frozen=slowing(other,'frozen'),
            cue_specific_fractional_difference=slowing(reinforced,'frozen')-slowing(other,'frozen')))
    result=dict(new_neural_steps=0,new_physics_steps=0,cases=cases,provenance=provenance,
        interpretation='Descriptive replay of archived stationary spike counts through the unchanged motor decoder. Command differences are not measured body-speed differences. No new significance test, navigation claim, or replacement of the stopped embodied protocol.')
    (out/'assessment.json').write_text(json.dumps(result,indent=2));print(json.dumps(cases,indent=2))

if __name__=='__main__':main()

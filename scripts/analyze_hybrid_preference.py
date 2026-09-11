"""Independent archive integrity and outcome analysis; never advances neurons."""
from pathlib import Path
import json,pickle,hashlib,sys
import numpy as np
ROOT=Path(__file__).resolve().parents[1];sys.path.insert(0,str(ROOT))
from flyplasticity.preference_evaluation import preference,assess
from flyplasticity.association import comparison


def main():
    out=ROOT/'results/hybrid_preference_v1';summary=json.loads((out/'assessment.json').read_text())
    checks={};cases=summary['cases']
    for case in cases:
        p=out/f"seed{case['seed']}_{case['reinforced']}"
        for label,r in case['probes'].items():
            q=p/label;meta=json.loads((q/'metadata.json').read_text());source=ROOT/meta['checkpoint']
            # Only trusted local artifacts produced by this repository's runner.
            initial=pickle.loads(source.read_bytes())['terminal']
            final=pickle.loads((q/'network_state.pkl').read_bytes())['terminal']
            rows=json.loads((q/'telemetry.json').read_text());neural=json.loads((q/'neural_telemetry.json').read_text())
            tape=np.load(q/'replay.npz')
            c=dict(source_hash=hashlib.sha256(source.read_bytes()).hexdigest()==meta['checkpoint_sha256'],
                all_weights_unchanged=np.array_equal(initial['sub_synapses']['w'][0],final['sub_synapses']['w'][0]),
                clocks_equal=abs(r['neural_time_s']-r['body_time_s'])<1e-8,
                spike_totals_match=int((final['spikemonitor']['count'][0]-initial['spikemonitor']['count'][0]).sum())==sum(n['total_spikes'] for n in neural),
                frames_match=len(rows)==len(tape['time_s']),
                frame_times_match=np.allclose(tape['time_s'],[b['time_s'] for b in rows]),
                finite_physics=all(np.isfinite(tape[k]).all() for k in ('qpos','qvel','act')))
            if r['completed']:
                measured=preference(rows,case['reinforced'])
                c['preference_matches']=abs(measured['index']-r['preference']['index'])<1e-12 if r['preference'] else False
            checks[f'{p.name}/{label}']={k:bool(v) for k,v in c.items()}
    outcome=assess(cases)
    result=dict(new_neural_steps=0,new_physics_steps=0,checks=checks,
        stationary_contrasts={f"seed{c['seed']}_{c['reinforced']}":comparison(c['training'],c['reinforced']) for c in cases},
        integrity_passed=bool(checks) and all(all(c.values()) for c in checks.values()),
        recomputed_outcome=outcome,runner_gate_matches=outcome['passed']==summary['passed'],
        total_neural_seconds=sum(r['neural_time_s'] for c in cases for r in list(c['training'].values())+list(c['probes'].values())))
    (out/'integrity.json').write_text(json.dumps(result,indent=2));print(json.dumps(result,indent=2))
    if checks and not result['integrity_passed']:raise SystemExit(1)

if __name__=='__main__':main()

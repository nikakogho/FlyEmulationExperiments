"""Independent integrity check of the six mechanical archives, no simulation."""
from pathlib import Path
import json,hashlib
import numpy as np
ROOT=Path(__file__).resolve().parents[1]


def main():
    out=ROOT/'results/saved_motor_body_v1';initial=None;checks={}
    for cue in ('A','B'):
        for arm in ('paired','unpaired','frozen'):
            p=out/f'{cue}_{arm}';report=json.loads((p/'report.json').read_text())
            rows=json.loads((p/'telemetry.json').read_text());tape=np.load(p/'replay.npz')
            source=ROOT/report['source'];raw=json.loads(source.read_text())
            commands=np.array([r['command'] for r in raw if r['phase']=='post_'+cue])
            if initial is None:initial={k:tape[k][0].copy() for k in ('qpos','qvel','act')}
            tests=dict(source_hash=hashlib.sha256(source.read_bytes()).hexdigest()==report['source_sha256'],
                frames=len(rows)==151 and len(tape['time_s'])==151,
                timestamps=np.allclose(tape['time_s'],np.arange(151)*.005,rtol=0,atol=1e-10),
                commands_unchanged=np.array_equal(np.array([r['command'] for r in rows[:50]]),commands),
                rest_commands_zero=all(r['command']==[0.,0.] for r in rows[50:]),
                finite_states=all(np.isfinite(tape[k]).all() for k in ('qpos','qvel','act')),
                same_initial_state=all(np.array_equal(tape[k][0],initial[k]) for k in initial),
                completed=report['status']=='completed',final_rest=report['final_speed_mm_s']<.5)
            checks[f'{cue}_{arm}']={k:bool(v) for k,v in tests.items()}
    result=dict(new_neural_steps=0,new_physics_steps=0,checks=checks,
                passed=all(all(c.values()) for c in checks.values()))
    (out/'integrity_checks.json').write_text(json.dumps(result,indent=2))
    print(json.dumps(result,indent=2))
    if not result['passed']:raise SystemExit(1)

if __name__=='__main__':main()

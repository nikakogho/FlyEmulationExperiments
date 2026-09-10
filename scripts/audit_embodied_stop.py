"""Offline audit of the stopped embodiment; no restoration or model steps."""
from pathlib import Path
import json,pickle,numpy as np
ROOT=Path(__file__).resolve().parents[1]

def main():
    out=ROOT/'results/embodied_speed_v1/A_paired'
    rows=json.loads((out/'telemetry.json').read_text());neural=json.loads((out/'neural_telemetry.json').read_text())
    report=json.loads((out/'report.json').read_text());meta=json.loads((out/'metadata.json').read_text())
    # Trusted files generated locally by our runner only.
    initial=pickle.loads((ROOT/meta['checkpoint']).read_bytes())['terminal']
    final=pickle.loads((out/'network_state.pkl').read_bytes())['terminal']
    stimulus=np.array([np.asarray(r['odor'])[0,2:].max() for r in rows])
    peak=int(np.argmax(stimulus));source=np.array(report['sources_mm'][0])
    last_ant=np.array(rows[-1]['sensor_positions_mm'])[2:].mean(axis=0)
    checks=dict(weights_equal=bool(np.array_equal(initial['sub_synapses']['w'][0],final['sub_synapses']['w'][0])),
                spike_delta_matches=int((final['spikemonitor']['count'][0]-initial['spikemonitor']['count'][0]).sum())==sum(r['total_spikes'] for r in neural),
                clocks_equal=abs(report['body_time_s']-report['neural_time_s'])<1e-8,
                equal_left_right_commands=all(r['command'][0]==r['command'][1] for r in rows))
    if not all(checks.values()):raise ValueError('Evidence integrity mismatch')
    result=dict(new_neural_steps=0,new_physics_steps=0,checks=checks,
                stop_time_s=rows[-1]['time_s'],peak_antenna_concentration_time_s=rows[peak]['time_s'],
                peak_antenna_concentration=float(stimulus[peak]),stop_antenna_concentration=float(stimulus[-1]),
                source_mm=source.tolist(),last_antenna_center_mm=last_ant.tolist(),
                crossed_source_x=bool(last_ant[0]>source[0]),body_start_mm=rows[0]['xyz'],body_end_mm=rows[-1]['xyz'],
                displacement_mm=float(np.linalg.norm(np.array(rows[-1]['xyz'])[:2]-np.array(rows[0]['xyz'])[:2])),
                interpretation='Concentration rose then fell during straight-command passage beyond the source. This is not a validated inference of aversive state; the conservative stop remains preserved.',
                behavioral_effect='Unassessed: paired run stopped before comparison controls; speed effect cannot be attributed to learning',
                next='Investigate a directional navigation circuit and causal behavioral monitoring offline before another neural protocol; no retries performed')
    (out/'stop_audit.json').write_text(json.dumps(result,indent=2));print(json.dumps(result,indent=2))

if __name__=='__main__':main()

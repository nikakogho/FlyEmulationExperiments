"""Check geometry and behavioral-monitor coverage on saved mechanical frames."""
from pathlib import Path
import sys,json
ROOT=Path(__file__).resolve().parents[1];sys.path.insert(0,str(ROOT))
import numpy as np
from flyplasticity.behavior_monitor import BehaviorMonitor
from flyplasticity.odor_scene import OdorField

def main():
    out=ROOT/'results/odor_scene_v2';rows=json.loads((out/'telemetry.json').read_text())
    field=OdorField([[8,4,1],[8,-4,1]]);monitor=BehaviorMonitor();errors=[];event=None
    for r in rows:
        p=np.asarray(r['sensor_positions_mm']);actual=field.sample(p)
        errors.append(float(np.max(np.abs(actual-np.asarray(r['odor'])))))
        if not monitor.stopped:
            try:monitor.observe(r['time_s']-rows[0]['time_s'],r['xyz'],r['command'],r['odor'])
            except RuntimeError as exc:event=dict(time_s=r['time_s'],reason=str(exc))
    report=dict(new_neural_steps=0,new_physics_steps=0,frames=len(rows),
                max_independent_field_error=max(errors),behavioral_proxy_event=event,
                coverage='Offline mechanical replay only; no subjective welfare conclusion',
                improvement='Use actual articulated antenna/palp sites; old body-offset proxy RMSE recorded separately')
    # Physical startup can settle before any brain is instantiated. This is not
    # resetting a stopped neural model; both audit outcomes are retained.
    settled=[r for r in rows if r['time_s']>=.3];post=BehaviorMonitor();post_event=None
    for r in settled:
        try:post.observe(r['time_s']-settled[0]['time_s'],r['xyz'],r['command'],r['odor'])
        except RuntimeError as exc:post_event=dict(time_s=r['time_s'],reason=str(exc));break
    report['post_mechanical_settling_event']=post_event
    report['startup_requirement']='Settle the physical body before neural construction; retain startup result, never suppress a neural-run stop'
    (out/'offline_audit.json').write_text(json.dumps(report,indent=2));print(json.dumps(report,indent=2))

if __name__=='__main__':main()

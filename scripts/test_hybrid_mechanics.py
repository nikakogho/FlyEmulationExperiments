"""Synthetic-input physics qualification; never constructs a neural model."""
from pathlib import Path
import json,sys
ROOT=Path(__file__).resolve().parents[1];sys.path.insert(0,str(ROOT))
import numpy as np
from hybrid_fixture import make_fixture,advance,observe,save_tapes,frame
from flyplasticity.hybrid_navigation import HybridNavigation
from flyplasticity.behavior_review import ReviewedBehaviorMonitor


def main():
    import argparse
    ap=argparse.ArgumentParser();ap.add_argument('--out',default='results/hybrid_mechanics_v2');args=ap.parse_args()
    out=ROOT/args.out;out.mkdir(exist_ok=False);reports=[]
    for name,heading,uniform in [('left',.6,True),('right',-.6,True),('field_left',.6,False),('field_right',-.6,False)]:
        p=out/name;p.mkdir();arena,fly,sim,obs=make_fixture(heading)
        sim.physics.model.save_binary(str(p/'scene.mjb'));motor=HybridNavigation();monitor=ReviewedBehaviorMonitor()
        rows=[];frames=[];error=None;prior=[0.,0.]
        try:
            for k in range(601):
                t=k*.005;arena.enabled=50<=k<450;body=observe(arena,fly,sim,obs)
                wind=[-1.,0.] if uniform and arena.enabled else body['wind']
                u=motor.step([1,1] if arena.enabled else [0,0],body['heading'],wind,float(np.asarray(body['odor'])[:,2:].mean(axis=1).sum()))
                if not arena.enabled:u=np.zeros(2)
                body.update(time_s=t,command=u.tolist(),stimulus_enabled=arena.enabled)
                rows.append(body);frames.append(frame(t,sim))
                monitor.observe(t,body['xyz'],body['heading'],prior,body['odor'],body['gradients'],stimulus_enabled=arena.enabled)
                if k==600:break
                obs=advance(sim,u);prior=u
            status='completed'
        except (RuntimeError,ValueError) as exc:status='stopped';error=str(exc)
        finally:
            sim.close();save_tapes(p,rows,frames)
        checks=dict(completed=status=='completed',rest=rows[-1]['speed_mm_s']<.5,
            displacement=np.linalg.norm(np.array(rows[-1]['xyz'])[:2]-np.array(rows[0]['xyz'])[:2])>1)
        if uniform:checks['corrected_heading']=abs(rows[min(250,len(rows)-1)]['heading'])<abs(rows[0]['heading'])
        report=dict(name=name,status=status,error=error,checks={k:bool(v) for k,v in checks.items()},
            passed=all(checks.values()),new_neural_steps=0,body_run=False,sources_mm=arena.field.sources.tolist(),
            scope='Synthetic constant-count mechanical test; no brain or learning',final_heading=rows[-1]['heading'])
        (p/'report.json').write_text(json.dumps(report,indent=2));reports.append(report);print(json.dumps(report),flush=True)
    (out/'assessment.json').write_text(json.dumps(dict(passed=all(r['passed'] for r in reports),reports=reports,new_neural_steps=0),indent=2))

if __name__=='__main__':main()

"""Review saved evidence with v2 proxies and actual compiled contact geometry."""
from pathlib import Path
import sys,json,hashlib
import numpy as np
ROOT=Path(__file__).resolve().parents[1];sys.path.insert(0,str(ROOT))
from view_delivery import load,set_frame
from flyplasticity.behavior_review import ReviewedBehaviorMonitor


def main():
    out=ROOT/'results/behavior_review_v2';out.mkdir(exist_ok=True);reports=[]
    for relative in ['results/embodied_speed_v1/A_paired','results/hybrid_mechanics_v1/left']:
        p=ROOT/relative;model,data,tape=load(p);rows=json.loads((p/'telemetry.json').read_text())
        old=json.loads((p/'report.json').read_text());monitor=ReviewedBehaviorMonitor();event=None;contacts=[];departures=[]
        indices=[i for i in range(model.nsensor) if model.sensor(i).name.endswith('thorax_orientx')]
        if len(indices)!=1:raise ValueError('Ambiguous recorded heading sensor')
        adr=model.sensor_adr[indices[0]]
        marker_geoms={i for i in range(model.ngeom) if 'odor_source_marker' in model.body(model.geom_bodyid[i]).name}
        for k,r in enumerate(rows):
            set_frame(model,data,tape,k);h=data.sensordata[adr:adr+3];heading=float(np.arctan2(h[1],h[0]))
            if any(c.geom1 in marker_geoms or c.geom2 in marker_geoms for c in data.contact):contacts.append(r['time_s'])
            if not monitor.stopped:
                enabled=r.get('stimulus_enabled',.25<=r['time_s']<1.2)
                if 'gradients' in r:g=r['gradients']
                else:
                    center=np.asarray(r['sensor_positions_mm'])[2:].mean(axis=0);delta=center-np.asarray(old['sources_mm'][0])
                    g=np.array([-delta*np.exp(-np.dot(delta,delta)/72)/36,np.zeros(3)]) if enabled else np.zeros((2,3))
                prior=rows[k-1]['command'] if k else [0,0]
                try:
                    result=monitor.observe(r['time_s'],r['xyz'],heading,prior,r['odor'],g,stimulus_enabled=bool(enabled))
                    if any(result['geometric_departure']):departures.append(r['time_s'])
                except RuntimeError as exc:event=dict(time_s=r['time_s'],reason=str(exc))
        reports.append(dict(path=relative,source_sha256=hashlib.sha256((p/'telemetry.json').read_bytes()).hexdigest(),
            historical_event=old.get('error'),review_event=event,geometric_departure_times=departures,
            marker_contact_frames=len(contacts),first_marker_contact_time=contacts[0] if contacts else None,
            interpretation='Offline reanalysis only; original stop is retained. Contact presence is not a diagnosis or proof of causation.'))
    (out/'assessment.json').write_text(json.dumps(dict(new_neural_steps=0,new_physics_steps=0,reports=reports),indent=2))
    print(json.dumps(reports,indent=2))

if __name__=='__main__':main()

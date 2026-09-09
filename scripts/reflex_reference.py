"""Export published FeCO pathways and audit native fly joint coordinates.

No neural simulation, actuation or physics integration is performed.
"""
from pathlib import Path
import json, hashlib
import requests
import pandas as pd
import numpy as np
import mujoco, flygym

ROOT=Path(__file__).resolve().parents[1]
COMMIT='4328b1d5549749f1014c4d73cccc0c5241d98ae4'
BASE=f'https://raw.githubusercontent.com/sagrawal/Lee_2024/{COMMIT}/synapse_tables/'


def type_lookup(frame):
    valid=frame.loc[frame.valid.eq('t'),['pt_root_id','cell_type']].drop_duplicates()
    if valid.pt_root_id.duplicated().any():
        raise ValueError('Conflicting cell-type annotations; resolve explicitly')
    return valid.set_index('pt_root_id').cell_type


def anatomical_angle(points):
    a,b=points[0]-points[1],points[2]-points[1]
    norms=np.linalg.norm(a)*np.linalg.norm(b)
    if not np.isfinite(points).all() or norms<=0:
        raise ValueError('Invalid segment geometry')
    return float(np.degrees(np.arccos(np.clip(a@b/norms,-1,1))))


def main():
    out=ROOT/'results/reflex_reference'; out.mkdir(exist_ok=True)
    data=ROOT/'data/reflex_reference'; data.mkdir(exist_ok=True)
    tables={}; manifest={}
    for name in ['feco_annotation_table','downstream_feco_annotation_table','feco_downstream_connections']:
        p=data/(name+'.csv')
        if not p.exists():
            response=requests.get(BASE+p.name,timeout=60); response.raise_for_status()
            p.write_bytes(response.content)
        # Neuron identifiers exceed the exact integer range of IEEE floats.
        tables[name]=pd.read_csv(p,dtype=str)
        manifest[name]=dict(url=BASE+p.name,sha256=hashlib.sha256(p.read_bytes()).hexdigest())
    pre=type_lookup(tables['feco_annotation_table'])
    post_frame=tables['downstream_feco_annotation_table']
    unique=post_frame.loc[post_frame.valid.eq('t'),['pt_root_id','cell_type']].drop_duplicates()
    ambiguous=unique[unique.pt_root_id.duplicated(False)]
    ambiguous.to_json(out/'ambiguous_target_annotations.json',orient='records',indent=2)
    post=type_lookup(post_frame[~post_frame.pt_root_id.isin(ambiguous.pt_root_id)])
    edges=tables['feco_downstream_connections']
    edges=edges[edges.valid.eq('t')].copy()
    if edges.id.duplicated().any(): raise ValueError('Duplicate synapse identifiers')
    edges['sensory_type']=edges.pre_pt_root_id.map(pre)
    edges['target_class']=edges.post_pt_root_id.map(post)
    selected=edges[edges.sensory_type.eq('claw_ext') & edges.target_class.isin(['13B','MN'])]
    # Each row is a synapse record, NOT its detector-confidence score contacts.
    counted=selected.groupby(['pre_pt_root_id','post_pt_root_id','target_class']).size().rename('synapse_records').reset_index()
    counted.to_json(out/'claw_extension_reference_edges.json',orient='records',indent=2)
    xml=Path(flygym.__file__).parent/'data/mjcf/neuromechfly_seqik_kinorder_ypr.xml'
    model=mujoco.MjModel.from_xml_path(str(xml)); state=mujoco.MjData(model)
    index=int(model.joint('joint_LFTibia').qposadr[0])
    rows=[]
    for q in np.linspace(.2,1.6,15):
        state.qpos[index]=q; mujoco.mj_forward(model,state)
        points=np.array([state.body(n).xpos.copy() for n in ['LFFemur','LFTibia','LFTarsus1']])
        rows.append(dict(qpos_rad=float(q),interior_angle_deg=anatomical_angle(points),
                         femur_length_native=float(np.linalg.norm(points[1]-points[0])),
                         tibia_length_native=float(np.linalg.norm(points[2]-points[1]))))
    assert state.time==0
    assert np.all(np.diff([r['interior_angle_deg'] for r in rows])<0)
    (out/'joint_coordinate_sweep.json').write_text(json.dumps(rows,indent=2))
    report=dict(reference_commit=COMMIT,sources=manifest,
        valid_synapse_records=len(edges), selected_reference_records=len(selected),
        target_counts=selected.target_class.value_counts().to_dict(),
        ambiguous_target_ids=ambiguous.pt_root_id.unique().tolist(),
        unknown_pre_records=int(edges.sensory_type.isna().sum()),
        unknown_post_records=int(edges.target_class.isna().sum()),
        joint_source=str(xml),joint_xml_sha256=hashlib.sha256(xml.read_bytes()).hexdigest(),
        geometry=rows[0],increasing_qpos_means='anatomical flexion over audited interval',
        muscle_force_calibrated=False,malecns_cell_matches_verified=False,
        neural_steps=0,physics_steps=0,
        limitation='13B is a hemilineage class, not an identification of the physiological 13B-alpha subtype; MN labels do not specify muscle targets.')
    (out/'report.json').write_text(json.dumps(report,indent=2))
    print(json.dumps({k:v for k,v in report.items() if k!='sources'},indent=2))


if __name__=='__main__': main()

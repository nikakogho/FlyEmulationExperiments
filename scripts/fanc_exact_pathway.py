"""Pinned FANC sensory-to-muscle identity chain. No neural execution."""
import pickle,importlib,json,hashlib
from pathlib import Path
import pandas as pd
ROOT=Path(__file__).resolve().parents[1]
SOURCE='https://raw.githubusercontent.com/tuthill-lab/Lesser_Azevedo_2023/93cafa55b8bbdb1493e8d73c941035969349b223/pkls/pre_to_mn_df_matched_typed_with_nt_v604_20230525.pkl'


class RestrictedTableReader(pickle.Unpickler):
    def find_class(self,module,name):
        if (module,name)==('pandas.core.indexes.numeric','Int64Index'):return pd.Index
        allowed={('pandas.core.frame','DataFrame'),('pandas.core.internals.managers','BlockManager'),
                 ('pandas._libs.internals','_unpickle_block'),('numpy.core.multiarray','_reconstruct'),
                 ('numpy','ndarray'),('numpy','dtype'),('builtins','slice'),
                 ('pandas.core.indexes.base','_new_Index'),('pandas.core.indexes.base','Index'),
                 ('pandas.core.indexes.multi','MultiIndex'),('numpy.core.numeric','_frombuffer')}
        if (module,name) not in allowed: raise ValueError('Unsupported serialized class')
        return getattr(importlib.import_module(module),name)


def join_targets(edges,motors):
    if motors.segID.duplicated().any():raise ValueError('Ambiguous motor identity')
    if not all(isinstance(x,str) for x in motors.segID):raise ValueError('IDs must remain exact strings')
    return edges.merge(motors,left_on='post_pt_root_id',right_on='segID',how='left',validate='many_to_one')


def main():
    p=ROOT/'data/motor_targets/fanc_v604.pkl'
    if not p.exists():
        import requests
        r=requests.get(SOURCE,timeout=60);r.raise_for_status();p.write_bytes(r.content)
    with p.open('rb') as f:table=RestrictedTableReader(f).load()
    motors=table.columns.to_frame(index=False)
    motors['segID']=motors.segID.map(str)
    edges=pd.DataFrame(json.loads((ROOT/'results/reflex_reference/claw_extension_reference_edges.json').read_text()))
    joined=join_targets(edges[edges.target_class.eq('MN')],motors)
    chosen=joined[joined.muscle.eq('main_tibia_flexor')].copy()
    if chosen.empty:raise ValueError('No supported pathway')
    out=ROOT/'results/fanc_exact_pathway';out.mkdir(exist_ok=True)
    chosen.to_json(out/'pathway.json',orient='records',indent=2)
    motors.to_json(out/'motor_target_table.json',orient='records',indent=2)
    report=dict(source=SOURCE,sha256=hashlib.sha256(p.read_bytes()).hexdigest(),
        sensory_source_commit='4328b1d5549749f1014c4d73cccc0c5241d98ae4',
        dataset='FANC',sensory_type='claw_ext',target='main_tibia_flexor',
        sensory_ids=chosen.pre_pt_root_id.unique().tolist(),motor_ids=chosen.segID.unique().tolist(),
        synaptic_contacts=int(chosen.synapse_records.sum()),
        same_identifier_join=True,unmatched_other_motor_contacts=int(joined.loc[joined.muscle.isna(),'synapse_records'].sum()),
        physiological_reflex_validated=False,whole_circuit=False,neural_steps=0,
        expected_action='Decrease anatomical femur-tibia angle; positive audited left-front FlyGym tibia qpos.',
        unknown=['single-cell receptor tuning','synaptic dynamics and gains','motor recruitment and force per spike','omitted circuit inputs'])
    (out/'report.json').write_text(json.dumps(report,indent=2));print(json.dumps(report,indent=2))


if __name__=='__main__':main()

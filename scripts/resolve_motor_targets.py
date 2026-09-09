"""Evidence-linked muscle targets; no physiology or cross-specimen IDs inferred."""
from pathlib import Path
import json,hashlib
import pandas as pd
import requests
import pyarrow.feather as feather
ROOT=Path(__file__).resolve().parents[1]
COMMIT='93cafa55b8bbdb1493e8d73c941035969349b223'
BASE=f'https://raw.githubusercontent.com/tuthill-lab/Lesser_Azevedo_2023/{COMMIT}/'


def exact_join(candidates,targets):
    if targets.bodyid.duplicated().any(): raise ValueError('Ambiguous MANC IDs')
    return candidates.merge(targets,left_on='manc_id',right_on='bodyid',how='left',
                            validate='many_to_one',suffixes=('_malecns','_manc'))


def classify_mapping(row):
    if pd.isna(row.get('target')): return 'unmatched'
    expected={'Ti flexor MN':'Ti flexor','Ti extensor MN':'Ti extensor'}
    if row['target']!=expected.get(row['type_malecns']): return 'target_conflict'
    if row.get('exit_nerve')!='ProLN_'+row['somaSide']: return 'nerve_or_side_conflict'
    return 'consistent_published_assignment_confidence_unreported'


def main():
    out=ROOT/'results/motor_targets';out.mkdir(exist_ok=True)
    data=ROOT/'data/motor_targets';data.mkdir(exist_ok=True)
    sources={}
    def fetch(name,url):
        p=data/name
        if not p.exists():
            r=requests.get(url,timeout=60);r.raise_for_status();p.write_bytes(r.content)
        sources[name]=dict(url=url,sha256=hashlib.sha256(p.read_bytes()).hexdigest())
        return p
    csv=fetch('manc_muscle_targets.csv','https://cdn.elifesciences.org/articles/96084/elife-96084-supp3-v1.csv')
    targets=pd.read_csv(csv,dtype=str)
    annotations=feather.read_feather(ROOT/'data/malecns/body-annotations-male-cns-v1.0-minconf-0.5.feather')
    candidate_ids=set(pd.read_json(ROOT/'results/malecns_audit/tibia_motor_candidates.json').bodyId)
    candidates=annotations[annotations.bodyId.isin(candidate_ids)][['bodyId','type','somaSide','mancBodyid']].copy()
    candidates['manc_id']=candidates.mancBodyid.map(lambda v:str(int(v)) if pd.notna(v) else None)
    joined=exact_join(candidates,targets)
    joined['status']=joined.apply(classify_mapping,axis=1)
    joined['mapping_level']='MaleCNS published MANC correspondence + MANC published target'
    joined.loc[joined.target.isna(),'mapping_level']='unresolved; no matched muscle-target record'
    joined.to_json(out/'malecns_motor_targets.json',orient='records',indent=2)
    consistent=joined[joined.status.eq('consistent_published_assignment_confidence_unreported')].copy()
    consistent['joint']='joint_LFTibia/RFTibia according to matched nerve side'
    consistent['signed_action_in_anatomical_angle']=consistent.target.map({'Ti flexor':'decrease','Ti extensor':'increase'})
    consistent['force_gain']=None
    consistent['neural_execution_enabled']=False
    consistent.to_json(out/'consistent_motor_assignments.json',orient='records',indent=2)
    pools=[]
    for name in ['mn_tibia_ta_flex_A','mn_tibia_ta_flex_B','mn_tibia_ta_flex_C','mn_tibia_extend']:
        p=fetch(name+'.json',BASE+'jsons/make_jsons/'+name+'.json')
        scene=json.loads(p.read_text())
        layer=[x for x in scene['layers'] if x.get('name')=='published FANC neurons']
        if len(layer)!=1: raise ValueError('Ambiguous scene layer')
        for root_id in layer[0]['segments']:
            pools.append(dict(fanc_id=str(root_id),pool=name,source=sources[p.name]['url']))
    pool=pd.DataFrame(pools)
    if pool.fanc_id.duplicated().any(): raise ValueError('Overlapping target pools')
    # Read with string IDs: never route 64-bit FANC IDs through floats.
    raw=json.loads((ROOT/'results/reflex_reference/claw_extension_reference_edges.json').read_text())
    edges=pd.DataFrame(raw)
    selected=edges[edges.target_class.eq('MN')].merge(pool,left_on='post_pt_root_id',right_on='fanc_id',how='left',validate='many_to_one')
    selected.to_json(out/'fanc_claw_extension_to_motor_pools.json',orient='records',indent=2)
    summary=dict(sources=sources, malecns_candidates=len(candidates),
        mapping_status_counts=joined.status.value_counts().to_dict(),
        malecns_with_recorded_muscle_target=int(joined.target.notna().sum()),
        manc_target_counts=joined.target.value_counts().to_dict(),
        manc_explicit_confidence_scores=int(joined['match_certainty(1-5)'].notna().sum()),
        fanc_reference_synapses=int(selected.synapse_records.sum()),
        fanc_pool_synapses=selected.groupby('pool').synapse_records.sum().to_dict(),
        fanc_unmatched_synapses=int(selected.loc[selected.pool.isna(),'synapse_records'].sum()),
        fanc_to_malecns_cell_identity_verified=False, physiological_13B_alpha_identified=False,
        neural_steps=0, muscle_force_parameters_validated=False)
    (out/'report.json').write_text(json.dumps(summary,indent=2))
    print(json.dumps({k:v for k,v in summary.items() if k!='sources'},indent=2))


if __name__=='__main__':main()

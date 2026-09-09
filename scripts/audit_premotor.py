"""Static two-hop pathway and missing-input audit; no neural dynamics."""
import json
import hashlib
from pathlib import Path
import sys
ROOT=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT))
import pandas as pd
import pyarrow as pa
import pyarrow.ipc as ipc
import pyarrow.feather as feather
import requests
from scripts.audit_malecns import incoming_edges


def main():
    data=ROOT/'data/malecns'
    source=ROOT/'results/malecns_audit'
    out=ROOT/'results/premotor_audit'
    out.mkdir(exist_ok=True)
    annotations=feather.read_feather(data/'body-annotations-male-cns-v1.0-minconf-0.5.feather')
    nt_path=data/'body-neurotransmitters-male-cns-v1.0.feather'
    if not nt_path.exists():
        response=requests.get('https://storage.googleapis.com/flyem-male-cns/v1.0/connectome-data/flat-connectome/'+nt_path.name,timeout=60)
        response.raise_for_status()
        temp=nt_path.with_suffix('.partial')
        temp.write_bytes(response.content)
        feather.read_table(temp)
        temp.replace(nt_path)
    nt=feather.read_feather(nt_path)
    edges=pd.read_json(source/'motor_incoming_edges.json')
    sensory=pd.read_json(source/'foreleg_chordotonal_candidates.json')
    motors=pd.read_json(source/'tibia_motor_candidates.json')
    # Include ALL annotated VNC-intrinsic sources, not just a weight-ranked few.
    premotor=annotations[annotations.bodyId.isin(edges.body_pre)
                         & annotations.superclass.eq('vnc_intrinsic')].copy()
    reader=ipc.open_file(pa.memory_map(str(data/'connectome-weights-male-cns-v1.0-minconf-0.5.feather')))
    incoming, rows=incoming_edges((reader.get_batch(i) for i in range(reader.num_record_batches)),premotor.bodyId)
    sensory_edges=incoming[incoming.body_pre.isin(sensory.bodyId)]
    total=incoming.groupby('body_post').weight.sum().rename('all_incoming_contacts')
    direct=sensory_edges.groupby('body_post').weight.sum().rename('candidate_sensory_contacts')
    output=edges.groupby('body_pre').weight.sum().rename('contacts_to_motor_pool')
    report=premotor[['bodyId','type','somaSide','statusLabel']].merge(total,left_on='bodyId',right_index=True,validate='one_to_one')
    report=report.merge(direct,left_on='bodyId',right_index=True,how='left',validate='one_to_one')
    report['candidate_sensory_contacts']=report.candidate_sensory_contacts.fillna(0).astype(int)
    report=report.merge(output,left_on='bodyId',right_index=True,validate='one_to_one')
    report=report.merge(nt[['body','consensus_nt','predicted_nt_confidence']],left_on='bodyId',right_on='body',how='left',validate='one_to_one')
    report.sort_values('contacts_to_motor_pool',ascending=False).to_json(out/'premotor_candidates.json',orient='records',indent=2)
    sensory_edges.to_json(out/'sensory_to_premotor_edges.json',orient='records',indent=2)
    proposed=set(premotor.bodyId)|set(sensory.bodyId)|set(motors.bodyId)
    retained=incoming.body_pre.isin(proposed)
    inside=int(incoming.loc[retained,'weight'].sum())
    outside=int(incoming.loc[~retained,'weight'].sum())
    assert inside+outside==int(incoming.weight.sum())
    motor_vnc=int(edges.loc[edges.body_pre.isin(premotor.bodyId),'weight'].sum())
    summary=dict(neural_steps=0, graph_rows_scanned=rows,
        premotor_candidates=len(premotor), candidates_with_selected_sensory_input=int((report.candidate_sensory_contacts>0).sum()),
        annotated_vnc_contacts_to_motors=motor_vnc,
        fraction_motor_input_from_annotated_vnc=motor_vnc/int(edges.weight.sum()),
        premotor_incoming_contacts=inside+outside,premotor_excluded_contacts=outside,
        premotor_excluded_fraction=outside/(inside+outside),
        candidate_consensus_transmitters=report.consensus_nt.fillna('unknown').value_counts().to_dict(),
        nt_source='https://storage.googleapis.com/flyem-male-cns/v1.0/connectome-data/flat-connectome/'+nt_path.name,
        nt_sha256=hashlib.sha256(nt_path.read_bytes()).hexdigest(),
        ready_for_neural_execution=False,
        limitations=['Two-hop connectivity is not validated reflex physiology.',
                    'Predicted transmitter does not establish receptor-specific functional sign.',
                    'Candidate pool omits recorded external inputs and unobserved synapses.',
                    'Muscle recruitment, afferent tuning and welfare telemetry remain uncalibrated.'])
    (out/'report.json').write_text(json.dumps(summary,indent=2))
    print(json.dumps(summary,indent=2))


if __name__=='__main__': main()

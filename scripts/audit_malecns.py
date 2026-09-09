"""Static anatomy audit only: never initializes or advances a neural model."""
from pathlib import Path
import hashlib
import json
import argparse
import requests
import pyarrow.feather as feather
import pyarrow as pa
import pyarrow.compute as pc
import pyarrow.ipc as ipc

ROOT = Path(__file__).resolve().parents[1]
NAME = 'body-annotations-male-cns-v1.0-minconf-0.5.feather'
URL = 'https://storage.googleapis.com/flyem-male-cns/v1.0/connectome-data/flat-connectome/' + NAME


def incoming_edges(batches, targets):
    selected = []
    rows = 0
    ids = pa.array(list(targets), type=pa.int64())
    for batch in batches:
        if not {'body_pre', 'body_post', 'weight'}.issubset(batch.schema.names):
            raise ValueError('Missing edge columns')
        for name in ('body_pre', 'body_post', 'weight'):
            column = batch.column(name)
            if column.null_count or pc.any(pc.less(column, 0)).as_py():
                raise ValueError('Invalid edge data')
        rows += batch.num_rows
        subset = batch.filter(pc.is_in(batch.column('body_post'), value_set=ids))
        if subset.num_rows:
            selected.append(subset)
    if not selected:
        raise ValueError('No incoming edges for selected motor pool')
    return pa.Table.from_batches(selected).to_pandas(), rows


def select_candidates(df):
    required = {'bodyId', 'superclass', 'subclass', 'type', 'somaNeuromere',
                'somaSide', 'rootSide', 'entryNerve', 'mancBodyid', 'statusLabel'}
    if not required.issubset(df.columns):
        raise ValueError('Missing annotation columns: ' + str(required-set(df.columns)))
    if df.bodyId.isna().any() or df.bodyId.duplicated().any():
        raise ValueError('Missing or duplicate neuron identifiers')
    motors = df[df.superclass.eq('vnc_motor') & df.subclass.eq('fl')
                & df.somaNeuromere.eq('T1')
                & df.statusLabel.eq('Reviewed')
                & df.type.isin(['Ti extensor MN', 'Ti flexor MN'])].copy()
    sensory = df[df.superclass.isin(['vnc_sensory', 'sensory_ascending'])
                 & df.entryNerve.isin(['ProLN', 'ProCN'])
                 & df.subclass.eq('chordotonal organ')].copy()
    return motors, sensory


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--download-connectivity', action='store_true',
                        help='Download the 1.05 GB anatomical edge table; no simulation')
    args = parser.parse_args()
    data = ROOT/'data/malecns'
    data.mkdir(exist_ok=True)
    path = data/NAME
    if not path.exists():
        response = requests.get(URL, timeout=60)
        response.raise_for_status()
        temp = path.with_suffix('.partial')
        temp.write_bytes(response.content)
        feather.read_table(temp)  # Validate before promoting a download.
        temp.replace(path)
    df = feather.read_feather(path)
    motors, sensory = select_candidates(df)
    out = ROOT/'results/malecns_audit'
    out.mkdir(exist_ok=True)
    motors.to_json(out/'tibia_motor_candidates.json', orient='records', indent=2)
    sensory.to_json(out/'foreleg_chordotonal_candidates.json', orient='records', indent=2)
    report = dict(dataset='male-cns:v1.0', source=URL,
        sha256=hashlib.sha256(path.read_bytes()).hexdigest(), bytes=path.stat().st_size,
        annotation_rows=len(df), motor_candidates=len(motors),
        sensory_candidates=len(sensory), motor_types=motors.type.value_counts().to_dict(),
        motor_manc_matches=int(motors.mancBodyid.notna().sum()),
        motor_status=motors.statusLabel.astype(str).value_counts().to_dict(),
        neuron_steps_executed=0, model_instantiated=False,
        muscle_mapping_validated=False, connectivity_extracted=False,
        ready_for_neural_simulation=False,
        unresolved=['Soma side alone does not validate peripheral muscle laterality.',
                    'Cell names identify candidate actions, not force/activation parameters.',
                    'Need connectivity and omitted-input audit before selecting interneurons.',
                    'Need proprioceptor subtype tuning and muscle target cross-check.',
                    'Need reviewed telemetry semantics and limits before neural execution.'])
    graph = data/'connectome-weights-male-cns-v1.0-minconf-0.5.feather'
    if args.download_connectivity and not graph.exists():
        temp = graph.with_suffix('.partial')
        with requests.get(URL.rsplit('/',1)[0]+'/'+graph.name, stream=True, timeout=60) as response:
            response.raise_for_status()
            with temp.open('wb') as handle:
                for block in response.iter_content(4*1024*1024):
                    handle.write(block)
        with pa.memory_map(str(temp)) as mapped:
            ipc.open_file(mapped)  # Validate Arrow container before promotion.
        temp.replace(graph)
    if graph.exists():
        reader = ipc.open_file(pa.memory_map(str(graph)))
        edges, nrows = incoming_edges((reader.get_batch(i) for i in range(reader.num_record_batches)),
                                     motors.bodyId.tolist())
        edges.to_json(out/'motor_incoming_edges.json', orient='records', indent=2)
        retained = edges.body_pre.isin(set(motors.bodyId) | set(sensory.bodyId))
        direct = edges.body_pre.isin(set(sensory.bodyId))
        total = int(edges.weight.sum())
        inside = int(edges.loc[retained, 'weight'].sum())
        outside = int(edges.loc[~retained, 'weight'].sum())
        assert inside + outside == total
        ranked = edges.groupby('body_pre').weight.sum().sort_values(ascending=False).head(40)
        ranking = ranked.rename('synapses_to_motor_pool').reset_index().merge(
            df[['bodyId', 'type', 'superclass', 'subclass', 'somaSide', 'rootSide']],
            left_on='body_pre', right_on='bodyId', how='left', validate='one_to_one')
        ranking.to_json(out/'top_motor_inputs.json', orient='records', indent=2)
        digest = hashlib.sha256()
        with graph.open('rb') as handle:
            for block in iter(lambda: handle.read(8*1024*1024), b''):
                digest.update(block)
        report['connectivity_extracted'] = True
        report['connectivity'] = dict(source=URL.rsplit('/',1)[0]+'/'+graph.name,
            sha256=digest.hexdigest(), graph_rows=nrows, incoming_edges=len(edges),
            incoming_synaptic_contacts=total, candidate_pool_contacts=inside,
            excluded_contacts=outside, excluded_fraction=outside/total,
            direct_sensory_contacts=int(edges.loc[direct, 'weight'].sum()),
            unannotated_source_contacts=int(edges.loc[~edges.body_pre.isin(df.bodyId),'weight'].sum()))
        report['unresolved'][2] = 'Motor input extraction complete; upstream closure and functional interneuron selection unresolved.'
    (out/'audit.json').write_text(json.dumps(report, indent=2)+'\n')
    print(json.dumps(report, indent=2))


if __name__ == '__main__':
    main()

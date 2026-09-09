"""Static connectome audit only; no neural simulation or assumed new wiring."""
import json
from pathlib import Path
import numpy as np
import pandas as pd
ROOT=Path(__file__).resolve().parents[1]
out=ROOT/'results/visual_learning_path';out.mkdir(exist_ok=True)
a=pd.read_csv(ROOT/'data/annotations.tsv',sep='\t',low_memory=False).set_index('root_id')
comp=pd.read_csv(ROOT/'upstream/Drosophila_brain_model/Completeness_783.csv',index_col=0)
c=pd.read_parquet(ROOT/'upstream/Drosophila_brain_model/Connectivity_783.parquet')
types=a.cell_type.fillna('');cc=a.cell_class.fillna('');sc=a.super_class.fillna('');ht=a.hemibrain_type.fillna('')
visual_ids=a.index[types=='KCg-d']
keep=a.index[(sc.str.contains('sensory')&cc.str.contains('olfactory'))|cc.isin(['ALLN','ALPN'])|
             cc.str.contains('Kenyon',case=False)|(types=='APL')|
             types.str.startswith(('MBON','PAM','PPL1'))|ht.str.startswith(('MBON','PAM','PPL1'))]
keep=np.intersect1d(keep,comp.index)
incoming=c[c.Postsynaptic_ID.isin(visual_ids)].copy()
incoming['pre_type']=incoming.Presynaptic_ID.map(types).fillna('unannotated')
incoming['pre_class']=incoming.Presynaptic_ID.map(cc).fillna('unannotated')
incoming['in_current_subnet']=incoming.Presynaptic_ID.isin(keep)
by_type=incoming.groupby(['pre_type','pre_class','in_current_subnet']).agg(
    connections=('Connectivity','size'),synapses=('Connectivity','sum'),
    source_neurons=('Presynaptic_ID','nunique'),target_kcs=('Postsynaptic_ID','nunique')).reset_index()
by_type.sort_values('synapses',ascending=False).to_csv(out/'visual_kc_inputs.csv',index=False)
spec=json.loads((ROOT/'upstream/flyvis/flyvis/connectome/fib25-fib19_v2.2.json').read_text())
flyvis_types={n['name'] for n in spec['nodes']}
visual_projection=incoming[incoming.pre_class.str.contains('visual',case=False)|incoming.pre_type.str.startswith(('aMe','MeTu','CB0156','PLP'))]
bridge=visual_projection.groupby('pre_type').agg(synapses=('Connectivity','sum'),neurons=('Presynaptic_ID','nunique')).reset_index()
bridge['in_flyvis']=bridge.pre_type.isin(flyvis_types)
bridge.to_csv(out/'candidate_visual_inputs.csv',index=False)
direct_overlap=incoming[incoming.pre_type.isin(flyvis_types)]
omitted_ids=incoming.loc[~incoming.in_current_subnet,'Presynaptic_ID'].unique()
upstream=c[c.Postsynaptic_ID.isin(omitted_ids)].copy()
upstream['pre_type']=upstream.Presynaptic_ID.map(types).fillna('unannotated')
upstream['post_type']=upstream.Postsynaptic_ID.map(types).fillna('unannotated')
overlap=upstream[upstream.pre_type.isin(flyvis_types)]
overlap.groupby(['pre_type','post_type']).Connectivity.sum().sort_values(ascending=False).to_csv(out/'two_hop_type_overlap.csv')
incoming.loc[~incoming.in_current_subnet].to_parquet(out/'omitted_inputs_to_visual_kcs.parquet',index=False)
overlap.to_parquet(out/'flyvis_type_inputs_to_missing_cells.parquet',index=False)
strong_down=incoming[(~incoming.in_current_subnet)&(incoming.Connectivity>=5)]
strong_up=overlap[(overlap.Connectivity>=5)&overlap.Postsynaptic_ID.isin(strong_down.Presynaptic_ID)]
bridge_ids=np.intersect1d(strong_up.Postsynaptic_ID, strong_down.Presynaptic_ID)
strong_down=strong_down[strong_down.Presynaptic_ID.isin(bridge_ids)]
strong_up.to_parquet(out/'candidate_bridge_upstream_edges.parquet',index=False)
strong_down.to_parquet(out/'candidate_bridge_downstream_edges.parquet',index=False)
a.loc[bridge_ids,['cell_type','side','pos_x','pos_y','pos_z','top_nt']].to_csv(out/'candidate_bridge_neurons.csv')
result=dict(neural_simulation=False,visual_kcs=len(visual_ids),current_subnet_size=len(keep),
            incoming_connections=len(incoming),incoming_synapses=int(incoming.Connectivity.sum()),
            incoming_synapses_from_omitted_neurons=int(incoming.loc[~incoming.in_current_subnet,'Connectivity'].sum()),
            flyvis_types_with_direct_kc_edges=sorted(direct_overlap.pre_type.unique()),
            direct_flyvis_type_overlap_synapses=int(direct_overlap.Connectivity.sum()),
            two_hop_type_overlap_synapses=int(overlap.Connectivity.sum()),
            two_hop_type_overlap_connections=len(overlap),
            candidate_bridge_neurons_at_5_synapses_each_leg=len(bridge_ids),
            candidate_bridge_upstream_edges=len(strong_up),candidate_bridge_downstream_edges=len(strong_down),
            integration_gate_passed=False,
            integration_gate_reason='No validated cross-specimen retinotopic identity map or functional model of the intermediate neurons.',
            major_input_types=by_type.sort_values('synapses',ascending=False).head(16).to_dict(orient='records'),
            mapping_limit='Cell-type overlap is not a neuron-to-neuron or retinotopic mapping across specimens.',
            connection_columns=c.columns.tolist(),
            compartment_resolved_synapse_coordinates_available=False)
(out/'checks.json').write_text(json.dumps(result,indent=2))
print(json.dumps(result,indent=2))

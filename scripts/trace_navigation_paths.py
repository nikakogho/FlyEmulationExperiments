"""Full-table offline pathway witnesses and closure audit; no neural imports."""
from pathlib import Path
import sys,json,hashlib
import numpy as np,pandas as pd
ROOT=Path(__file__).resolve().parents[1];sys.path.insert(0,str(ROOT))
from flyplasticity.navigation_audit import contact_graph,shortest_paths,input_coverage


def main():
    files=[ROOT/'data/annotations.tsv',ROOT/'upstream/Drosophila_brain_model/Completeness_783.csv',
           ROOT/'upstream/Drosophila_brain_model/Connectivity_783.parquet']
    a=pd.read_csv(files[0],sep='\t',low_memory=False).set_index('root_id')
    comp=pd.read_csv(files[1],index_col=0);a=a.reindex(comp.index)
    c=pd.read_parquet(files[2]);pre=c.Presynaptic_Index.to_numpy();post=c.Postsynaptic_Index.to_numpy()
    if not np.array_equal(comp.index.to_numpy()[pre],c.Presynaptic_ID.to_numpy()) or not np.array_equal(comp.index.to_numpy()[post],c.Postsynaptic_ID.to_numpy()):
        raise ValueError('Root IDs and graph index order disagree')
    g=contact_graph(len(a),pre,post,c.Connectivity.to_numpy())
    types=['MBON01','MBON06','MBON07','MBON14','SMP353','SMP354','SMP108',
           'FB6D','FB6I','FB6T','hDeltaC','PFL3','DNa01','DNa02']
    groups={t:np.flatnonzero(a.cell_type==t) for t in types}
    def cell(i):
        r=a.iloc[i]
        return dict(root_id=str(comp.index[i]),cell_type=None if pd.isna(r.cell_type) else r.cell_type,
                    side=None if pd.isna(r.side) else r.side)
    def witness(path):
        return None if path is None else dict(cells=[cell(i) for i in path],
            contacts=[int(g[x,y]) for x,y in zip(path,path[1:])])
    routes=[]
    for s in groups['MBON01']:
        paths=shortest_paths(g,int(s),np.concatenate([groups[t] for t in ['SMP353','SMP108','DNa01','DNa02']]))
        routes.append(dict(source=cell(s),paths=[dict(target=cell(t),witness=witness(p)) for t,p in paths.items()]))
    direct=[]
    for s in types:
        for t in types:
            count=int(g[groups[s]][:,groups[t]].sum())
            if count:direct.append(dict(source_type=s,target_type=t,contacts=count))
    selected=np.concatenate(list(groups.values()))
    male_path=ROOT/'data/malecns/body-annotations-male-cns-v1.0-minconf-0.5.feather'
    male=pd.read_feather(male_path)
    cross=male[male.type.eq('SMP354')][['bodyId','type','flywireType','hemibrainType','statusLabel']]
    aliases=sorted(cross.flywireType.dropna().unique().tolist())
    alias_cells=np.flatnonzero(a.cell_type.isin(aliases))
    expanded=np.union1d(selected,alias_cells)
    alias_inputs=[]
    for i in alias_cells:
        alias_inputs.append(dict(cell=cell(i),mbon_input_contacts={t:int(g[groups[t],i].sum())
            for t in ['MBON01','MBON06','MBON07','MBON14']},
            outputs_to_candidates={t:int(g[i,groups[t]].sum()) for t in ['SMP108','FB6D','FB6I','FB6T']}))
    result=dict(new_neural_steps=0,new_physics_steps=0,
        provenance={str(p.relative_to(ROOT)):hashlib.sha256(p.read_bytes()).hexdigest() for p in files+[male_path]},
        group_sizes={t:len(v) for t,v in groups.items()},
        selected_input_coverage=input_coverage(g,selected),
        per_type_input_coverage={t:input_coverage(g,v) for t,v in groups.items()},
        direct_type_contacts=direct,mbon01_shortest_witnesses=routes,
        smp354_crossreference=dict(source_rows=cross.to_dict('records'),flywire_type_aliases=aliases,
            matched_cells=alias_inputs,expanded_cell_count=len(expanded),
            expanded_input_coverage=input_coverage(g,expanded),
            limitation='Dataset-provided type correspondence, not individual-cell identity across specimens; tracing status preserved'),
        interpretation='All contacts positive anatomical counts. Shortest witnesses are arbitrary among ties, not functional pathways. SMP354 correspondence comes from the MaleCNS flywireType annotation, not name similarity. Selected groups do not constitute a closed calibrated circuit.')
    out=ROOT/'results/navigation_paths_v1.json';out.write_text(json.dumps(result,indent=2))
    print(json.dumps({k:v for k,v in result.items() if k not in ('direct_type_contacts','mbon01_shortest_witnesses','per_type_input_coverage','provenance')},indent=2))

if __name__=='__main__':main()

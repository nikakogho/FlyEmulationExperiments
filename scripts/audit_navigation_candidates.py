"""Static candidate-cell audit; does not construct or advance neural models."""
from pathlib import Path
import pandas as pd,numpy as np,json
ROOT=Path(__file__).resolve().parents[1]

def main():
    ann=pd.read_csv(ROOT/'data/annotations.tsv',sep='\t',low_memory=False).set_index('root_id')
    comp=pd.read_csv(ROOT/'upstream/Drosophila_brain_model/Completeness_783.csv',index_col=0)
    a=ann.reindex(comp.index)
    c=pd.read_parquet(ROOT/'upstream/Drosophila_brain_model/Connectivity_783.parquet')
    pre=c.Presynaptic_Index.to_numpy();post=c.Postsynaptic_Index.to_numpy()
    mb=np.flatnonzero(a.cell_type=='MBON01');candidates=np.flatnonzero(a.cell_type.isin(['SMP353','SMP354','SMP108']))
    cc=a.cell_class.fillna('');sc=a.super_class.fillna('');ct=a.cell_type.fillna('');ht=a.hemibrain_type.fillna('')
    included=(sc.str.contains('sensory')&cc.str.contains('olfactory'))|(cc=='ALLN')|(cc=='ALPN')|cc.str.contains('Kenyon',case=False)|(ct=='APL')|ct.str.startswith('MBON')|ht.str.startswith('MBON')|ct.str.startswith('PAM')|ht.str.startswith('PAM')|ct.str.startswith('PPL1')|ht.str.startswith('PPL1')
    rows=[]
    for i in candidates:
        direct=c[np.isin(pre,mb)&(post==i)];reverse=c[(pre==i)&np.isin(post,mb)]
        rows.append(dict(root_id=str(comp.index[i]),cell_type=a.iloc[i].cell_type,side=a.iloc[i].side,
                         mbon01_input_edges=len(direct),mbon01_input_signed_weight_sum=float(direct['Excitatory x Connectivity'].sum()),
                         edges_back_to_mbon01=len(reverse),included_in_current_subnet=bool(included.iloc[i])))
    result=dict(analysis_neural_steps=0,candidates=rows,
                weight_unit='Raw Excitatory x Connectivity field; not a calibrated physiological strength',
                interpretation='Candidate navigation-related types are excluded from the current olfactory subnet. Edges do not validate dynamics or a motor mapping. SMP353 has no direct MBON01 edge here; do not invent one.')
    (ROOT/'results/navigation_candidate_audit.json').write_text(json.dumps(result,indent=2));print(json.dumps(result,indent=2))

if __name__=='__main__':main()

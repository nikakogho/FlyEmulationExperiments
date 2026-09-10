"""Static correspondence for the pinned upstream subnet; no neural stepping."""
from pathlib import Path
import sys
ROOT=Path(__file__).resolve().parents[1];sys.path.insert(0,str(ROOT))
import numpy as np,pandas as pd
from flyplasticity.odor_scene import OrnTransport

def transport_for(brain):
    a=pd.read_csv(ROOT/'data/annotations.tsv',sep='\t',low_memory=False).set_index('root_id')
    comp=pd.read_csv(ROOT/'upstream/Drosophila_brain_model/Completeness_783.csv',index_col=0)
    a=a.reindex(comp.index)
    cc=a.cell_class.fillna('');sc=a.super_class.fillna('');ct=a.cell_type.fillna('');ht=a.hemibrain_type.fillna('')
    mask=(sc.str.contains('sensory')&cc.str.contains('olfactory'))|(cc=='ALLN')|(cc=='ALPN')|cc.str.contains('Kenyon',case=False)|(ct=='APL')|ct.str.startswith('MBON')|ht.str.startswith('MBON')|ct.str.startswith('PAM')|ht.str.startswith('PAM')|ct.str.startswith('PPL1')|ht.str.startswith('PPL1')
    local=a.loc[mask]
    if len(local)!=len(brain.neu):raise ValueError('Subnet annotation order mismatch')
    neurons=np.array(list(brain.A)+list(brain.B),dtype=int)
    records=local.iloc[neurons];channels=[0]*len(brain.A)+[1]*len(brain.B)
    bridge=OrnTransport(channels,records.side.tolist(),records.nerve.tolist())
    drive_idx=np.array([brain.pos[i] for i in neurons])
    rows=[dict(root_id=str(root),local_index=int(i),channel=int(c),side=str(row.side),nerve=str(row.nerve))
          for (root,row),i,c in zip(records.iterrows(),neurons,channels)]
    return bridge,drive_idx,rows

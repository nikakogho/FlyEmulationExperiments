"""Anatomical inventory of the pooled output; no inferred behavioral labels."""
import json
import numpy as np
import pandas as pd
from light_brain import LightBrain, ROOT


def main():
    brain=LightBrain(101)
    annotations=pd.read_csv(ROOT/'data/annotations.tsv',sep='\t',low_memory=False).set_index('root_id')
    completeness=pd.read_csv(ROOT/'upstream/Drosophila_brain_model/Completeness_783.csv',index_col=0)
    ids={new:int(completeness.index[old]) for old,new in brain.old2new.items()}
    targets=np.array(brain.b.syn.j[brain.plastic])
    rows=[]
    for neuron in brain.b.g['mbon']:
        record=annotations.loc[ids[neuron]]
        rows.append(dict(root_id=ids[neuron],cell_type=record.cell_type,side=record.side,
                         predicted_transmitter=record.top_nt,
                         known_transmitter=None if pd.isna(record.known_nt) else record.known_nt,
                         visual_kc_edges=int((targets==neuron).sum())))
    result=dict(output_cells=len(rows),output_types=len(set(r['cell_type'] for r in rows)),rows=rows,
                note='All these cell types are pooled equally by hemisphere in the current decoder. Transmitter alone does not establish behavioral valence.')
    (ROOT/'results/light_readout_inventory.json').write_text(json.dumps(result,indent=2))
    print(json.dumps({k:v for k,v in result.items() if k!='rows'},indent=2))


if __name__=='__main__': main()

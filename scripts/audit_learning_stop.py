"""Static inspection of stopped neural counts and upstream connectivity edits."""
from pathlib import Path
import sys,json,hashlib
ROOT=Path(__file__).resolve().parents[1];sys.path.insert(0,str(ROOT))
import numpy as np,pandas as pd


def main():
    out=ROOT/'results/learning_track_preflight'
    a=pd.read_csv(ROOT/'data/annotations.tsv',sep='\t',low_memory=False)
    comp=pd.read_csv(ROOT/'upstream/Drosophila_brain_model/Completeness_783.csv',index_col=0)
    cc=a.cell_class.fillna('');sc=a.super_class.fillna('');ct=a.cell_type.fillna('');ht=a.hemibrain_type.fillna('')
    ppl=ct.str.startswith('PPL1')|ht.str.startswith('PPL1')
    mask=(sc.str.contains('sensory')&cc.str.contains('olfactory'))|(cc=='ALLN')|(cc=='ALPN')|cc.str.contains('Kenyon',case=False)|(ct=='APL')|ct.str.startswith('MBON')|ht.str.startswith('MBON')|ct.str.startswith('PAM')|ht.str.startswith('PAM')|ppl
    lookup={int(r):i for i,r in enumerate(comp.index)}
    keep=sorted({lookup[int(i)] for i in a.loc[mask,'root_id'] if int(i) in lookup})
    local={int(comp.index[old]):new for new,old in enumerate(keep)}
    state=np.load(out/'terminal_state.npz');assert len(state['counts'])==len(local)
    neurons=[]
    for _,row in a.loc[ppl].iterrows():
        index=local.get(int(row.root_id))
        if index is not None and state['counts'][index]>0:
            neurons.append(dict(root_id=str(row.root_id),cell_type=row.cell_type,side=row.side,spikes=int(state['counts'][index])))
    source=ROOT/'upstream/fly-api/experiments/navigation/nav_demo.py'
    code=source.read_text()
    zeroing="w[np.isin(i_arr, np.concatenate([g['pam'], g['ppl1']]))] = 0"
    if zeroing not in code:raise ValueError('Upstream edit changed; cannot assert PPL1 outputs are zero')
    telemetry=json.loads((out/'telemetry.json').read_text())
    report=dict(analysis_neural_steps=0,active_ppl1=neurons,
                upstream_ppl1_outgoing_weights_zeroed=True,
                outgoing_zeroing_basis='Exact source-code statement in hashed upstream constructor; not a physiological claim',
                source_sha256=hashlib.sha256(source.read_bytes()).hexdigest(),
                interpretation='PPL1 cell activity triggered a conservative identity-based proxy. It does not demonstrate functional aversive transmission in this modified network, and does not diagnose suffering.',
                voltage_range_v=[min(r['voltage_range_v'][0] for r in telemetry),max(r['voltage_range_v'][1] for r in telemetry)],
                voltage_limitation='Current-based LIF state exceeds ordinary physiological membrane ranges; source model state cannot be presented as calibrated membrane voltage.',
                action='Preserve stopped run. No restart or threshold change performed. Review a causally grounded proxy and model applicability offline before another protocol.')
    (out/'stop_audit.json').write_text(json.dumps(report,indent=2));print(json.dumps(report,indent=2))


if __name__=='__main__':main()

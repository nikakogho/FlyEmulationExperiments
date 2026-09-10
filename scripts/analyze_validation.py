"""Offline cohort attribution, integrity checks and plots; no neural steps."""
from pathlib import Path
import json,pickle,sys
ROOT=Path(__file__).resolve().parents[1];sys.path.insert(0,str(ROOT))
import numpy as np
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt

def main():
    out=ROOT/'results/association_validation_v1'
    assessment=json.loads((out/'assessment.json').read_text())
    # Trusted local files created by our own Brian2 runner, not downloaded pickles.
    initial=pickle.loads((ROOT/'results/learning_track_preflight_v2/network_state.pkl').read_bytes())['terminal']['sub_synapses']['w'][0]
    attribution={}
    for case in assessment['cases']:
        name=f"seed{case['seed']}_{case['reinforced']}";casedir=out/name;arms={}
        for arm in ('paired','unpaired','frozen'):
            p=casedir/arm
            if not (p/'report.json').exists():continue
            r=json.loads((p/'report.json').read_text());a=np.load(p/'learning_arrays.npz')
            state=pickle.loads((p/'network_state.pkl').read_bytes())['terminal'];full=state['sub_synapses']['w'][0]
            rows=json.loads((p/'telemetry.json').read_text());positions=a['plastic_positions']
            mask=np.ones(len(full),dtype=bool);mask[positions]=False
            checks=dict(nonplastic_unchanged=bool(np.array_equal(initial[mask],full[mask])),
                        final_tape_matches=bool(np.array_equal(full[positions],a['final'])),
                        spike_totals_match=int(state['spikemonitor']['count'][0].sum())==sum(row['total_spikes'] for row in rows))
            if not all(checks.values()):raise ValueError('Checkpoint mismatch: '+str(p))
            trained=case['reinforced'];other='B' if trained=='A' else 'A'
            active=a['pre_'+trained][a['plastic_pre']]>0;control=a['pre_'+other][a['plastic_pre']]>0
            groups={}
            for label,m in [('reinforced_only',active&~control),('other_only',control&~active),('both',active&control)]:
                groups[label]=dict(edges=int(m.sum()),mean_weight_fraction=float(np.mean(a['final'][m]/a['initial'][m])) if m.any() else None)
            arms[arm]=dict(checks=checks,groups=groups,
                           pretraining_weights_unchanged=bool('250' in a and np.array_equal(a['250'],a['initial'])),
                           recovery_pass=r['recovery_pass'])
        attribution[name]=arms
    (out/'attribution.json').write_text(json.dumps(dict(neural_steps=0,cases=attribution),indent=2))
    labels=[f"Seed {r['seed']} / pair {r['reinforced']}" for r in assessment['cases']]
    fig,ax=plt.subplots(figsize=(10,4.8));x=np.arange(len(labels))
    for i,(arm,color) in enumerate([('paired','#197e91'),('unpaired','#9caab7'),('frozen','#dba34d')]):
        bars=ax.bar(x+(i-1)*.24,[100*r['scores'][arm] for r in assessment['cases']],.24,label=arm,color=color)
        ax.bar_label(bars,fmt='%.1f',padding=3,fontsize=9)
    ax.axhline(15,color='#53606a',linestyle='--',label='15% selectivity margin')
    ax.axhline(0,color='#999',linewidth=.7);ax.set_xticks(x,labels);ax.set_ylabel('Reinforced-cue selectivity (%)')
    ax.set_title('Fixed validation cohort · four counterbalanced cases / two seeds')
    ax.spines[['top','right']].set_visible(False);ax.legend(frameon=False,ncol=2)
    fig.tight_layout();fig.savefig(out/'validation.png',dpi=170);plt.close(fig)
    print(json.dumps(assessment,indent=2))

if __name__=='__main__':main()

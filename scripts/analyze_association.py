"""Offline plots and synaptic diagnostics from the controlled pilot tapes."""
from pathlib import Path
import sys,json,pickle
ROOT=Path(__file__).resolve().parents[1];sys.path.insert(0,str(ROOT))
import numpy as np
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
from flyplasticity.association import comparison


def main():
    out=ROOT/'results/controlled_association_v1';reports={};diagnostics={}
    # Only our own locally generated Brian2 files; never load downloaded pickles.
    baseline=pickle.loads((ROOT/'results/learning_track_preflight_v2/network_state.pkl').read_bytes())['terminal']
    baseline_w=baseline['sub_synapses']['w'][0]
    for arm in ('paired','unpaired','frozen'):
        if not (out/arm/'report.json').exists():continue
        r=json.loads((out/arm/'report.json').read_text());reports[arm]=r
        data=np.load(out/arm/'learning_arrays.npz');pre=data['plastic_pre']
        active_a=data['pre_A'][pre]>0;active_b=data['pre_B'][pre]>0
        groups={'A_only':active_a&~active_b,'B_only':active_b&~active_a,
                'both':active_a&active_b,'neither':~active_a&~active_b}
        table={}
        for name,mask in groups.items():
            table[name]=dict(edges=int(mask.sum()),
                final_mean_fraction=float((data['final'][mask]/data['initial'][mask]).mean()) if mask.any() else None,
                pretraining_mean_fraction=float((data['250'][mask]/data['initial'][mask]).mean()) if mask.any() and '250' in data else None,
                posttraining_mean_fraction=float((data['550'][mask]/data['initial'][mask]).mean()) if mask.any() and '550' in data else None)
        rows=json.loads((out/arm/'telemetry.json').read_text())
        terminal=pickle.loads((out/arm/'network_state.pkl').read_bytes())['terminal']
        final_w=terminal['sub_synapses']['w'][0]
        nonplastic=np.ones(len(final_w),dtype=bool);nonplastic[data['plastic_positions']]=False
        checks=dict(nonplastic_weights_match_independent_preflight=bool(np.array_equal(final_w[nonplastic],baseline_w[nonplastic])),
                    tape_weights_match_full_checkpoint=bool(np.array_equal(final_w[data['plastic_positions']],data['final'])),
                    trace_spikes_match_full_checkpoint=int(terminal['spikemonitor']['count'][0].sum())==sum(x['total_spikes'] for x in rows),
                    probe_counts_match_trace=all(r['probe_spikes'][p]==sum(x['mbon01_spikes'] for x in rows if x['observed_phase']==p)
                                                 for p in r['probe_spikes']))
        if not all(checks.values()):raise ValueError('Saved evidence mismatch: '+arm)
        diagnostics[arm]=dict(weight_groups=table,
            independent_checkpoint_checks=checks,
            max_population_hz=max(x['mean_population_hz'] for x in rows),
            observed_pam_spikes=sum(x.get('pam01_spikes',0) for x in rows),
            final_quiet_s=round(r['neural_time_s']-max((x['time_s'] for x in rows if x['total_spikes']),default=0),6))
    (out/'offline_diagnostics.json').write_text(json.dumps(dict(neural_steps=0,arms=diagnostics),indent=2))
    assessment=comparison(reports)
    assessment['analysis_neural_steps']=0
    assessment['reporting_correction']='Original generic failure label was too broad. Same scores and thresholds; explicit failed criterion added offline.'
    (out/'assessment.json').write_text(json.dumps(assessment,indent=2))
    fig,axes=plt.subplots(1,len(reports),figsize=(4.1*len(reports),4.2),squeeze=False)
    for ax,(arm,r) in zip(axes[0],reports.items()):
        c=r['probe_spikes'];x=np.arange(2)
        for offset,phase,color in [(-.18,'pre','#8b9fb2'),(.18,'post','#247b91')]:
            vals=[c[phase+'_A'],c[phase+'_B']]
            bars=ax.bar(x+offset,vals,width=.34,label=phase,color=color)
            ax.bar_label(bars,padding=3,fontsize=10)
        ax.set_xticks(x,['Odor A','Odor B']);ax.set_title(arm.capitalize())
        ax.set_ylim(0,max(c.values())*1.25 if max(c.values()) else 1)
        ax.set_ylabel('MBON01 spikes / 250 ms');ax.spines[['top','right']].set_visible(False)
        ax.legend(frameon=False)
    fig.suptitle('Controlled association pilot · one seed · stationary modified circuit',fontsize=12)
    fig.tight_layout();fig.savefig(out/'probe_comparison.png',dpi=160);plt.close(fig)
    print(json.dumps(diagnostics,indent=2))


if __name__=='__main__':main()

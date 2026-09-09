"""Account for every planned pilot episode; never discard failed/missing runs."""
import json
from pathlib import Path
import numpy as np
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
ROOT=Path(__file__).resolve().parents[1]
OUT=ROOT/'results/light_garden'


def main():
    rows=[]; missing=[]; failures=[]
    for seed in (0,1,2):
        for condition in ('plastic','frozen','yoked'):
            train=[]; tests=[]
            for name,destination in [(f'train{i}',train) for i in range(3)]+[(f'test_swap{i}',tests) for i in range(2)]:
                path=OUT/f'seed{seed}_{condition}_{name}.json'
                if not path.exists(): missing.append(path.name); continue
                d=json.loads(path.read_text())
                if not d.get('completed'): failures.append(dict(file=path.name,error=d.get('error'))); continue
                if len(d['rows'])!=24: raise RuntimeError('Unexpected completed episode length')
                if d['physics_dt']!=.0001 or d['arena_revision']!=2:
                    raise RuntimeError('Mixed physical configurations in final cohort')
                if name.startswith('test') and (d['food_present'] or d['learning']):
                    raise RuntimeError('Evaluation must disable food and plasticity')
                destination.append(d)
            if len(train)!=3 or len(tests)!=2: continue
            metric=[]
            for test in tests:
                distances=np.array([r['cue_distances'] for r in test['rows']])
                occupancy=(distances<=3).mean(axis=0)
                metric.append(dict(swapped=test['swapped'],green_occupancy=float(occupancy[0]),
                    blue_occupancy=float(occupancy[1]),preference=float(occupancy[0]-occupancy[1]),
                    closest_distance_mm=distances.min(axis=0).tolist(),final_distance_mm=distances[-1].tolist()))
                if any(r['taste'] for r in test['rows']): raise RuntimeError('Reward leaked into food-free evaluation')
            initial_path=OUT/f'seed{seed}_initial_weights.npy'
            weight_path=OUT/f'seed{seed}_{condition}_weights.npy'
            if not initial_path.exists() or not weight_path.exists():
                missing.append(str(weight_path)); continue
            initial=np.load(initial_path); learned=np.load(weight_path)
            if condition=='frozen' and not np.array_equal(initial,learned):
                raise RuntimeError('Frozen control weights changed')
            alltrain=[r for ep in train for r in ep['rows']]
            if condition=='yoked':
                for ep,record in enumerate(train):
                    paired=json.loads((OUT/f'seed{seed}_plastic_train{ep}.json').read_text())
                    expected=np.roll([r['taste'] for r in paired['rows']],12)
                    np.testing.assert_array_equal([r['taste'] for r in record['rows']],expected)
            else:
                if any(r['taste']!=float(r['physical_food_contact']) for r in alltrain):
                    raise RuntimeError('Nonlocal external reinforcement detected')
            taste=np.array([r['taste'] for r in alltrain])
            features=np.array([r['features'] for r in alltrain]).mean(axis=1)
            rewarded_visual=features[taste>0].mean(axis=0).tolist() if taste.sum() else None
            rows.append(dict(seed=seed,condition=condition,preference=float(np.mean([m['preference'] for m in metric])),
                acquisition_contacts=sum(r['physical_food_contact'] for r in alltrain),
                reinforcement_steps=int(taste.sum()),reinforced_mean_visual=rewarded_visual,
                weight_L1_fraction=float(np.abs(learned).sum()/np.abs(initial).sum()),
                changed_weights=int(np.count_nonzero(initial!=learned)),tests=metric))
    paired=[]
    for seed in (0,1,2):
        r={x['condition']:x for x in rows if x['seed']==seed}
        if len(r)==3: paired.append(dict(seed=seed,plastic_minus_frozen=r['plastic']['preference']-r['frozen']['preference'],
            plastic_minus_yoked=r['plastic']['preference']-r['yoked']['preference']))
    report=dict(complete=not missing and not failures,missing=missing,failures=failures,
        metric='green minus blue occupancy within 3 mm; average of original and swapped tests',
        rows=rows,paired_effects=paired,
        limitations=['Three seeds, descriptive pilot only','Engineered camera-to-KC and taste-to-PAM adapters',
            'Shifted reward may remain correlated with persistent cues',
            'Revision 2 flat 3D floor, 0.1 ms physics; no obstacle-navigation or convergence claim',
            'Prior terraced cohorts failed physically and are retained separately'])
    if len(paired)==3:
        report['mean_plastic_minus_frozen']=float(np.mean([r['plastic_minus_frozen'] for r in paired]))
        report['mean_plastic_minus_yoked']=float(np.mean([r['plastic_minus_yoked'] for r in paired]))
        report['all_plastic_seeds_encountered_food']=all(r['acquisition_contacts']>0 for r in rows if r['condition']=='plastic')
        report['descriptive_advantage_over_both_controls']=(report['mean_plastic_minus_frozen']>0 and report['mean_plastic_minus_yoked']>0)
        report['learning_claim']='No biological learning or superiority claim follows from this pilot alone'
    OUT.mkdir(parents=True,exist_ok=True)
    (OUT/'summary.json').write_text(json.dumps(report,indent=2))
    fig,axes=plt.subplots(1,3,figsize=(12,3.8),layout='constrained')
    for ax,seed in zip(axes,(0,1,2)):
        subset=[r for r in rows if r['seed']==seed]
        ax.bar([r['condition'] for r in subset],[r['preference'] for r in subset],color=['#248675','#657184','#b28143'][:len(subset)])
        ax.axhline(0,color='.3',lw=.8); ax.set_ylim(-1,1); ax.set_title(f'Seed {seed}')
        ax.set_ylabel('Green minus blue occupancy')
    fig.suptitle('Food-free light preference; both light positions tested')
    fig.savefig(OUT/'preference.png',dpi=160)
    print(json.dumps({k:v for k,v in report.items() if k not in ('rows',)},indent=2))


if __name__=='__main__': main()

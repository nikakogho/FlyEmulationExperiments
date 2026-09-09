"""Run the predeclared Figure 5c reproduction gate, without parameter fitting."""
import hashlib
import json
import sys
from pathlib import Path
from time import perf_counter
import numpy as np
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt

ROOT=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT))
from flyplasticity.huang2024 import load_parameters,run,figure5c_protocol,parameter_file


def main():
    out=ROOT/'results/huang2024'; out.mkdir(parents=True,exist_ok=True)
    source=json.loads((ROOT/'research/huang2024/source_data.json').read_text())['figure5']['Panel c']
    expected=np.array([[source[3+8*n][7:11],source[6+8*n][7:11]] for n in range(6)])
    experimental=np.array([[source[3+8*n][1:5],source[6+8*n][1:5]] for n in range(6)])
    sem=np.array([[source[4+8*n][1:5],source[7+8*n][1:5]] for n in range(6)])
    start=perf_counter()
    fitted,_=run(load_parameters(),figure5c_protocol())
    samples,_=run(load_parameters(ensemble=True),figure5c_protocol())
    predicted=np.median(samples,axis=0)[:,:,:4]
    error=predicted-expected
    names=['PPL1 gamma1','PPL1 alpha2','PPL1 alpha3','MBON gamma1','MBON alpha2','MBON alpha3']
    times=['Pre','Mid','5 min','1 h']
    rows=[]
    for n,o,t in np.ndindex(expected.shape):
        rows.append(dict(neuron=names[n],odor=['CS+','CS-'][o],time=times[t],
            source_cell=f'{chr(72+t)}{4+8*n+3*o}',published=float(expected[n,o,t]),
            reproduced=float(predicted[n,o,t]),error=float(error[n,o,t]),
            passed=bool(abs(error[n,o,t])<=.05)))
    report=dict(gate='Figure 5c published model medians, 48 cells, tolerance 0.05 Hz',
        passed=all(r['passed'] for r in rows),passed_cells=sum(r['passed'] for r in rows),
        total_cells=len(rows),max_abs_error_Hz=float(abs(error).max()),
        rmse_Hz=float(np.sqrt(np.mean(error**2))),samples=len(samples),
        runtime_sec=perf_counter()-start,refitted=False,rows=rows,
        source_hashes={str(p.relative_to(ROOT)):hashlib.sha256(p.read_bytes()).hexdigest()
            for p in [parameter_file(),ROOT/'research/huang2024/figure5.xlsx',
                      ROOT/'research/huang2024/supplement.pdf',ROOT/'research/huang2024/validation_plan.md']})
    (out/'reproduction_gate.json').write_text(json.dumps(report,indent=2))
    np.savez_compressed(out/'model_outputs.npz',fitted=fitted,samples=samples,
                        expected=expected,experimental=experimental,sem=sem)
    fig,axes=plt.subplots(2,3,figsize=(13,7),layout='constrained')
    for n,ax in enumerate(axes.flat):
        for o,color in enumerate(('#b54a3a','#286991')):
            ax.plot(times,expected[n,o],color=color,marker='o',label=f'Published CS{"+" if o==0 else "-"}')
            ax.plot(times,predicted[n,o],color=color,marker='x',ls='--',label=f'Python CS{"+" if o==0 else "-"}')
        ax.set_title(names[n]); ax.set_ylabel('Evoked rate change (Hz)'); ax.axhline(0,color='.85',lw=.7)
    axes[0,0].legend(fontsize=8)
    fig.suptitle(f'Figure 5c reproduction: {report["passed_cells"]}/48 cells within 0.05 Hz; no refitting')
    fig.savefig(out/'figure5c_comparison.png',dpi=160)
    print(json.dumps({k:v for k,v in report.items() if k not in ('rows','source_hashes')},indent=2))
    return 0 if report['passed'] else 1


if __name__=='__main__': sys.exit(main())

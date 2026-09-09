"""Post-gate provenance diagnostics; do not overwrite the original gate.

Neither the data-derived ceiling nor alternate samples become default settings.
"""
import json
import sys
from pathlib import Path
import numpy as np
ROOT=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT))
import flyplasticity.huang2024 as m

def main():
    expected=np.load(ROOT/'results/huang2024/model_outputs.npz')['expected']
    paths=[m.parameter_file(),m.UPSTREAM/'matlab_code/model_fitting/figures/Dx_steady_state_nonlinear_3_17-Apr-2024_3modules.mat']
    original=m.MAXIMUM.copy()
    rows=[]
    try:
        for path in paths:
            p=m.load_parameters(ensemble=True,path=path)
            for cap in (8.9,8.46):
                m.MAXIMUM[1]=m.BASELINE[4]+cap
                x,_=m.run(p,m.figure5c_protocol())
                error=np.median(x,axis=0)[:,:,:4]-expected
                rows.append(dict(parameter_path=str(path.relative_to(ROOT)),
                    alpha2_evoked_ceiling_Hz=cap,passed_cells=int((abs(error)<=.05).sum()),
                    max_abs_error_Hz=float(abs(error).max()),rmse_Hz=float(np.sqrt(np.mean(error**2)))))
    finally:
        m.MAXIMUM[:]=original
    report=dict(posthoc=True,default_model_changed=False,refitted=False,
        note='Alternate deposited samples and a ceiling inferred from published saturation values. These are diagnostic hypotheses, not independent validation.',cases=rows)
    (ROOT/'results/huang2024/provenance_diagnostics.json').write_text(json.dumps(report,indent=2))
    print(json.dumps(report,indent=2))

if __name__=='__main__': main()

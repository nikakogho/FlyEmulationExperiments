"""Run the authors' flash stimulus and unmodified FRI analysis, default model."""
import os
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1]
os.environ['FLYVIS_ROOT_DIR']=str(ROOT/'data/flyvis')
os.environ['OMP_NUM_THREADS']='2'
import json
import numpy as np
import torch
torch.set_num_threads(2)
import flyvis
from flyvis_windows import install
install()
from flyvis.analysis.stimulus_responses import flash_responses
from flyvis.analysis.flash_responses import flash_response_index

out=ROOT/'results/author_polarity';out.mkdir(exist_ok=False)
view=flyvis.NetworkView(flyvis.results_dir/'flow/0000/000')
data=flash_responses(view,radius=(-1,6),dt=.005,batch_size=1)
np.savez_compressed(out/'flash_responses.npz',responses=data.responses.values,
                    time=data.time.values,cell_type=data.cell_type.values.astype(str),
                    radius=data.radius.values,intensity=data.intensity.values)
rows=[]
for radius in (6,-1):
    # The upstream function can modify its input view; use a deep copy each call.
    fri=flash_response_index(data.copy(deep=True),radius=radius)
    for name in [f'T{f}{s}' for f in (4,5) for s in 'abcd']:
        selected=fri.where(fri.cell_type==name,drop=True)
        value=float(selected.values.squeeze())
        rows.append(dict(cell=name,radius=radius,author_fri=value,
                         expected_sign_pass=bool(value>0 if name.startswith('T4') else value<0)))
    # Independent numerical check of the exact authors' formula and time window.
    mask=(data.time.values>=-.005)&(data.time.values<=1.)
    samples=data.radius.values==radius
    r=data.responses.values[:,samples][:,:,mask,:].copy()
    shifted=r+np.abs(r.min(axis=(1,2)))[:,None,None,:]
    intensity=data.intensity.values[samples]
    on=shifted[:,intensity==1].max(axis=2)
    off=shifted[:,intensity==0].max(axis=2)
    manual=(on-off)/(on+off+1e-16)
    np.testing.assert_allclose(np.sort(manual.flatten()),np.sort(fri.values.flatten()),atol=1e-7)
result=dict(checkpoint='flow/0000/000',whole_brain_simulated=False,
            author_function_used=True,independent_formula_check=True,rows=rows,
            config=data.attrs['config'])
(out/'checks.json').write_text(json.dumps(result,indent=2,default=str))
print(json.dumps(result,indent=2,default=str))

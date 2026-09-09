"""Fixed ten checkpoints printed in the upstream Fig 2d notebook; no selection."""
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

out=ROOT/'results/author_ensemble';out.mkdir(exist_ok=False)
models=['000','001','002','003','004','005','007','009','006','013']
names=[f'T{f}{s}' for f in (4,5) for s in 'abcd']
rows=[]
for model in models:
    view=flyvis.NetworkView(flyvis.results_dir/f'flow/0000/{model}')
    data=flash_responses(view,radius=(-1,6),dt=.005,batch_size=1)
    fri=flash_response_index(data.copy(deep=True),radius=6)
    values={name:float(fri.where(fri.cell_type==name,drop=True).values.squeeze()) for name in names}
    rows.append(dict(model=model,fri=values))
    np.savez_compressed(out/f'{model}_flashes.npz',responses=data.responses.values,
                        time=data.time.values,cell_type=data.cell_type.values.astype(str),
                        radius=data.radius.values,intensity=data.intensity.values)
    (out/'checks.json').write_text(json.dumps(dict(complete=False,models=models,rows=rows),indent=2))
    print(model,values,flush=True)
summary={name:dict(median=float(np.median([r['fri'][name] for r in rows])),
                   expected_sign_count=sum(r['fri'][name]>0 if name.startswith('T4') else r['fri'][name]<0 for r in rows))
         for name in names}
(out/'checks.json').write_text(json.dumps(dict(complete=True,models=models,rows=rows,summary=summary),indent=2))
print(json.dumps(summary,indent=2))

"""Recorded body-eye stream into isolated visual model; no new body/brain run."""
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
from calibrate_flyvis import digest
out=ROOT/'results/retinal_replay';out.mkdir(exist_ok=False)
record=np.load(ROOT/'results/retinal_bridge/recorded_eye_movie.npz')
movie=record['input'].transpose(1,0,2)[:,:,None,:].astype(np.float32)
rows=[]
# Fixed author-listed set; do not pick a passing polarity model.
for model in ['000','001','002','003','004','005','007','009','006','013']:
    net=flyvis.NetworkView(flyvis.results_dir/f'flow/0000/{model}').init_network()
    before=digest(net)
    nodes=net.connectome.nodes
    index=net.connectome.central_cells_index[:]
    with torch.no_grad():
        response=net.simulate(torch.tensor(movie),.005).detach().cpu().numpy()
    assert np.isfinite(response).all()
    assert before==digest(net)
    np.savez_compressed(out/f'{model}.npz',responses=response[:,:,index],
                        cell_type=nodes.type[:][index].astype(str),time=record['time_s'])
    rows.append(dict(model=model,finite=True,parameters_unchanged=True))
    print('Replayed model',model,flush=True)
(out/'checks.json').write_text(json.dumps(dict(passed=True,rows=rows,whole_brain_simulated=False,
    visual_subsystem_simulated=True,body_simulated=False,source_frames=70,integration_frames=movie.shape[1],
    limitation='Transport/stability only. No directional ground truth or learning score.'),indent=2))

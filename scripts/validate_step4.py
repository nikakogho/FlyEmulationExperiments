"""Check anatomical candidates and identifiability of the current visual input.

Static data and pixel arithmetic only. Does not construct a fitted neural route.
"""
import json
import sys
from pathlib import Path
import numpy as np
import pandas as pd
from flygym.vision import Retina
ROOT=Path(__file__).resolve().parents[1];sys.path.insert(0,str(ROOT))
from flyplasticity.retinal_bridge import RetinalBridge
out=ROOT/'results/step4';out.mkdir(exist_ok=True)
retina=Retina()
centers=np.array(json.loads((ROOT/'results/visual_learning_path/flyvis_receptor_centers.json').read_text()))
bridge=RetinalBridge(retina.ommatidia_id_map,centers)
# The light scene defines (.05,1,.05) and (.05,.05,1). Equal mean is exact.
green=np.broadcast_to(np.array([13,255,13]),(2,*retina.ommatidia_id_map.shape,3))
blue=green[...,[0,2,1]]
g=bridge.encode(green);b=bridge.encode(blue)
np.testing.assert_array_equal(g,b)
rgb_difference=float(np.max(np.abs(bridge.encode_rgb(green)-bridge.encode_rgb(blue))))
assert rgb_difference>.9
# Stronger invariant on a recorded scene: arbitrary G/B channel exchange is invisible.
import imageio.v3 as iio
stored=iio.imread(ROOT/'results/light_flat_preflight/preflight_0.0_eyes.png')
eyes=np.stack(np.split(stored,2,axis=1))
np.testing.assert_array_equal(bridge.encode(eyes),bridge.encode(eyes[...,[0,2,1]]))
a=pd.read_csv(ROOT/'data/annotations.tsv',sep='\t',low_memory=False).set_index('root_id')
c=pd.read_parquet(ROOT/'upstream/Drosophila_brain_model/Connectivity_783.parquet')
ids=lambda kind:a.index[a.cell_type==kind]
def edges(pre,post):return c[c.Presynaptic_ID.isin(pre)&c.Postsynaptic_ID.isin(post)].copy()
photo=edges(a.index[a.cell_type.isin(['R7','R8'])],ids('aMe12'))
vpn=edges(ids('aMe12'),ids('KCg-d'))
kcmbon=edges(ids('KCg-d'),ids('MBON01'))
danmbon=edges(ids('PAM01'),ids('MBON01'))
for name,e in [('photoreceptor_to_ame12',photo),('ame12_to_visual_kc',vpn),
               ('visual_kc_to_mbon01',kcmbon),('pam01_to_mbon01',danmbon)]:
    e['pre_type']=e.Presynaptic_ID.map(a.cell_type)
    e['post_type']=e.Postsynaptic_ID.map(a.cell_type)
    e['pre_side']=e.Presynaptic_ID.map(a.side)
    e['post_side']=e.Postsynaptic_ID.map(a.side)
    e.to_csv(out/f'{name}.csv',index=False)
candidate=a.loc[a.index.isin(set(vpn.Presynaptic_ID)|set(kcmbon.Postsynaptic_ID)|set(danmbon.Presynaptic_ID)),
                ['cell_type','hemibrain_type','side','top_nt']]
candidate.to_csv(out/'candidate_cells.csv')
result=dict(step4_passed=False,step5_run=False,neural_or_body_simulation=False,
    diagnostics_passed=True,
    color_distinction_preserved=False,green_blue_max_input_difference=float(np.max(np.abs(g-b))),
    separate_rgb_transport_preserves_color=True,rgb_transport_max_difference=rgb_difference,
    recorded_scene_channel_swap_identical=True,
    photoreceptor_to_ame12_synapses=int(photo.Connectivity.sum()),
    ame12_to_visual_kc_synapses=int(vpn.Connectivity.sum()),
    ame12_connected_visual_kcs=int(vpn.Postsynaptic_ID.nunique()),
    visual_kc_to_mbon01_synapses=int(kcmbon.Connectivity.sum()),
    visual_kc_to_mbon01_edges=len(kcmbon),
    pam01_to_mbon01_synapses=int(danmbon.Connectivity.sum()),
    coarse_gamma5_assignment_supported=True,
    individual_dan_subcompartment_assignment_validated=False,
    sensory_transfer_function_validated=False,
    blockers=['Current grayscale input aliases the actual green/blue task cues.',
              'No validated spectral/receptive-field transfer function for the chosen aMe12 route.',
              'PAM01 group contains finer functional/anatomical subdivisions not assigned here.'])
(out/'checks.json').write_text(json.dumps(result,indent=2));print(json.dumps(result,indent=2))
if not result['step4_passed']:raise SystemExit(1)

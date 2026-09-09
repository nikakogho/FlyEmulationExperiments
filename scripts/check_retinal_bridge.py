"""Validate recorded 3D eye transport against FlyGym's own permutation."""
import ast
import json
import sys
from pathlib import Path
from typing import Optional
import numpy as np
from flygym.vision import Retina
ROOT=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT))
from flyplasticity.retinal_bridge import RetinalBridge,sample_hold
out=ROOT/'results/retinal_bridge';out.mkdir(exist_ok=True)
retina=Retina()
centers=np.array(json.loads((ROOT/'results/visual_learning_path/flyvis_receptor_centers.json').read_text()),dtype=int)
bridge=RetinalBridge(retina.ommatidia_id_map,centers)
# Execute only the inspected upstream mapper class, without importing its neural runtime.
import flygym
source=Path(flygym.__file__).parent/'examples/vision/vision_network.py'
tree=ast.parse(source.read_text())
node=next(n for n in tree.body if isinstance(n,ast.ClassDef) and n.name=='RetinaMapper')
class TensorAdapter:
    def cpu(self):return self
    def numpy(self):return centers
class BoxAdapter:
    def __init__(self,**kwargs):self.receptor_centers=TensorAdapter()
scope=dict(np=np,Optional=Optional,Retina=Retina,BoxEye=BoxAdapter)
exec(compile(ast.Module(body=[node],type_ignores=[]),str(source),'exec'),scope)
official=scope['RetinaMapper']()
marker=np.arange(721)
np.testing.assert_array_equal(bridge.to_target,official.flygym_to_flyvis(marker))
np.testing.assert_array_equal(marker[bridge.to_target][bridge.to_source],marker)
record=np.load(ROOT/'results/standing_v2_seed101/body_sensor_recording.npz')
encoded=np.array([bridge.encode(frame) for frame in record['eye_rgb']])
times=record['vision_time_s']
query=times[0]+np.arange(round((times[-1]-times[0])/.005)+1)*.005
# Round timestamp comparisons to eliminate floating accumulation at exact boundaries.
sampled,actual=sample_hold(encoded,np.round(times,8),np.round(query,8))
np.savez_compressed(out/'recorded_eye_movie.npz',input=sampled,time_s=query,
                    acquisition_time_s=actual,source_input=encoded,source_time_s=times)
mask=retina.ommatidia_id_map
rows,cols=np.indices(mask.shape)
horizontal=np.broadcast_to((cols/cols.max()*255)[None,:,:,None],(2,*mask.shape,3))
vertical=np.broadcast_to((rows/rows.max()*255)[None,:,:,None],(2,*mask.shape,3))
for image,axis in [(horizontal,1),(vertical,0)]:
    values=bridge.encode(image)[0]
    assert np.corrcoef(values,centers[:,axis])[0,1]>.999
dark=np.zeros((2,*mask.shape,3));dark[0]=255
np.testing.assert_allclose(bridge.encode(dark)[0],1)
np.testing.assert_allclose(bridge.encode(dark)[1],0)
checks=dict(passed=True,official_permutation_matches=True,round_trip_exact=True,
            gradient_axes_preserved=True,eyes_independent=True,
            max_mapping_error_pixels=bridge.max_mapping_error_pixels,
            source_frames=len(times),held_integrator_frames=len(query),
            max_age_s=float(np.max(query-actual)),
            limitation='Image-axis convention only; world-bearing and biological spectral calibration remain unvalidated.')
(out/'checks.json').write_text(json.dumps(checks,indent=2));print(json.dumps(checks,indent=2))

"""Small diagnostic profile of the existing CPU simulation and GL renderer."""
import cProfile
import importlib.util
import json
from pathlib import Path
import pstats
import time
import numpy as np
import brian2 as br
from flygym import Fly, Camera
from flygym.examples.locomotion import HybridTurningController
from garden3d import ROOT, make_arena, camera_axes

br.prefs.codegen.target='numpy'
path=ROOT/'upstream/fly-api/experiments/navigation/nav_demo.py'
spec=importlib.util.spec_from_file_location('nav',path)
nav=importlib.util.module_from_spec(spec); spec.loader.exec_module(nav)
nav.ANN=str(ROOT/'data/annotations.tsv')
t=time.perf_counter()
brain=nav.Brain(str(ROOT/'upstream/Drosophila_brain_model'))
result={'brain_build_sec':time.perf_counter()-t}
t=time.perf_counter(); brain.valence(.5,.3)
result['first_sniff_sec']=time.perf_counter()-t
times=[]
for _ in range(3):
    t=time.perf_counter(); brain.valence(.5,.3); times.append(time.perf_counter()-t)
result['warm_sniff_sec']=times
arena=make_arena()
fly=Fly(enable_adhesion=True,spawn_pos=(0,0,.2),contact_sensor_placements=[f'{leg}{seg}'
    for leg in ['LF','LM','LH','RF','RM','RH'] for seg in ['Tibia','Tarsus1','Tarsus2','Tarsus3','Tarsus4','Tarsus5']])
pos=(23.,-29.,28.)
cam=Camera(attachment_point=arena.root_element.worldbody,camera_name='profile_view',
    camera_parameters={'mode':'fixed','pos':pos,'xyaxes':camera_axes(pos,(12,0,0)),'fovy':48},
    play_speed=.5,window_size=(960,720))
sim=HybridTurningController(fly=fly,cameras=[cam],timestep=1e-4,seed=0,arena=arena)
sim.reset(0); sim.render()
from OpenGL import GL
with sim.physics.contexts.gl.make_current() as ctx:
    result['gl_vendor']=ctx.call(GL.glGetString,GL.GL_VENDOR).decode()
    result['gl_renderer']=ctx.call(GL.glGetString,GL.GL_RENDERER).decode()
profile=cProfile.Profile(); profile.enable()
step_time=render_time=0
for _ in range(1500):
    t=time.perf_counter(); sim.step(np.array([1.,1.])); step_time+=time.perf_counter()-t
    t=time.perf_counter(); sim.render(); render_time+=time.perf_counter()-t
profile.disable()
result.update(body_step_sec=step_time,render_sec=render_time,
              note='One 150ms body segment under cProfile, straight walking; not a full-run benchmark')
out=ROOT/'results/performance'; out.mkdir(parents=True,exist_ok=True)
with (out/'cpu_profile.txt').open('w') as stream:
    pstats.Stats(profile,stream=stream).sort_stats('cumtime').print_stats(30)
(out/'runtime.json').write_text(json.dumps(result,indent=2))
sim.close()
print(json.dumps(result,indent=2))

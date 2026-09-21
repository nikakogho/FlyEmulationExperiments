"""Actual eye-camera occlusion counterfactual; zero physics/neural steps."""
import argparse, json
import numpy as np
import mujoco
from dm_control.mujoco.wrapper.core import MjvOption
from sensory_fixture import ROOT, make_fixture


def main():
    ap=argparse.ArgumentParser(); ap.add_argument('--out',required=True); args=ap.parse_args()
    out=ROOT/args.out; out.mkdir(parents=True,exist_ok=False)
    _,fly,sim,_,eye,_,_,_,_=make_fixture()
    p=sim.physics; m=p.model
    target=m.name2id('sensor_calibration_probe','geom'); blocker=m.name2id('sensor_card_uv','geom')
    option=MjvOption();option.geomgroup[:]=0;option.geomgroup[5]=1
    saved={key:getattr(m,key).copy() for key in ('geom_pos','geom_size','geom_quat','geom_rgba','geom_group','geom_sameframe')}
    state_before=p.get_state().copy();time_before=float(p.data.time);rows=[]
    try:
        for side in ('L','R'):
            name=f'{fly.name}/{side}Eye_cam';cam=m.name2id(name,'camera')
            origin=p.data.cam_xpos[cam].copy();rotation=p.data.cam_xmat[cam].reshape(3,3).copy()
            m.geom_pos[target]=origin+rotation@np.array([0,0,-3.])
            m.geom_size[target,0]=.10
            m.geom_pos[blocker]=origin+rotation@np.array([0,0,-1.5])
            m.geom_size[blocker]=[.3,.3,.03]
            quat=np.zeros(4);mujoco.mju_mat2Quat(quat,rotation.ravel());m.geom_quat[blocker]=quat
            # The compiled identity-orientation shortcut otherwise ignores edits.
            m.geom_sameframe[blocker]=0
            m.geom_group[blocker]=5
            def visible(alpha):
                m.geom_rgba[blocker,3]=alpha;p.forward()
                np.testing.assert_allclose(p.data.geom_xmat[blocker].reshape(3,3),rotation,atol=1e-12)
                seg=p.render(height=eye.ommatidia_id_map.shape[0],width=eye.ommatidia_id_map.shape[1],
                             camera_id=name,segmentation=True,scene_option=option)
                return int(np.sum((seg[...,0]==target)&(seg[...,1]==5)))
            before=visible(0);occluded=visible(1);after=visible(0)
            rows.append(dict(eye=side,visible_pixels=before,occluded_pixels=occluded,
                restored_pixels=after,passed=before>0 and occluded==0 and after==before))
    finally:
        for key,value in saved.items():getattr(m,key)[:]=value
        p.forward()
        unchanged=np.array_equal(state_before,p.get_state()) and time_before==float(p.data.time)
        sim.close()
    result=dict(passed=all(r['passed'] for r in rows) and unchanged,eyes=rows,
        physical_state_unchanged=unchanged,new_physics_steps=0,new_neural_steps=0,
        scope='Rendered occlusion, not biological eye validation')
    (out/'checks.json').write_text(json.dumps(result,indent=2));print(json.dumps(result,indent=2))
    raise SystemExit(not result['passed'])


if __name__=='__main__':main()

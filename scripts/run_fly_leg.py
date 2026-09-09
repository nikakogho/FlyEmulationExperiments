"""Mechanical-only foreleg demonstration and verified stop; no fly neurons."""
from pathlib import Path
import sys,json,hashlib
ROOT=Path(__file__).resolve().parents[1];sys.path.insert(0,str(ROOT))
import numpy as np,mujoco,imageio.v2 as imageio
from PIL import Image,ImageDraw
from flyplasticity.fly_leg_rig import FlyLegRig,SOURCE


def main():
    import argparse
    ap=argparse.ArgumentParser(description=__doc__);ap.add_argument('--out',default='results/fly_leg');args=ap.parse_args()
    out=ROOT/args.out;out.mkdir(exist_ok=False)
    rig=FlyLegRig();reference=FlyLegRig()
    (out/'model.xml').write_text(rig.xml)
    try:
        with mujoco.Renderer(rig.model,height=608,width=800) as renderer,imageio.get_writer(out/'foreleg.mp4',fps=25) as writer:
            for i in range(2400):
                cmd=[1,0] if i<700 else ([0,1] if i<1400 else [0,0])
                row=rig.step(cmd);reference.step(cmd)
                if i%40==0:
                    renderer.update_scene(rig.data,camera=rig.camera());im=Image.fromarray(renderer.render());draw=ImageDraw.Draw(im)
                    draw.rectangle((0,0,800,100),fill='#14202a')
                    draw.text((14,10),'ACTUAL FLYGYM FORELEG GEOMETRY | mechanical test, no neurons',fill='white')
                    draw.text((14,32),f't={row["time_s"]:.3f}s | anatomical angle={row["anatomical_angle_deg"]:.2f} degrees',fill='white')
                    phase='Flexion' if i<700 else ('Extension' if i<1400 else 'Passive settling (no spring return)')
                    draw.text((14,54),phase+' | actuation forces are engineering inputs',fill='white')
                    draw.text((14,76),'Guard: '+row['guard_status'],fill='white')
                    writer.append_data(np.asarray(im))
                    if i==680:im.save(out/'preview.png')
            before=(rig.data.time,rig.steps)
            try:rig.step([0,0],fault=True)
            except RuntimeError:pass
            assert before==(rig.data.time,rig.steps)
            draw.rectangle((0,0,800,100),fill='#502020');draw.text((14,20),'STOP - synthetic telemetry fault; no further physics step',fill='white')
            for _ in range(25):writer.append_data(np.asarray(im))
        np.testing.assert_array_equal(rig.data.qpos,reference.data.qpos)
        report=dict(source=str(SOURCE),sha256=hashlib.sha256(SOURCE.read_bytes()).hexdigest(),
                    neural_steps=0,physics_steps=rig.steps,rendering_invariant=True,
                    fault_prevents_next_step=True,final_velocity=float(rig.data.qvel[0]),
                    final_guard=rig.guard.events[-1],muscle_forces_calibrated=False,
                    passive_model='Source damping and zero stiffness, gravity disabled; other joints fixed.')
        (out/'report.json').write_text(json.dumps(report,indent=2));print(json.dumps(report,indent=2))
    finally:
        (out/'telemetry.json').write_text(json.dumps(rig.rows));(out/'guard_events.json').write_text(json.dumps(rig.guard.events))


if __name__=='__main__':main()

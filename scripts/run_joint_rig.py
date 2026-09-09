"""Render a guarded mechanical fixture, no brain instantiated."""
import argparse
import json
from pathlib import Path
import sys
ROOT=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT))
import mujoco
import imageio.v2 as imageio
from PIL import Image, ImageDraw
from flyplasticity.joint_rig import JointRig


def main():
    ap=argparse.ArgumentParser(description=__doc__)
    ap.add_argument('--out',default='results/joint_rig')
    args=ap.parse_args()
    out=ROOT/args.out
    out.mkdir(parents=True,exist_ok=False)
    rig=JointRig()
    reference=JointRig()
    phases=[]
    try:
        with mujoco.Renderer(rig.model,height=600,width=800) as renderer, imageio.get_writer(out/'mechanical_fixture.mp4',fps=25) as writer:
            for i in range(3000):
                cmd=[.8,0] if i<700 else ([0,.8] if i<1400 else [0,0])
                phase='Positive actuator' if i<700 else ('Negative actuator' if i<1400 else 'Passive rest')
                rig.step(cmd); reference.step(cmd)
                if i%40==0:
                    renderer.update_scene(rig.data,camera=rig.camera())
                    im=Image.fromarray(renderer.render())
                    draw=ImageDraw.Draw(im)
                    draw.rectangle((0,0,800,115),fill='#101820')
                    draw.text((15,12),'MECHANICAL FIXTURE - no neurons; not fly-calibrated',fill='white')
                    draw.text((15,34),f'{phase} | t={rig.data.time:.3f}s | angle={rig.data.qpos[0]:.3f} rad',fill='white')
                    draw.text((15,56),f'activation={rig.data.act.round(3)} | torque={rig.data.qfrc_actuator[0]:.6f} Nm',fill='white')
                    draw.text((15,78),'Guard: '+rig.guard.events[-1]['status']+' | neural welfare: not applicable to this fixture',fill='white')
                    import numpy as np
                    writer.append_data(np.asarray(im))
                    if i==680: im.save(out/'preview.png')
            before=(rig.data.time,rig.steps)
            try: rig.step([0,0],fault=True)
            except RuntimeError: pass
            stopped_unchanged=before==(rig.data.time,rig.steps)
            draw.rectangle((0,0,800,115),fill='#502020')
            draw.text((15,12),'STOP - synthetic telemetry fault; physics frozen',fill='white')
            for _ in range(25): writer.append_data(np.asarray(im))
        import numpy as np
        np.testing.assert_array_equal(rig.data.qpos,reference.data.qpos)
        report=dict(neural_model_instantiated=False, simulated_seconds=rig.data.time,
                    steps=rig.steps, rendering_preserves_dynamics=True,
                    injected_fault_stops_before_step=stopped_unchanged,
                    final_guard=rig.guard.events[-1],
                    biological_muscle_calibration=False, suffering_assessed=False)
        (out/'report.json').write_text(json.dumps(report,indent=2))
    finally:
        (out/'telemetry.json').write_text(json.dumps(rig.rows))
        (out/'guard_events.json').write_text(json.dumps(rig.guard.events))
    print(json.dumps(report,indent=2))


if __name__=='__main__': main()

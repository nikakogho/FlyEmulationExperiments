"""Render all six mechanical diagnostic replays; never advance physics."""
from pathlib import Path
import sys,json
import numpy as np,mujoco,imageio.v2 as iio
from PIL import Image,ImageDraw,ImageFont
ROOT=Path(__file__).resolve().parents[1];sys.path.insert(0,str(ROOT/'scripts'))
from view_delivery import load,set_frame


def main():
    out=ROOT/'results/saved_motor_body_v1';panels=[];counts=[]
    font=ImageFont.truetype('C:/Windows/Fonts/arial.ttf',18)
    for cue in ('A','B'):
        for arm in ('paired','unpaired','frozen'):
            p=out/f'{cue}_{arm}';model,data,tape=load(p)
            report=json.loads((p/'report.json').read_text())
            if report['status']!='completed':raise ValueError('Comparison requires complete mechanical tapes')
            camera=mujoco.MjvCamera();camera.azimuth=135;camera.elevation=-30;camera.distance=9
            frames=[]
            with mujoco.Renderer(model,height=280,width=400) as renderer:
                for i,t in enumerate(tape['time_s']):
                    set_frame(model,data,tape,i)
                    if i==0:camera.lookat[:]=data.qpos[:3]+np.array([.75,0,.3])
                    renderer.update_scene(data,camera=camera)
                    im=Image.fromarray(renderer.render());d=ImageDraw.Draw(im)
                    d.rectangle((0,0,400,54),fill='#182630')
                    d.text((10,5),f'Odor {cue} | {arm}',font=font,fill='white')
                    d.text((10,29),f'Probe speed {report["mean_probe_speed_mm_s"]:.2f} mm/s',font=font,fill='#f9cd82')
                    frames.append(np.asarray(im))
            panels.append(frames);counts.append(len(frames))
            print('Rendered',cue,arm,flush=True)
    if len(set(counts))!=1:raise ValueError('Unequal comparison tapes')
    with iio.get_writer(out/'comparison.mp4',fps=25) as writer:
        for i in range(counts[0]):
            frame=Image.new('RGB',(1200,640),'#101b24');d=ImageDraw.Draw(frame)
            d.text((16,8),'ARCHIVED NEURAL OUTPUTS -> 3D MECHANICS | no live brain or sensory feedback',font=font,fill='white')
            d.text((16,35),f'{i*.005:.3f} s | '+('250ms recorded odor-probe commands' if i<50 else 'zero-command rest')+' | playback 0.125x',font=font,fill='#f9cd82')
            for j,panel in enumerate(panels):frame.paste(Image.fromarray(panel[i]),((j%3)*400,80+(j//3)*280))
            writer.append_data(np.asarray(frame))
            if i==45:frame.save(out/'comparison.png')
    with iio.get_reader(out/'comparison.mp4') as reader:decoded=sum(1 for _ in reader)
    if decoded!=counts[0]:raise ValueError('Decoded frame count mismatch')
    (out/'video_checks.json').write_text(json.dumps(dict(decoded_frames=decoded,panels=6,
        width=1200,height=640,fps=25,new_neural_steps=0,new_physics_steps=0),indent=2))
    print('Decoded',decoded,'comparison frames')

if __name__=='__main__':main()

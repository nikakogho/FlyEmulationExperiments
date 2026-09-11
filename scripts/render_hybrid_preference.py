"""Comparison of recorded live probes; missing controls remain visibly missing."""
from pathlib import Path
import sys,json
import numpy as np,mujoco,imageio.v2 as iio
from PIL import Image,ImageDraw,ImageFont
ROOT=Path(__file__).resolve().parents[1];sys.path.insert(0,str(ROOT/'scripts'))
from view_delivery import load,set_frame


def main():
    out=ROOT/'results/hybrid_preference_v1';summary=json.loads((out/'assessment.json').read_text())
    font=ImageFont.truetype('C:/Windows/Fonts/arial.ttf',18);total_frames=0
    with iio.get_writer(out/'comparison.mp4',fps=25) as writer:
        for case in summary['cases']:
            p=out/f"seed{case['seed']}_{case['reinforced']}";panels={};duration=0
            for label,report in case['probes'].items():
                model,data,tape=load(p/label);camera=mujoco.MjvCamera()
                camera.azimuth=90;camera.elevation=-60;camera.distance=16;camera.lookat[:]=[5,0,1]
                frames=[];times=[]
                with mujoco.Renderer(model,height=320,width=600) as renderer:
                    for i in range(0,len(tape['time_s']),4):
                        set_frame(model,data,tape,i);renderer.update_scene(data,camera=camera)
                        im=Image.fromarray(renderer.render());d=ImageDraw.Draw(im)
                        d.rectangle((0,0,600,56),fill='#182630')
                        name='BEFORE TRAINING' if label=='pre' else label.upper()+' AFTER TRAINING'
                        d.text((10,5),name+' | '+report['status'],font=font,fill='white')
                        d.text((10,30),f'Recorded {float(tape["time_s"][i]):.2f}s | '+('odor on' if .25<=tape['time_s'][i]<2.25 else 'odor off / rest'),font=font,fill='#f9cd82')
                        frames.append(np.asarray(im));times.append(float(tape['time_s'][i]))
                panels[label]=(frames,times);duration=max(duration,len(frames));print('Rendered',p.name,label,flush=True)
            for i in range(duration):
                image=Image.new('RGB',(1200,736),'#101b24');d=ImageDraw.Draw(image)
                d.text((16,10),'LIVE RECORDED MEMORY + ENGINEERED NAVIGATION | no reinforcement during probes',font=font,fill='white')
                d.text((16,40),f'Seed {case["seed"]} | reinforced odor {case["reinforced"]} | blue A, orange B | playback 0.5x',font=font,fill='#f9cd82')
                for j,label in enumerate(('pre','paired','unpaired','frozen')):
                    x,y=(j%2)*600,96+(j//2)*320
                    if label in panels:
                        frames,times=panels[label];image.paste(Image.fromarray(frames[min(i,len(frames)-1)]),(x,y))
                    else:d.text((x+20,y+50),label.upper()+': NOT RUN',font=font,fill='white')
                writer.append_data(np.asarray(image));total_frames+=1
                if i==min(60,duration-1):image.save(p/'comparison.png')
    with iio.get_reader(out/'comparison.mp4') as reader:decoded=sum(1 for _ in reader)
    if decoded!=total_frames:raise ValueError('Video decode mismatch')
    (out/'video_checks.json').write_text(json.dumps(dict(decoded_frames=decoded,fps=25,
        new_neural_steps=0,new_physics_steps=0,rendered_from_saved_state=True),indent=2))
    print('Decoded',decoded,'comparison frames')

if __name__=='__main__':main()

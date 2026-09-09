"""Interactive recorded 3D scene. Orbit/zoom freely; no physics/neural advancement."""
from pathlib import Path
import argparse,time,threading,json
import numpy as np,mujoco


def load(path):
    path=Path(path)
    model=mujoco.MjModel.from_binary_path(str(path/'scene.mjb'))
    tape=np.load(path/'replay.npz');data=mujoco.MjData(model)
    if tape['qpos'].shape[1]!=model.nq:raise ValueError('Replay/model mismatch')
    return model,data,tape


def set_frame(model,data,tape,i):
    data.qpos[:]=tape['qpos'][i];data.qvel[:]=tape['qvel'][i];data.act[:]=tape['act'][i];data.time=tape['time_s'][i]
    mujoco.mj_forward(model,data)


def main():
    ap=argparse.ArgumentParser(description=__doc__)
    ap.add_argument('--path',default='results/delivery_arena');ap.add_argument('--video',action='store_true');ap.add_argument('--smoke',action='store_true');ap.add_argument('--ui-smoke',action='store_true');args=ap.parse_args()
    model,data,tape=load(args.path)
    camera=mujoco.MjvCamera();camera.azimuth=135;camera.elevation=-30;camera.distance=7
    set_frame(model,data,tape,0)
    if args.smoke:
        for i in range(len(tape['time_s'])):set_frame(model,data,tape,i)
        print('Replay restored every frame without mj_step');return
    if args.video:
        import imageio.v2 as iio
        from PIL import Image,ImageDraw,ImageFont
        font=ImageFont.truetype('C:/Windows/Fonts/arial.ttf',20)
        model.vis.global_.offwidth=960;model.vis.global_.offheight=608
        with mujoco.Renderer(model,height=608,width=960) as renderer,iio.get_writer(Path(args.path)/'fly_in_3d.mp4',fps=25) as writer:
            for i in range(len(tape['time_s'])):
                set_frame(model,data,tape,i)
                camera.lookat[:]=data.qpos[:3];renderer.update_scene(data,camera=camera)
                frame=Image.fromarray(renderer.render());draw=ImageDraw.Draw(frame)
                draw.rectangle((0,0,960,92),fill='#14202a')
                draw.text((18,10),'3D FLY | mechanical walking, turning and rest',font=font,fill='white')
                draw.text((18,38),f'Recorded time {data.time:.2f}s | playback 0.25x | no neural simulation',font=font,fill='white')
                draw.text((18,64),'Learning not demonstrated; camera follows position for viewing only',font=font,fill='#f9cd82')
                writer.append_data(np.asarray(frame))
                if i==120:frame.save(Path(args.path)/'preview.png')
        cap=iio.get_reader(Path(args.path)/'fly_in_3d.mp4');count=sum(1 for _ in cap);cap.close()
        assert count==len(tape['time_s'])
        (Path(args.path)/'video_checks.json').write_text(json.dumps(dict(decoded_frames=count,fps=25,playback_speed=.25,rendered_from_replay=True,new_physics_steps=0,new_neural_steps=0),indent=2))
        print('Rendered and decoded',count,'frames');return
    from mujoco import viewer as mjviewer
    state={'playing':False,'frame':0};lock=threading.Lock()
    def key(code):
        with lock:
            if code==32:state['playing']=not state['playing']
            elif code==262:state['frame']=min(len(tape['time_s'])-1,state['frame']+1)
            elif code==263:state['frame']=max(0,state['frame']-1)
            elif code in (82,114):state.update(frame=0,playing=False)
    print('RECORDED MECHANICAL SCENE. Space: play/pause; arrows: frame; R: rewind. Mouse: orbit/zoom. No learning or neural execution.')
    with mjviewer.launch_passive(model,data,key_callback=key) as viewer:
        viewer.cam.azimuth=135;viewer.cam.elevation=-30;viewer.cam.distance=7
        start=time.monotonic()
        while viewer.is_running():
            if args.ui_smoke and time.monotonic()-start>3:
                viewer.close();break
            with lock,viewer.lock():
                i=state['frame'];set_frame(model,data,tape,i)
                if state['playing']:
                    state['frame']=min(len(tape['time_s'])-1,i+1)
                    if state['frame']==len(tape['time_s'])-1:state['playing']=False
            viewer.cam.lookat[:]=data.qpos[:3];viewer.sync();time.sleep(.04)


if __name__=='__main__':main()

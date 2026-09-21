"""Synchronized saved-body, spectral-receptor and trace video. No model stepping."""
from pathlib import Path
import argparse, json, sys
import numpy as np
import mujoco, imageio.v2 as iio
from PIL import Image, ImageDraw, ImageFont
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
ROOT=Path(__file__).resolve().parents[1]; sys.path.insert(0, str(ROOT/'scripts'))
from view_delivery import load, set_frame


def main():
    ap=argparse.ArgumentParser(); ap.add_argument('--path', required=True); args=ap.parse_args()
    out=ROOT/args.path
    report=json.loads((out/'report.json').read_text()); audit=json.loads((out/'audit.json').read_text())
    model,data,tape=load(out)
    with np.load(out/'sensors.npz') as archive: a={k:archive[k] for k in archive.files}
    t=a['time_s']; n=len(t)
    font=ImageFont.truetype('C:/Windows/Fonts/arial.ttf',19)
    small=ImageFont.truetype('C:/Windows/Fonts/arial.ttf',16)
    title=ImageFont.truetype('C:/Windows/Fonts/arialbd.ttf',25)
    cmap=plt.get_cmap('viridis')
    centers=a['retinal_centers_rc']; low=centers.min(axis=0); span=np.ptp(centers,axis=0)
    # Exactly the saved ommatidial samples, no fabricated high-resolution image.
    pixels=(centers-low)/span*np.array([125.,175.])+np.array([28.,12.])
    limits=np.max(a['eye_excitation'],axis=(0,1,2))
    limits=np.maximum(limits,1e-12)  # fixed over movie, not adaptive display normalization
    fig,axs=plt.subplots(3,1,figsize=(12.8,3.6),dpi=100,sharex=True)
    fig.patch.set_facecolor('#12212b')
    leg_indices=[i for i,name in enumerate(report['joint_names']) if 'Coxa' in name and 'roll' not in name and 'yaw' not in name]
    if len(leg_indices)>6:leg_indices=leg_indices[:6]
    for i in leg_indices: axs[0].plot(t,a['joint_angles_rad'][:,i],lw=1,label=report['joint_names'][i].replace('joint_',''))
    forces=np.linalg.norm(a['contact_vectors_native'],axis=-1).reshape(n,6,6).sum(axis=2)
    for i,leg in enumerate(('LF','LM','LH','RF','RM','RH')):axs[1].plot(t,forces[:,i],lw=1,label=leg)
    for i,label in enumerate(('L palp','R palp','L antenna','R antenna')):axs[2].plot(t,a['odor_concentration'][:,0,i],lw=1.4,label=label)
    for ax,label in zip(axs,('Joint angle\n(rad)','Contact load\n(native units)','Tracer\nconcentration')):
        ax.set_facecolor('#12212b');ax.set_ylabel(label,color='white',fontsize=9)
        ax.tick_params(colors='#b9c8cc',labelsize=8);ax.grid(alpha=.15);ax.set_xlim(0,3)
        for spine in ax.spines.values():spine.set_color('#53626b')
        ax.axvspan(0,.3,color='white',alpha=.035);ax.axvspan(2.1,3,color='white',alpha=.035)
        ax.legend(loc='upper right',ncol=6,fontsize=7,framealpha=.85)
    axs[-1].set_xlabel('Recorded simulation time (s)',color='white',fontsize=9)
    fig.subplots_adjust(left=.115,right=.985,top=.97,bottom=.12,hspace=.22)
    fig.canvas.draw(); traces=Image.fromarray(np.asarray(fig.canvas.buffer_rgba())[:,:,:3].copy())
    plot_boxes=[ax.get_window_extent().bounds for ax in axs];plt.close(fig)
    traces.save(out/'traces.png')
    camera=mujoco.MjvCamera();camera.azimuth=115;camera.elevation=-40;camera.distance=15
    model.vis.global_.offwidth=640;model.vis.global_.offheight=360
    with mujoco.Renderer(model,height=360,width=640) as renderer, iio.get_writer(out/'sensory_walk.mp4',fps=25) as writer:
        for i in range(n):
            image=Image.new('RGB',(1280,944),'#12212b'); draw=ImageDraw.Draw(image)
            draw.text((20,15),'A WALK THROUGH THE SENSORY APPARATUS',font=title,fill='white')
            phase='REST' if t[i]<.3 or t[i]>=2.1 else 'TURN' if 1.1<=t[i]<1.6 else 'WALK'
            draw.text((20,52),f'{t[i]:.2f} s | {phase} | mechanical replay, no brain | all sensors 100 Hz | playback 0.25x',font=font,fill='#f7cd88')
            set_frame(model,data,tape,i);camera.lookat[:]=data.qpos[:3]+np.array([2,0,0])
            renderer.update_scene(data,camera=camera); image.paste(Image.fromarray(renderer.render()),(0,98))
            draw.text((18,100),'External camera (human RGB display)',font=small,fill='white')
            for eye in range(2):
                for channel,label in enumerate(('Outer / Rh1','R7 / UV','R8 / blue-green')):
                    x,y=650+channel*207,95+eye*180
                    draw.text((x+6,y+2),('LEFT ' if eye==0 else 'RIGHT ')+label,font=small,fill='white')
                    colors=(cmap(np.clip(a['eye_excitation'][i,eye,:,channel]/limits[channel],0,1))[:,:3]*255).astype(np.uint8)
                    for rc,color in zip(pixels,colors):
                        py,px=rc;draw.ellipse((x+px-2.1,y+py-2.1,x+px+2.1,y+py+2.1),fill=tuple(color))
            draw.text((20,470),'721 samples per eye | spectral excitation heatmaps; human colors do not drive these sensors',font=font,fill='white')
            draw.text((20,500),'Steady input continues during rest. Synthetic odor; contact loads are not sensory-neuron firing.',font=small,fill='#b9c8cc')
            draw.text((20,525),'Fixed heatmap ranges (relative units): '+ ' | '.join(f'{name}: 0-{limit:.3f}' for name,limit in zip(('Rh1','R7','R8'),limits)),font=small,fill='#b9c8cc')
            image.paste(traces,(0,548));draw=ImageDraw.Draw(image)
            for left,bottom,width,height in plot_boxes:
                x=left+t[i]/3*width;top=548+360-bottom-height
                draw.line((x,top,x,top+height),fill='#f7cd88',width=2)
            draw.text((20,920),'Consistency checks: '+('PASS' if audit['passed'] else 'FAIL')+' | no learning, physiological-fidelity or welfare claim',font=small,fill='#f7cd88')
            writer.append_data(np.asarray(image))
            if i in (0,130,n-1):image.save(out/f'preview_{i}.png')
            if i%100==0:print(f'Rendered {i}/{n}',flush=True)
    with iio.get_reader(out/'sensory_walk.mp4') as reader: decoded=sum(1 for _ in reader)
    if decoded!=n:raise ValueError('Video frame mismatch')
    (out/'video_checks.json').write_text(json.dumps(dict(decoded_frames=decoded,fps=25,
        duration_s=decoded/25,playback_speed=.25,new_neural_steps=0,new_physics_steps=0,
        limits_per_channel=limits.tolist(),eye_display='false-color receptor samples; not reconstructed RGB'),indent=2))
    print('Decoded all',decoded,'frames')


if __name__=='__main__':main()

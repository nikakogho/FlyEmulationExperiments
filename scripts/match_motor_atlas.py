"""Offline matching of the exact public mesh to five published atlas panels.

Scores are image distances, not probabilities or independent physiological tests.
"""
from pathlib import Path
import sys, json, hashlib
ROOT=Path(__file__).resolve().parents[1];sys.path.insert(0,str(ROOT))
import numpy as np
from PIL import Image
from scipy.ndimage import distance_transform_edt
from scipy.optimize import differential_evolution


def mesh_xy(raw):
    if len(raw)<4: raise ValueError('Missing mesh header')
    n=int(np.frombuffer(raw[:4],dtype='<u4')[0])
    if not n or len(raw)<4+n*12: raise ValueError('Truncated mesh vertices')
    v=np.frombuffer(raw,dtype='<f4',count=n*3,offset=4).reshape(-1,3)[:,:2].astype(float)/1000
    if not np.isfinite(v).all(): raise ValueError('Nonfinite mesh')
    return v-v.min(axis=0)


def image_distance(points, transform, distance):
    xy=np.rint(points*transform[0]+transform[1:]).astype(int)
    h,w=distance.shape
    valid=(xy[:,0]>=0)&(xy[:,0]<w)&(xy[:,1]>=0)&(xy[:,1]<h)
    values=np.full(len(points),30.)
    q=xy[valid];values[valid]=distance[q[:,1],q[:,0]]
    return float(np.mean(np.minimum(values,30)))


def main():
    import argparse
    ap=argparse.ArgumentParser(description=__doc__);ap.add_argument('--out',default='results/motor_atlas_match');args=ap.parse_args()
    cache=ROOT/'data/motor_physiology';out=ROOT/args.out;out.mkdir(exist_ok=False)
    mesh=cache/'cell160_mesh.bin';atlas=cache/'atlas_A12.png'
    raw=mesh.read_bytes();v=mesh_xy(raw)
    points=np.unique(np.round(v*3).astype(int),axis=0)/3
    rng=np.random.default_rng(123);points=points[rng.choice(len(points),min(6000,len(points)),replace=False)]
    train=points[points[:,1]<65];held=points[points[:,1]>=65]
    image=Image.open(atlas).convert('L')
    if image.size!=(1546,2000): raise ValueError('Unexpected atlas raster size')
    rows=[];overlays=[]
    # Panel grays intentionally vary in the atlas. Thresholds follow those shades;
    # all are perturbed equally by +/-10 and results are retained, not optimized.
    panels=[(41,155,185),(42,455,160),(43,754,135),(44,1040,110),(45,1343,80)]
    for shift in (-10,0,10):
        for number,top,threshold in panels:
            crop=np.asarray(image.crop((110,top,400,top+310)))
            mask=crop<threshold+shift
            mask[:45,:48]=False;mask[260:,:]=False;mask[:,255:]=False
            distance=distance_transform_edt(~mask)[:260]
            fit=differential_evolution(lambda z:image_distance(train,z,distance),
                                      [(1.65,2.05),(0,35),(0,45)],seed=0,
                                      popsize=8,maxiter=60,polish=False)
            rows.append(dict(atlas_number=number,threshold_shift=shift,
                             train_distance_px=float(fit.fun),
                             heldout_distance_px=image_distance(held,fit.x,distance),
                             transform=fit.x.tolist()))
            if shift==0: overlays.append((number,crop,fit.x))
    winners=[min([r for r in rows if r['threshold_shift']==s],key=lambda r:r['heldout_distance_px'])['atlas_number'] for s in (-10,0,10)]
    report=dict(root_id='648518346496932836',public_cell_id='160',
                method='same-reconstruction image match to atlas, not new genetic validation',
                winners=winners,all_thresholds_choose_44=winners==[44,44,44],
                identity_status='image_verified_atlas_correspondence' if winners==[44,44,44] else 'unresolved',
                atlas_number=44 if winners==[44,44,44] else None,driver='R22A08-Gal4',
                physiological_class='intermediate',
                spatial_holdout='Fit y<65 um, score y>=65 um; not independent animals',
                scores=rows,neural_steps=0,
                mesh_sha256=hashlib.sha256(raw).hexdigest(),
                atlas_raster_sha256=hashlib.sha256(atlas.read_bytes()).hexdigest(),
                atlas_pdf_sha256=hashlib.sha256((ROOT/'data/motor_targets/azevedo24_appendix.pdf').read_bytes()).hexdigest(),
                mesh_url='https://storage.googleapis.com/lee-lab_female-adult-nerve-cord/meshes/FANC/FANC_neurons/meshes/648518346496932836:0:1',
                atlas_pdf='https://faculty.washington.edu/tuthill/docs/azevedo24_appendix.pdf',
                render_command='pdftoppm -f 32 -singlefile -scale-to 2000 -png azevedo24_appendix.pdf atlas_A12',
                limitations=['Fixed XY projection and manually delimited panels',
                             'Foreground thresholds depend on atlas neuron shades',
                             'Image correspondence inherits authors EM-to-driver assignment',
                             'No cell-specific dynamics or welfare conclusion follows'])
    (out/'report.json').write_text(json.dumps(report,indent=2))
    import matplotlib;matplotlib.use('Agg')
    import matplotlib.pyplot as plt
    fig,axes=plt.subplots(1,5,figsize=(15,4))
    for ax,(number,crop,z) in zip(axes,overlays):
        ax.imshow(crop,cmap='gray',vmin=0,vmax=255)
        xy=held*z[0]+z[1:];ax.scatter(xy[:,0],xy[:,1],s=.2,c='#e63d55',alpha=.5)
        score=next(r['heldout_distance_px'] for r in rows if r['atlas_number']==number and r['threshold_shift']==0)
        ax.set_title(f'MN {number}: {score:.2f} px');ax.set_xlim(0,290);ax.set_ylim(310,0);ax.axis('off')
    fig.suptitle('Exact cell 160 mesh: red held-out branches over atlas panels (lower distance is better)')
    fig.tight_layout();fig.savefig(out/'comparison.png',dpi=160);plt.close(fig)
    print(json.dumps(dict(winners=winners,central_scores={r['atlas_number']:r['heldout_distance_px'] for r in rows if r['threshold_shift']==0}),indent=2))


if __name__=='__main__':main()

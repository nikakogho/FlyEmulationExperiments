"""Position-tuning fit in measured calcium units; never converts calcium to spikes."""
from pathlib import Path
import sys,json,zipfile,pickle,io,hashlib
ROOT=Path(__file__).resolve().parents[1];sys.path.insert(0,str(ROOT))
import numpy as np
from scipy.optimize import least_squares
from scipy.special import expit


class ArrayOnlyUnpickler(pickle.Unpickler):
    def find_class(self,module,name):
        from numpy._core.multiarray import _reconstruct
        allowed={('numpy.core.multiarray','_reconstruct'):_reconstruct,
                 ('numpy','ndarray'):np.ndarray,('numpy','dtype'):np.dtype}
        if (module,name) not in allowed:raise ValueError('Unsupported serialized type')
        return allowed[module,name]


def main():
    import argparse
    ap=argparse.ArgumentParser();ap.add_argument('--out',default='results/claw_calcium');args=ap.parse_args()
    out=ROOT/args.out;out.mkdir(exist_ok=False)
    path=ROOT/'data/proprioceptor/2023_Mamiya_etal_Proprioceptor_feature_selectivity.zip'
    digest=hashlib.sha256(path.read_bytes()).hexdigest()
    if digest!='866e8487b51b8e2cbc1c9ec7d875a33f918249d14c76c115e37601b05cf59862':raise ValueError('Source mismatch')
    with zipfile.ZipFile(path) as archive:
        member=next(n for n in archive.namelist() if 'JR688' in n and n.endswith('type2'))
        x,y,raw,norm,angle,flyid,time=ArrayOnlyUnpickler(io.BytesIO(archive.read(member))).load()
    flies=np.asarray(flyid).ravel();train=flies<6;test=flies==6
    def collect(mask):
        a=np.asarray(angle[:,mask]).ravel();v=np.asarray(norm[:,mask]).ravel();valid=np.isfinite(a)&np.isfinite(v)
        return a[valid],v[valid]
    a,v=collect(train);ta,tv=collect(test)
    def predict(a,z):return z[0]+z[1]*expit((a-z[2])/z[3])
    fit=least_squares(lambda z:predict(a,z)-v,[0,1,110,20],bounds=([-1,0,0,1],[1,3,180,90]))
    if not fit.success:raise ValueError('Calcium fit failed')
    mse=float(np.mean((predict(ta,fit.x)-tv)**2));baseline=float(np.mean((v.mean()-tv)**2))
    report=dict(neural_steps=0,source_sha256=digest,download_url='https://datadryad.org/downloads/file_stream/2453318',
                archive_member=member,train_fly_ids=[1,2,3,4,5],evaluation_fly_ids=[6],
                train_cells=int(sum(train)),evaluation_cells=int(sum(test)),parameters=fit.x.tolist(),
                parameter_names=['offset','amplitude','midpoint_degrees','slope_degrees'],
                evaluation_normalized_calcium_rmse=float(np.sqrt(mse)),training_mean_baseline_rmse=float(np.sqrt(baseline)),
                evaluation_mse_reduction_fraction=1-mse/baseline,validation_pass=bool(mse<baseline),
                measured_units='author normalized DR/R calcium fluorescence',spike_conversion_validated=False,
                exact_FANC_cell_mapping_validated=False,
                limitations=['Position-only population fit omits hysteresis, adaptation and reporter kinetics.',
                             'One held-out animal; no claim of population validation or spike-rate prediction.',
                             'Author normalized fluorescence may use full within-cell recordings; fit predicts normalized tuning only.',
                             'No correspondence identifies the five selected FANC cells in these recordings.'])
    (out/'report.json').write_text(json.dumps(report,indent=2));print(json.dumps(report,indent=2))
    import matplotlib;matplotlib.use('Agg')
    import matplotlib.pyplot as plt
    fig,ax=plt.subplots(figsize=(7,4));ax.scatter(ta,tv,s=1,alpha=.08,label='Held-out fly 6')
    line=np.linspace(0,180,200);ax.plot(line,predict(line,fit.x),'k',label='Fit to flies 1-5')
    ax.set(xlabel='Tibia angle (degrees)',ylabel='Normalized calcium DR/R',title='Claw extension: population position tuning, not spike rates')
    ax.legend();fig.tight_layout();fig.savefig(out/'fit.png',dpi=150);plt.close(fig)
    if not report['validation_pass']:raise SystemExit(1)


if __name__=='__main__':main()

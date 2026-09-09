"""Offline fixed-checkpoint motion calibration. No body, reward or whole brain."""
import os
from pathlib import Path
ROOT = Path(__file__).resolve().parents[1]
os.environ['FLYVIS_ROOT_DIR'] = str(ROOT/'data/flyvis')
os.environ.setdefault('NUMBA_NUM_THREADS', '2')
os.environ.setdefault('OMP_NUM_THREADS', '2')
import argparse
import hashlib
import json
import time
import numpy as np
import torch
torch.set_num_threads(2)
import flyvis
from flyvis_windows import install
install()
from flyvis.datasets.moving_bar import MovingEdge


def digest(network):
    h = hashlib.sha256()
    for key, value in sorted(network.state_dict().items()):
        h.update(key.encode())
        h.update(value.detach().cpu().numpy().tobytes())
    return h.hexdigest()


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('--dt', type=float, default=.005)
    parser.add_argument('--out', required=True)
    args = parser.parse_args()
    out = ROOT/args.out
    out.mkdir(parents=True, exist_ok=False)
    start = time.perf_counter()
    network = flyvis.NetworkView(flyvis.results_dir/'flow/0000/000').init_network()
    before = digest(network)
    nodes = network.connectome.nodes
    types = nodes.type[:].astype(str)
    central = (nodes.u[:] == 0) & (nodes.v[:] == 0)
    names = [f'T{family}{subtype}' for family in (4,5) for subtype in 'abcd']
    indices = [int(np.flatnonzero(central & (types == name)).item()) for name in names]
    dataset = MovingEdge(offsets=[-10,11], intensities=[0,1], speeds=[19], height=80,
                         post_pad_mode='continue', t_pre=1., t_post=1., dt=args.dt,
                         angles=[0,90,180,270])
    metadata = dataset.arg_df.to_dict(orient='records')
    traces = []
    all_finite = True
    for i, meta in enumerate(metadata):
        movie = dataset[i].reshape(1,-1,1,721)
        with torch.no_grad():
            response = network.simulate(movie, args.dt).detach().cpu().numpy()[0]
        all_finite = all_finite and bool(np.isfinite(response).all())
        traces.append(response[:,indices])
        print('Completed edge', meta, flush=True)
    traces = np.array(traces)
    gray = torch.full((1,int(2/args.dt),1,721), .5)
    with torch.no_grad():
        control = network.simulate(gray,args.dt).detach().cpu().numpy()[0]
    all_finite = all_finite and bool(np.isfinite(control).all())
    control = control[:,indices]
    pre = int(1/args.dt)
    baseline = traces[:,pre-20:pre,:].mean(axis=1)
    peaks = np.maximum(0, (traces[:,pre:,:]-baseline[:,None,:]).max(axis=1))
    metrics = []
    for k, name in enumerate(names):
        angle = dict(a=180,b=0,c=90,d=270)[name[-1]]
        polarity = int(name.startswith('T4'))
        pick = lambda a,p: next(i for i,m in enumerate(metadata)
                                if m['angle']==a and m['intensity']==p)
        preferred = float(peaks[pick(angle,polarity),k])
        null = float(peaks[pick((angle+180)%360,polarity),k])
        index = (preferred-null)/(preferred+null) if preferred+null>0 else 0.
        expected = max(float(peaks[pick(a,polarity),k]) for a in (0,90,180,270))
        other = max(float(peaks[pick(a,1-polarity),k]) for a in (0,90,180,270))
        metrics.append(dict(cell=name,preferred_angle=angle,preferred_peak=preferred,
                            null_peak=null,direction_index=index,expected_polarity_peak=expected,
                            other_polarity_peak=other,direction_pass=bool(index>=.2 and preferred>null),
                            polarity_pass=bool(expected>other)))
    gray_drift = float(np.max(np.abs(control[pre:]-control[pre])))
    unchanged = before == digest(network)
    passed = bool(all_finite and unchanged and gray_drift<.001 and
                  all(m['direction_pass'] and m['polarity_pass'] for m in metrics))
    np.savez_compressed(out/'responses.npz',traces=traces,gray=control,peaks=peaks,
                        names=np.array(names),dt=args.dt)
    result = dict(passed=passed,whole_brain_simulated=False,visual_subsystem_simulated=True,
                  dt=args.dt,checkpoint='flow/0000/000',nodes=len(types),device=str(flyvis.device),
                  finite=all_finite,parameters_unchanged=unchanged,parameter_sha256=before,
                  gray_drift=gray_drift,metrics=metrics,stimuli=metadata,
                  elapsed_s=time.perf_counter()-start,
                  protocol_sha256=hashlib.sha256((ROOT/'research/vision_calibration_protocol.md').read_bytes()).hexdigest())
    (out/'checks.json').write_text(json.dumps(result,indent=2))
    print(json.dumps(result,indent=2))
    if not passed: raise SystemExit(1)


if __name__ == '__main__': main()

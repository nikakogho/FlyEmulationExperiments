"""Fit force through measured probe dynamics and verify MuJoCo against the ODE."""
from pathlib import Path
import sys, json, hashlib
ROOT=Path(__file__).resolve().parents[1];sys.path.insert(0,str(ROOT))
import numpy as np, mujoco
from flyplasticity.loaded_probe import response, fit_force, mujoco_probe
from flyplasticity.figure_twitch import twitch


def main():
    import argparse
    ap=argparse.ArgumentParser();ap.add_argument('--out',default='results/probe_physics');args=ap.parse_args()
    out=ROOT/args.out;out.mkdir(exist_ok=False)
    source=ROOT/'results/raw_motor_calibration/report.json'
    recording=json.loads(source.read_text())['cells']['180222_F1_C1']['single_spike_probe']
    train=[(np.array(r['time_ms']),np.array(r['displacement_um'])) for r in recording['traces'] if r['trial'] in recording['train_trials']]
    test=[(np.array(r['time_ms']),np.array(r['displacement_um'])) for r in recording['traces'] if r['trial'] in recording['evaluation_trials']]
    parameters=fit_force(train)
    model,data,xml=mujoco_probe();times=[];positions=[]
    for _ in range(10000):
        # uN -> native mg*mm/s^2 = 1000; qpos mm -> um = 1000.
        data.ctrl[0]=float(twitch(data.time*1000,*parameters))*1000
        mujoco.mj_step(model,data);times.append(data.time*1000);positions.append(data.qpos[0]*1000)
    expected=response(times,parameters)
    error=float(np.max(np.abs(expected-positions)))
    rmse=float(np.sqrt(np.mean([np.mean((response(t,parameters)-y)**2) for t,y in test])))
    report=dict(neural_steps=0,force_peak_un=parameters[0],force_tau_ms=parameters[1],force_delay_ms=parameters[2],
                evaluation_displacement_rmse_um=rmse,mujoco_vs_exact_ode_max_error_um=error,
                numerical_equivalence_pass=error<.05,source_sha256=hashlib.sha256(source.read_bytes()).hexdigest(),
                mass_kg=.17e-6,damping_kg_s=.14e-3,stiffness_n_m=.2234,
                limb_contact_lever_arm=None,full_leg_calibrated=False,
                limitation='Probe load is measured; experimental limb contact location/lever arm remains unmeasured. No angle or muscle calibration claim.')
    (out/'report.json').write_text(json.dumps(report,indent=2));(out/'model.xml').write_text(xml)
    np.savez_compressed(out/'trajectory.npz',time_ms=times,displacement_um=positions)
    import matplotlib;matplotlib.use('Agg')
    import matplotlib.pyplot as plt
    fig,ax=plt.subplots(figsize=(8,4))
    for t,y in test:ax.plot(t,y,lw=.7,alpha=.5)
    ax.plot(times,positions,'k',label='MuJoCo loaded-probe prediction')
    ax.set(xlim=(-20,120),xlabel='Time from recorded spike (ms)',ylabel='Probe displacement (um)',title='Measured probe dynamics: five evaluation trials')
    ax.legend();fig.tight_layout();fig.savefig(out/'fit.png',dpi=150);plt.close(fig)
    print(json.dumps(report,indent=2))
    if not report['numerical_equivalence_pass']:raise RuntimeError('Physics mismatch')


if __name__=='__main__':main()

"""Run independent controls concurrently; stop dependent work on failure."""
import concurrent.futures
import hashlib
import json
import platform
import subprocess
import sys
from pathlib import Path

ROOT=Path(__file__).resolve().parents[1]


def run(seed,conditions):
    results=[]
    for condition in conditions:
        log=ROOT/f'results/light_seed{seed}_{condition}.log'
        with log.open('w') as stream:
            command=[sys.executable,str(ROOT/'scripts/light_garden.py'),'--seed',str(seed),
                     '--condition',condition,'--physics-dt','0.0001']
            process=subprocess.run(command,cwd=ROOT,stdout=stream,stderr=subprocess.STDOUT)
        result=dict(seed=seed,condition=condition,exit_code=process.returncode,log=str(log))
        results.append(result)
        print(json.dumps(result),flush=True)
        if process.returncode: break
    return results


def main():
    for probe in ('-0.3','0.0','0.3'):
        check=json.loads((ROOT/f'results/light_flat_preflight/preflight_{probe}.json').read_text())
        if not check.get('completed') or len(check['rows'])!=24:
            raise RuntimeError('Complete the body preflight before running the cohort')
    if list((ROOT/'results/light_garden').glob('seed*_*.json')):
        raise RuntimeError('Existing cohort present; preserve it before starting a fresh run')
    sources=['scripts/light_garden.py','scripts/light_brain.py','flyplasticity/light_task.py',
             'scripts/analyze_light_garden.py','research/light_protocol.md','requirements-lock.txt']
    manifest=dict(python=platform.python_version(),arena_revision=2,seeds=[0,1,2],
                  physics_dt=.0001,decision_seconds=.1,decisions_per_episode=24,
                  script_sha256={p:hashlib.sha256((ROOT/p).read_bytes()).hexdigest() for p in sources})
    (ROOT/'results/light_manifest.json').write_text(json.dumps(manifest,indent=2))
    with concurrent.futures.ThreadPoolExecutor(max_workers=6) as pool:
        futures=[pool.submit(run,seed,conditions) for seed in (0,1,2)
                 for conditions in [('plastic','yoked'),('frozen',)]]
        results=[row for future in concurrent.futures.as_completed(futures) for row in future.result()]
    (ROOT/'results/light_runner.json').write_text(json.dumps(results,indent=2))
    if any(row['exit_code'] for row in results): raise SystemExit(1)


if __name__=='__main__': main()

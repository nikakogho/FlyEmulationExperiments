"""Exact matched mechanical replay comparison; no model execution."""
from pathlib import Path
import argparse, json
import numpy as np
ROOT=Path(__file__).resolve().parents[1]


def main():
    ap=argparse.ArgumentParser(); ap.add_argument('first'); ap.add_argument('second'); args=ap.parse_args()
    p,q=(ROOT/v for v in (args.first,args.second)); checks={}
    for name in ('sensors.npz','replay.npz'):
        with np.load(p/name) as a, np.load(q/name) as b:
            checks[name+'/fields']=set(a.files)==set(b.files)
            for key in a.files:
                checks[name+'/'+key]=key in b and np.array_equal(a[key],b[key])
    a,b=(json.loads((r/'report.json').read_text()) for r in (p,q))
    checks['source_hashes']=a['source_sha256']==b['source_sha256']
    result=dict(passed=all(checks.values()),first=args.first,second=args.second,checks=checks,
                new_neural_steps=0,new_physics_steps=0,
                scope='Deterministic numerical reproduction of one mechanical fixture, not independent biological replication')
    (q/'reproducibility.json').write_text(json.dumps(result,indent=2));print(json.dumps(result,indent=2))
    raise SystemExit(not result['passed'])


if __name__=='__main__':main()

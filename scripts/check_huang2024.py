"""One command for software tests and the separate scientific reproduction gate.

Exit 1 on either failure. JSON explicitly distinguishes these two outcomes.
"""
import json
from pathlib import Path
import subprocess
import sys
ROOT=Path(__file__).resolve().parents[1]
OUT=ROOT/'results/huang2024'

def main():
    OUT.mkdir(parents=True,exist_ok=True)
    checks=[]
    for label,args in [
        ('source_provenance',['scripts/record_huang_provenance.py']),
        ('software_tests',['-m','unittest','discover','-s','tests','-v']),
        ('published_figure_gate',['scripts/reproduce_huang2024.py']),
    ]:
        p=subprocess.run([sys.executable,*args],cwd=ROOT,capture_output=True,text=True)
        (OUT/f'{label}.log').write_text(p.stdout+p.stderr,encoding='utf8')
        checks.append(dict(check=label,passed=p.returncode==0,exit_code=p.returncode))
        print(f'{label}: {"PASS" if p.returncode==0 else "FAIL"}',flush=True)
        if label=='source_provenance' and p.returncode:
            break  # never run a reference gate on unverified source files
    report=dict(checks=checks,promotion_allowed=len(checks)==3 and all(x['passed'] for x in checks))
    (OUT/'checks.json').write_text(json.dumps(report,indent=2))
    return 0 if report['promotion_allowed'] else 1

if __name__=='__main__': sys.exit(main())

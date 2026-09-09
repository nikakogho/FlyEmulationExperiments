"""Distinguish passing component checks from permission to claim integrated learning."""
import json
import hashlib
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1]
paths={
    'anatomy':'results/visual_learning_path/checks.json',
    'retinal_transport':'results/retinal_bridge/checks.json',
    'visual_replay':'results/retinal_replay/checks.json',
    'synthetic_locality':'results/compartment_learning_matched/checks.json',
}
data={k:json.loads((ROOT/v).read_text()) for k,v in paths.items()}
result=dict(components_passed=all(data[k]['passed'] for k in ['retinal_transport','visual_replay','synthetic_locality']),
            anatomy_integration_passed=data['anatomy']['integration_gate_passed'],
            improved_biological_learning_demonstrated=False,
            new_embodied_learning_experiment_run=False,
            reason=data['anatomy']['integration_gate_reason'],
            evidence_sha256={k:hashlib.sha256((ROOT/v).read_bytes()).hexdigest() for k,v in paths.items()})
(ROOT/'results/pipeline_gates.json').write_text(json.dumps(result,indent=2))
print(json.dumps(result,indent=2))
if not result['anatomy_integration_passed']:raise SystemExit(1)

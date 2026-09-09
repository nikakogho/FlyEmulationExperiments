import hashlib
import json
from pathlib import Path
import subprocess

ROOT = Path(__file__).resolve().parents[1]
manifest = {'fly_api_commit': subprocess.check_output(['git', '-C', str(ROOT/'upstream/fly-api'), 'rev-parse', 'HEAD'], text=True).strip(),
            'shiu_commit': subprocess.check_output(['git', '-C', str(ROOT/'upstream/Drosophila_brain_model'), 'rev-parse', 'HEAD'], text=True).strip(),
            'annotation_commit': '8587524c1748ce5ef2080822a2fc890fc03bf597',
            'annotation_note': 'Downloaded from main on 2026-09-08; matches pinned commit byte-for-byte (checked separately). Original Daniel annotation checksum unavailable.',
            'files': {}}
for relative in ['data/annotations.tsv', 'upstream/Drosophila_brain_model/Completeness_783.csv', 'upstream/Drosophila_brain_model/Connectivity_783.parquet']:
    path = ROOT/relative
    manifest['files'][relative] = {'bytes': path.stat().st_size, 'sha256': hashlib.sha256(path.read_bytes()).hexdigest()}
(ROOT/'research/provenance.json').write_text(json.dumps(manifest, indent=2))
print(json.dumps(manifest, indent=2))

"""Retrieve authors' public checkpoint archive and verify their published hash."""
import ast
import hashlib
import io
from pathlib import Path
import requests
import zipfile

ROOT = Path(__file__).resolve().parents[1]
source = ROOT/'upstream/flyvis/flyvis_cli/download_pretrained_models.py'
tree = ast.parse(source.read_text())
# Use only the public download credentials distributed in the authors' source.
values = {n.targets[0].id: n.value.value for n in ast.walk(tree)
          if isinstance(n,ast.Assign) and isinstance(n.targets[0],ast.Name)
          and n.targets[0].id in ('api_key','folder_id') and isinstance(n.value,ast.Constant)}
inventory = requests.get('https://www.googleapis.com/drive/v3/files', params={
    'q': f"'{values['folder_id']}' in parents and mimeType='application/zip'",
    'fields': 'files(id,name,size)', 'key': values['api_key']}, timeout=30)
if not inventory.ok: raise RuntimeError(f'Public inventory HTTP {inventory.status_code}')
entry = next(x for x in inventory.json()['files'] if x['name']=='results_pretrained_models.zip')
out = ROOT/'data/flyvis'
out.mkdir(parents=True,exist_ok=True)
archive = out/entry['name']
if archive.exists():
    payload = archive.read_bytes()
else:
    response = requests.get('https://www.googleapis.com/drive/v3/files/'+entry['id'],
                            params={'alt':'media','key':values['api_key']},timeout=60)
    if not response.ok: raise RuntimeError(f'Public archive HTTP {response.status_code}')
    payload = response.content
expected = '71c78d4070556a536b13b23ee3139cd2788aa2a9d07d430a223b4edead281db1'
assert hashlib.sha256(payload).hexdigest()==expected, 'Published archive checksum mismatch'
if not archive.exists(): archive.write_bytes(payload)
if not (out/'results').exists():
    with zipfile.ZipFile(io.BytesIO(payload)) as z:
        for member in z.namelist():
            if not (out/member).resolve().is_relative_to(out.resolve()):
                raise ValueError('Archive path escapes destination')
        z.extractall(out)
print('Published checkpoint checksum verified; existing results preserved.')

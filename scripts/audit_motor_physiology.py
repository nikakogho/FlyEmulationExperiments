"""Resolve supported identity links and report conditional physiological targets.

Reads cached public sources or restores them from a checked-in hash manifest.
No neural models are instantiated and no missing identity link is guessed.
"""
from pathlib import Path
import json, hashlib, sys
ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
import pandas as pd
from flyplasticity.motor_calibration import INTERMEDIATE_REFERENCE, hyperpolarizing_voltage_prediction, probe_force_un


def main():
    import argparse
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument('--out', default='results/motor_physiology')
    args = ap.parse_args()
    manifest = json.loads((ROOT/'research/motor_physiology_sources.json').read_text())
    for source in manifest:
        path = ROOT / source['cache_path']
        if not path.exists():
            import requests
            response = requests.get(source['url'], timeout=60)
            response.raise_for_status()
            if hashlib.sha256(response.content).hexdigest() != source['sha256']:
                raise ValueError('Source changed: '+source['url'])
            path.parent.mkdir(parents=True, exist_ok=True)
            path.write_bytes(response.content)
        if hashlib.sha256(path.read_bytes()).hexdigest() != source['sha256']:
            raise ValueError('Cached source hash mismatch: '+str(path))
    out = ROOT / args.out
    out.mkdir(exist_ok=False)
    cache = ROOT/'data/motor_physiology'
    root_id = '648518346496932836'
    table = pd.read_parquet(cache/'cell_ids_v1444.parquet')
    row = table[table.pt_root_id.astype(str).eq(root_id) & table.valid.eq('t')]
    if len(row) != 1: raise ValueError('Ambiguous stable cell-ID crosswalk')
    cell_id = str(int(row.iloc[0]['id']))
    supervoxel = str(int(row.iloc[0]['pt_supervoxel_id']))
    props = json.loads((cache/'published_properties.json').read_text())['inline']
    idx = props['ids'].index(cell_id)
    tags_property = next(p for p in props['properties'] if p['id']=='tags')
    tags = [tags_property['tags'][k] for k in tags_property['values'][idx]]
    scene = json.loads((cache/'atlas_fast_tibia_flexor.json').read_text())
    fast = next(l['segments'] for l in scene['layers'] if l.get('name')=='published FANC neurons')
    if root_id in fast: raise ValueError('Unexpected overlap with named fast-neuron scene')
    report = dict(
        neural_steps=0, identity_status='candidate_not_confirmed_exact_crosswalk',
        selected_root_id=root_id, public_cell_id=cell_id, soma_supervoxel_id=supervoxel,
        public_tags=tags, named_fast_root_ids=fast,
        candidate=dict(atlas_neuron_number=44, driver='R22A08-Gal4', physiological_class='intermediate',
                       basis='Main-flexor rank 3 plus atlas #44 morphology/driver context; not an exact ID crosswalk'),
        confirmed_links=['selected root ID to stable public cell ID and soma supervoxel',
                         'selected root ID is in the published five-cell main-flexor scene',
                         'atlas Figure A12 #44 to GMR22A08, visually inspected',
                         'R22A08 physiology class is intermediate in Azevedo 2020'],
        missing_link='selected root/public cell ID to atlas neuron #44 or R22A08',
        class_reference=INTERMEDIATE_REFERENCE,
        derived_reference=dict(current_pa=-5, predicted_soma_voltage_mv=float(hyperpolarizing_voltage_prediction(-5)),
                               probe_deflection_um=5, static_probe_force_un=float(probe_force_un(5,0,0))),
        force_context='Paper example: intermediate single-spike response about 1 uN; not a universal gain. Figure 4D varies across cells and spike counts.',
        probe_parameters=dict(stiffness_n_m=.2234, drag_kg_s=.14e-3, mass_kg=.17e-6),
        raw_data=dict(doi='10.5061/dryad.76hdr7stb', version=105831,
                      available=True, downloaded=False, fit_performed=False,
                      file_stream_http_status=403, api_download_http_status=401,
                      access_note='Observed 2026-09-09; browser access also failed to attach/time out'),
        cell_calibration_complete=False, heldout_validation_performed=False,
        activation_authorized=False,
        welfare='Offline source analysis and algebra only; no neural welfare assessment',
    )
    scene_main=json.loads((cache/'atlas_ti_flexor.json').read_text())
    members=next(l['segments'] for l in scene_main['layers'] if l.get('name')=='published FANC neurons')
    if root_id not in members: raise ValueError('Selected cell missing from main-flexor scene')
    (out/'report.json').write_text(json.dumps(report, indent=2))
    (out/'source_manifest.json').write_text(json.dumps(manifest, indent=2))
    print(json.dumps(report, indent=2))


if __name__ == '__main__': main()

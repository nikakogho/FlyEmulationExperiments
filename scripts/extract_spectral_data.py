"""Read-only extraction of Sharkey et al. 2020 Supplementary Data 1.

Run with bundled Python (openpyxl). Never rewrites the source workbook.
"""
import hashlib
import io
import json
from pathlib import Path
import zipfile
import openpyxl
import numpy as np

ROOT = Path(__file__).resolve().parents[1]
folder = ROOT / 'data/spectral'
archive = folder / 'supplementary.zip'
member = '41598_2020_74742_MOESM2_ESM.xlsx'
with zipfile.ZipFile(archive) as z:
    raw = z.read(member)
w = openpyxl.load_workbook(io.BytesIO(raw), data_only=True, read_only=True)
s = w['Sheet 1']
assert [s.cell(1, c).value for c in (5, 7, 9, 11, 13)] == ['Rh1', 'Rh3', 'Rh4', 'Rh5', 'Rh6']
values = np.array([[s.cell(r, c).value for c in range(4, 15)] for r in range(3, 51)], dtype=float)
assert np.array_equal(values[:, 0], np.arange(315, 551, 5))
# Do not silently splice differently scaled grating measurements, extrapolate
# unmeasured Rh3/4/5 tails, or interpret cross-genotype ERG amplitudes as gains.
means = values[:, [1, 3, 5, 7, 9]]
assert np.isfinite(means).all() and (means >= 0).all()
curves = means / means.max(axis=0)
np.savez_compressed(folder / 'receptor_curves.npz', wavelength_nm=values[:, 0],
                    response=curves, raw_mean=means, raw_sd=values[:, [2, 4, 6, 8, 10]])
metadata = dict(source='https://www.nature.com/articles/s41598-020-74742-1',
    download='https://www.ebi.ac.uk/europepmc/webservices/rest/PMC7588446/supplementaryFiles',
    source_member=member, source_sha256=hashlib.sha256(raw).hexdigest(),
    sheet='Sheet 1', range='D3:N50', channels=['Rh1', 'Rh3', 'Rh4', 'Rh5', 'Rh6'],
    support_nm=[315, 550], normalization='Each mean divided by its maximum within 315-550 nm.',
    interpretation='Measured red-eye single-opsin-rescue ERG response shapes; relative excitation proxy, not absolute photon catch or calibrated single-cell voltage.',
    limitations=['Only common measured wavelength support is accepted.',
                 'No cross-receptor gain calibration; Rh6 maximum within this band is not its full-spectrum peak.',
                 'No adaptation kinetics, polarization, photon noise or downstream opponency inferred.'])
(folder / 'provenance.json').write_text(json.dumps(metadata, indent=2))
print(json.dumps(metadata, indent=2))

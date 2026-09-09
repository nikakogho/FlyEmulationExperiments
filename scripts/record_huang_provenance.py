"""Pin research inputs and source claims; verify publisher-supplied MD5s."""
import hashlib
import json
import subprocess
import posixpath
import xml.etree.ElementTree as ET
from zipfile import ZipFile
from pathlib import Path

ROOT=Path(__file__).resolve().parents[1]
RESEARCH=ROOT/'research/huang2024'
UPSTREAM=ROOT/'upstream/Luo_Huang_2024_MB_model'
COMMIT='5d7c08a9a88f923169a0c3008aca68af421e9a7f'
FILES={
    'supplement.pdf':('3','pdf','08f8a6686c3ee23f39610fa589686c86'),
    'figure5.xlsx':('10','xlsx','ab60fdc20374f31becc5c9631d47fb38'),
    'extended10.xlsx':('20','xlsx','f62bb69fe9637bdfa8d316ea3b845819'),
}


def verify_panelc_extract():
    """Check every experimental/model input used by the gate against raw XLSX."""
    ns={'s':'http://schemas.openxmlformats.org/spreadsheetml/2006/main'}
    rel_ns='{http://schemas.openxmlformats.org/officeDocument/2006/relationships}id'
    with ZipFile(RESEARCH/'figure5.xlsx') as z:
        workbook=ET.fromstring(z.read('xl/workbook.xml'))
        sheet=next(s for s in workbook.findall('s:sheets/s:sheet',ns) if s.attrib['name']=='Panel c')
        links=ET.fromstring(z.read('xl/_rels/workbook.xml.rels'))
        target=next(r.attrib['Target'] for r in links if r.attrib['Id']==sheet.attrib[rel_ns])
        target=target.lstrip('/') if target.startswith('/') else posixpath.normpath('xl/'+target)
        worksheet=ET.fromstring(z.read(target))
        cells={c.attrib['r']:c for c in worksheet.findall('.//s:sheetData/s:row/s:c',ns)}
    extracted=json.loads((RESEARCH/'source_data.json').read_text())['figure5']['Panel c']
    count=0
    for neuron in range(6):
        for odor_offset in (0,3):
            for offset,columns in ((0,'BCDEHIJK'),(1,'BCDE')):
                row=4+8*neuron+odor_offset+offset
                for col in columns:
                    cell=cells[f'{col}{row}']
                    if cell.attrib.get('t') not in (None,'n') or cell.find('s:f',ns) is not None:
                        raise RuntimeError('Gate requires original numeric source values, not formulas')
                    raw=float(cell.findtext('s:v',namespaces=ns))
                    decoded=extracted[row-1][ord(col)-65]
                    if abs(raw-decoded)>1e-12:
                        raise RuntimeError(f'Source JSON differs from raw XLSX at {col}{row}')
                    count+=1
    return count

def main():
    head=subprocess.check_output(['git','-C',str(UPSTREAM),'rev-parse','HEAD'],text=True).strip()
    if head!=COMMIT: raise RuntimeError('Author checkout differs from pinned reference')
    if subprocess.check_output(['git','-C',str(UPSTREAM),'status','--porcelain'],text=True).strip():
        raise RuntimeError('Author checkout contains modifications')
    records=[]
    for name,(number,ext,expected_md5) in FILES.items():
        path=RESEARCH/name; data=path.read_bytes()
        md5=hashlib.md5(data).hexdigest()
        if md5!=expected_md5: raise RuntimeError(f'Publisher checksum mismatch: {name}')
        records.append(dict(path=str(path.relative_to(ROOT)),bytes=len(data),md5=md5,
            sha256=hashlib.sha256(data).hexdigest(),
            url=f'https://static-content.springer.com/esm/art%3A10.1038%2Fs41586-024-07819-w/MediaObjects/41586_2024_7819_MOESM{number}_ESM.{ext}'))
    extracted_count=verify_panelc_extract()
    for path in sorted(UPSTREAM.rglob('*')):
        if path.is_file() and '.git' not in path.parts:
            records.append(dict(path=str(path.relative_to(ROOT)),sha256=hashlib.sha256(path.read_bytes()).hexdigest()))
    report=dict(doi='10.1038/s41586-024-07819-w',repository='https://github.com/schnitzer-lab/Luo_Huang_2024_MB_model',
        commit=COMMIT,upstream_license='GPL-3.0-or-later',retrieved='2026-09-08',
        raw_xlsx_values_verified=extracted_count,files=records)
    (RESEARCH/'provenance.json').write_text(json.dumps(report,indent=2))
    print(f'Pinned {len(records)} files; publisher MD5 checks passed; {extracted_count} raw XLSX values verified; author checkout clean.')

if __name__=='__main__': main()

"""Read-only OPJ export using pinned liborigin in a network-disabled container.

Never evaluates Origin column commands, formulas, scripts, or embedded macros.
"""
import argparse
import gzip
import hashlib
import json
import math
from pathlib import Path
import liborigin


def plain(value):
    if isinstance(value, bytes):
        return value.decode('cp1252', errors='replace')
    if value is None or isinstance(value, (str, bool, int)):
        return value
    if isinstance(value, float):
        return value if math.isfinite(value) else None
    if isinstance(value, (list, tuple)):
        return [plain(v) for v in value]
    if isinstance(value, dict):
        return {str(k):plain(v) for k,v in value.items()}
    return {k:plain(getattr(value, k)) for k in dir(value)
            if not k.startswith('_') and not callable(getattr(value, k))}


def main():
    ap = argparse.ArgumentParser(); ap.add_argument('source'); ap.add_argument('output')
    args = ap.parse_args(); src, dst = Path(args.source), Path(args.output)
    if dst.exists(): raise ValueError('Refusing to overwrite an export')
    result = liborigin.parseOriginFile(str(src))
    if not isinstance(result, dict): raise ValueError('Origin parser failed')
    exported = plain(result)
    exported['source_sha256'] = hashlib.sha256(src.read_bytes()).hexdigest()
    exported['parser_revision'] = 'f19e74517059769f9525b477ab934b6f9b1602d5'
    with gzip.open(dst, 'wt', encoding='utf-8') as f:
        json.dump(exported, f, allow_nan=False, separators=(',', ':'))
    print(json.dumps(dict(source=src.name, output=dst.name,
        counts={k:len(result[k]) for k in result}), indent=2))


if __name__ == '__main__': main()

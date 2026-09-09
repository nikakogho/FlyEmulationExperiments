"""Run the pinned upstream experiment with explicit local data and RNG seed.

Only portability/reproducibility adjustments; upstream equations are unmodified.
"""
import argparse
import hashlib
import importlib.util
import json
from pathlib import Path
import subprocess
import sys

ROOT = Path(__file__).resolve().parents[1]


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("experiment", choices=["learning", "navigation"])
    parser.add_argument("--seed", type=int, default=0)
    parser.add_argument("--backend", choices=["numpy", "cython"], default="numpy")
    args, extra = parser.parse_known_args()
    import brian2
    brian2.prefs.codegen.target = args.backend
    brian2.seed(args.seed)
    name = "learning/learning_driver_mb.py" if args.experiment == "learning" else "navigation/nav_demo.py"
    path = ROOT / "upstream/fly-api/experiments" / name
    spec = importlib.util.spec_from_file_location("upstream_experiment", path)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    module.ANN = str(ROOT / "data/annotations.tsv")
    sys.argv = [str(path), "--model-dir", str(ROOT / "upstream/Drosophila_brain_model")]
    if args.experiment == "learning":
        sys.argv += ["--seed", str(args.seed), "--orn-hz", "500", "--n-classes", "6", "--eta", "0.5", "--n-pair", "5", "--kc-thresh", "1", "--kcmbon-gain", "20"]
    elif args.seed != 0:
        parser.error("upstream navigation hard-codes seed 0; only seed 0 supported")
    sys.argv += extra
    print(json.dumps({"experiment": args.experiment, "brian_seed": args.seed, "backend": args.backend, "argv": sys.argv}), flush=True)
    module.main()


if __name__ == "__main__":
    main()

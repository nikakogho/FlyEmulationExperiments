"""CUDA viability / weight-update microbenchmark, NOT a GPU fly simulator.

Uses actual saved connectome weights and synthetic eligibility values. Measures
only multiplicative weight updates; excludes spikes, body, rendering, and learning
quality. Both implementations use float64, checked against each other.
"""
import json
import faulthandler
from pathlib import Path
from time import perf_counter
import numpy as np
import cupy as cp

faulthandler.dump_traceback_later(45, repeat=True)

ROOT=Path(__file__).resolve().parents[1]
weights=np.load(ROOT/'results/temporal_pilot/paired_weights.npz')['weights']
rng=np.random.default_rng(0)
kernel=cp.ElementwiseKernel('float64 e, float64 alpha','float64 w',
                           'w *= exp(-alpha * e);','local_ltd_benchmark')
props=cp.cuda.runtime.getDeviceProperties(0)
result={'gpu':props['name'].decode(),'compute_capability':cp.cuda.Device().compute_capability,
        'vram_bytes':props['totalGlobalMem'],'cupy':cp.__version__,
        'runtime_version':cp.cuda.runtime.runtimeGetVersion(),
        'limitation':'Weight-update kernel only; saved weights, synthetic eligibility, no live brain or body.',
        'cases':[]}
for batch in [1,64,256]:
    print(f'Preparing batch {batch}', flush=True)
    initial=np.tile(weights,(batch,1))
    eligibility=rng.uniform(0,1,initial.shape)
    alpha=np.linspace(.001,.01,batch)[:,None]
    t=perf_counter()
    gw=cp.asarray(initial); ge=cp.asarray(eligibility); ga=cp.asarray(alpha)
    cp.cuda.Stream.null.synchronize()
    upload=perf_counter()-t
    print(f'Upload complete: {upload:.3f}s; compiling/warming kernel', flush=True)
    kernel(ge,ga,gw); cp.cuda.Stream.null.synchronize()  # compile + warmup
    gw.set(initial)
    cpu=initial.copy()
    t=perf_counter()
    for _ in range(100): cpu *= np.exp(-alpha*eligibility)
    cpu_sec=perf_counter()-t
    cp.cuda.Stream.null.synchronize(); t=perf_counter()
    for _ in range(100): kernel(ge,ga,gw)
    cp.cuda.Stream.null.synchronize(); gpu_sec=perf_counter()-t
    t=perf_counter(); actual=cp.asnumpy(gw); download=perf_counter()-t
    np.testing.assert_allclose(actual,cpu,rtol=1e-12,atol=1e-15)
    row=dict(batch=batch,synapses=len(weights),updates=100,cpu_sec=cpu_sec,gpu_resident_sec=gpu_sec,
             upload_sec=upload,download_sec=download,kernel_speedup=cpu_sec/gpu_sec,
             max_abs_error=float(np.max(np.abs(actual-cpu))))
    result['cases'].append(row)
    print(json.dumps(row),flush=True)
    del gw,ge,ga
    cp.get_default_memory_pool().free_all_blocks()
out=ROOT/'results/performance';out.mkdir(parents=True,exist_ok=True)
(out/'gpu_benchmark.json').write_text(json.dumps(result,indent=2))
print(json.dumps(result,indent=2))
faulthandler.cancel_dump_traceback_later()

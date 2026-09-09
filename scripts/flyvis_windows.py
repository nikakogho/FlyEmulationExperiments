"""Work around datamate's unlink-of-open-HDF5-file failure on Windows.

Only storage is changed. Each write closes its handle; values/dtypes are retained.
"""
import h5py
import numpy as np


def write_h5_closed(path, value):
    path.parent.mkdir(parents=True, exist_ok=True)
    with h5py.File(path, 'w', libver='latest') as handle:
        handle['data'] = np.asarray(value)
        handle.swmr_mode = True


def install():
    import datamate.io
    import datamate.directory
    datamate.io._write_h5 = write_h5_closed
    datamate.directory._write_h5 = write_h5_closed

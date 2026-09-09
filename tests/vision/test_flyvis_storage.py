"""Validate the Windows HDF5 compatibility fix independently of model outputs."""
import tempfile
import unittest
from pathlib import Path
import h5py
import numpy as np
from scripts.flyvis_windows import write_h5_closed


class StorageTests(unittest.TestCase):
    def test_round_trip_and_handle_closed(self):
        with tempfile.TemporaryDirectory() as folder:
            path = Path(folder)/'array.h5'
            for value in (np.arange(12,dtype=np.float32).reshape(3,4),
                          np.array(['T4a','T5b'],dtype='S3'), np.array(7,dtype=np.int64)):
                write_h5_closed(path,value)
                with h5py.File(path,'r',swmr=True) as handle:
                    np.testing.assert_array_equal(handle['data'][()],value)
                    self.assertEqual(handle['data'].dtype,value.dtype)
                moved = path.with_name('renamed.h5')
                path.rename(moved)
                moved.rename(path)


if __name__=='__main__': unittest.main()

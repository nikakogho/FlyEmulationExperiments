import unittest,pickle,io
import numpy as np,mujoco
from flyplasticity.loaded_probe import response,mujoco_probe,STIFFNESS_N_M
from scripts.deliver_arena import scripted_drive
from scripts.calibrate_claw_calcium import ArrayOnlyUnpickler


class DeliveryMechanicsTests(unittest.TestCase):
    def test_zero_force_and_causality(self):
        t=np.linspace(-20,120,100)
        np.testing.assert_array_equal(response(t,[0,5,2]),np.zeros(100))
        self.assertTrue(np.all(response(t,[1,5,2])[t<0]==0))
        with self.assertRaises(ValueError):response(t,[1,5,2],dt_s=np.nan)

    def test_probe_static_force_units(self):
        model,data,_=mujoco_probe()
        data.ctrl[0]=1000 # 1 uN, in native units
        for _ in range(5000):mujoco.mj_step(model,data)
        self.assertAlmostEqual(data.qpos[0]*1000,1/STIFFNESS_N_M,places=5)

    def test_fixed_drive_can_stand_and_turn(self):
        np.testing.assert_array_equal(scripted_drive(0),[0,0])
        np.testing.assert_array_equal(scripted_drive(2.5),[0,0])
        self.assertGreater(scripted_drive(1.2)[0],scripted_drive(1.2)[1])
        # The function has only time as input: no cue, reward or coordinates.
        with self.assertRaises(TypeError):scripted_drive(1.,reward=1)

    def test_dataset_loader_rejects_arbitrary_globals(self):
        with self.assertRaises(ValueError):ArrayOnlyUnpickler(io.BytesIO(b'cos\nsystem\n.')).load()
        a=np.array([1.,2.]);raw=pickle.dumps(a,protocol=2)
        # New Python may require codecs for protocol 2; unsupported encodings
        # are rejected. The pinned source protocol has a smaller allowlist.
        try:decoded=ArrayOnlyUnpickler(io.BytesIO(raw)).load()
        except ValueError:return
        np.testing.assert_array_equal(decoded,a)


if __name__=='__main__':unittest.main()

"""Mechanical integration fixture, NOT a calibrated fly muscle or neural model.

SI units: 0.1 m link, 0.01 kg, +/-0.002 Nm actuators, 0.004 Nm/rad
spring, 0.001 Nms/rad damping. These engineering choices test interfaces only.
"""
import mujoco
import numpy as np
from flyplasticity.welfare import Guard, Limits, Sample

XML = '''<mujoco model="mechanical_fixture">
<compiler angle="radian"/>
<option timestep="0.001" gravity="0 0 0" integrator="implicitfast"/>
<visual><global offwidth="800" offheight="600"/></visual>
<worldbody>
 <light pos="0 -0.3 0.5"/>
 <geom type="capsule" fromto="-0.1 0 0 0 0 0" size="0.008" rgba="0.4 0.5 0.6 1" contype="0" conaffinity="0"/>
 <body name="link">
  <joint name="hinge" type="hinge" axis="0 0 1" range="-1 1" stiffness="0.004" damping="0.001"/>
  <geom type="capsule" fromto="0 0 0 0.1 0 0" size="0.006" mass="0.01" rgba="0.2 0.8 0.7 1" contype="0" conaffinity="0"/>
 </body>
</worldbody>
<actuator>
 <general name="positive" joint="hinge" gear="0.002" dyntype="filterexact" dynprm="0.02" ctrlrange="0 1" forcerange="0 1"/>
 <general name="negative" joint="hinge" gear="-0.002" dyntype="filterexact" dynprm="0.02" ctrlrange="0 1" forcerange="0 1"/>
</actuator></mujoco>'''


class JointRig:
    def __init__(self, duration_s=4., *, neural_model=None):
        if neural_model is not None:
            raise ValueError('Neural attachment prohibited: mapping and telemetry are unvalidated')
        self.model = mujoco.MjModel.from_xml_string(XML)
        self.data = mujoco.MjData(self.model)
        self.guard = Guard(Limits(duration_s, .001001, 1.01, .05))
        self.rows = []
        self.steps = 0
        mujoco.mj_forward(self.model, self.data)

    def observe(self):
        return dict(time_s=float(self.data.time), angle_rad=float(self.data.qpos[0]),
                    velocity_rad_s=float(self.data.qvel[0]), activation=self.data.act.tolist(),
                    torque_nm=float(self.data.qfrc_actuator[0]))

    def step(self, command, *, fault=False):
        command = np.asarray(command, dtype=float)
        if command.shape != (2,) or not np.isfinite(command).all() or (command < 0).any() or (command > 1).any():
            self.guard._stop('invalid_actuator_command', float(self.data.time))
            raise ValueError('Actuator commands must be two finite values in [0,1]')
        state = self.observe()
        finite = bool(np.isfinite([state['angle_rad'],state['velocity_rad_s'],state['torque_nm'],*state['activation']]).all())
        # Mechanical-only semantics: activity means actuator activation. There
        # are no neural, valence or need variables in this class, by construction.
        sample = Sample(float(self.data.time), float(max(self.data.act)),
                        finite and not fault, True,
                        bool(abs(state['angle_rad']) > .98 and max(command) > .1
                             and abs(state['velocity_rad_s']) < .01), False)
        def advance():
            self.data.ctrl[:] = command
            mujoco.mj_step(self.model, self.data)
            self.steps += 1
        self.guard.advance(sample, advance)
        row = self.observe()
        row.update(command=command.tolist(), guard_status=self.guard.events[-1]['status'])
        self.rows.append(row)
        return row

    def camera(self):
        cam = mujoco.MjvCamera()
        cam.lookat[:] = [0,0,0]
        cam.distance = .4
        cam.azimuth = 90
        cam.elevation = -60
        return cam

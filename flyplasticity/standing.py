"""Explicit mechanical standing; no neural model or position clamp."""
import numpy as np
from flygym import SingleFlySimulation
from flygym.examples.locomotion import HybridTurningController


class StandingController(HybridTurningController):
    """Use ordinary joint actuators and foot adhesion to request neutral stance.

    Rest bypasses stepping phases and corrective stepping. Physics continues.
    This engineering controller is not a reconstructed fly motor circuit.
    """

    def reset(self, *args, **kwargs):
        self._standing_start = None
        self._standing_angles = None
        return super().reset(*args, **kwargs)

    def step(self, action):
        action = np.asarray(action, dtype=float)
        if action.shape != (2,) or not np.isfinite(action).all():
            raise ValueError('Expected two finite motor commands')
        if np.any(action != 0):
            if self._standing_start is not None:
                # Resume from zero gait amplitude, without old corrective kicks.
                self.cpg_network.curr_magnitudes[:] = 0
                self.retraction_correction[:] = 0
                self.stumbling_correction[:] = 0
                self.retraction_persistence_counter[:] = 0
            self._standing_start = None
            return super().step(action)
        if self._standing_start is None:
            self._standing_start = self.curr_time
            self._standing_angles = self.get_observation()['joints'][0].copy()
        fraction = np.clip((self.curr_time-self._standing_start)/.1, 0, 1)
        blend = fraction*fraction*(3-2*fraction)
        neutral = self.preprogrammed_steps.default_pose
        low_action = dict(joints=(1-blend)*self._standing_angles+blend*neutral,
                          adhesion=np.ones(6, dtype=int))
        obs, reward, terminated, truncated, info = SingleFlySimulation.step(self, low_action)
        info.update(low_action)
        info['explicit_standing'] = True
        return obs, reward, terminated, truncated, info

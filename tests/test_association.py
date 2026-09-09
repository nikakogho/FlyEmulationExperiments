import inspect
import unittest
import numpy as np
from flyplasticity.association import GammaEligibilityLTD,PlasticPathwayAudit,schedule,comparison,output_compartments
from flyplasticity.learning_preflight import NeuralPreflightGuard


class AssociationTests(unittest.TestCase):
    def test_input_compartment_uses_wiring_not_cell_body_side(self):
        self.assertEqual(output_compartments([0,1],[3,2],{0:'left',1:'right'},[2,3]),
                         {2:'right',3:'left'})
        with self.assertRaises(ValueError):output_compartments([0,1],[2,2],{0:'left',1:'right'},[2])

    def rule(self):return GammaEligibilityLTD([0,1],[0,1],{0:[2],1:[3]},5,[1.,1.])

    def test_locality_and_no_cue_interface(self):
        r=self.rule();w=np.ones(2)
        for _ in range(30):w=r.step([1,1,1,0,0],w)
        self.assertLess(w[0],1);self.assertEqual(w[1],1)
        self.assertEqual(list(inspect.signature(r.step).parameters),['counts','weights','frozen'])

    def test_either_input_alone_cannot_write(self):
        for c in ([1,0,0,0,0],[0,0,1,0,0]):
            r=self.rule();w=np.ones(2)
            for _ in range(30):w=r.step(c,w)
            np.testing.assert_array_equal(w,1)

    def test_timing_control_and_frozen(self):
        paired=self.rule();unpaired=self.rule();frozen=self.rule()
        wp=wu=wf=np.ones(2)
        for k in range(250):
            active=k<30
            wp=paired.step([int(active),0,int(active),0,0],wp)
            wu=unpaired.step([int(active),0,int(150<=k<180),0,0],wu)
            wf=frozen.step([int(active),0,int(active),0,0],wf,frozen=True)
        self.assertLess(wp[0],wu[0]-.1)
        np.testing.assert_array_equal(wf,1)

    def test_floor_and_invalid_input_preserve_state(self):
        r=self.rule();w=np.ones(2)
        for _ in range(1000):w=r.step([1,1,5,5,0],w)
        np.testing.assert_array_equal(w,.5)
        before=r.rule.rules[0][1].e.copy()
        with self.assertRaises(ValueError):r.step([np.nan,0,0,0,0],w)
        np.testing.assert_array_equal(before,r.rule.rules[0][1].e)

    def audit(self):
        return PlasticPathwayAudit(5,[4],[0,1,4],[2,2,0],[1.,1.,0.],
                                   modulatory_sources=[3],plastic_positions=[0],gamma_kcs=[0],output_neurons=[2])

    def test_authorized_write_only(self):
        a=self.audit();a.authorize_update([1,1,0],[.8])
        self.assertEqual(a.inspect([0]*5,[0,1,4],[2,2,0],[.8,1,0],[3]),0)
        for current,proposed in [([.8,.9,0],[.7]),([.8,1,0],[.81]),
                                 ([.8,1,0],[.49]),([.8,1,0],[np.nan])]:
            with self.assertRaises(ValueError):a.authorize_update(current,proposed)

    def test_ppl1_cannot_enter_write_set(self):
        with self.assertRaises(ValueError):
            PlasticPathwayAudit(3,[2],[2],[0],[1.],modulatory_sources=[],
                                plastic_positions=[0],gamma_kcs=[2],output_neurons=[0])

    def test_reward_is_explicit_and_checked(self):
        a=self.audit();g=NeuralPreflightGuard(5,[4],pathways=a);z=np.zeros(5)
        kw=dict(pre=[0,1,4],post=[2,2,0],weights=[1,1,0],modulatory_sources=[3])
        g.inspect(0,z,z,z,[60],[60],expected_reward_rates=[60],**kw)
        with self.assertRaises(RuntimeError):g.inspect(.005,z,z,z,[60],[60],expected_reward_rates=[0],**kw)
        self.assertTrue(g.guard.stopped)

    def test_equal_apparatus_dose_different_timing(self):
        for arm in ('paired','unpaired','frozen'):
            s=[schedule(k,arm) for k in range(800)]
            self.assertEqual(sum(x[1] for x in s)*.005,9.)
            self.assertEqual(sum(x[0]=='A' for x in s),150)
            self.assertEqual(sum(x[0]=='B' for x in s),100)
        self.assertEqual(schedule(275,'unpaired')[1],0)
        self.assertEqual(schedule(400,'unpaired')[0],None)

    def test_comparison_rejects_general_suppression_and_failed_controls(self):
        def report(a,b):return dict(status='completed',recovery_pass=True,
                                   probe_spikes=dict(pre_A=100,pre_B=100,post_A=a,post_B=b))
        rs=dict(paired=report(50,50),unpaired=report(100,100),frozen=report(100,100))
        self.assertFalse(comparison(rs)['passed'])
        rs['paired']=report(50,100);self.assertTrue(comparison(rs)['passed'])
        rs['unpaired']['status']='stopped';self.assertFalse(comparison(rs)['passed'])


if __name__=='__main__':unittest.main()

import unittest
import numpy as np
from flyplasticity.huang2024 import (
    Bout, load_parameters, figure5c_protocol, run, steady_state, direct_state,
    decay_factor, BASELINE, MAXIMUM, PUNISHMENT,
    fitting_protocol, UPSTREAM,
)


class PublishedModelTests(unittest.TestCase):
    def setUp(self):
        self.p = load_parameters()

    def test_parameter_mapping_matches_published_table(self):
        np.testing.assert_allclose(self.p[0][0, 0],
            [-2.11, -3.75, 4.68, 25.4, 17.3, 16.3, 5.14, 2.94, 13.7], atol=.05, rtol=0)
        self.assertAlmostEqual(self.p[1].item()/3, -7.12, delta=.01)
        self.assertAlmostEqual(self.p[2][0, 0, 0]*11.38/3, -21.3, delta=.05)
        self.assertAlmostEqual(self.p[3][0, 3, 2], -.382, delta=.001)
        self.assertAlmostEqual(self.p[3][0, 3, 4], -.309, delta=.001)
        np.testing.assert_allclose(self.p[4][0, 0], [2020, 6220, 243000], rtol=.002)

    def test_native_matlab_saved_figures_144_values(self):
        from scipy.io import loadmat
        # Independent expected values saved by the authors' MATLAB execution.
        for valence in ('attractive','repulsive'):
            fig=UPSTREAM/f'matlab_code/model_fitting/figures/Dx_steady_state_nonlinear_3_17-Apr-2024_3modules_{valence}.fig'
            axes=loadmat(fig,simplify_cells=True)['hgS_070000']['children']
            expected=[]
            for axis in axes:
                curves=[c['properties'] for c in axis['children'] if c['type']=='graph2d.lineseries']
                self.assertEqual(len(curves),2)
                np.testing.assert_array_equal(curves[0]['Color'],[1,0,0])
                np.testing.assert_array_equal(curves[1]['Color'],[0,0,1])
                expected.append([c['YData'] for c in curves])
            actual,_=run(self.p,fitting_protocol(),valence)
            np.testing.assert_allclose(actual[0],np.asarray(expected),atol=1e-10,rtol=0)

    def test_protocol_matches_author_indices_and_imaging_times(self):
        b = figure5c_protocol()
        self.assertEqual(len(b), 51)
        self.assertEqual(sum(x.punishment for x in b), 6)
        self.assertEqual([i+1 for i,x in enumerate(b) if x.imaging == 1], [1,17,33,38,43,48])
        for i in (4,16,20,32):
            self.assertEqual(b[i-1].duration, 300)
        starts = np.r_[0., np.cumsum([x.duration for x in b])[:-1]]
        final_training_end = starts[31]  # final CS- offset, before trailing 300s ISI
        np.testing.assert_array_equal(starts[[32,37,42,47]]-final_training_end,
                                      [300,3600,10800,86400])

    def test_direct_neural_solver_matches_iterative_under_saturation(self):
        rng = np.random.default_rng(31)
        p = load_parameters(ensemble=True)
        recurrent = p[3][:256]
        weights = rng.normal(0, 100, (256, 2, 6))
        kc = rng.uniform(0, 2, (256, 2))
        for shock in (0., 1., 3.):
            np.testing.assert_allclose(steady_state(kc,shock,weights,recurrent),
                direct_state(kc,shock,weights,recurrent),atol=1e-10,rtol=0)

    def test_full_protocol_solver_equivalence(self):
        for modules in (2,3):
            for valence in ('attractive','repulsive'):
                p=load_parameters(modules)
                a,_=run(p,figure5c_protocol(),valence)
                b,_=run(p,figure5c_protocol(),valence,solver=direct_state)
                np.testing.assert_allclose(a,b,atol=1e-10,rtol=0)

    def test_no_input_is_zero_evoked_activity(self):
        _,h=run(self.p,[Bout('rest',50.)],trace=True)
        np.testing.assert_array_equal(h[0]['rates'],0.)
        np.testing.assert_array_equal(h[0]['weights'],np.repeat(self.p[0][:,:,:6],2,axis=1))

    def test_learning_disabled_freezes_weights_not_sensory_adaptation(self):
        _,h=run(self.p,figure5c_protocol(),learn=False,trace=True)
        initial=np.repeat(self.p[0][:,:,:6],2,axis=1)
        for state in h:
            np.testing.assert_array_equal(state['weights'],initial)
        self.assertLess(h[0]['odor_end'][0,0],1.)

    def test_signed_dopamine_gives_opposite_plasticity(self):
        # A causal intervention isolates the plasticity rule from feedback.
        for dopamine,sign in ((2.,-1.),(-2.,1.)):
            p=[c.copy() for c in self.p]
            p[3][:]=0
            p[0][0,0,:3]=dopamine
            _,h=run(p,[Bout('probe',30.,(1.,0.))],trace=True)
            change=h[0]['weights'][0,0,3:]-p[0][0,0,3:6]
            self.assertTrue(np.all(sign*change>0))
            np.testing.assert_array_equal(h[0]['weights'][0,1,3:],p[0][0,0,3:6])

    def test_zero_dopamine_blocks_update(self):
        p=[c.copy() for c in self.p]
        p[0][0,0,:3]=0
        p[3][:]=0
        _,h=run(p,[Bout('probe',30.,(1.,0.))],trace=True)
        np.testing.assert_array_equal(h[0]['weights'][0,0,3:],p[0][0,0,3:6])

    def test_odor_swap_equivariance(self):
        from dataclasses import replace
        b=figure5c_protocol()
        a,ha=run(self.p,b,trace=True)
        z,hz=run(self.p,[replace(x,odor=x.odor[::-1]) for x in b],trace=True)
        np.testing.assert_allclose(a,z,atol=1e-12,rtol=0)
        for x,y in zip(ha,hz):
            np.testing.assert_allclose(x['weights'],y['weights'][:,::-1],atol=1e-12,rtol=0)

    def test_decay_split_and_semigroup(self):
        tau=self.p[4][:,0]
        whole=decay_factor(200.,10900.,tau)
        split=decay_factor(100.,10800.,tau)*decay_factor(100.,10900.,tau)
        np.testing.assert_allclose(whole,split,atol=1e-15,rtol=0)
        expected=np.exp(-100/tau[:,[0,1,1]]-100/tau[:,[0,2,2]])
        np.testing.assert_allclose(whole,expected,atol=1e-15,rtol=0)

    def test_rates_bounded_and_input_parameters_unchanged(self):
        before=[p.copy() for p in self.p]
        x,_=run(self.p,figure5c_protocol(),'repulsive')
        self.assertTrue(np.all(x[:,3:]>=-BASELINE[None,3:,None,None]))
        self.assertTrue(np.all(x[:,3:]<= (MAXIMUM-BASELINE[3:])[None,:,None,None]+1e-12))
        for a,b in zip(self.p,before): np.testing.assert_array_equal(a,b)

    def test_batch_matches_single_samples(self):
        p=[x[:3] for x in load_parameters(ensemble=True)]
        batch,_=run(p,figure5c_protocol())
        for i in range(3):
            single,_=run([x[i:i+1] for x in p],figure5c_protocol())
            np.testing.assert_allclose(batch[i],single[0],atol=1e-10,rtol=0)

    def test_invalid_input_rejected(self):
        for args in (('bad',-1.),('bad',float('nan')),('bad',1.,(1.,1.))):
            with self.assertRaises(ValueError): Bout(*args)
        with self.assertRaises(ValueError): load_parameters(4)
        p=[x.copy() for x in self.p]; p[4][:]=0
        with self.assertRaises(ValueError): run(p,[Bout('rest',1.)])


if __name__=='__main__': unittest.main()

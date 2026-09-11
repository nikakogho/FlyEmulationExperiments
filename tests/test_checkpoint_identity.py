import unittest,copy
import numpy as np
from flyplasticity.checkpoint_identity import equivalent,input_group_name


class CheckpointIdentityTests(unittest.TestCase):
    def setUp(self):
        self.a={'terminal':{'poissongroup':{'rates':(np.array([2.,3.]),2)},
            'neurons':{'v':np.array([-.05,-.04])},'_random_generator_state':np.array([10,20]),
            'queue':[np.array([1,2])],'clock':1.25}}

    def test_generated_name_and_dict_order_are_not_neural_state(self):
        b=copy.deepcopy(self.a);s=b['terminal'];s['poissongroup_12']=s.pop('poissongroup')
        b['terminal']=dict(reversed(list(s.items())))
        self.assertTrue(equivalent(self.a,b));self.assertEqual(input_group_name(b),'poissongroup_12')

    def test_voltage_rng_queue_clock_changes_rejected(self):
        for key in ('neurons','_random_generator_state','queue','clock'):
            b=copy.deepcopy(self.a)
            if key=='neurons':b['terminal'][key]['v'][0]+=.001
            elif key=='queue':b['terminal'][key][0][0]+=1
            elif key=='clock':b['terminal'][key]+=.001
            else:b['terminal'][key][0]+=1
            self.assertFalse(equivalent(self.a,b))

    def test_multiple_input_groups_and_dtype_changes_rejected(self):
        b=copy.deepcopy(self.a);b['terminal']['poissongroup_1']=b['terminal']['poissongroup']
        with self.assertRaises(ValueError):equivalent(self.a,b)
        b=copy.deepcopy(self.a);b['terminal']['neurons']['v']=b['terminal']['neurons']['v'].astype('float32')
        self.assertFalse(equivalent(self.a,b))

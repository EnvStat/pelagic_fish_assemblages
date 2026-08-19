import unittest

import dec_mod
from dec_mod import Model, derived_quantity, likelihood_factor, prior, ModelParameter, Indexer, NotComputed, Constant
from numpy import array


class TestCase(unittest.TestCase):

    def test_1(self):

        class MyModel(Model):
            x: ModelParameter = 1
            y: ModelParameter = 2

            @derived_quantity
            def z(x, y):
                return x + y

        m = MyModel()
        self.assertEqual(m.z_list_args(), {'x': 1, 'y': 2})
        self.assertEqual(m.x, 1)
        self.assertEqual(m.y, 2)
        self.assertEqual(m.z, 3)
        self.assertEqual(m.z_list_args(), {'x': 1, 'y': 2})


        m.set_par('x', 10)
        self.assertEqual(m.x, 10)
        self.assertEqual(m.y, 2)
        self.assertEqual(m.z, 12)

        self.assertEqual(m.parameters, {'x': 10, 'y': 2})
        self.assertEqual(m.structure(), {'x': None, 'y': None, 'z': ('x', 'y')})
        self.assertEqual(m._downstream, {'x': {'z'}, 'y': {'z'}, 'z': set()})



    def test_1b(self):

        class MyModel(Model):
            x: ModelParameter = 1
            y: Constant = 2

            @derived_quantity
            def z(x, y):
                return x + y

        m = MyModel()
        self.assertEqual(m.z_list_args(), {'x': 1, 'y': 2})
        self.assertEqual(m.x, 1)
        self.assertEqual(m.y, 2)
        self.assertEqual(m.z, 3)
        self.assertEqual(m.z_list_args(), {'x': 1, 'y': 2})


        m.set_par('x', 10)
        self.assertEqual(m.x, 10)
        self.assertEqual(m.y, 2)
        self.assertEqual(m.z, 12)

        self.assertEqual(m.parameters, {'x': 10})
        self.assertEqual(m.structure(), {'x': None, 'z': ('x', 'y')})
        self.assertEqual(m._downstream, {'x': {'z'}, 'y': {'z'}, 'z': set()})

    def test_2(self):

        glob = []

        class MyModel(Model):
            x: ModelParameter = 1
            y: ModelParameter = 2

            @derived_quantity
            def complicated_simulation(x):
                glob.append('x')
                return x

            @derived_quantity
            def z(complicated_simulation, y):
                glob.append('y')
                return complicated_simulation + y

        m = MyModel()
        self.assertEqual(glob, [])
        self.assertEqual(m.z_list_args(), {'complicated_simulation': NotComputed, 'y': 2})

        self.assertEqual(m.x, 1)
        self.assertEqual(m.y, 2)
        self.assertEqual(m.z, 3)
        self.assertEqual(glob, ['x', 'y'])
        self.assertEqual(m.z_list_args(), {'complicated_simulation': 1, 'y': 2})

        m.set_par('x', 10)
        self.assertEqual(m.x, 10)
        self.assertEqual(m.y, 2)
        self.assertEqual(m.z, 12)
        self.assertEqual(glob, ['x', 'y', 'x', 'y'])

        m.set_par('y', 20)
        self.assertEqual(m.x, 10)
        self.assertEqual(m.y, 20)
        self.assertEqual(m.z, 30)
        self.assertEqual(glob, ['x', 'y', 'x', 'y', 'y'])

        self.assertEqual(m.structure(), {'x': None, 'y': None, 'complicated_simulation': ('x',), 'z': ('complicated_simulation', 'y')})
        self.assertEqual(m._downstream, {'x': {'z', 'complicated_simulation'}, 'y': {'z'}, 'complicated_simulation': {'z'}, 'z': set()})



    def test_3(self):
        class MyModel(Model):
            log_x: ModelParameter = 0
            logit_y: ModelParameter = 0
            termsof_z: ModelParameter = [1, 2, 3, 4]

        m = MyModel()
        self.assertEqual(m.x, 1)
        self.assertEqual(m.y, 0.5)
        self.assertEqual(m.z, 10)

        self.assertEqual(m.parameters, {'log_x': 0, 'logit_y': 0, 'termsof_z': [1, 2, 3, 4]})
        self.assertEqual(m.basic_transformations(), {'log_x': 0, 'logit_y': 0, 'termsof_z': [1, 2, 3, 4], 'x': 1, 'y':0.5, 'z':10})
        self.assertEqual(m.transformed_pars(), {'x': 1, 'y':0.5, 'z':10})

        self.assertEqual(m.structure(), {'log_x': None, '*x': ('log_x',), 'logit_y': None, '*y': ('logit_y',), 'termsof_z': None, '*z': ('termsof_z',)})


    def test_4(self):
        class MyModel(Model):

            @derived_quantity
            def log_x(): return 0
            @derived_quantity
            def logit_y(): return 0
            @derived_quantity
            def termsof_z(): return [1, 2, 3, 4]

        m = MyModel()
        self.assertEqual(m.x, 1)
        self.assertEqual(m.y, 0.5)
        self.assertEqual(m.z, 10)

        self.assertEqual(m.structure(), {'log_x': (), '*x': ('log_x',), 'logit_y': (), '*y': ('logit_y',), 'termsof_z': (), '*z': ('termsof_z',)})
        print()
        m.draw_structure()

    def test_5(self):
        class MyModel(Model):
            x: 'free parameter' = 1
            y: 'free parameter' = 2

            @derived_quantity(term_of='Total')
            def X(x):
                return x
            @derived_quantity(term_of='Total')
            def Y(y):
                return y

        m = MyModel()
        self.assertEqual(m.X, 1)
        self.assertEqual(m.Y, 2)
        self.assertEqual(m.Total, 3)

        m.set_par('x', 10)
        self.assertEqual(m.X, 10)
        self.assertEqual(m.Y, 2)
        self.assertEqual(m.Total, 12)

        m.set_par('y', 20)
        self.assertEqual(m.X, 10)
        self.assertEqual(m.Y, 20)
        self.assertEqual(m.Total, 30)

        self.assertEqual(m.structure(), {'x': None, 'y': None, 'X': ('x',), '*Total': ('X', 'Y'), 'Y': ('y',)})
        self.assertEqual(m._downstream, {'x': {'Total', 'X'}, 'y': {'Y', 'Total'}, 'X': {'Total'}, 'Total': set(), 'Y': {'Total'}})


    def test_5b(self):
        class MyModel(Model):
            @derived_quantity(term_of='AB')
            def A():
                return 1
            @derived_quantity(term_of=('AB', 'BC'))
            def B():
                return 2
            @derived_quantity(term_of=('BC', ))
            def C():
                return 4

        m = MyModel()
        self.assertEqual(m.A, 1)
        self.assertEqual(m.B, 2)
        self.assertEqual(m.C, 4)
        self.assertEqual(m.AB, 3)
        self.assertEqual(m.BC, 6)

        self.assertEqual(m.structure(), {'A': (), '*AB': ('A', 'B'), 'B': (), '*BC': ('B', 'C'), 'C': ()})
        self.assertEqual(m._downstream, {'A': {'AB'}, 'AB': set(), 'B': {'BC', 'AB'}, 'BC': set(), 'C': {'BC'}})
        print()
        m.draw_structure()

    def test_5c(self):
        class MyModel(Model):
            x: ModelParameter(term_of='Total') = 1
            @derived_quantity(term_of='Total')
            def X():
                return 2

        m = MyModel()

        self.assertEqual(m.x, 1)
        self.assertEqual(m.X, 2)
        self.assertEqual(m.Total, 3)

        m.set_par('x', 10)
        self.assertEqual(m.x, 10)
        self.assertEqual(m.X, 2)
        self.assertEqual(m.Total, 12)


        self.assertEqual(m.structure(), {'x': None, 'X': (), '*Total': ('x', 'X')})
        self.assertEqual(m._downstream, {'x': {'Total'}, 'Total': set(), 'X': {'Total'}})


    def test_6(self):

        class MyModel(Model):
            x: (lambda y: -y) = 1
            y: 'free parameter' = 2

            @prior
            def P(y):
                return -y

            @likelihood_factor
            def L(x):
                return x*3

            @likelihood_factor()
            def constant():
                return 10


        m = MyModel()
        self.assertEqual(m.x, 1)
        self.assertEqual(m.prior_x, -1)
        self.assertEqual(m.P, -2)
        self.assertEqual(m.Prior, -3)
        self.assertEqual(m.L, 3)
        self.assertEqual(m.Likelihood, 13)
        self.assertEqual(m.Posterior, 10)

        m.set_par('x', 10)
        self.assertEqual(m.x, 10)
        self.assertEqual(m.prior_x, -10)
        self.assertEqual(m.Prior, -12)
        self.assertEqual(m.L, 30)
        self.assertEqual(m.Likelihood, 40)
        self.assertEqual(m.Posterior, 28)

        self.assertEqual(m.structure(), {'x': None, 'prior_x': ('x',), '*Prior': ('prior_x', 'P'), 'y': None, 'P': ('y',), 'L': ('x',), '*Likelihood': ('L', 'constant'), 'constant': (), '*Posterior': ('Prior', 'Likelihood')})
        self.assertEqual(m._downstream, {'x': {'L', 'Posterior', 'prior_x', 'Likelihood', 'Prior'}, 'prior_x': {'Posterior', 'Prior'}, 'Prior': {'Posterior'}, 'y': {'Posterior', 'Prior', 'P'}, 'P': {'Posterior', 'Prior'}, 'L': {'Posterior', 'Likelihood'}, 'Likelihood': {'Posterior'}, 'constant': {'Posterior', 'Likelihood'}, 'Posterior': set()})
        self.assertEqual(m.parameters_with_prior(), ['x', 'y'])


    def test_7(self):

        class A(Model):
            x: 'free parameter' = 1

        class B(A):
            y: 'free parameter' = 2

            @derived_quantity
            def z(x, y):
                return x + y

        m = B()
        self.assertEqual(m.x, 1)
        self.assertEqual(m.y, 2)
        self.assertEqual(m.z, 3)

        m.set_par('x', 10)
        self.assertEqual(m.x, 10)
        self.assertEqual(m.y, 2)
        self.assertEqual(m.z, 12)

        self.assertEqual(m.parameters, {'x': 10, 'y': 2})


    def test_8(self):

        class A(Model):
            x: (lambda y: -y) = 1

            @likelihood_factor
            def L(x):
                return x*3

        class B(A):
            y: 'free parameter' = 2

            @prior
            def P(y):
                return -y

            @likelihood_factor()
            def constant():
                return 10

        m = B()
        self.assertEqual(m.x, 1)
        self.assertEqual(m.prior_x, -1)
        self.assertEqual(m.P, -2)
        self.assertEqual(m.Prior, -3)
        self.assertEqual(m.L, 3)
        self.assertEqual(m.Likelihood, 13)
        self.assertEqual(m.Posterior, 10)

        m.set_par('x', 10)
        self.assertEqual(m.x, 10)
        self.assertEqual(m.prior_x, -10)
        self.assertEqual(m.Prior, -12)
        self.assertEqual(m.L, 30)
        self.assertEqual(m.Likelihood, 40)
        self.assertEqual(m.Posterior, 28)

        print()
        m.draw_structure()


    def test_10(self):

        class MyModel(Model):
            x: ModelParameter = 1
            y: ModelParameter = 2

            @derived_quantity
            def z(x, y):
                return x + y

        m = MyModel()
        self.assertEqual(m.x, 1)
        self.assertEqual(m.y, 2)
        self.assertEqual(m.z, 3)

        m.do_intervention('z', 'ha ha')
        self.assertEqual(m.z, 'ha ha')


    def test_11(self):

        class MyModel(Model):
            x: ModelParameter = 1
            y: ModelParameter = 2

            @derived_quantity
            def z(x, y):
                return x*2 + y*3

        m = MyModel()
        self.assertAlmostEqual(m.measure_derivative('x', 'z'), 2)
        self.assertAlmostEqual(m.measure_derivative('y', 'z'), 3)
        self.assertAlmostEqual(m.measure_derivative('z', 'z'), 1)
        print()
        m.draw_structure()


    def test_12(self):

        class MyModel(Model):
            x: ModelParameter = 1
            y: ModelParameter = 2

            @derived_quantity
            def z(x, y):
                return x + y
            @derived_quantity
            def zz(y):
                return y
        m = MyModel()
        print()
        m.draw_structure()





    def test_20(self):

        class MyModel(Model):
            _k: Indexer(['_A', '_B'])
            par_k: ModelParameter = 1

        m = MyModel()
        self.assertEqual(m.par_A, 1)
        self.assertEqual(m.par_B, 1)
        self.assertEqual(m._ind_A, 0)
        self.assertEqual(m._ind_B, 1)

        self.assertEqual(m.structure(), {'par_A': None, 'par_B': None})


    def test_21(self):

        class MyModel(Model):
            _k: Indexer(['_A', '_B'], '_T')
            par_k: ModelParameter = 1

        m = MyModel()
        self.assertEqual(m.par_A, 1)
        self.assertEqual(m.par_B, 1)
        self.assertEqual(m.par_T, (1, 1))

        self.assertEqual(m.structure(), {'par_A': None, 'par_B': None, '*par_T': ('par_A', 'par_B')})


    def test_22(self):

        class MyModel(Model):
            _k: Indexer(['_A', '_B'])
            par_k: ModelParameter = 1
            par_B: ModelParameter = 2

        m = MyModel()
        self.assertEqual(m.par_A, 1)
        self.assertEqual(m.par_B, 2)

        self.assertEqual(m.structure(), {'par_A': None, 'par_B': None})


    def test_23(self):

        class MyModel(Model):
            _i: Indexer(['_1', '_2', '_3'])
            par_1: ModelParameter = 1
            par_2: ModelParameter = 2
            par_3: ModelParameter = 3

            @derived_quantity
            def dq_i(par_i):
                return par_i*10

        m = MyModel()
        self.assertEqual(m.par_1, 1)
        self.assertEqual(m.par_2, 2)
        self.assertEqual(m.par_3, 3)

        self.assertEqual(m.dq_1, 10)
        self.assertEqual(m.dq_2, 20)
        self.assertEqual(m.dq_3, 30)

        self.assertEqual(m.parameters, {'par_1': 1, 'par_2': 2, 'par_3': 3})

        self.assertEqual(m.structure(), {'par_1': None, 'par_2': None, 'par_3': None, 'dq_1': ('par_1',), 'dq_2': ('par_2',), 'dq_3': ('par_3',)})


    def test_24(self):

        class MyModel(Model):
            _I: Indexer(['_1', '_2', '_3'], combine='_i')
            par_I: ModelParameter = 1
            par_2: ModelParameter = 2
            par_3: ModelParameter = 3

            @derived_quantity
            def dq_I(par_I):
                return par_I*10

        m = MyModel()
        self.assertEqual(m.par_1, 1)
        self.assertEqual(m.par_2, 2)
        self.assertEqual(m.par_3, 3)
        self.assertEqual(m.par_i, (1, 2, 3))

        self.assertEqual(m.dq_1, 10)
        self.assertEqual(m.dq_2, 20)
        self.assertEqual(m.dq_3, 30)
        self.assertEqual(m.dq_i, (10, 20, 30))

        self.assertEqual(m.parameters, {'par_1': 1, 'par_2': 2, 'par_3': 3})

        self.assertEqual(m.structure(), {'par_1': None, 'par_2': None, 'par_3': None, '*par_i': ('par_1', 'par_2', 'par_3'), 'dq_1': ('par_1',), 'dq_2': ('par_2',), 'dq_3': ('par_3',), '*dq_i': ('dq_1', 'dq_2', 'dq_3')})


    def test_25(self):

        class MyModel(Model):
            _I: Indexer(['_1', '_2'])
            par_1: ModelParameter = 1
            par_2: ModelParameter = 2

            @derived_quantity(term_of='total_I')
            def term1_I(par_I):
                return par_I*2

            @derived_quantity(term_of='total_I')
            def term2_I(par_I):
                return par_I*10

        m = MyModel()
        self.assertEqual(m.par_1, 1)
        self.assertEqual(m.par_2, 2)

        self.assertEqual(m.term1_1, 2)
        self.assertEqual(m.term1_2, 4)

        self.assertEqual(m.term2_1, 10)
        self.assertEqual(m.term2_2, 20)

        self.assertEqual(m.total_1, 12)
        self.assertEqual(m.total_2, 24)

        self.assertEqual(m.structure(), {'par_1': None, 'par_2': None, 'term1_1': ('par_1',), '*total_1': ('term1_1', 'term2_1'), 'term1_2': ('par_2',), '*total_2': ('term1_2', 'term2_2'), 'term2_1': ('par_1',), 'term2_2': ('par_2',)})

        print()
        m.draw_structure()

    def test_26(self):

        class MyModel(Model):
            _I: Indexer(['_1', '_2'])
            par_1: ModelParameter = 1
            par_2: ModelParameter = 2

            @prior
            def dq_I(par_I):
                return par_I*10


        m = MyModel()
        self.assertEqual(m.par_1, 1)
        self.assertEqual(m.par_2, 2)

        self.assertEqual(m.dq_1, 10)
        self.assertEqual(m.dq_2, 20)

        self.assertEqual(m.Prior, 30)

        self.assertEqual(m.structure(), {'par_1': None, 'par_2': None, 'dq_1': ('par_1',), '*Prior': ('dq_1', 'dq_2'), 'dq_2': ('par_2',), '*Likelihood': (), '*Posterior': ('Prior', 'Likelihood')})


    def test_27(self):

        class MyModel(Model):
            _I: Indexer(['_1', '_2'])
            par_1: ModelParameter = 1
            par_2: ModelParameter = 2

            @prior
            def termsof_dq_I(par_I):
                return par_I, par_I*2, par_I*3, par_I*4


        m = MyModel()
        self.assertEqual(m.par_1, 1)
        self.assertEqual(m.par_2, 2)

        self.assertEqual(m.dq_1, 10)
        self.assertEqual(m.dq_2, 20)
        self.assertEqual(m.termsof_dq_1, (1, 2, 3, 4))
        self.assertEqual(m.termsof_dq_2, (2, 4, 6, 8))

        self.assertEqual(m.Prior, 30)

        print()
        m.draw_structure()

    def test_28(self):

        class MyModel(Model):
            _I: Indexer(['_1', '_2'], combine='_i')
            _J: Indexer(['_A', '_B'], combine='_j')
            par_I_J: ModelParameter = 1

            @prior
            def dq_I_J(par_I_J):
                return par_I_J*10

        m = MyModel()
        self.assertEqual(m.par_1_A, 1)
        self.assertEqual(m.par_2_A, 1)
        self.assertEqual(m.par_1_B, 1)
        self.assertEqual(m.par_2_B, 1)

        m.set_par('par_2_A', 2)
        m.set_par('par_1_B', 3)
        m.set_par('par_2_B', 4)

        self.assertEqual(m.par_i_A, (1, 2))
        self.assertEqual(m.par_i_B, (3, 4))
        self.assertEqual(m.par_1_j, (1, 3))
        self.assertEqual(m.par_2_j, (2, 4))
        self.assertEqual(m.par_i_j, ((1, 2), (3, 4)))

        self.assertEqual(m.dq_1_A, 10)
        self.assertEqual(m.dq_2_A, 20)
        self.assertEqual(m.dq_1_B, 30)
        self.assertEqual(m.dq_2_B, 40)

        self.assertEqual(m.dq_i_A, (10, 20))
        self.assertEqual(m.dq_i_B, (30, 40))
        self.assertEqual(m.dq_1_j, (10, 30))
        self.assertEqual(m.dq_2_j, (20, 40))
        self.assertEqual(m.dq_i_j, ((10, 20), (30, 40)))

        print()
        m.draw_structure()

    def test_29(self):
        class MyModel(Model):
            ECOV_: Indexer('AA_ BB_'.split())
            _SPEC: Indexer('_1 _2'.split())

            @derived_quantity(term_of='expected_SPEC')
            def ECOV_factor_SPEC():
                return _array_ECOV @ log_ECOV_SPEC

        m = MyModel()

        self.assertEqual(m._accumulators, {'expected_1': ['AA_factor_1', 'BB_factor_1'], 'expected_2': ['AA_factor_2', 'BB_factor_2']})
        self.assertEqual(m.structure(), {'AA_factor_1': (), 'AA_factor_2': (), 'BB_factor_1': (), '*expected_1': ('AA_factor_1', 'BB_factor_1'), 'BB_factor_2': (), '*expected_2': ('AA_factor_2', 'BB_factor_2')})


    def test_29b(self):
        class MyModel(Model):
            _SPEC: Indexer('_1 _2'.split())
            ECOV_: Indexer('AA_ BB_'.split())

            @derived_quantity(term_of='expected_SPEC')
            def ECOV_factor_SPEC():
                return _array_ECOV @ log_ECOV_SPEC

        m = MyModel()
        #print(m._accumulators)
        #print(m.structure())
        #print(m._downstream)

        self.assertEqual(m._accumulators, {'expected_1': ['AA_factor_1', 'BB_factor_1'], 'expected_2': ['AA_factor_2', 'BB_factor_2']})
        self.assertEqual(m.structure(), {'AA_factor_1': (), 'AA_factor_2': (), 'BB_factor_1': (), '*expected_1': ('AA_factor_1', 'BB_factor_1'), 'BB_factor_2': (), '*expected_2': ('AA_factor_2', 'BB_factor_2')})


if __name__ == '__main__':
    unittest.main()

import unittest

import prob_prog
from prob_prog import Model, derived_quantity, likelihood_factor, prior
from numpy import array


class TestCase(unittest.TestCase):

    def test_1(self):

        class MyModel(Model):
            x: 'free parameter' = 1
            y: 'free parameter' = 2

            @derived_quantity
            def z(x, y):
                return x + y

        m = MyModel()
        self.assertEqual(m.x, 1)
        self.assertEqual(m.y, 2)
        self.assertEqual(m.z, 3)

        m.set_par('x', 10)
        self.assertEqual(m.x, 10)
        self.assertEqual(m.y, 2)
        self.assertEqual(m.z, 12)

        self.assertEqual(m.parameters, {'x': 10, 'y': 2})


    def test_2(self):

        glob = []

        class MyModel(Model):
            x: 'free parameter' = 1
            y: 'free parameter' = 2

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

        self.assertEqual(m.x, 1)
        self.assertEqual(m.y, 2)
        self.assertEqual(m.z, 3)
        self.assertEqual(glob, ['x', 'y'])

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


    def test_3(self):
        class MyModel(Model):
            log_x: 'free parameter' = 0
            logit_y: 'free parameter' = 0
            #termsof_z: 'free parameter' = [1, 2, 3, 4]

        m = MyModel()
        self.assertEqual(m.x, 1)
        self.assertEqual(m.y, 0.5)
        #self.assertEqual(m.z, 10)


    def test_4(self):
        class MyModel(Model):

            @derived_quantity
            def log_x(): return 0
            @derived_quantity
            def logit_y(): return 0
            @derived_quantity
            def termsof_z(): return array([1, 2, 3, 4])

        m = MyModel()
        self.assertEqual(m.x, 1)
        self.assertEqual(m.y, 0.5)
        self.assertEqual(m.z, 10)


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
            @derived_quantity
            def _dummy(Total):
                pass

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
        self.assertEqual(m._prior_x, -1)
        self.assertEqual(m.P, -2)
        self.assertEqual(m.Prior, -3)
        self.assertEqual(m.L, 3)
        self.assertEqual(m.Likelihood, 13)
        self.assertEqual(m.Posterior, 10)

        m.set_par('x', 10)
        self.assertEqual(m.x, 10)
        self.assertEqual(m._prior_x, -10)
        self.assertEqual(m.Prior, -12)
        self.assertEqual(m.L, 30)
        self.assertEqual(m.Likelihood, 40)
        self.assertEqual(m.Posterior, 28)


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
        self.assertEqual(m._prior_x, -1)
        self.assertEqual(m.P, -2)
        self.assertEqual(m.Prior, -3)
        self.assertEqual(m.L, 3)
        self.assertEqual(m.Likelihood, 13)
        self.assertEqual(m.Posterior, 10)

        m.set_par('x', 10)
        self.assertEqual(m.x, 10)
        self.assertEqual(m._prior_x, -10)
        self.assertEqual(m.Prior, -12)
        self.assertEqual(m.L, 30)
        self.assertEqual(m.Likelihood, 40)
        self.assertEqual(m.Posterior, 28)

    def test_10(self):

        class MyModel(Model):
            x: 'free parameter' = 1
            y: 'free parameter' = 2

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
            x: 'free parameter' = 1
            y: 'free parameter' = 2

            @derived_quantity
            def z(x, y):
                return x*2 + y*3

        m = MyModel()
        self.assertAlmostEqual(m.measure_derivative('x', 'z'), 2)
        self.assertAlmostEqual(m.measure_derivative('y', 'z'), 3)
        self.assertAlmostEqual(m.measure_derivative('z', 'z'), 1)


if __name__ == '__main__':
    unittest.main()

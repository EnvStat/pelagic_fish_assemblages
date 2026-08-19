"""
Probabilistic Programming

(c) Mikhail Shubin, December 2020

This module provides tools for defining models with a declarative language.



Simple Example
--------------

::

    class MyModel(Model):
        x: 'free parameter' = 1
        y: 'free parameter' = 2

        @derived_quantity
        def z(x, y):
            return x + y

This would create a model with two free parameters: ``x`` and ``y``, and a derived quantity ``z=x+y``

::

    m = MyModel()
    print(m.x)  # 1
    print(m.y)  # 2
    print(m.z)  # 3

    m.set_par('x', 10)
    print(m.x)  # 10
    print(m.y)  # 2
    print(m.z)  # 12

    print(m.parameters)
    # {'x': 1, 'y': 0.5}

Derived quantity ``z`` is linked to variables ``self.x`` and ``self.y`` through the names of the arguments. To change the parameter value, function ``.set_par(<name>, <new value>)`` have to be used.

.. note:: Current implementation uses python type annotations for its inner workings, so it is better to avoid using any other type annotations



Cached Computations
-------------------
Derived quantities are cached and recomputed only when needed. This is useful when running MCMC. ::

    class MyModel(Model):
        x: 'free parameter' = 1
        y: 'free parameter' = 2

        @derived_quantity
        def complicated_simulation(x):
            # ...
            # some long simulation
            # ...
            return result

        @derived_quantity
        def final_step(complicated_simulation, y):
            return complicated_simulation + y

    m = MyModel()  # complicated_simulation is not executed yet
    m.final_step   # first time to run complicated_simulation, as it is required for the final_step

    m.set_par('y', 3)
    m.final_step   # x is not changed, no need to recompute complicated_simulation

    m.set_par('x', 0)
    m.final_step   # x is changed, complicated_simulation is recomputed

    m.set_par('x', 1)
    m.final_step   # only the last value of x is cached, complicated_simulation is recomputed again


function ``.list_dependencies()`` prints put the dependency graph and all values cached, it can be usefull for debugging.



Automatic Transformations
-------------------------

::

    class MyModel(Model):
        log_x:   'free parameter' = 0
        logit_y: 'free parameter' = 0

        @derived_quantity
        def z(x, y):
            return x + y


    m = MyModel()
    print(m.log_x)    # 0
    print(m.logit_y)  # 0
    print(m.x)        # 1
    print(m.y)        # 0.5
    print(m.z)        # 1.5

Free parameters with names starting with ``log_`` and ``logit_`` automatically create derived quantities with
parameter values in a linear scale. These transformed parameters can be used in other declarations. ::

    class MyModel(Model):
        log_x:   'free parameter' = 0
        logit_y: 'free parameter' = 0

        @derived_quantity  # this is redundant
        def x(log_x):
            return exp(x)

        @derived_quantity  # this is redundant
        def y(logit_y):
            return logistic(logit_y)

Opposite is not true: declaring free parameter ``x`` would not create derived quantities ``log_x`` and ``logit_x``. These have to be added manually ::

    class MyModel(Model):
        x: 'free parameter' = 1

        @derived_quantity  # this is new derived quantity
        def log_x(x):
            return log(x)


Use ``.transformed_pars()`` to access all the transformed values at once ::

    print(m.transformed_pars())
    # {'log_x': 0, 'logit_y': 0}


If you wish your custom derived quantity to be added to the list of transformations, use ``@basic_transformation`` decorator instead ::

    class MyModel(Model):
        x: 'free parameter' = 1

        @basic_transformation
        def log_x(x):
            return log(x)

    m = MyModel()
    print(m.transformed_pars())
    # {'log_x': 0.0}


Vector Parameters
-----------------

::

    class MyModel(Model):
        x: 'free parameter' = [1, 2, 3, 4]

        @derived_quantity
        def sum_x(x):
            return sum(x)

    m = MyModel()
    print(m.x)    # [1, 2, 3, 4]
    print(m.sum_x)  # 10

    m.set_par(('x', 2), 0)
    print(m.sum_x)  # 7


To change an item in a vector parameter, use ``.set_par((<parameter name>, <index>), <new value>)``.

.. note:: Only one-dimensional vectors are supported



Prior, Likelihood and Posterior
---------------------------------

::

    class MyModel(Model):
        x: 'free parameter' = 1
        y: 'free parameter' = 2

        @prior
        def prior_x(x):
            return -x**2

        @prior
        def prior_y(y):
            return -y**2

        @likelihood_factor
        def likelihood(x, y):
            return -(y+x - 3)**2

    m = MyModel()
    print(m.prior_x)     # -1
    print(m.prior_y)     # -4
    print(m.Prior)       # -5
    print(m.Likelihood)  # 0
    print(m.Posterior)   # -5


In each model, three derived quantities are created automatically:
``Prior`` which sums up all functions with decorator ``@prior``,
``Likelihood`` which sums up all functions with decorator ``@likelihood_factor`` and
``Posterior`` which sums ``Prior`` and ``Likelihood``. We assume all priors and likelihood are written in log scales, so we use addition, not multiplication.
Otherwise, decorators ``@prior`` and ``@likelihood_factor`` act the same ways as ``@derived_quantity``.

This definition is functionally identical to the previous one ::

    class MyModel(Model):
        x: 'free parameter' = 1
        y: 'free parameter' = 2

        @derived_quantity
        def prior_x(x):
            return -x**2

        @derived_quantity
        def prior_y(y):
            return -y**2

        @derived_quantity
        def likelihood(x, y):
            return -(y+x - 3)**2

        @derived_quantity
        def Prior(prior_x, prior_y):
            return prior_x + prior_y

        @derived_quantity
        def Likelihood(likelihood):
            return likelihood

        @derived_quantity
        def Posterior(Likelihood, Prior):
            return Likelihood + Prior


Prior of a single parameter can be defined by using callable instead of ``'free_parameter'``. ::

    def prior_centered_at_zero(param):
        return -param**2

    class MyModel(Model):
        x: prior_centered_at_zero = 1
        y: prior_centered_at_zero = 0


In this case, callable will be saved in `_prior_{parame_name}`. Callable should have a single argument of any name. ::

    class MyModel(Model):
        x: lambda z: -z**2 = 1
        y: sum = [1, 2, 3]


As values of priors and likelihood components are cached, they are only recomputed when corresponding parameters are changed.

List of all priors and likelihood factors can be accessed with ``.all_priors()`` and ``.all_likelihood_factors()``.
ist of all parameters for which prior is defined can be accessed with ``.all_params_with_prior``.



Derived Quantities with Multiple Outputs
--------------------------------------

::

    class MyModel(Model):
        x: 'free parameter' = 1

        @derived_quantity -> 'A B C'
        def hidden_states(x):
            return x+1, x+2, x+3

        @derived_quantity()
        def observed(A):
            return A*10

    m = MyModel()
    print(m.x)  # 1
    print(m.hidden_states)  # (2, 3, 4)
    print(m.A)  # 2
    print(m.B)  # 3
    print(m.C)  # 4
    print(m.observed)  # 20


When derived quantity return multiple values, each value can be assigned a name for a simpler access.
The following declaration is identical to the first ::

    class MyModel(moels.Model):
        x: 'free parameter' = 1

        @derived_quantity
        def hidden_states(x):
            return x+1, x+2, x+3

        @derived_quantity
        def A(hidden_states):
            return hidden_states[0]

        @derived_quantity
        def B(hidden_states):
            return hidden_states[1]

        @derived_quantity
        def C(hidden_states):
            return hidden_states[3]

        @derived_quantity()
        def observed(A):
            return A*10


Model constants
---------------

Derived quantities cannot access to the object's ``self`` directly, but in case it is needed, one may use constants ::


    class MyModel(Model):
        x: 'free parameter' = 1
        N: 'constant' = 10

        @derived_quantity
        def product(x, N):
            return x*N

    m = MyModel()
    print(m.product)  # 10

    m = MyModel(N=2)
    print(m.product)  # 2

"""



import copy

from numpy import exp, array

def logistic(x):
    return 1/(1+exp(-x))

import inspect
import datetime


_PROFILING = False
_PROFILING_RESULTS = {}


def _list_arg_names(func):
    spec = inspect.getfullargspec(func)
    if spec.varargs is not None or spec.varkw is not None or spec.defaults is not None and spec.kwonlyargs is not None:
        raise Exception(f'derived qunatity {func.__name__} should only have positional arguments.')
    return spec.args



################
## Decorators ##
################

# Decorators dont do much work, they only annotate function for future analysis by Model.__init_subclass

def derived_quantity(func=None, is_prior=False, is_likelihood_factor=False, is_basic_transformation=False, redeclare=False, overwrite_func=None, term_of=None):
    # have to work both ways, with and without ()

    def annotate_derived_quantity(func):
        if 'return' in func.__annotations__:
            outputs = func.__annotations__['return'].split()
        else:
            outputs = []
        # function is turned into derived quantity later, when Model.__init_subclass class is finalized
        # this decorator just marks a function for later
        arg_names = _list_arg_names(func)
        if overwrite_func:
            func = overwrite_func
        func.__is_derived_quantity__ = True
        func.__derived_quantity_kwargs__ = {
            'is_prior': is_prior,
            'is_likelihood_factor': is_likelihood_factor,
            'is_basic_transformation': is_basic_transformation,
            'redeclare': redeclare,
            'arg_names': arg_names,
            'outputs': outputs,
            'term_of': term_of}
        return func

    if callable(func):
        return annotate_derived_quantity(func)
    else:
        return annotate_derived_quantity


def prior(func=None, **kwargs):
    return derived_quantity(func, is_prior=True, **kwargs)


def likelihood_factor(func=None, **kwargs):
    return derived_quantity(func, is_likelihood_factor=True, **kwargs)


def basic_transformation(func=None, **kwargs):
    return derived_quantity(func, is_basic_transformation=True, **kwargs)


def derived_quantity_sum(func=None, **kwargs):
    return derived_quantity(func, overwrite_func=lambda *args: sum(args), **kwargs)



#################################################
## Functions for constuction Model's structure ##
#################################################

# these functions are called from Model.__init_subclass, and do the majority of work


def _add_constant(cls, name):
    cls._reserved_names |= {name}
    cls._constants |= {name}


def _add_parameter(cls, name):
    cls._reserved_names |= {name}
    cls._initial_values[name] = getattr(cls, name)
    cls._downstream[name] = set()

    def param_getter(self):
        return self.parameters[name]

    setattr(cls, name, property(param_getter, doc='model parameter'))

    # add default transformation
    if name.startswith('log_') and not hasattr(cls, name[4:]):
        _add_derived_quantity(cls, name=name[4:], arg_names=[name], func=exp, is_basic_transformation=True)

    if name.startswith('logit_') and not hasattr(cls, name[6:]):
        _add_derived_quantity(cls, name=name[6:], arg_names=[name], func=logistic, is_basic_transformation=True)


def _add_derived_quantity(cls, name, func, arg_names, is_prior=False, is_likelihood_factor=False, is_basic_transformation=False, redeclare=False, outputs=None, term_of=None):
    #print('- declating', name, 'function of', arg_names)

    # check if name can be used
    if name in cls._reserved_names and not redeclare:
        raise KeyError(f'derived quantity {name} already declared')

    # create auto sum function
    for arg in arg_names:
        if arg in cls._autosums and cls._autosums[arg] != 'declared':
            autosum_terms = cls._autosums[arg]
            cls._autosums[arg] = 'declared'
            _add_derived_quantity(cls, name=arg, func=lambda *as_args: sum(as_args), arg_names=autosum_terms, redeclare=True)

    # append dependency graph
    cls._downstream[name] = set()
    _declare_dependency(cls, arg_names, name)
    cls._upstream[name] = arg_names

    # lazy computer version is different if we used profiler
    if _PROFILING:
        # n calls; n calls when recomputed; time total; local time; arg collection time
        _PROFILING_RESULTS[name] = {
            'total_calls': 0,
            'total_time': 0,
            'recompute_calls': 0,
            'recompute_time': 0,
            'arguments_time': 0}
        print(f'Declaring derived quantity {name}{arg_names}')

        def lazy_computer(self):
            # re-compute values if needed
            total_start = datetime.datetime.now()

            if self._computed[name] is None:

                arg_start = datetime.datetime.now()

                args = [getattr(self, key) for key in arg_names]

                _PROFILING_RESULTS[name]['arguments_time'] += (datetime.datetime.now()-arg_start).total_seconds()
                local_start = datetime.datetime.now()

                self._computed[name] = func(*args)

                _PROFILING_RESULTS[name]['recompute_time'] += (datetime.datetime.now()-local_start).total_seconds()
                _PROFILING_RESULTS[name]['recompute_calls'] += 1

            _PROFILING_RESULTS[name]['total_time'] += (datetime.datetime.now()-total_start).total_seconds()
            _PROFILING_RESULTS[name]['total_calls'] += 1

            return self._computed[name]

    else:

        def lazy_computer(self):
            # re-compute values if needed
            if self._computed[name] is None:
                args = [getattr(self, key) for key in arg_names]
                self._computed[name] = func(*args)
            return self._computed[name]

    setattr(cls, name, property(lazy_computer))

    # add partial outputer
    if outputs:

        def make_item_getter(name, i):

            def item_getter(self):
                return getattr(self, name)[i]

            return item_getter

        for i, out in enumerate(outputs):
            if out in cls._reserved_names and not redeclare:
                raise KeyError(f'parial output {out} of derived quantity {name} already declared')
            cls._reserved_names |= {out}
            cls._downstream[out] = set()
            cls._upstream[out] = {name}
            cls._partial_outputs[out] = name
            setattr(cls, out, property(make_item_getter(name, i)))

    # add default transformation
    if name.startswith('log_') and not hasattr(cls, name[4:]):
        _add_derived_quantity(cls, name=name[4:], arg_names=[name], func=exp, is_basic_transformation=is_basic_transformation)

    if name.startswith('logit_') and not hasattr(cls, name[6:]):
        _add_derived_quantity(cls, name=name[6:], arg_names=[name], func=logistic, is_basic_transformation=is_basic_transformation)

    if name.startswith('termsof_') and not hasattr(cls, name[8:]):
        _add_derived_quantity(cls, name=name[8:], arg_names=[name], func=lambda x: x.sum(), is_basic_transformation=is_basic_transformation,
                              is_prior=is_prior, is_likelihood_factor=is_likelihood_factor)
        # only sum should contribute to Prior or Likelihood
        is_prior = False
        is_likelihood_factor = False


    # add derived quantity's name where necessary
    cls._reserved_names |= {name}
    cls._derived_quantities |= {name}
    if term_of:
        if term_of in cls._autosums:
            if cls._autosums[term_of] == 'declared':
                raise KeyError(f'autosum {name} already declared (bacause it was mentioned before)')
            cls._autosums[term_of].append(name)
        else:
            cls._autosums[term_of] = [name]
    if is_prior:
        cls._priors |= {name}
    if is_likelihood_factor:
        cls._likelihood_factors |= {name}
    if is_basic_transformation:
        cls._basic_transformations |= {name}


def _declare_dependency(cls, upstream, new_dependency):
    # go up the graph of dependency
    for key in upstream:
        cls._downstream[key] |= {new_dependency}
        if key in cls._initial_values:
            # parameter is an end point, it never depend on anything
            pass
        elif key in cls._constants:
            # constant is an end point, it should not be changed
            pass
        elif key in cls._upstream:
            # continue moving up
            _declare_dependency(cls, cls._upstream[key], new_dependency)
        else:
            raise KeyError(f'constant, parameter or derived quantity "{key}", used to declare "{new_dependency}" is not declared')


########################
## Model class itself ##
########################


class Model():
    # Variables to define the model structure
    _reserved_names = set()
    _derived_quantities = set()
    _constants = set()
    _initial_values = {}
    _downstream = {}
    _upstream = {}
    _partial_outputs = {}
    _priors = set()
    _likelihood_factors = set()
    _basic_transformations = set()
    _autosums = {}

    def __init_subclass__(cls):
        # Copy model definition from the parent class (so that inheretance would work)
        cls._reserved_names        = cls._reserved_names.copy()
        cls._derived_quantities    = cls._derived_quantities.copy()
        cls._constants             = cls._constants.copy()
        cls._initial_values        = cls._initial_values.copy()
        cls._downstream            = cls._downstream.copy()
        cls._upstream              = cls._upstream.copy()
        cls._priors                = cls._priors.copy()
        _partial_outputs           = cls._partial_outputs.copy()
        cls._likelihood_factors    = cls._likelihood_factors.copy()
        cls._basic_transformations = cls._basic_transformations.copy()

        # go through annotations the class body
        for k, t in cls.__annotations__.items():
            if callable(t):
                # free parameter with prior
                _add_parameter(cls, name=k)
                _add_derived_quantity(cls, name='_prior_'+k, func=t, arg_names=[k], is_prior=True)

            elif not isinstance(t, str):
                raise Exception(f'in Model Class, annotations should be str or callable, not {t}')

            elif t == 'constant':
                _add_constant(cls, name=k)

            elif t == 'free parameter':
                _add_parameter(cls, name=k)

            else:
                raise Exception(f'Unknown annotation {t} for {k}')

        # remove annotations for inheritance to work
        cls.__annotations__ = {}

        # now, go through functions, seach for all derived quantities and then declare them
        derived_quantities = [(k, f) for k, f in cls.__dict__.items() if hasattr(f, '__is_derived_quantity__') and f.__is_derived_quantity__]
        for k, f in derived_quantities:
            _add_derived_quantity(cls, name=k, func=f, **f.__derived_quantity_kwargs__)

        # define a prior function, likelihood and posterior functions
        _add_derived_quantity(cls, name='Prior',      func=lambda *args: sum(args), arg_names=cls._priors,             redeclare=True)
        _add_derived_quantity(cls, name='Likelihood', func=lambda *args: sum(args), arg_names=cls._likelihood_factors, redeclare=True)
        _add_derived_quantity(cls, name='Posterior',  func=lambda a, b: a+b,        arg_names=['Likelihood', 'Prior'], redeclare=True)

    def __init__(self, **constants):
        self.parameters = copy.deepcopy(self._initial_values)
        self.clear()
        for k, v in constants.items():
            setattr(self, k, v)

    #########################
    ## changing parameters ##
    #########################

    def clear(self):
        """ Drop all precomputed values """
        self._computed = {k: None for k in self._derived_quantities}

    def copy(self, other):
        """ Copies all values from other paramter to itself. Assumes self and other belong to the same Class"""
        self.parameters = {k: copy.copy(v) for k, v in other.parameters.items()}
        self._computed = copy.copy(other._computed)

    def load(self, new_vals):
        """
        Update parameters with the new values taken from a dict. Unused values are ignored
        """
        for k, v in new_vals.items():
            if k in self.parameters:
                self.set_par(k, v)
        return self

    def get_par(self, par):
        """
        Return a value of one parameter.
        If parameter is scalar, par is the name of the parameter.
        If parameter is vector, par is either the name of the parameter (in this case whole vector is returned), or a tuple (name, index)
        (in this case single value from the vector is returned).
        """
        if isinstance(par, tuple):
            return self.parameters[par[0]][par[1]]
        else:
            return self.parameters[par]

    def set_par(self, par, val):
        """
        Set a value of one parameter.
        If parameter is scalar, par is the name of the parameter.
        If parameter is vector, par is either the name of the parameter (in this case whole vector is set), or a tuple (name, index)
        (in this case single value from the vector is set).
        """
        if isinstance(par, tuple):
            par, index = par
            self.parameters[par][index] = val
        else:
            self.parameters[par] = val
        for key in self._downstream[par]:
            self._computed[key] = None

    def do_intervention(self, name, val):
        self._computed[name] = val
        for key in self._downstream[name]:
            self._computed[key] = None

    def measure_derivative(self, par, target, epsilon=0.0001):
        cp = self.__class__()
        cp.copy(self)
        if not isinstance(par, (list, tuple)):
            par = [par]
        for p in par:
            val = getattr(self, p)
            try:
                val = val + epsilon
            except:
                val = array(val) + epsilon
            if p in self.parameters:
                cp.set_par(p, val)
            else:
                cp.do_intervention(p, val)

        if not isinstance(target, (list, tuple)):
            return (getattr(cp, target) - getattr(self, target))/epsilon
        else:
            return [(getattr(cp, t) - getattr(self, t))/epsilon for t in target]

    def get_params(self, params):
        """ Return values of multiple parameters as a flat list """
        result = []
        for par in params:
            val = self.get_par(par)
            try:
                result.extend(val)
            except TypeError:
                result.append(val)
        return result

    def set_params(self, params, values):
        """
        Set values for multiple parameters.
        Values should be a flat list: items would be distributed among parameters according to their size
        """
        for par in params:
            if isinstance(par, tuple):
                par, index = par
                self.parameters[par][index], values = values[0], values[1:]
            else:
                target = self.parameters[par]
                if isinstance(target, list):
                    target[:], values = values[: len(target)], values[len(target):]
                else:
                    self.parameters[par], values = values[0], values[1:]

            for key in self._downstream[par]:
                self._computed[key] = None

    ######################
    ## helper functions ##
    ######################

    def __repr__(self):
        rep = []
        for k, v in self.parameters.items():
            if isinstance(v, (tuple, list)):
                rep.append(f'{k}:[' + ','.join(f'{x:.1f}' for x in v)+']')
            else:
                rep.append(f'{k}:{v:.1f}')
        return ' '.join(rep)

    def list_dependencies(self):
        """ Print out all the derived quantities """
        for key in sorted(self._computed):
            print(key, '-empty-' if self._computed[key] is None else ("'"+str(self._computed[key])[:20]+"'"), self._upstream[key])

    def all_params_with_prior(self):
        """ List all parameters with log prior defined """
        return sum([self._upstream[name] for name in self._priors], [])

    def transformed_pars(self):
        """ Return the dictionary with all the free parameters and their basic transformations """
        return {key: getattr(self, key) for key in self._basic_transformations}

    def all_priors(self):
        return {key: getattr(self, key) for key in self._priors}

    def all_likelihood_factors(self):
        return {key: getattr(self, key) for key in self._likelihood_factors}


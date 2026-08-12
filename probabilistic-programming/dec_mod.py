"""
Declarative Modelling

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


If you wish yout custom derived quantity to ve added to the list of transformations, use ``@basic_transformation`` decorator instead ::

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

from numpy import exp, array, ndarray
import numpy

#from useful import logistic  # *** dependency
import inspect
import datetime


_PROFILING = False
_PROFILING_RESULTS = {}


def _list_arg_names(func):
    """
    Return the list of pisitional arguments from the function.
    Raises an expection if non-positional arguments are present.
    """
    spec = inspect.getfullargspec(func)
    if spec.varargs is not None or spec.varkw is not None or spec.defaults is not None and spec.kwonlyargs is not None:
        raise Exception(f'derived qunatity {func.__name__} should only have positional arguments.')
    return spec.args


def logistic(x):
    return 1/(1+exp(-x))


def cumsumzero(X):
    S = numpy.append(0, numpy.cumsum(X))
    return S - numpy.mean(S)

def _fastest_sum(X):
    try:
        return X.sum()
    except:
        return sum(X)

def _arg_sum(*args):
    return sum(args)

def _mirror(*args):
    return args

def _zero():
    return 0

def _Posterior(Prior, Likehood):
    return Prior + Likehood


def format_timedelta(td):
    seconds = int(td.total_seconds())
    days = seconds // 60 // 60 // 24
    hours = seconds // 60 // 60 % 24
    if days: return f'{days}d-{hours}h'

    minut = seconds // 60 % 60
    if hours: return f'{hours}h-{minut}m'
    if minut > 10: return f'{minut}m'

    seconds = seconds % 60
    if minut: return f'{minut}m-{seconds}sec'
    if seconds > 10: return f'{seconds}sec'

    microsec = td.total_seconds() % 60
    if seconds: return f'{microsec:0.2f}sec'
    return f'{1000*microsec:4.2f}ms'


class CumulativeStopwatch():
    def __init__(self):
        self.total = datetime.timedelta()

    def start(self):
        self.start_time = datetime.datetime.now()
    def stop(self):
        self.total += (datetime.datetime.now() - self.start_time)

    def total_seconds(self):
        return self.total.total_seconds()

    def __enter__(self): self.start()
    def __exit__(self, exc_type, exc_value, traceback): self.stop()

    def __str__(self):
        return format_timedelta(self.total)


###############
## Notations ##
###############

# Typing class that do nothing by themselves

class ModelParameter():
    def __init__(self, is_constant=False, term_of=(), prior=None):
        self.kwargs = {
            'is_constant' : is_constant,
            'term_of': (term_of, ) if isinstance(term_of, str) else term_of,
            'prior': prior}

class Constant():
    pass

class Submodel():
    def __init__(self, term_of=(), rename=None):
        self.rename = rename
        self.kwargs = {
            'term_of': (term_of, ) if isinstance(term_of, str) else term_of,
            }

class _DerivedQuantity():
    pass

class _AutogeneratedDQ():
    pass

class Indexer():
    def __init__(self, indxs, combine=None):
        self.indxs = [str(x) for x in indxs]
        self.combine = combine

class NotComputed():
    pass


################
## Decorators ##
################

# Decorators dont do much work, they only annotate function for future analysis by Model.__init_subclass

def derived_quantity(func=None, is_basic_transformation=False, term_of=(), redeclare=False):

    # function is turned into derived quantity later, when Model.__init_subclass class is finalized
    # this decorator just marks a function for later
    def annotate_derived_quantity(func):
        arg_names = _list_arg_names(func)
        func.__is_derived_quantity__ = True
        func.__derived_quantity_kwargs__ = {
            'is_basic_transformation': is_basic_transformation,
            'redeclare': redeclare,
            'arg_names': arg_names,
            'term_of': (term_of, ) if isinstance(term_of, str) else term_of}
        return func

    # have to work both ways, with and without ()
    if callable(func):
        return annotate_derived_quantity(func)
    else:
        return annotate_derived_quantity


def prior(func=None, **kwargs):
    return derived_quantity(func, term_of='Prior', **kwargs)

def likelihood_factor(func=None, **kwargs):
    return derived_quantity(func, term_of='Likelihood', **kwargs)

def basic_transformation(func=None, **kwargs):
    return derived_quantity(func, is_basic_transformation=True, **kwargs)


#################################################
## Functions for constuction Model's structure ##
#################################################

# these functions are called from Model.__init_subclass, and do the majority of work


def _add_indexer(cls, name, indexer):
    assert indexer.combine != name
    cls._indexers[name] = indexer
    for i, k in enumerate(indexer.indxs):
        cls._reserved_names['_ind'+k] = Constant
        cls._downstream['_ind'+k] = set()
        cls._args['_ind'+k] = set()
        cls._arg_of['_ind'+k] = set()
        cls._basic_transformations.add('_ind'+k)
        setattr(cls, '_ind'+k, i)


def _add_parameter(cls, name, initial_val, prior=None, is_constant=False, term_of=(), _rename=None):
    # apply rename
    if _rename:
        a, b = _rename
        name = name.replace(a, b)
        term_of = [accumulator.replace(a, b) for accumulator in term_of]

    # check for indexers
    substr, indexer = _find_indexer(cls, name)
    if indexer:
        # declare different instead
        for i in indexer.indxs:
            _add_parameter(cls, name, copy.copy(initial_val), prior=prior, _rename=(substr, i))

        if indexer.combine:
            _add_derived_quantity(
                cls, name.replace(substr, indexer.combine), func=_mirror, arg_names=[name.replace(substr, i) for i in indexer.indxs],
                is_basic_transformation=True, autogenerated=True)
        return

    # add to relevant places
    cls._basic_transformations |= {name}
    cls._args[name] = set()
    cls._arg_of[name] = set()
    cls._downstream[name] = set()

    if is_constant:
        cls._reserved_names[name] = Constant

    if not is_constant:
        cls._reserved_names[name] = ModelParameter
        cls._initial_values[name] = initial_val

        def param_getter(self):
            return self.parameters[name]
        def param_setter(self, val):
            return self.set_par(name, val)
        setattr(cls, name, property(param_getter, param_setter, doc='model parameter'))

    _add_default_transformations(cls, name, term_of=term_of)

    if prior:
        _add_derived_quantity(cls, name='prior_'+name, func=prior, arg_names=[name], term_of=('Prior', ), is_basic_transformation=False)


def _add_default_transformations(cls, name, term_of=()):
    if name.startswith('log_'):
        _add_derived_quantity(cls, name=name[4:], arg_names=[name], func=exp, autogenerated=True)

    if name.startswith('logit_'):
        _add_derived_quantity(cls, name=name[6:], arg_names=[name], func=logistic, autogenerated=True)

    #if name.startswith('derof_'):
     #   _add_derived_quantity(cls, name=name[6:], arg_names=[name], func=cumsumzero, autogenerated=True)

    # termsof_ and term_of are exclusive
    if name.startswith('termsof_'):
        _add_derived_quantity(cls, name=name[8:], arg_names=[name], func=_fastest_sum, term_of=term_of, autogenerated=True)
        term_of = ()

    for accumulator in term_of:
        cls._accumulators[accumulator] = all_terms = cls._accumulators.get(accumulator, []) + [name]
        _add_derived_quantity(cls, name=accumulator, arg_names=all_terms, func=_arg_sum, autogenerated=True)


def _add_derived_quantity(cls, name, func, arg_names, is_basic_transformation=None, term_of=(), autogenerated=False, redeclare=False, _rename=None):
    # apply rename
    if _rename:
        a, b = _rename
        name = name.replace(a, b)
        arg_names = [arg.replace(a, b) for arg in arg_names]
        term_of = [accumulator.replace(a, b) for accumulator in term_of]

    # check for indexers
    substr, indexer = _find_indexer(cls, name)
    if indexer:
        # declare different things instead
        for i in indexer.indxs:
            _add_derived_quantity(
                cls, name, func=func, arg_names=arg_names,
                is_basic_transformation=is_basic_transformation, autogenerated=autogenerated,
                term_of=term_of, _rename=(substr, i))
        if indexer.combine:
            _add_derived_quantity(
                cls, name.replace(substr, indexer.combine), func=_mirror, arg_names=[name.replace(substr, i) for i in indexer.indxs],
                is_basic_transformation=is_basic_transformation, autogenerated=True,
                term_of=())
        return

    # check if derived quantity can be created
    if name in cls._reserved_names:
        if cls._reserved_names[name] == ModelParameter:
            raise KeyError(f'derived quantity {name} already declared as a parameter')
        if cls._reserved_names[name] == Constant:
            raise KeyError(f'derived quantity {name} already declared as a Constant')
        if cls._reserved_names[name] == _DerivedQuantity and not redeclare:
            raise KeyError(f'derived quantity {name} already declared')
        if not set(cls._args[name]).issubset(arg_names):
            raise KeyError(f'While redeclaring {name}, {set(cls._args[name])-set(arg_names)} was lost from arguments; Redaclaration is impossible')
        # delete the name and add it back, for order of operations to look better
        del cls._reserved_names[name]

    for arg in arg_names:
        if arg not in cls._reserved_names:
            raise KeyError(f'parameter or derived quantity "{arg}", used to declare "{name}" is not declared')

    # add derived quantity's name where necessary
    cls._reserved_names[name] = _AutogeneratedDQ if autogenerated else _DerivedQuantity
    cls._derived_quantities |= {name}

    # check if basic transformation is applicable   # do wo need these? probaby not
    if is_basic_transformation:
        if not (cls._basic_transformations).issuperset(arg_names):
            raise KeyError(f'basic transformation {name} can only depend on parameters and other basic transformations' +
                           f' ({set(arg_names) - cls._basic_transformations} is not)')
    elif is_basic_transformation is None:
        is_basic_transformation = cls._basic_transformations.issuperset(arg_names)

    if is_basic_transformation:
        cls._basic_transformations |= {name}
    else:
        cls._basic_transformations -= {name}

    # append dependency graph
    cls._downstream[name] = cls._downstream.get(name, set())
    cls._args[name] = arg_names
    cls._arg_of[name] = set()
    for k in arg_names: cls._arg_of[k] |= {name}
    _declare_dependency(cls, arg_names, {name} | cls._downstream[name])

    # lazy computer version is different if profiler is on
    if _PROFILING:
        # n calls; n calls when recomputed; time total; local time; arg collection time
        _PROFILING_RESULTS[name] = {
            'total_calls': 0,
            'total_time': CumulativeStopwatch(),
            'recompute_calls': 0,
            'recompute_time': CumulativeStopwatch(),
            'arguments_time': CumulativeStopwatch()}
        print(f'Declaring derived quantity {name}{arg_names}')

        def lazy_computer(self):
            # re-compute values if needed
            with _PROFILING_RESULTS[name]['total_time']:
                if self._computed[name] is NotComputed:
                    with _PROFILING_RESULTS[name]['arguments_time']:
                        args = [getattr(self, key) for key in arg_names]

                    with _PROFILING_RESULTS[name]['recompute_time']:
                        self._computed[name] = func(*args)

                    _PROFILING_RESULTS[name]['recompute_calls'] += 1

            _PROFILING_RESULTS[name]['total_calls'] += 1

            return self._computed[name]

    else:

        def lazy_computer(self):
            # re-compute values if needed
            if self._computed[name] is NotComputed:
                args = [getattr(self, key) for key in arg_names]
                self._computed[name] = func(*args)
            return self._computed[name]

    lazy_computer.args = lambda x: [getattr(self, key) for key in arg_names]
    setattr(cls, name, property(lazy_computer))

    # define arg lister
    def arg_lister(self):
        return {k: self._computed[k] if k in self._computed else getattr(self, k) for k in arg_names}
    setattr(cls, name+'_list_args', arg_lister)

    # autogenerate extra functions
    _add_default_transformations(cls, name, term_of=term_of)


def _declare_dependency(cls, upstream, new_dependency):
    # go up the graph of dependency
    for key in upstream:
        cls._downstream[key] |= new_dependency
        _declare_dependency(cls, cls._args[key], new_dependency)

def _find_indexer(cls, name):
    for k, v in cls._indexers.items():
        if k in name: return k, v
    return None, None


########################
## Model class itself ##
########################


class Model():
    _indexers_declarations = {}
    _par_declarations = {}
    _dq_declarations = {}

    def __init_subclass__(cls):

        # Variables to define the model structure
        cls._reserved_names = {}
        cls._initial_values = {}
        cls._derived_quantities = set()
        cls._downstream = {}
        cls._args = {}
        cls._arg_of = {}
        cls._basic_transformations = set()
        cls._accumulators = {}
        cls._indexers = {}

        # we need to keep this for inheretence to work
        cls._indexers_declarations = cls._indexers_declarations.copy()
        cls._par_declarations = cls._par_declarations.copy()
        cls._dq_declarations = cls._dq_declarations.copy()

        # declare parameters and indexers
        if hasattr(cls, '__annotations__'):
            for k, ann in cls.__annotations__.items():
                if isinstance(ann, Indexer):
                    cls._indexers_declarations[k] = ann

                elif isinstance(ann, Submodel):
                    submodel = getattr(cls, k)
                    a, b = ann.rename if ann.rename else ('', '')
                    for sk, sargs in submodel._par_declarations.items():
                        sargs = sargs.copy()
                        if 'term_of' in sargs:
                            sargs['term_of'] = [x.replace(a, b).replace('OUTPUT', k) for x in sargs['term_of']]
                        cls._par_declarations[sk.replace(a, b)] = sargs
                    for sk, sargs in submodel._dq_declarations.items():
                        sargs = sargs.copy()
                        sargs['arg_names'] = [x.replace(a, b) for x in sargs['arg_names']]
                        if 'term_of' in sargs:
                            sargs['term_of'] = [x.replace(a, b).replace('OUTPUT', k) for x in sargs['term_of']]
                        cls._dq_declarations[sk.replace(a, b)] = sargs

                    if 'OUTPUT' in submodel._dq_declarations:
                        output_kwargs = submodel._dq_declarations['OUTPUT'].copy()
                        output_kwargs |= ann.kwargs
                        output_kwargs['arg_names'] = [x.replace(a, b) for x in output_kwargs['arg_names']]
                        cls._dq_declarations[k] = output_kwargs
                        del cls._dq_declarations['OUTPUT']

                elif ann == 'constant' or ann is Constant:
                    cls._par_declarations[k] = {'initial_val': getattr(cls, k), 'is_constant': True}

                elif ann == 'free parameter' or ann is ModelParameter:
                    cls._par_declarations[k] = {'initial_val': getattr(cls, k)}
                elif isinstance(ann, ModelParameter):
                    cls._par_declarations[k] = {'initial_val': getattr(cls, k), **ann.kwargs}
                elif callable(ann):
                    cls._par_declarations[k] = {'initial_val': getattr(cls, k), 'prior': ann}
                else:
                    raise Exception(f'Unknown annotation {ann} for {k}')

        for k, f in cls.__dict__.items():
            if hasattr(f, '__is_derived_quantity__') and f.__is_derived_quantity__:
                cls._dq_declarations[k] = {'func':f, **f.__derived_quantity_kwargs__}

        # declare indexers
        for k, indexer in cls._indexers_declarations.items():
            _add_indexer(cls, k, indexer)

        # declare parameters
        for k, kwargs in cls._par_declarations.items():
            _add_parameter(cls, k, **kwargs)

        # declare derived quantities
        for k, kwargs in cls._dq_declarations.items():
            _add_derived_quantity(cls, name=k, **kwargs)

        # add Posterior if either prior or likelihood is declared
        if 'Prior' in cls._accumulators or 'Likelihood' in cls._accumulators:
            if 'Prior' not in cls._reserved_names:
                _add_derived_quantity(cls, name='Prior', func=_zero, arg_names=[], autogenerated=True)
            if 'Likelihood' not in cls._reserved_names:
                _add_derived_quantity(cls, name='Likelihood', func=_zero, arg_names=[], autogenerated=True)
            _add_derived_quantity(cls, name='Posterior',  func=_Posterior, arg_names=['Prior', 'Likelihood'], autogenerated=True)

        # sort derivered qunatities for a better presentation
        structure = []
        to_sort = list(cls._reserved_names)
        while to_sort:
            k, *to_sort = to_sort
            structure.append(k)
            moved = []
            #for kk in cls._arg_of[k]:
                #if len(cls._args[kk]) == 1 and kk in to_sort:
                    #i = to_sort.index(kk)
                    #to_sort = to_sort[:i] + to_sort[i+1:]
                    #moved.append(kk)
                #elif len(cls._args[kk]) > len(cls._arg_of[kk]) and kk in to_sort:
                    #i = to_sort.index(kk)
                    #to_sort = [kk] + to_sort[:i] + to_sort[i+1:]
            #moved.sort(key=lambda k: len(cls._args[k]))
            #to_sort = moved + to_sort

            for kk in to_sort:
                if kk in cls._arg_of[k] and set(cls._args[kk]).issubset(structure):
                    moved.append(kk)
            #moved.sort(key=lambda k: (len(cls._args[k]), -len(cls._downstream[k])))
            moved.sort(key=lambda k: len(cls._args[k]))
            to_sort = moved + [kk for kk in to_sort if kk not in moved]

        structure, to_sort = [], structure[::-1]
        while to_sort:
            k, *to_sort = to_sort
            structure.append(k)
            moved = []
            for kk in to_sort:
                if kk in cls._args[k] and cls._arg_of[kk].issubset(structure):
                    moved.append(kk)
            moved.sort(key=lambda k: len(cls._arg_of[k]))
            to_sort = moved + [kk for kk in to_sort if kk not in moved]

        structure = structure[::-1]


        #to_sort = [(len(cls._args[k]), len(cls._arg_of[k]), k) for k in cls._reserved_names]
        #while to_sort:
            #to_sort.sort(key=lambda x: x[0:2])  # sort only according to weight
            #(_, _, cur), *to_sort = to_sort
            #structure.append(cur)
            #to_sort = [(v - int(k in cls._arg_of[cur]), w, k) for v, w, k in to_sort]

        cls._reserved_names = {k: cls._reserved_names[k] for k in structure}
        cls._structure = structure


    def __init__(self, **setters):
        self.parameters = copy.deepcopy(self._initial_values)
        self.clear()
        for k, v in setters.items():
            setattr(self, k, v)

    #########################
    ## changing parameters ##
    #########################

    def clear(self):
        """ Drop all precomputed values """
        self._computed = {k: NotComputed for k in self._derived_quantities}

    def copy(self, other=None):
        """ Return a copy of oneself, or copies a different instance of the same class """
        if other is None:
            other = self.__class__()
            other.copy(self)
            return other
        else:
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
            self._computed[key] = NotComputed

    def do_intervention(self, name, val):
        """
        Change the one computed value to the given value; Reset all the values downstread from it.
        """
        self._computed[name] = val
        for key in self._downstream[name]:
            self._computed[key] = NotComputed

    def measure_derivative(self, par, target, epsilon=0.0001):
        cp = self.copy()
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

    def get_values(self, params):
        """ Return values of multiple parameters as a flat list """
        result = []
        for par in params:
            val = getattr(self, par)
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
                if isinstance(target, (ndarray, list)):
                    target[:], values = values[: len(target)], values[len(target):]
                else:
                    self.parameters[par], values = values[0], values[1:]

            for key in self._downstream[par]:
                self._computed[key] = NotComputed


    ######################
    ## helper functions ##
    ######################

    def structure(self):
        """ Print out all the derived quantities """
        s = {}
        for key, t in self._reserved_names.items():
            if t == ModelParameter:
                s[key] = None
            elif t == Constant:
                pass
            elif t == _DerivedQuantity:
                s[key] = tuple(self._args[key])
            elif t == _AutogeneratedDQ:
                s['*'+key] = tuple(self._args[key])
        return s

    def print_structure(self):
        print('\n'.join((k if v is None else f'{k}{v}') + f' -> {", ".join(n for n, us in self._args.items() if k.replace("*", "") in us)}' for k, v in self.structure().items()))
    def print_dependencies(self):
        print('\n'.join(f'{k} -> {sorted(v)}' for k, v in self._downstream))

    def get_structure(self, show_constants=False, mark_autogenerated=True):
        def name(k):
            return ('*' if (mark_autogenerated and self._reserved_names[k] is _AutogeneratedDQ) else '') + k

        if show_constants:
            return {
                name(k): ([name(kk) for kk in self._args[k]], [name(kk) for kk in self._arg_of[k]])
                for k, t in self._reserved_names.items()}
        else:
            return {
                name(k): ([name(kk) for kk in self._args[k] if self._reserved_names[kk] is not Constant], [name(kk) for kk in self._arg_of[k]])
                for k, t in self._reserved_names.items() if t is not Constant}


    def draw_structure(self, to_print=True):
        output = []
        structure = self.structure()
        nums = {}
        j = 0

        BOLD_SYMBOLS = {'|': '\u2503', '-': '\u2501', '-|': '\u252B', '+': '\u254B', '-.':'\u2513', 'T':'\u2533', 'r':'\u250F', '-^':'\u251B'}
        THIN_SYMBOLS = {'|': '\u2502', '-': '\u2500', '-|': '\u2524', '+': '\u253C', '-.':'\u2510', 'T':'\u252C', 'r':'\u250C', '-^':'\u2518'}
        UD = THIN_SYMBOLS
        for key, dep in structure.items():
            if dep:
                dep = list(sorted(dep, key=lambda k: nums[k]))
                i = nums[dep[0]]
                m = max(len(s) for s in output[i:j])+1
                for k in range(i, j):
                    output[k] = output[k] + ' '*(m-len(output[k])) + UD['|']
                for x in dep:
                    k = nums[x]
                    output[k] = output[k].replace(' ', UD['-']).replace(UD['-|'], UD['+']).replace(UD['-.'], UD['T'])
                    output[k] = output[k][:-1] + UD['-|']
                output[i] = output[i][:-1] + UD['-.']

                mi = min(len(key)//2, m-1)
                output.append(' '*mi + UD['r'] + UD['-']*(m-mi-1) +UD['-^'])
                j += 1
            output.append(key)
            nums[key.replace('*', '')] = j
            j += 1

        if to_print:
            print('\n'.join(output))
        else:
            return '\n'.join(output)

    def draw_structure(self, to_print=True):
        output = []
        structure = self.structure()
        nums = {}
        groups = []
        leaves = {}

        BOLD_SYMBOLS = {'|': '\u2503', '-': '\u2501', '-|': '\u252B', '+': '\u254B', '-.':'\u2513', 'T':'\u2533', 'r':'\u250F', '-^':'\u251B'}
        THIN_SYMBOLS = {'|': '\u2502', '-': '\u2500', '-|': '\u2524', '+': '\u253C', '-.':'\u2510', 'T':'\u252C', 'r':'\u250C', '-^':'\u2518'}
        UD = BOLD_SYMBOLS

        for key, dep in structure.items():
            nkey = key.replace('*', '')
            j = len(output)
            if dep:
                if len(dep) == 1:
                    k = nums[dep[0]]
                    if self._downstream[dep[0]] == self._downstream[nkey] | {nkey}:
                        output[k] += UD['-']*2 + key
                        nums[nkey] = k
                        continue
                    elif not self._downstream[nkey]:
                        leaves[k] = leaves.get(k, []) + [key]
                        continue
                output.append('.'*(len(key)//2) + UD['r'])
                groups.append([nums[k] for k in dep]+[j])
                j += 1
            output.append(key)
            nums[nkey] = j

        #groups2 = []
        #groups3 = []
        #while groups:
            #groups2, groups = groups[:], []
            #i = -1
            #while groups2:
                #cur, *groups2 = groups2
                #if min(cur) > i:
                    #groups3.append(cur)
                    #i = max(cur)
                #else:
                    #groups.append(cur)
        #groups = groups3

        for dep in groups:
            i, j = min(dep), max(dep)
            m = max(len(s) for s in output[i:j+1])+1
            for k in range(i, j+1):
                output[k] = output[k] + ' '*(m-len(output[k])) + UD['|']
            for k in dep:
                output[k] = output[k].replace(' ', UD['-']).replace(UD['-|'], UD['+']).replace(UD['-.'], UD['T'])
                output[k] = output[k][:-1] + UD['-|']
            output[i] = output[i][:-1] + UD['-.']
            output[j] = output[j][:-1] + UD['-^']

        for k, deps in leaves.items():
            output[k] = output[k].replace(UD['-|'], UD['+']).replace(UD['-.'], UD['T']).replace(UD['-.'], UD['T']) + UD['-']*2 + ', '.join(deps)

        for i in range(len(output)):
            output[i] = output[i].replace('.', ' ')

        if to_print:
            print('\n'.join(output))
        else:
            return '\n'.join(output)


    def draw_structure(self, to_print=True):
        output = []
        order = {}

        BOLD_SYMBOLS = {'|': '\u2503', '-': '\u2501', '-|': '\u252B', '+': '\u254B', '-.':'\u2513', 'T':'\u2533', 'r':'\u250F', '-^':'\u251B', 'L':'\u2517', '|-':'\u2523', '-^-':'\u253B'}
        THIN_SYMBOLS = {'|': '\u2502', '-': '\u2500', '-|': '\u2524', '+': '\u253C', '-.':'\u2510', 'T':'\u252C', 'r':'\u250C', '-^':'\u2518', 'L':'\u2514', '|-':'\u251C', '-^-':'\u2534'}
        UD = BOLD_SYMBOLS

        for j, (key, (args, arg_of)) in enumerate(self.get_structure().items()):
            output.append([' ']*j*2 + [key])
            order[key] = j
            for x in args:
                k = order[x]
                output[j][k*2] = output[j][k*2].replace(UD['-'], UD['-^-']).replace(' ', UD['L'])
                for l in range(k*2+1, j*2): output[j][l] = output[j][l].replace(' ', UD['-']).replace(UD['L'], UD['-^-'])
                for l in range(k, j): output[l][k*2] = output[l][k*2].replace(' ', UD['|']).replace(UD['L'], UD['|-']).replace(UD['-'], UD['|']).replace(UD['-^-'], UD['+'])

        print('\n'.join(''.join(line) for line in output))



    def parameters_with_prior(self):
        """ List all parameters with prior defined """
        return [p for p in self.parameters if any(dq in self._accumulators['Prior'] for dq in self._downstream[p])]
    def basic_transformations(self):
        """ Return the dictionary with all the parameters and basic transformations """
        return {key: getattr(self, key) for key in self._basic_transformations}
    def transformed_pars(self):
        """ Return the dictionary with all the basic transformations """
        return {key: getattr(self, key) for key in self._basic_transformations if key in self._computed}
    def priors(self):
        return {key: getattr(self, key) for key in self._accumulators['Prior']}
    def likelihood_factors(self):
        return {key: getattr(self, key) for key in self._accumulators['Likelihood']}



class Model2(Model):
    def __init__(self, **setters):
        super().__init__(**setters)
        self.drop_records()
        self._batch_getters = {}
        self._batch_setters = {}
        self._batch_n = {}

    def load(self, other):
        super().load(other)
        self.drop_records()

    def drop_records(self):
        self._saved_parameters = {}
        self._saved_computed = {}

    def set_par(self, par, val):
        """
        Set a value of one parameter.
        If parameter is scalar, par is the name of the parameter.
        If parameter is vector, par is either the name of the parameter (in this case whole vector is set), or a tuple (name, index)
        (in this case single value from the vector is set).
        """
        self.drop_records()
        if isinstance(par, tuple):
            par, index = par
            self._saved_parameters[par] = copy.deepcopy(self.parameters[par])
            self.parameters[par][index] = val
        else:
            self._saved_parameters[par] = copy.deepcopy(self.parameters[par])
            self.parameters[par] = val
        for key in self._downstream[par]:
            self._saved_computed[key], self._computed[key] = self._computed[key], NotComputed

    def do_intervention(self, name, val):
        """
        Change the one computed value to the given value; Reset all the values downstread from it.
        """
        self._saved_computed[name] = copy.deepcopy(self._computed[name])
        self._computed[name] = val
        for key in self._downstream[name]:
            self._saved_computed[key], self._computed[key] = self._computed[key], NotComputed


    def flatten_names(self, names):
        if isinstance(names, str):
            names = [names]
        f = []
        for n in names:
            x = self.get_par(n)
            try:
                l = len(x)
                f.extend((n, i) for i in range(l))
            except:
                f.append(n)
        return f

    def measure_derivative(self, par, target, epsilon=0.0001):
        if not isinstance(target, (list, tuple)):
            target = [target]
        old = array(self.get_values(target))
        if not isinstance(par, (list, tuple)):
            par = [par]
        val = array(self.get_params(par), dtype=float)
        val += epsilon
        self.set_params(par, val)

        derivative = (self.get_values(target) - old)/epsilon
        self.reverse_change()
        return derivative

    def measure_hessian(self, pars, target, epsilon=0.001):
        pars = self.flatten_names(pars)
        hess = array([[0.0]*len(pars) for _ in pars])
        first_dirs = [self.measure_derivative([p], target, epsilon=epsilon) for p in pars]
        for i, p1 in enumerate(pars):
            d1 = first_dirs[i]
            d2 = self.measure_derivative([p1], target, epsilon=-epsilon)
            hess[i, i] = (d1-d2) / epsilon
            for j, p2 in enumerate(pars[:i]):
                d2 = first_dirs[j]
                d3 = self.measure_derivative([p1, p2], target, epsilon=epsilon)
                hess[i, j] = hess[j, i] = (d3-d2-d1) / epsilon
        return hess

    def set_params(self, params, values):
        """
        Set values for multiple parameters.
        Values should be a flat list: items would be distributed among parameters according to their size
        """
        self.drop_records()

        pars_to_change = set()
        for par in params:
            if isinstance(par, tuple):
                par, index = par
                pars_to_change.add(par)
            else:
                pars_to_change.add(par)

        for par in pars_to_change:
            self._saved_parameters[par] = copy.deepcopy(self.parameters[par])

        for par in params:
            if isinstance(par, tuple):
                par, index = par
                self.parameters[par][index], values = values[0], values[1:]
            else:
                target = self.parameters[par]
                if isinstance(target, (ndarray, list)):
                    target[:], values = values[: len(target)], values[len(target):]
                else:
                    self.parameters[par], values = values[0], values[1:]

        dq_to_save = set()
        for par in pars_to_change:
            dq_to_save |= self._downstream[par]
        for key in dq_to_save:
            self._saved_computed[key], self._computed[key] = self._computed[key], NotComputed

    def reverse_change(self):
        self.parameters.update(self._saved_parameters)
        self._computed.update(self._saved_computed)
        self.drop_records()

    def measure_change(self, name):
        return getattr(self, name) - self._saved_computed[name]


    def define_batch(self, params):
        # special case: batch has a single parameter
        if len(params) == 1 and len(params[0]) == 1:
            name = params[0]
            self._batch_getters[params] = lambda: [self.parameters[name]]
            self._batch_setters[params] = lambda val: self.set_par(name, val)
            try:
                self._batch_n = len(self.parameters[name])
            except:
                self._batch_n = 1
            return

        pars_to_copy = set()
        pars_to_deepcopy = set()
        dq_to_copy = set()

        for par in params:
            if isinstance(par, tuple):
                par, index = par
                pars_to_deepcopy.add(par)
            else:
                pars_to_copy.add(par)
        for par in pars_to_copy | pars_to_deepcopy:
            dq_to_save |= self._downstream[par]

        is_whole = []
        lengths = []
        for par in params:
            if isinstance(par, tuple):
                is_whole.append(False)
                lengths.append(None)
            else:
                is_whole.append(True)
                if isinstance(self.parameters[par], (ndarray, list)):
                    lengths.append(self.parameters[par])
                else:
                    lengths.append(None)

        def batch_setter(self):
            for par in pars_to_copy:
                self._saved_parameters[par] = self.parameters[par]
            for par in pars_to_copy:
                self._saved_parameters[par] = copy.deepcopy(self.parameters[par])
            for key in dq_to_copy:
                self._saved_computed[key], self._computed[key] = self._computed[key], NotComputed

            for par, w, l in zip(params, is_whole, lengths):
                if w:
                    if l is None:
                        self.parameters[par], values = values[0], values[1:]
                    else:
                        self.parameters[par], values = values[: n], values[n:]
                else:
                    self.parameters[par[0]][par[1]], values = values[0], values[1:]

        self._batch_getters[params] = lambda: self.get_params(params)
        self._batch_setters[params] = batch_setter
        self._batch_n = sum(1 if l is None else l for l in lengths)

    def get_batch(self, name):
        return self._batch_getters[name]()
    def set_batch(self, name, vals):
        self._batch_setters[name](vals)
    def get_batch_n(self, name):
        return self._batch_n[name]


if __name__ == '__main__':
    class MyModel(Model):
        _I: Indexer(['_1', '_2'], combine='_i')
        _J: Indexer(['_A', '_B'], combine='_j')
        par_I_J: ModelParameter = 1

        @prior
        def dq_I_J(par_I_J):
            return par_I_J*10

    m = MyModel()
    m.draw_structure()

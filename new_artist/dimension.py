import math
from copy import copy

from new_artist.color import Color, basic_color_sequence
from new_artist.mapping import CoordinateMapping, LinearMapping
from new_artist.mapping import MAPPINGS_LIBRARY
from new_artist.base import VERY_LARGE_NUMBER, Number

from typing import List, Tuple  # *** remove when updating


class AbstractDimension:

    mapping: CoordinateMapping

    def __init__(self, name, settings=None):
        self._dim_name = name

        self.data_domain = []
        self._assigned_min = None
        self._assigned_max = None
        self._assigned_size = None

        self.mapping = LinearMapping()
        self._scale = 1
        self._shift = 0
        self._singular_value = False
        self.pixel_min = None
        self.pixel_max = None

        if isinstance(settings, dict):
            self.set(**settings)
        elif isinstance(settings, (tuple, list)):
            self.fit(*settings)
        elif settings:
            self.fit(settings)
        else:
            self._calibrate()

    @property
    def k(self): return self._scale
    @k.setter
    def k(self, value):
        self._scale = value
        self.assigned_size = None
        self._calibrate()

    @property
    def assigned_min(self): return self._assigned_min
    @assigned_min.setter
    def assigned_min(self, value):
        self._assigned_min = value
        self._calibrate()

    @property
    def assigned_max(self): return self._assigned_max
    @assigned_max.setter
    def assigned_max(self, value):
        self._assigned_max = value
        self._calibrate()

    @property
    def assigned_size(self): return self._assigned_size
    @assigned_size.setter
    def assigned_size(self, value):
        self._assigned_size = value
        self._calibrate()

    @property
    def assigned_domain(self):
        return [self._assigned_min, self._assigned_max]

    @property
    def data_min(self): return self.data_domain[0] if self.data_domain else None
    @property
    def data_max(self): return self.data_domain[-1] if self.data_domain else None

    @property
    def displayed_min(self): return self._assigned_min if self._assigned_min is not None else self.data_min
    @property
    def displayed_max(self): return self._assigned_max if self._assigned_max is not None else self.data_max
    @property
    def displayed_domain(self):
        return [self.displayed_min, self.displayed_max]


    def _calibrate(self):
        """ abstract """
        pass
    def __call__(self, x):
        """ abstract """
        pass
    def transform(self, X: list) -> List[int]:
        return [self(x) for x in X]


    def get_domain(self, X: list) -> List:
        domain = set()
        for x in X:
            try:
                val = self.mapping.to_value(x)
                int(val)
                domain.add((val, x))
            except Exception as e:
                try:
                    self(x)
                except:
                    raise TypeError(f'Wrong datatype given to dimension {self._dim_name}. Failed to convert {x!r} with mapping {self.mapping}\n') from e
        if not domain:
            return []
        elif len(domain) == 1:
            return [next(iter(domain))[1]]
        else:
            return [min(domain)[1], max(domain)[1]]

    def add_to_domain(self, new:list):
        if new:
            self.data_domain = self.get_domain(self.data_domain + new)
            self.check_type(self.data_domain)
            self._calibrate()

    def check_type(self, values):
        for x in values:
            try:
                self(x)
            except Exception as e:
                raise TypeError(f'Wrong datatype given to dimension {self._dim_name}. Failed to convert {x!r} with mapping {self.mapping}\n') from e

    def set(self, mapping=None, *, k=..., min=..., max=..., size=Ellipsis, **mapping_kwargs):
        if mapping is not None:
            self.mapping = MAPPINGS_LIBRARY[mapping](**mapping_kwargs)
            self.check_type(self.data_domain)

        if k is not Ellipsis and size is not Ellipsis:
            raise TypeError('.fit() got both k and size arguments. Only one can be given.')
        elif k is not Ellipsis:
            self._assigned_size = None
            self._scale = k
        elif size is not Ellipsis:
            self._assigned_size = size
        if min is not Ellipsis: self._assigned_min = min
        if max is not Ellipsis: self._assigned_max = max
        self._calibrate()


class PixelDimension(AbstractDimension):

    def __call__(self, x) -> int:   #*** or None
        """
        Convert given value into number of pixels.
        """
        try:
            y = self.mapping.to_value(x) * self._scale + self._shift
        except:
            # tranformation [data --> value] failed.
            if x is None:
                return None
            raise TypeError(f'Failed to process {x!r} with {self.mapping}')

        try:
            return int(round(y))
        except:
            # tranformation [value --> pixel] failed.
            if isinstance(y, float):
                if math.isnan(y):
                    return None
                elif y == float('-inf'):
                    return -VERY_LARGE_NUMBER
                elif y == float('inf'):
                    return +VERY_LARGE_NUMBER
            raise TypeError(f'Failed to convert {y!r} (recieved from {x!r} with {self.mapping}) to int')


    def _calibrate(self):
        """ Define pixel dimensions """
        a, b = self.displayed_domain
        if a is None or b is None:
            # pixel domain is undefined
            self.pixel_max = self.pixel_min = 0
            return

        size = self._assigned_size
        if size is None:
            # shift may need adjustment
            # leave scale as it is
            val_a = self.mapping.to_value(a)
            self._shift = -val_a * self._scale
        else:
            # shift and scale may need adjustment
            val_a = self.mapping.to_value(a)
            val_b = self.mapping.to_value(b)

            if val_a == val_b:
                # special case
                self._singular_value = True
                self._scale = 0
                self.pixel_min, self.pixel_max = 0, size-1
                self._shift = int(size / 2)
                return

            if size < 2:
                size = self._assigned_size = 2

            self._scale = (size-1) / (val_b - val_a)
            self._shift = -val_a * self._scale

        self._singular_value = False
        self.pixel_min, self.pixel_max = sorted([self(a), self(b)])


    @property
    def pixel_domain(self):
        return [self.pixel_min, self.pixel_max]
    @property
    def current_pixel_size(self):
        return abs(self.pixel_max - self.pixel_min) + 1


    def bounded_min(self, X: list) -> int:
        m = min(self(x) for x in X)
        if self._assigned_min is not None and self._assigned_max is not None:   # *** too wordly?
            return min(self.pixel_max, max(self.pixel_min, m))
        if self._assigned_min is not None:
            return max(self.pixel_min, m)
        elif self._assigned_max is not None:
            return min(self.pixel_max, m)
        else:
            return m

    def bounded_max(self, X: list) -> int:
        m = max(self(x) for x in X)
        if self._assigned_min is not None and self._assigned_max is not None:   # *** too wordly?
            return min(self.pixel_max, max(self.pixel_min, m))
        if self._assigned_max is not None:
            return min(self.pixel_max, m)
        elif self._assigned_min is not None:
            return max(self.pixel_min, m)
        else:
            return m


    def fit(self, *args, **mapping_kwargs):
        # move arguments
        #*** use pattern matching  when moving to 3.10+
        if len(args) and isinstance(args[0], str):
            mapping_name, *args = args
            self.mapping = MAPPINGS_LIBRARY[mapping_name](**mapping_kwargs)
            self.check_type(self.data_domain)
        elif mapping_kwargs:
            raise Exception('Mapping kwargs are given to .fit(), but no mapping type provided')

        if len(args) == 3:
            a, b, size = args
            self._assigned_min = a
            self._assigned_max = b
            self._assigned_size = max(1, size)
        elif len(args) == 2:
            a, b = args
            self._assigned_min = a
            self._assigned_max = b
        elif len(args) == 1:
            size = args[0]
            self._assigned_size = max(1, size)
        elif len(args) == 0:
            pass
        else:
            raise AttributeError(f'Wrong number of arguments in .fit(). {len(args)} recieved, 0-3 required.')

        # fit to the constrains
        self._calibrate()


    def get_ticks(self, min_interval, defaults=None, multiline=False) -> dict:
        mapping = self.mapping

        a, b = self.displayed_domain
        A, B = self.pixel_domain
        if a is None or b is None:
            raise TypeError(f'Cannot get ticks for dimension {self._dim_name}, as some bound are undefined: min={a}, max={b}')

        if self._singular_value:
            return {self._shift: self.mapping.to_label(a, min_interval=0, multiline=multiline, leading=True)}

        if isinstance(defaults, dict):
            # ticks positions are labels are given
            ticks = {self(x): label for x, label in defaults.items()}
            # check that all ticks are in the domain
            return {p: label for p, label in ticks.items() if A <= p <= B}

        scale = min_interval / abs(self._scale)
        if defaults is not None:
            # ticks position are given
            # make labels for them
            labelled_coords, unlabelled_coords = defaults, {}
        else:
            # nothing is given
            # get ticks
            labelled_coords, unlabelled_coords = mapping.propose_ticks(a, b, scale)

        # process ticks
        # convert coordinates into pixels
        unlabelled_ticks = {self(x) for x in unlabelled_coords}
        labelled_ticks = {self(x): x for x in labelled_coords}

        # drop all ticks outside given range
        unlabelled_ticks = {p: None for p in unlabelled_ticks if A <= p <= B}
        labelled_ticks = {p: x for p, x in labelled_ticks.items() if A <= p <= B}

        # create labels
        leading_p = min(labelled_ticks.keys(), default=None)
        labelled_ticks = {p: mapping.to_label(x, min_interval=scale, multiline=multiline, leading=(p==leading_p)) for p, x in labelled_ticks.items()}

        # merge
        ticks = {**unlabelled_ticks, **labelled_ticks}  # *** use + operator after moving to 3.9

        return ticks

    def __str__(self):
        a, b = self.displayed_domain
        if a == b:
            return f'{self.mapping}[{"" if a is None else a}]->{self.current_pixel_size}'
        else:
            return f'{self.mapping}[{a}:{b}]->{self.current_pixel_size}'

    def __repr__(self):
        return f'Dimension {self._dim_name} ({self.mapping}, data={self.data_domain}, borders={self.assigned_domain}, size={self.current_pixel_size}, k={self._scale}, shift={self._shift})'



class ColorDimension(AbstractDimension):

    def __init__(self, name, settings=None):
        self._assigned_shift = 0
        self.grad = 'basic_color_sequence'
        super().__init__(name, settings=settings)

    @property
    def shift(self): return self._assigned_shift
    @shift.setter
    def shift(self, value):
        self._assigned_shift = value
        self._calibrate()


    def val_to_color(self, y) -> Color:   #*** or None
        grad = self.grad

        if isinstance(grad, str):
            return Color.from_function(grad, y)
        elif grad is None:
            return basic_color_sequence(y)
        else:
            return Color(grad(y))

    def __call__(self, x) -> Color:   #*** or None
        """
        Convert given value into a Color.
        """
        try:
            y = self.mapping.to_value(x) * self._scale + self._shift
        except:
            # tranformation [data --> value] failed.
            # try transforming to color directly
            try:
                return Color(x)
            except:
                raise TypeError(f'Failed to process {x!r} with {self.mapping}; it is also not a Color')

        try:
            return self.val_to_color(y)
        except:
            # tranformation [value --> color] failed.
            if isinstance(y, float) and math.isnan(y):
                return None
            raise TypeError(f'Failed to convert {y!r} (recieved from {x!r} with {self.mapping}) to Color with grad={self.grad}')


    def _calibrate(self):
        """ Define pixel dimensions """
        a, b = self.displayed_domain
        if a is None or b is None:
            # pixel domain is undefined
            self.color_val_max = self.color_val_min = 1
            self._shift = self._assigned_shift
            return

        size = self._assigned_size
        shift = self._assigned_shift
        if size is not None:
            # shift and scale may need adjustment
            val_a = self.mapping.to_value(a)
            val_b = self.mapping.to_value(b)

            if val_a == val_b:
                self._singular_value = True
                self._scale = 0
                self.color_val_min = shift
                self._shift        = shift + size/2
                self.color_val_max = shift + size
                return

            self._scale = size / (val_b - val_a)
            self._shift = shift - val_a * self._scale
        else:
            self._shift = shift

        self._singular_value = False
        self.color_val_min = self.mapping.to_value(a) * self._scale + self._shift
        self.color_val_max = self.mapping.to_value(b) * self._scale + self._shift

    @property
    def color_val_domain(self):
        return [self.color_val_min, self.color_val_max]
    @property
    def color_min(self):
        return self._to_color(self.color_val_min)
    @property
    def color_max(self):
        return self._to_color(self.color_val_max)

    def fit(self, *args, grad=None, **mapping_kwargs):
        # move arguments
        # *** use pattern matching  when moving to 3.10+
        if grad is not None:
            self.grad = grad

        if len(args) and isinstance(args[0], str):
            mapping_name, *args = args
            self.mapping = MAPPINGS_LIBRARY[mapping_name](**mapping_kwargs)
            self.check_type(self.data_domain)
        elif mapping_kwargs:
            raise('Mapping kwargs are given to .fit(), but no mapping type provided')

        size = 1
        shift = 0
        if len(args) == 4:
            a, b, A, B = args
            self._assigned_min = a
            self._assigned_max = b
            size = B - A
            shift = A
        elif len(args) == 3:
            a, b, size = args
            self._assigned_min = a
            self._assigned_max = b
        elif len(args) == 2:
            a, b = args
            self._assigned_min = a
            self._assigned_max = b
        elif len(args) == 1:
            size = args[0]
        elif len(args) == 0:
            pass
        else:
            raise AttributeError(f'wrong number of arguments in .fit(). {len(args)} recieved, 0-4 required.')
        self._assigned_size = size
        self._assigned_shift = shift

        # fit to the constrains
        self._calibrate()

    def set(self, *args, shift=..., grad=None, **kwargs):
        if shift is not Ellipsis: self._assigned_shift = shift
        if grad is not None: self.grad = grad
        super().set(*args, **kwargs)


    def get_ticks(self, min_interval, width, *args, **kwargs) -> dict:
        dim = self.make_ticks_dim(width)
        return dim.get_ticks(min_interval, *args, **kwargs)

    def __str__(self):
        a, b = self.displayed_domain
        if a == b:
            return f'{self.mapping}[{"" if a is None else a}]'
        else:
            return f'{self.mapping}[{a}:{b}]'

    def __repr__(self):
        if hasattr(self.grad, '__name__'):
            grad = self.grad.__name__
        else:
            grad = self.grad
        return f'Color Dimension {self._dim_name} ({self.mapping}, data={self.data_domain}, borders={self.assigned_domain}, values={self.color_val_domain}, grad={grad}, k={self._scale}, shift={self._shift})'


class GradientDimenstion(PixelDimension):
    """ Dimention used solely for color axes """

    def __init__(self, ref:ColorDimension, size:int, gradient_type=None):
        a, b = ref.displayed_domain

        self._assigned_min = a
        self._assigned_max = b
        self._assigned_size = size

        self.mapping = ref.mapping
        self.gradient_type = gradient_type or ref.mapping.suggested_gradient_type

        self._calibrate()

        self._col_scale = ref._scale
        self._col_shift = ref._shift
        self.val_to_color = ref.val_to_color


    def _calibrate(self):

        size = self._assigned_size
        if size is None:
            return
            # size should always be present in this dimension
        if size < 2:
            size = self._assigned_size = 2
        self.pixel_min, self.pixel_max = 0, size-1

        a, b = self.displayed_domain
        val_a = self.mapping.to_value(a)
        val_b = self.mapping.to_value(b)
        if self.gradient_type == 'cat':
            self.shades = range(int(val_a), int(val_b)+1)
            val_a = val_a - 0.5
            val_b = val_b + 0.5
        elif self.gradient_type == 'bins':
            val_a = int(val_a)
            val_b = int(val_b) + 1
            self.shades = range(val_a, val_b)

        if val_a == val_b:
            # special case
            self._singular_value = True
            self._scale = 0
            self._shift = int(size / 2)
        else:
            self._singular_value = False
            self._scale = (size-1) / (val_b - val_a)
            self._shift = -val_a * self._scale

    def gradient(self):
        if self._singular_value:
            val = self.mapping.to_value(self.assigned_min)
            return [(self.pixel_min, self.pixel_max, self.get_color(val))]

        k, c = self._scale, self._shift
        if self.gradient_type == 'cat':
            return [((i-0.5)*k+c, (i+0.5)*k+c, self.get_color(i)) for i in self.shades]
        elif self.gradient_type == 'bins':
            return [(i*k+c, (i+1)*k+c, self.get_color(i)) for i in self.shades]
        else:
            return [(i, i, self.get_color((i-c)/k)) for i in range(self._assigned_size)]

    def get_color(self, x):
        val = x * self._col_scale + self._col_shift
        return self.val_to_color(val)

    def __str__(self):
        a, b = self.displayed_domain
        k, c = self._col_scale, self._col_shift
        return f'{self.mapping}[{a}:{b}]->{self.current_pixel_size}->[{a*k+c}:{b*k+c}]'

    def __repr__(self):
        return f'Gradient Dimension ({self.mapping}, borders={self.assigned_domain}, size={self.current_pixel_size}, k={self._scale}, shift={self._shift}, col_scale={self._col_scale}, col_shift={self._col_shift})'

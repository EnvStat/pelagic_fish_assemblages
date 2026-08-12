from abc import abstractclassmethod, abstractmethod
from inspect import signature, isabstract

from new_artist import base
from new_artist.color import Color
from new_artist.canvas import Canvas
from new_artist.dimension import PixelDimension, ColorDimension
from new_artist.drawable import Drawable


GRAPH_LIBRARY = {}

_CALL_WHEN_REGISTERING_GRAPHS = []


class Graph(Drawable):

    # constants, specifying if .draw function should get
    # a single argument insread of a list
    _single_x_coord = False
    _single_y_coord = False
    _single_col_arg = False

    def __init_subclass__(cls):
        super().__init_subclass__()

        if isabstract(cls): return
        name = cls.__name__
        if name.startswith('_'): return

        # register Graph
        GRAPH_LIBRARY[name] = cls
        for fun in _CALL_WHEN_REGISTERING_GRAPHS:
            fun(name, cls)

    def __init__(self, space, *args, z=0, **kwards):
        self.__init_defaults__()
        self.space = space
        self.z = z

        self.define(*args, **kwards)
        self.__register_in_space__(self.space)
        self._check_consistency()

    def __init_defaults__(self):
        super().__init_defaults__()
        self.data_x = []
        self.data_y = []
        self.data_c = []
        self.kwargs = {}

    def __register_in_space__(self, space):
        self.domain_x = space.X.get_domain(self.data_x)
        self.domain_y = space.Y.get_domain(self.data_y)
        self.domain_c = space.C.get_domain(self.data_c)
        space.X.add_to_domain(self.domain_x)
        space.Y.add_to_domain(self.domain_y)
        space.C.add_to_domain(self.domain_c)

    @abstractmethod
    def define(self, *args, **kwards):
        # here one could define all the necessart properties of the Graph
        # self.data_x = [...]
        # self.data_y = [...]
        # self.data_c = [...]
        # self.margins = ...
        #
        # self.kwargs = {...} all extra arguments to sent to the draw function
        pass

    @Drawable.margins.setter
    def margins(self, value):  # *** int or dict
        if isinstance(value, base.Number):
            margin = int(value)
            self.margin_left = self.margin_right = self.margin_bottom = self.margin_top = margin
        elif isinstance(value, dict):
            self.margin_left   = int(value.get('<', 0))
            self.margin_right  = int(value.get('>', 0))
            self.margin_bottom = int(value.get('v', 0))
            self.margin_top    = int(value.get('^', 0))
        else:
            raise AttributeError(f'.margins should be assigned number of dict, got {type(value)} instead')

    def _check_consistency(self):
        # check if .kwargs would fit the .draw() function
        sign = signature(self.draw)
        try:
            sign.bind('canvas', 'X', 'Y', 'C', **self.kwargs)
        except TypeError:
            raise TypeError(f'{self.__class__.__name__} would not be able to draw: cannot bind kwargs.')

        try:
            self.inner_x0
            self.inner_x1
        except:
            raise TypeError(f'Impossible to get X-coordinates for {self.__class__.__name__}. Maybe no data in .data_x')
        try:
            self.inner_y0
            self.inner_y1
        except:
            raise TypeError(f'Impossible to get Y-coordinates for {self.__class__.__name__}. Maybe no data in .data_y')

    def render(self, canvas: Canvas, debug=False):
        # convert coordinates according to the parent space
        X = self.space.X.transform(self.data_x)
        Y = self.space.Y.transform(self.data_y)
        C = self.space.C.transform(self.data_c)
        if self._single_x_coord: X = X[0]
        if self._single_y_coord: Y = Y[0]
        if self._single_col_arg: C = C[0]

        self.draw(canvas, X, Y, C, **self.kwargs)

    @abstractclassmethod
    def draw(self, canvas, X, Y, C, **kwargs):
        # draw figure into canvas here
        pass

    @property
    def inner_x0(self): return self.space.X.bounded_min(self.domain_x)
    @property
    def inner_x1(self): return self.space.X.bounded_max(self.domain_x)
    @property
    def inner_y0(self): return self.space.Y.bounded_min(self.domain_y)
    @property
    def inner_y1(self): return self.space.Y.bounded_max(self.domain_y)


    def __str__(self):
        return f'{self.__class__.__name__}'
    def __repr__(self):
        return f'{self.__class__.__name__}(X={self.domain_x}, Y={self.domain_y}, C={self.domain_c}, kwards={self.kwargs})'


class RotatableGraph(Graph):
    rotation = None
    _x_y_swap_when_rotating = False

    def __init__(self, space, *args, z=0, **kwards):
        self.__init_defaults__()
        self.space = space
        self.z = z

        self.define(*args, **kwards)
        if self.rotation is None:
            raise TypeError('RotatableGraph have not defined its ".rotation" attribute. Should set at least to ">^" (as default).')
        # rotate margins
        self.margins, x_y_swap = base.rotate_margins(self.margins, self.rotation)
        if self._x_y_swap_when_rotating and x_y_swap:
            # swap x and y sides
            self.data_x, self.data_y = self.data_y, self.data_x
        self.__register_in_space__(self.space)
        self._check_consistency()

    def render(self, canvas: Canvas, debug=False):
        # convert coordinates according to the parent space
        X = self.space.X.transform(self.data_x)
        Y = self.space.Y.transform(self.data_y)
        C = self.space.C.transform(self.data_c)

        view = canvas.view(0, 0, rotation=self.rotation)
        if view.direction.vertical:
            # rotate coordinates back
            X, Y = Y, X

        if self._single_x_coord: X = X[0]
        if self._single_y_coord: Y = Y[0]
        if self._single_col_arg: C = C[0]

        self.draw(view, X, Y, C, **self.kwargs)

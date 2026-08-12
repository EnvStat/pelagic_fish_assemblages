from typing import List
from math import nan, isnan

from new_artist.canvas import Canvas
from new_artist.figure import FloatingDrawable
from new_artist.axis import make_axis
from new_artist.axis import Caption, CaptionDescriptor, AxisDescriptor
from new_artist.dimension import PixelDimension, ColorDimension, GradientDimenstion

from new_artist.graph import Drawable, Graph, GRAPH_LIBRARY, _CALL_WHEN_REGISTERING_GRAPHS
# import several sets of graphs
from new_artist import graphlib_shapes
from new_artist import graphlib_matrices
from new_artist import graphlib_markup
from new_artist import graphlib_hist


# *** typing: replace List with list


class Panel(FloatingDrawable):
    """
    list of graphs inside a Figure, sharing the same coordinate space and axes
    """
    items: List[Graph]
    X: PixelDimension
    Y: PixelDimension
    C: ColorDimension

    left   = AxisDescriptor()
    right  = AxisDescriptor()
    bottom = AxisDescriptor()
    top    = AxisDescriptor()

    title      = CaptionDescriptor()
    caption    = CaptionDescriptor()
    panel_name = CaptionDescriptor()

    def __init__(self, X=None, Y=None, axes='', *, C=None, caption=None, title=None, panel_name=None):
        self.__init_defaults__()

        self.items = []

        self.caption    = Caption(text=caption, font='caption')
        self.title      = Caption(text=title, font='title')
        self.panel_name = Caption(text=panel_name, font='panel name')

        self.X = PixelDimension(name='X', settings=X)
        self.Y = PixelDimension(name='Y', settings=Y)
        self.C = ColorDimension(name='C', settings=C)

        self.left   = make_axis(self.Y, axes, '<')
        self.right  = make_axis(self.Y, axes, '>')
        self.bottom = make_axis(self.X, axes, 'v')
        self.top    = make_axis(self.X, axes, '^')

        self.domain_x = []
        self.domain_y = []
        self.domain_col = []

        self._total_x0 = nan
        self._total_x1 = nan
        self._total_y0 = nan
        self._total_y1 = nan

    @classmethod
    def __register_graph__(cls, name, graph):
        def fun(self, *args, **kwargs):
            grf = graph(self, *args, **kwargs)
            self.items.append(grf)
            return grf
        fun.__name__ = name
        fun.__doc__ = graph.__doc__
        setattr(cls, name, fun)


    def __getitem__(self, i):
        return self.items[i]
    def __len__(self):
        return len(self.items)
    def __iter__(self):
        return iter(self.items)

    def append(self, grf: Graph):
        if not isinstance(grf, Graph):
            raise(f'Panel can only contain istances of type "Graph". {type(grf)} recieved instead.')
        if grf.space is not self:
            grf.space = self
            grf.__register_in_space__(self)
        self.items.append(grf)


    def render(self, canvas, debug=False):
        self._total_x0, self._total_y0, self._total_x1, self._total_y1 = self.inner_box

        for graph in sorted(self.items, key=lambda x: x.z):
            try:
                layer = graph.make(debug=debug)
                canvas.paste(
                    graph.outer_x0 + graph.shift_x,
                    graph.outer_y0 + graph.shift_y,
                    layer)
            except:
                if debug:
                    print(f'Effor when drawing {graph} in {self}, ignoring in the debug mode')
                else:
                    raise
        self.render_margins(canvas, debug=debug)

        self._total_x0 = self._total_y0 = self._total_x1 = self._total_y1 = nan

        return canvas

    def render_margins(self, canvas, debug=False):
        # draw captions
        if self.title:
            self.title.draw(
                canvas, self.inner_xc, self.outer_y1, pos='.v')
        if self.caption:
            self.caption.draw(
                canvas, self.inner_xc, self.outer_y0, pos='.^')
        if self.panel_name:
            self.panel_name.draw(
                canvas, self.outer_x0, self.inner_y1, pos='>v')

        # draw axes
        if self.bottom:
            self.bottom.draw(
                canvas.view(0, self.inner_y0, '>^'), debug=debug)
        if self.top:
            self.top.draw(
                canvas.view(0, self.inner_y1, '>v'), debug=debug)
        if self.left:
            self.left.draw(
                canvas.view(self.inner_x0, 0, '^>'), debug=debug)
        if self.right:
            self.right.draw(
                canvas.view(self.inner_x1, 0, '^<'), debug=debug)


    def fit_hist(self, height, relative=False, sqrt=False):
        histograms = [graph for graph in self if hasattr(graph, 'histogram_height')]
        if not histograms: return

        # maximal height of a bin, measured in items [or proportion to hist size]
        values = [graph.histogram_height(relative) for graph in histograms]
        max_value = max(values)
        for graph, val in zip(histograms, values):
            relative_size = val / max_value
            if sqrt:
                relative_size = relative_size**0.5
            graph.set_height(int(relative_size * height))

    def color_axis(self, dir='>', w=20, h=500, text=None) -> FloatingDrawable:
        axis = ColorAxis(self.C, w=w, h=h, axes=dir)
        if axis.left: axis.left.text = text
        if axis.right: axis.right.text = text
        if axis.top: axis.top.text = text
        if axis.bottom: axis.bottom.text = text
        return axis



    @property
    def inner_x0(self): return min([grf.outer_x0 + grf.shift_x for grf in self if not isnan(grf.outer_x0)] + [self.X.pixel_min])
    @property
    def inner_x1(self): return max([grf.outer_x1 + grf.shift_x for grf in self if not isnan(grf.outer_x1)] + [self.X.pixel_max])
    @property
    def inner_y0(self): return min([grf.outer_y0 + grf.shift_y for grf in self if not isnan(grf.outer_y0)] + [self.Y.pixel_min])
    @property
    def inner_y1(self): return max([grf.outer_y1 + grf.shift_y for grf in self if not isnan(grf.outer_y1)] + [self.Y.pixel_max])


    @property
    def margin_left(self):
        return max([self.left.pixel_h,  self.top.pixel_w, self.bottom.pixel_w]) + self.panel_name.pixel_w
    @property
    def margin_right(self):
        return max([self.right.pixel_h, self.top.pixel_w, self.bottom.pixel_w])
    @property
    def margin_bottom(self):
        return max([self.bottom.pixel_h, self.left.pixel_w, self.right.pixel_w]) + self.caption.pixel_h
    @property
    def margin_top(self):
        return max([self.top.pixel_h,    self.left.pixel_w, self.right.pixel_w]) + self.title.pixel_h


    def __repr__(self):
        caption = self.title.text or self.caption.text or self.__class__.__name__
        return f'{self.__class__.__name__} {caption} of len {len(self)}(X={self.X} Y={self.Y} C={self.C})'



[Panel.__register_graph__(name, graph) for name, graph in GRAPH_LIBRARY.items()]
_CALL_WHEN_REGISTERING_GRAPHS.append(Panel.__register_graph__)



class ColorAxis(FloatingDrawable):
    """
    Color Axis, saparated from a Panel
    """
    left   = AxisDescriptor()
    right  = AxisDescriptor()
    bottom = AxisDescriptor()
    top    = AxisDescriptor()

    ref_C: ColorDimension
    grad: GradientDimenstion

    def __init__(self, C: ColorDimension, w, h, axes='>'):
        self.__init_defaults__()
        self.w = w
        self.h = h

        if '<' in axes or '>' in axes:
            self.vertical = True
        else:
            self.vertical = False
        self.ref_C = C  # reference to the color dimension
        self._recompute_dimension()

        self.left   = make_axis(self.grad, axes, '<')
        self.right  = make_axis(self.grad, axes, '>')
        self.bottom = make_axis(self.grad, axes, 'v')
        self.top    = make_axis(self.grad, axes, '^')

    def _recompute_dimension(self):
        self.grad = GradientDimenstion(self.ref_C, size=self.h if self.vertical else self.w)

    def render(self, canvas:Canvas, debug=False):
        if self.vertical:
            size = self.w
            rotated = canvas.view(0, 0, rotation='^>')
        else:
            size = self.h
            rotated = canvas

        for a, b, col in self.grad.gradient():
            rotated.rect([a, b], [0, size-1], col)

        self.render_margins(canvas, debug=debug)
        return canvas

    def render_margins(self, canvas, debug=False):
        # draw axes
        self._recompute_dimension()
        if self.bottom:
            self.bottom.draw(
                canvas.view(0, self.inner_y0, '>^'), debug=debug)
        if self.top:
            self.top.draw(
                canvas.view(0, self.inner_y1, '>v'), debug=debug)
        if self.left:
            self.left.draw(
                canvas.view(self.inner_x0, 0, '^>'), debug=debug)
        if self.right:
            self.right.draw(
                canvas.view(self.inner_x1, 0, '^<'), debug=debug)

    @property
    def inner_x0(self): return 0
    @property
    def inner_x1(self): return self.w-1
    @property
    def inner_y0(self): return 0
    @property
    def inner_y1(self): return self.h-1


    @property
    def margin_left(self):
        self._recompute_dimension()
        return max([self.left.pixel_h,   self.top.pixel_w, self.bottom.pixel_w])
    @property
    def margin_right(self):
        self._recompute_dimension()
        return max([self.right.pixel_h,  self.top.pixel_w, self.bottom.pixel_w])
    @property
    def margin_bottom(self):
        self._recompute_dimension()
        return max([self.bottom.pixel_h, self.left.pixel_w, self.right.pixel_w])
    @property
    def margin_top(self):
        self._recompute_dimension()
        return max([self.top.pixel_h,    self.left.pixel_w, self.right.pixel_w])

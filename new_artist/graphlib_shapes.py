from new_artist import base
from new_artist.graph import Graph
from new_artist.color import Color
from new_artist.canvas import Canvas

from collections import Counter


## Graphs with a single coordinate pair
## -----------------------------------

class circle(Graph):
    """ Draw a cirle """
    _single_x_coord = True
    _single_y_coord = True
    _single_col_arg = True

    def define(self, *xy, r=1, col=1, legend=None):
        x, y = base.unpack_xy(*xy)
        self.data_x = [x]
        self.data_y = [y]
        self.data_c = [col]
        self.margins = r
        self.kwargs = {'r': r}
        if legend: self.legend = col, legend, '()'

    @staticmethod
    def draw(canvas: Canvas, x, y, col, r):
        canvas.circle(x, y, r=r, col=col)


class circle_sector(circle):
    """ Draw a sector of a circle """

    def define(self, *xy, r=1, a=0, b=0, col=1):
        x, y = base.unpack_xy(*xy)
        self.data_x = [x]
        self.data_y = [y]
        self.data_c = [col]
        self.margins = r
        self.kwargs = {'r': r, 'start': a, 'end': b}

    @staticmethod
    def draw(canvas: Canvas, x, y, col, r, start, end):
        canvas.sector([x-r, x+r], [y-r, y+r], col, start=start, end=end)


## Graphs with two coordinate pairs
## -------------------------------


class rect(Graph):
    """ Draw filled rectangle """
    _single_col_arg = True

    def define(self, *xyxy, col=1, legend=None):
        x0, y0, x1, y1 = base.unpack_xyxy(*xyxy)
        self.data_x = [x0, x1]
        self.data_y = [y0, y1]
        self.data_c = [col]
        if legend: self.legend = col, legend, '[]'

    @staticmethod
    def draw(canvas: Canvas, X, Y, col):
        canvas.rect(X, Y, col)


class line(Graph):
    """ Draw a single line """
    _single_col_arg = True

    def define(self, *xyxy, col=1, p=3, legend=None):
        x0, y0, x1, y1 = base.unpack_xyxy(*xyxy)
        self.data_x = [x0, x1]
        self.data_y = [y0, y1]
        self.data_c = [col]
        self.margins = p//2
        self.kwargs = {'p': p}
        if legend: self.legend = col, legend, '-'

    @staticmethod
    def draw(canvas: Canvas, X, Y, col, p):
        canvas.line(X, Y, col, p=p)


class box(Graph):
    """ Draw rectangle without filling """
    _single_col_arg = True

    def define(self, *xyxy, col=1, p=3):
        x0, y0, x1, y1 = base.unpack_xyxy(*xyxy)
        self.data_x = [x0, x1]
        self.data_y = [y0, y1]
        self.data_c = [col]
        self.margins = p//2
        self.kwargs = {'p': p}

    @staticmethod
    def draw(canvas: Canvas, X, Y, col, p):
        canvas.box(X, Y, col, p=p)


class ellipse(Graph):
    """ Draw an ellipse """
    _single_col_arg = True

    def define(self, *xyxy, col=1):
        x0, y0, x1, y1 = base.unpack_xyxy(*xyxy)
        self.data_x = [x0, x1]
        self.data_y = [y0, y1]
        self.data_c = [col]

    @staticmethod
    def draw(canvas: Canvas, X, Y, col):
        canvas.ellipse(X, Y, col)


class sector(Graph):
    """ Draw an ellipse """
    _single_col_arg = True

    def define(self, xyxy, start, end, col=1):
        x0, y0, x1, y1 = base.unpack_xyxy(*xyxy)
        self.data_x = [x0, x1]
        self.data_y = [y0, y1]
        self.data_c = [col]
        self.kwargs = {'start': start, 'end': end}

    @staticmethod
    def draw(canvas: Canvas, X, Y, col, start, end):
        canvas.sector(X, Y, col, start=start, end=end)


## Graphs with multiple coordinate pairs
## ------------------------------------


class lines(Graph):
    """ Draw multiple lines """
    _single_col_arg = True

    def define(self, *xxxyyy, col=1, p=3, legend=None):
        self.data_x, self.data_y = base.unpack_xxxyyy(*xxxyyy)
        self.margins = p//2
        self.data_c = [col]
        self.kwargs = {'p': p}
        if legend: self.legend = col, legend, '-'

    @staticmethod
    def draw(canvas: Canvas, X, Y, col, p):
        canvas.line(X, Y, col=col, p=p)


class points(Graph):
    """ Draw a scattergraph """
    def define(self, *xxxyyy, col=1, colors=None, p=3, legend=None):
        self.data_x, self.data_y = base.unpack_xxxyyy(*xxxyyy)
        self.margins = (p+1)//2
        # number of colors are scaled to the number of points
        if colors is not None:
            self.data_c = colors
        else:
            self.data_c = [col]*len(self.data_x)
        self.kwargs = {'p': p}
        if legend: self.legend = col, legend, '()'

    @staticmethod
    def draw(canvas: Canvas, X, Y, C, p):
        canvas.points(X, Y, C, p)


class recpoints(points):
    """ Draw a scattergraph """
    @staticmethod
    def draw(canvas: Canvas, X, Y, C, p):
        canvas.recpoints(X, Y, C, p)


class mist(Graph):
    """ Draw a scattergraph with stacking points """
    _single_col_arg = True

    def define(self, *xxxyyy, col=1, p=1, k=None):
        self.data_x, self.data_y = base.unpack_xxxyyy(*xxxyyy)
        self.margins = p//2
        self.data_c = [col]
        self.kwargs = {'p': p, 'max_n': k}

    @staticmethod
    def draw(canvas: Canvas, X, Y, col: Color, p, max_n):
        pts = Counter(zip(X, Y))
        if not pts:
            return  # no points given
        pts = [(x, y, n) for (x, y), n in pts.most_common()]
        max_n = max_n or pts[0][2]
        X, Y, N = zip(*pts[::-1])  # reversed
        C = [col.alpha(n/max_n) for n in N]
        canvas.points(X, Y, C, p)


class polygon(Graph):
    """ Draw a filled polygon """
    _single_col_arg = True

    def define(self, *xxxyyy, col=1, legend=None):
        self.data_x, self.data_y = base.unpack_xxxyyy(*xxxyyy)
        self.data_c = [col]
        if legend: self.legend = col, legend, '[]'

    @staticmethod
    def draw(canvas: Canvas, X, Y, col):
        canvas.polygon(X, Y, col=col)

class area(polygon):
    """ fill an area, limited by two lines """
    def define(self, X, Y1, Y2, col=1, legend=None):
        X = list(X)
        Y1 = list(Y1)
        Y2 = list(Y2)
        self.data_x = X + X[::-1]
        self.data_y = Y1 + Y2[::-1]
        self.data_c = [col]
        if legend: self.legend = col, legend, '[]'


class shape(polygon):
    """  Draw a filled polygon, which always touches x-axis at y=0"""
    def define(self, *xxxyyy, col=1, legend=None):
        self.data_x, self.data_y = base.unpack_xxxyyy(*xxxyyy)
        self.data_x = [self.data_x[0], *self.data_x, self.data_x[-1]]
        self.data_y = [0, *self.data_y, 0]
        self.data_c = [col]
        if legend: self.legend = col, legend, '[]'

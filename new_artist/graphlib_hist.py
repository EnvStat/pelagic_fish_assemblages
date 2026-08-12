from new_artist import base
from new_artist.graph import Graph, RotatableGraph
from new_artist.font import Font
from new_artist.color import Color
from new_artist.canvas import Canvas

from collections import Counter


class bar(RotatableGraph):
    """ Bar with a given values """
    _single_x_coord = True
    _single_col_arg = True
    _x_y_swap_when_rotating = True

    def define(self, *xy, col=1, p=10, zero=0, vertical=True):
        x, y = base.unpack_xy(*xy)
        self.data_x = [x]
        self.data_y = [zero, y]
        self.data_c = [col]
        self.margins = {'<': p//2, '>': p//2}
        self.rotation = '>^' if vertical else '^>'
        self.kwargs = {'p': p}

    @staticmethod
    def draw(canvas: Canvas, x, Y, col, p, zero=0):
        if Y[0] != Y[1]:
            canvas.line([x, x], Y, col=col, p=p)


class bars(RotatableGraph):
    """ Set of bars with a given values """
    _x_y_swap_when_rotating = True

    def define(self, *xxxyyy, col=1, p=10, zero=0, vertical=True, items=None):
        if items is not None:
            counts = Counter(items)
            self.data_x, self.data_y = list(counts.keys()), list(counts.values())
        else:
            self.data_x, self.data_y = base.unpack_xxxyyy(*xxxyyy)
        self.data_y += [zero]
        self.margins = {'<': p//2, '>': p//2}
        # number of colors are scaled to the number of points
        if isinstance(col, base.Sequence) and not isinstance(col, str):
            self.data_c = col
        else:
            self.data_c = [col]*len(self.data_x)
        self.rotation = '>^' if vertical else '^>'
        self.kwargs = {'p': p, 'zero': zero}

    @staticmethod
    def draw(canvas: Canvas, X, Y, C, p, zero=0):
        for x, y, col in zip(X, Y[:-1], C):  # last item if Y should be zero
            if y != zero:
                canvas.line([x, x], [zero, y], col=col, p=p)


class bhist(RotatableGraph):
    """ Construct a histiogram from a given list of values """
    _single_col_arg = True
    _x_y_swap_when_rotating = True

    def define(self, data, borders=10, col=1, precomputed=False, ensure_coverage=True, vertical=True, gap=0):
        counts, borders = base.compute_bin_histogram(data, borders, precomputed, ensure_coverage)
        self.data_x = borders
        self.data_y = counts + [0]
        self.data_c = [col]
        self.rotation = '>^' if vertical else '^>'
        self.kwargs = {'gap': gap}

    @staticmethod
    def draw(canvas: Canvas, X, Y, col, gap):
        for x0, x1, y in zip(X, X[1:], Y[:-1]):  # last item if Y should be 0
            if y:
                canvas.rect([x0, x1], [0, y], col=col)
        if gap:
            for x in X:
                canvas.line([x, x], [canvas.y0, canvas.y1], col=(0, 0, 0, 0), p=gap)


class gradient(RotatableGraph):
    """ series of vertical lines """
    _single_x_coord = True
    _single_y_coord = True
    _x_y_swap_when_rotating = False

    def define(self, colors, heights=None, loc=(0, 0), p=1, pos='>^'):
        if heights is None:
            colors, heights = zip(*colors)
        elif isinstance(heights, base.Number):
            heights = [heights]*len(colors)

        self.data_x = [loc[0]]
        self.data_y = [loc[1]]
        self.data_c = colors

        w, h = len(colors), max(heights)
        self.margins = {'>': w, '^': h}
        self.rotation = pos

        self.kwargs = {'heights': heights}

    @staticmethod
    def draw(canvas: Canvas, x, y, C, heights):
        canvas.gradient(zip(C, heights), x=x, y=y)


class hist(RotatableGraph):
    """ Construct a histiogram from a given list of values """
    _single_y_coord = True
    _single_col_arg = True
    _x_y_swap_when_rotating = True

    def define(self, data, height=100, col=1, loc=0, vertical=True):
        if not len(data):
            raise Exception('Histogram should be initiated with a non-empty sequence')
        self.data_x = data
        self.data_y = [loc]
        self.data_c = [col]
        self.margins = {'^': height}
        self.rotation = '>^' if vertical else '^>'
        self.kwargs = {'height': height}

    def hist_core(self):
        if self.rotation == '^>':
            H = self.space.Y.transform(self.data_y)
        else:
            H = self.space.X.transform(self.data_x)
        return Counter(H)

    def histogram_height(self, relative=False):
        H = self.hist_core()
        val = H.most_common(1)[0][1]
        if relative:
            # *** use H.total after 3.10
            return val / sum(H.values())
        else:
            return val

    def set_height(self, height):
        self.kwargs['height'] = height
        self.margins = {self.rotation[1]: height}

    def draw(self, canvas: Canvas, _, y, col, height):
        L = self.hist_core()
        k = height / L.most_common(1)[0][1]
        for x, h in L.items():
            y1 = y+int(h*k)-1
            canvas.line([x, x], [y, y1], col, p=1)


class cum_hist(hist):
    def hist_core(self):
        if self.rotation == '^>':
            data = [x for x in self.data_y if 0 <= x <= 1]
            H = self.space.Y.transform(data)
        else:
            data = [x for x in self.data_x if 0 <= x <= 1]
            H = self.space.X.transform(data)
        H = Counter(H)
        C = {}
        s = sum(H.values())
        for i in range(max(H.keys())):
            s -= H[i]
            C[i] = s
        return C

    def histogram_height(self, relative=False):
        H = self.hist_core()
        val = H[0]
        if relative:
            # *** use H.total after 3.10
            return 1
        else:
            return val

    def draw(self, canvas: Canvas, _, y, col, height):
        L = self.hist_core()
        k = height / L[0]
        for x, h in L.items():
            y1 = y+int(h*k)-1
            canvas.line([x, x], [y, y1], col, p=1)

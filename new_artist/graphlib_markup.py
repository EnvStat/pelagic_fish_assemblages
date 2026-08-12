from new_artist import base
from new_artist.graph import Graph, RotatableGraph
from new_artist.font import Font
from new_artist.color import Color
from new_artist.canvas import Canvas

from collections import Counter


class text(Graph):
    """ Write a text """
    _single_x_coord = True
    _single_y_coord = True
    _single_col_arg = True

    def define(self, x, y, s, font='normal', pos='>^', col=None):
        # unpacking coords
        if   x == '<': x = self.space.X.data_min
        elif x == '>': x = self.space.X.data_max
        elif x == '.': x = sum(self.space.X.data_domain)/2
        if   y == 'v': y = self.space.Y.data_min
        elif y == '^': y = self.space.Y.data_max
        elif y == '.': y = sum(self.space.Y.data_domain)/2
        self.data_x = [x]
        self.data_y = [y]
        self.data_c = [col]

        font = Font(font)
        w, h = font.measure(s)

        dx, dy, vertical = base.pos_to_shift(w, h, pos)
        if vertical: w, h = h, w
        self.margins = {'<': -dx, '>': w + dx, 'v': -dy, '^': h + dy}

        self.kwargs = {'s': str(s), 'font': font, 'pos': pos}

    @staticmethod
    def draw(canvas: Canvas, x, y, col, s, font, pos):
        canvas.write(x, y, s, font=font, pos=pos, col=col)


class symbol(Graph):
    """ Draw a sumbol """
    _single_x_coord = True
    _single_y_coord = True
    _single_col_arg = True

    def define(self, x, y, s, size=30, pos='..', col='k'):
        self.data_x = [x]
        self.data_y = [y]
        self.data_c = [col]
        self.margins = {'>': size, '^': size}
        self.shift_x, self.shift_y, _ = base.pos_to_shift(size, size, pos)
        self.kwargs = {'s': str(s), 'size': size}

    @staticmethod
    def draw(canvas: Canvas, x, y, col, s, size):
        canvas.symbol(x, y, s, size=size, col=col)


class legend(RotatableGraph):
    """ Write a legend """
    _single_x_coord = True
    _single_y_coord = True

    def define(self, x='<', y='^', cols=None, labels=None, symbols='[]', font='normal', pos='>^', ref_panel=None, bgcol=None):
        # unzip arguments
        # *** pattern matching?
        if cols is None:
            # pick information from the reference Panel
            if ref_panel is None:
                ref_panel = self.space
            lines = []
            for drw in ref_panel.items:
                if hasattr(drw, 'legend') and drw.legend not in lines:
                    lines.append(drw.legend)
            if not lines:
                raise Exception('Legend is called for the panel with no legend given')
            cols, labels, symbols = zip(*lines)

        elif labels is None and not isinstance(symbols, (tuple, list)):
            try:
                cols, labels, symbols = zip(*cols)
            except ValueError:
                cols, labels = zip(*cols)
                symbols = [symbols] * len(cols)

        elif not isinstance(symbols, (tuple, list)):
            symbols = [symbols] * len(cols)

        self.data_c = cols

        # unpacking xy-coords
        if   x == '<': x = self.space.X.displayed_min
        elif x == '>': x = self.space.X.displayed_max
        elif x == '.': x = (self.space.X.displayed_min + self.space.X.displayed_max)/2
        if   y == 'v': y = self.space.Y.displayed_min
        elif y == '^': y = self.space.Y.displayed_max
        elif y == '.': y = (self.space.Y.displayed_min + self.space.Y.displayed_max)/2
        self.data_x = [x]
        self.data_y = [y]

        font = Font(font)
        w, h = font.measure('\n'.join(labels))

        mark_size = int(font.max_h * 0.8)
        w = w+mark_size+10
        self.margins = {'>': w, 'v': h}
        dx, dy, x_y_swap = base.pos_to_shift(w, h, pos)
        self.move(dx, h+dy)
        self.rotation = '^<' if x_y_swap else '>^'

        self.kwargs = {'labels': labels, 'symbols': symbols, 'font': font, 'bgcol': Color(bgcol)}

    def draw(self, canvas: Canvas, x, y, cols, labels, symbols, font, bgcol):
        if bgcol is not None:
            canvas.fill(bgcol)
        mark_size = int(font.max_h * 0.8)
        for col, lab, symbol in zip(cols, labels, symbols):
            canvas.symbol(x, y-mark_size, symbol, mark_size, col=col, font=font)
            canvas.write(x+mark_size + 10, y+1, lab, font=font, pos='>v')
            y -= font.measure_h(lab)


class x_mark(Graph):
    """ Draw a single vertical line on the whole space """
    _single_x_coord = True
    _single_col_arg = True

    def define(self, x=0, col='axis', p=1, legend=None):
        self.data_x = [x]
        self.data_c = [col]
        self.kwargs = {'p': p}
        self.margins = {'<': p//2, '>': p//2}
        if legend: self.legend = col, legend, '-'

    @property
    def inner_y0(self): return self.space._total_y0
    @property
    def inner_y1(self): return self.space._total_y1

    @staticmethod
    def draw(canvas: Canvas, x, _, col, p):
        canvas.line([x, x], [canvas.y0, canvas.y1], col=col, p=p)


class y_mark(Graph):
    """ Draw a single horozontal line on the whole space """
    _single_y_coord = True
    _single_col_arg = True

    def define(self, y=0, col='axis', p=1, legend=None):
        self.data_y = [y]
        self.data_c = [col]
        self.kwargs = {'p': p}
        self.margins = {'v': p//2, '^': p//2}
        if legend: self.legend = col, legend, '-'

    @property
    def inner_x0(self): return self.space._total_x0
    @property
    def inner_x1(self): return self.space._total_x1

    @staticmethod
    def draw(canvas: Canvas, _, y, col, p):
        canvas.line([canvas.x0, canvas.x1], [y, y], col=col, p=p)


class x_marked_area(Graph):
    """ Draw a single vertical line on the whole space """
    _single_col_arg = True

    def define(self, x1, x2, col='axis', legend=None):
        self.data_x = [x1, x2]
        self.data_c = [col]
        if legend: self.legend = col, legend, '[]'

    @property
    def inner_y0(self): return self.space._total_y0
    @property
    def inner_y1(self): return self.space._total_y1

    @staticmethod
    def draw(canvas: Canvas, X, _, col):
        canvas.rect(X, [canvas.y0, canvas.y1], col=col)


class y_marked_area(Graph):
    """ Draw a single vertical line on the whole space """
    _single_col_arg = True

    def define(self, y1, y2, col='axis', legend=None):
        self.data_y = [y1, y2]
        self.data_c = [col]
        if legend: self.legend = col, legend, '[]'

    @property
    def inner_x0(self): return self.space._total_x0
    @property
    def inner_x1(self): return self.space._total_x1

    @staticmethod
    def draw(canvas: Canvas, _, Y, col):
        canvas.rect([canvas.x0, canvas.x1], Y, col=col)


class GrapheWholeInnerSpace(Graph):
    @property
    def inner_x0(self): return self.space._total_x0
    @property
    def inner_x1(self): return self.space._total_x1
    @property
    def inner_y0(self): return self.space._total_y0
    @property
    def inner_y1(self): return self.space._total_y1


class GrapheWholeDataSpace(Graph):
    @property
    def inner_x0(self): return self.space.X.pixel_min
    @property
    def inner_x1(self): return self.space.X.pixel_max
    @property
    def inner_y0(self): return self.space.Y.pixel_min
    @property
    def inner_y1(self): return self.space.Y.pixel_max


class background(GrapheWholeInnerSpace):
    """ Fill the whole space with the color """
    _single_col_arg = True

    def define(self, col='#'):
        self.data_c = [col]

    @staticmethod
    def draw(canvas: Canvas, _, __, col):
        canvas.fill(col=col)


class grid(GrapheWholeInnerSpace):

    def define(self, axis='<v', col='#', p=2, only_labelled_ticks=True):
        if '<' in axis:
            h_axis = self.space.left
        elif '>' in axis:
            h_axis = self.space.right
        else:
            h_axis = None

        if 'v' in axis:
            v_axis = self.space.bottom
        elif '^' in axis:
            v_axis = self.space.top
        else:
            v_axis = None

        self.kwargs = {'v_axis': v_axis, 'h_axis': h_axis, 'color': Color(col), 'only_labelled_ticks': only_labelled_ticks, 'p': p}

    def draw(self, canvas: Canvas, _, __, ___, v_axis, h_axis, color, only_labelled_ticks, p):
        if v_axis is not None:
            a, b = self.space.X.pixel_domain
            for x, label in v_axis.ticks.items():
                if (label is not None or not only_labelled_ticks) and (a < x < b):
                    canvas.line([x, x], [canvas.y0, canvas.y1], col=color, p=p)
        if h_axis is not None:
            a, b = self.space.Y.pixel_domain
            for y, label in h_axis.ticks.items():
                if (label is not None or not only_labelled_ticks) and (a < y < b):
                    canvas.line([canvas.x0, canvas.x1], [y, y], col=color, p=p)


class border(GrapheWholeInnerSpace):
    """ makes a border around the panel space """
    _single_col_arg = True

    def define(self, col='#', p=1, margin=0):
        self.data_c = [col]
        self.kwargs = {'p': p}

    @staticmethod
    def draw(canvas: Canvas, _, __, col, p):
        canvas.border(col=col, p=p)


class data_background(GrapheWholeDataSpace):
    """ Fill the whole space with the color """
    _single_col_arg = True

    def define(self, col='#'):
        self.data_c = [col]

    @staticmethod
    def draw(canvas: Canvas, _, __, col):
        canvas.fill(col=col)



class data_border(GrapheWholeDataSpace):
    """ makes a border around the panel space """
    _single_col_arg = True

    def define(self, col='#', p=1, margin=0):
        self.data_c = [col]
        self.kwargs = {'p': p}

    @staticmethod
    def draw(canvas: Canvas, _, __, col, p):
        canvas.border(col=col, p=p)

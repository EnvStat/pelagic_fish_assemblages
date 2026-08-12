from new_artist import base
from new_artist.graph import Graph, RotatableGraph
from new_artist.font import Font
from new_artist.color import Color
from new_artist.canvas import Canvas

from collections import Counter


class bitmap(RotatableGraph):
    """ Load a bitmap from a file and draw it. Very simple objects, does not support any transformations """
    _single_x_coord = True
    _single_y_coord = True

    def define(self, path, x=None, y=None, pos='>^', rotate=True):
        bmp = Canvas.load(path)
        if x is None and y is None:
            x, y = 0, 0
        elif y is None:
            x, y = base.unpack_xy(x)
        self.data_x = [x]
        self.data_y = [y]

        self.margins = {'>': bmp.w, '^': bmp.h}
        if rotate:
            self.rotation = pos
        else:
            # only position, dont rotate
            dx, dy, x_y_swap = base.pos_to_shift(bmp.w, bmp.h, pos)
            self.move(dx, dy)
            self.rotation = '^>' if x_y_swap else '>^'

        self.kwargs = {'bmp': bmp}

    @staticmethod
    def draw(canvas: Canvas, x, y, _, bmp):
        canvas.paste(x, y, bmp)


class image(Graph):
    """ Draw a matrix, represetnting values with a color """
    def define(self, M, *, size=10, gap=0, x_borders=None, y_borders=None, x_vals=None, y_vals=None):
        # get the size of the matrix
        linearized_data, data_x, data_y = base.unpack_matrix(M, default_step=size+gap, x_borders=x_borders, y_borders=y_borders, x_vals=x_vals, y_vals=y_vals)
        self.data_x = data_x
        self.data_y = data_y
        self.data_c = linearized_data
        if x_borders is None:
            self.margin_left = size // 2
            self.margin_right = (size-1) // 2
        if y_borders is None:
            self.margin_bottom = size // 2
            self.margin_top = (size-1) // 2
        self.kwargs = {
            'gap': int(gap),
            'size': int(size),
            'x_defined_with_vals': x_borders is None,
            'y_defined_with_vals': y_borders is None}

    @staticmethod
    def draw(canvas: Canvas, X, Y, C, gap, size=None, x_defined_with_vals=False, y_defined_with_vals=False):
        if x_defined_with_vals:
            X = [(x-size//2, x+(size-1)//2) for x in X]
        else:
            X = [(x0+(gap+1)//2, x1-gap//2-1) for x0, x1 in zip(X, X[1:])]

        if y_defined_with_vals:
            Y = [(y-size//2, y+(size-1)//2) for y in Y]
        else:
            Y = [(y0+(gap+1)//2, y1-gap//2-1) for y0, y1 in zip(Y, Y[1:])]

        for x0x1 in X:
            for y0y1 in Y:
                col, *C = C
                canvas.rect(x0x1, y0y1, col)

class text_matrix(Graph):
    """ Write down a matrix as a table """
    def define(self, M, size=100, font='small', *, col=None, x_borders=None, y_borders=None,  x_vals=None, y_vals=None, format_func=None):
        labels, data_x, data_y = base.unpack_matrix(M, default_step=size, x_borders=x_borders, y_borders=y_borders, x_vals=x_vals, y_vals=y_vals)
        self.data_x = data_x
        self.data_y = data_y

        if isinstance(col, base.Sequence):
            if len(col) != len(labels):
                raise ValueError(f'Wrong size of the color matrix: expected {len(labels)} elements, got {len(col)}')
            self.data_c = col
        else:
            self.data_c = [col]*len(labels)

        self.kwargs = {
            'labels': labels,
            'font': Font(font),
            'x_defined_with_vals': x_borders is None,
            'y_defined_with_vals': y_borders is None}

    @staticmethod
    def draw(canvas: Canvas, X, Y, C, labels, font, x_defined_with_vals=True, y_defined_with_vals=True):
        if not x_defined_with_vals:
            X = [(x0+x1)//2 for x0, x1 in zip(X, X[1:])]
        if not y_defined_with_vals:
            Y = [(y0+y1)//2 for y0, y1 in zip(Y, Y[1:])]

        for x in X:
            for y in Y:
                col, *C = C
                txt, *labels = labels
                canvas.write(x, y, s=txt, font=font, pos='..', col=col)


class color_matrix(image):
    """ Draw a matrix, represetnting values with a color and a label """
    def define(self, M, size=100, gap=0, *, font='small', format_func=base.goodround, labels=None, **kwargs):
        super().define(M, gap=gap, size=size, **kwargs)

        if labels is None:
            labels = [format_func(x) for x in self.data_c]
        else:
            h = len(M)
            w = len(M[0])
            labels = [labels[i][j] for j in range(w) for i in range(h)]

        self.kwargs['labels'] = labels
        self.kwargs['font'] = font

    @staticmethod
    def draw(canvas: Canvas, X, Y, C, size, gap, labels, font, x_defined_with_vals=False, y_defined_with_vals=False):
        # draw the underlying image
        image.draw(
            canvas, X, Y, C, size=size, gap=gap,
            x_defined_with_vals=x_defined_with_vals,
            y_defined_with_vals=y_defined_with_vals)
        text_matrix.draw(
            canvas, X, Y, [c.text_color() for c in C],
            labels=labels,
            font=font,
            x_defined_with_vals=x_defined_with_vals,
            y_defined_with_vals=y_defined_with_vals)

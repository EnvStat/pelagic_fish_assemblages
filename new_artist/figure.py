from typing import List

from new_artist.axis import Caption, CaptionDescriptor
from new_artist.canvas import Canvas
from new_artist.drawable import Drawable, FloatingDrawable


# *** typing: replace List with list

SEPARATOR = 20


class Figure(FloatingDrawable):
    """
    Collection of Drawables.
    """

    items: List[Drawable]
    _group_label = None

    title      = CaptionDescriptor()  # top
    caption    = CaptionDescriptor()  # bottom
    panel_name = CaptionDescriptor()  # left

    def __init__(self, content=(), group=None, caption=None, title=None, panel_name=None):
        self.__init_defaults__()
        self.items = []
        self.items[:] = content[:]
        self.caption    = Caption(text=caption, font='caption')
        self.title      = Caption(text=title, font='title')
        self.panel_name = Caption(text=panel_name, font='panel name')
        self._group_label = group

    @classmethod
    def from_stack(cls, *stack: List[FloatingDrawable]):
        return cls([item for drw in stack for item in drw._unpack()])

    @classmethod
    def from_row(cls, row: List[FloatingDrawable], sep=SEPARATOR):
        for left, right in zip(row, row[1:]):
            a = left.outer_x1 + left.space_right
            b = -right.outer_x0 + right.space_left
            right.shift_x = left.shift_x + a + sep + 1 + b
        new = cls.from_stack(*row)
        new.space_left = row[0].space_left
        new.space_right = row[-1].space_right
        return new

    @classmethod
    def from_column(cls, column: List[FloatingDrawable], sep=SEPARATOR):
        for bottom, top in zip(column[::-1], column[-2::-1]):
            a = bottom.outer_y1 + bottom.space_top
            b = -top.outer_y0 + top.space_bottom
            top.shift_y = bottom.shift_y + a + sep + 1 + b
        new = cls.from_stack(*column)
        new.space_top = column[0].space_top
        new.space_bottom = column[-1].space_bottom
        return new


    def __getitem__(self, i):
        return self.items[i]
    def __len__(self):
        return len(self.items)
    def __iter__(self):
        return iter(self.items)

    def append(self, drw: Drawable):
        self.items.append(drw)

    @property
    def margin_bottom(self):
        return self.caption.pixel_h
    @property
    def margin_top(self):
        return self.title.pixel_h
    @property
    def margin_left(self):
        return self.panel_name.pixel_h
    @property
    def margin_right(self):
        return 0

    @property
    def inner_x0(self): return min([drw.inner_x0 + drw.shift_x for drw in self], default=0)
    @property
    def inner_x1(self): return max([drw.inner_x1 + drw.shift_x for drw in self], default=0)
    @property
    def inner_y0(self): return min([drw.inner_y0 + drw.shift_y for drw in self], default=0)
    @property
    def inner_y1(self): return max([drw.inner_y1 + drw.shift_y for drw in self], default=0)

    @property
    def outer_x0(self): return min([drw.outer_x0 + drw.shift_x for drw in self], default=0) - self.margin_left
    @property
    def outer_x1(self): return max([drw.outer_x1 + drw.shift_x for drw in self], default=0) + self.margin_right
    @property
    def outer_y0(self): return min([drw.outer_y0 + drw.shift_y for drw in self], default=0) - self.margin_bottom
    @property
    def outer_y1(self): return max([drw.outer_y1 + drw.shift_y for drw in self], default=0) + self.margin_top


    def render(self, canvas, debug=False):
        for drw in sorted(self.items, key=lambda x: x.z):
            try:
                layer = drw.make(debug=debug)
                canvas.paste(
                    drw.outer_x0 + drw.shift_x,
                    drw.outer_y0 + drw.shift_y,
                    layer)
            except:
                if debug:
                    print(f'Effor when drawing {drw} in {self}, ignoring in the debug mode')
                else:
                    raise
        self.render_margins(canvas, debug=debug)
        return canvas

    def render_margins(self, canvas, debug=False):
        if self.title:
            self.title.draw(
                canvas, self.inner_xc, self.outer_y1, pos='.v')
        if self.caption:
            self.caption.draw(
                canvas, self.inner_xc, self.outer_y0, pos='.^')
        if self.panel_name:
            self.panel_name.draw(
                canvas, self.outer_x0, self.inner_y1, pos='>v')

    def group(self, label=''):
        self._group_label = label
        return self

    def _unpack(self):
        if self._group_label is not None or self.title or self.caption or self.panel_name:
            return [self]
        for drw in self:
            drw.move(self.shift_x, self.shift_y)
        self.shift_x = 0
        self.shift_y = 0
        return self.items[:]


    def __str__(self):
        caption = self._group_label or self.title.text or self.caption.text or ''
        return f'{self.__class__.__name__}({caption}) of len {len(self)}'
    def __repr__(self):
        return self.tree_repr(2)
    def tree_repr(self, level=2):
        if level == 0:
            return str(self)
        lines = [str(self) + ':']
        for drw in self:
            if hasattr(drw, 'tree_repr'):
                lines += drw.tree_repr(level-1).split('\n')
            else:
                lines += [repr(drw)]
        return '\n    '.join(lines)


# declare the missing reference
FloatingDrawable._ref_to_Figure = Figure



def matrix(M: List[List[FloatingDrawable]], sep=SEPARATOR) -> Figure:
    height = [max(panel.outer_h for panel in row if panel is not None) + sep for row in M]
    length = [max(panel.outer_w for panel in col if panel is not None) + sep for col in zip(*M)]
    F = Figure()
    for i, row in enumerate(M):
        for j, drw in enumerate(row):
            if isinstance(drw, FloatingDrawable):  # this could be None
                drw.move( sum(length[:j])   - drw.inner_x0,
                         -sum(height[:i+1]) - drw.inner_y0)
                F.append(drw)
    return F


def as_rows(drawables: List[FloatingDrawable], w=2000, sep=SEPARATOR) -> Figure:
    column = []
    while drawables:
        row = []
        size = 0
        while drawables and size < w:
            drw, *drawables = drawables
            row += [drw]
            size += drw.outer_w + sep
        column += [Figure.from_row(row, sep=sep)]
    return Figure.from_column(column, sep=sep)


def as_cols(drawables: List[FloatingDrawable], h=2000, sep=SEPARATOR) -> Figure:
    row = []
    while drawables:
        column = []
        size = 0
        while drawables and size < h:
            drw, *drawables = drawables
            column += [drw]
            size += drw.outer_h + sep
        row += [Figure.from_column(column, sep=sep)]
    return Figure.from_row(row, sep=sep)

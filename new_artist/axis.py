from new_artist.canvas import Canvas
from new_artist.font import FontDescriptor, Font
from new_artist.color import Color, ColorDescriptor
from new_artist.dimension import PixelDimension


class Caption:
    font = FontDescriptor()

    def __init__(self, text='', font='caption'):
        self.text = text
        self.font = font

    def __bool__(self):
        return bool(self.text)

    @property
    def pixel_w(self):
        if self.text:
            return self.font.measure_w(self.text)
        return 0
    @property
    def pixel_h(self):
        if self.text:
            return self.font.measure_h(self.text)
        return 0

    def draw(self, canvas, x, y, pos, debug=False):
        canvas.write(x, y, self.text, font=self.font, pos=pos)

    def __str__(self):
        return f'{self.__class__.__name__} {self.__dict__}'



def draw_labels(canvas: Canvas, a, b, y, ticks: dict, col: Color, font: Font, debug=False):
    # labels
    ticks = [(loc, label) for loc, label in sorted(ticks.items()) if label is not None]
    left, right = a-font.max_h, b+font.max_h

    if len(ticks) > 0:
        # border ticks label
        # left tick
        (loc, label), *ticks = ticks
        size = font.measure_w(label)
        loc = max(left + size//2, loc)
        loc = min(right - size//2, loc)
        canvas.write(loc, y-15, label, font=font, pos='.v', debug=debug)
        left = loc + font.measure_w(label.split('\n')[0])/2

    if len(ticks) > 0:
        # right tick
        *ticks, (loc, label) = ticks
        size = font.measure_w(label)
        loc = min(right - size//2, loc)
        canvas.write(loc, y-15, label, font=font, pos='.v', debug=debug)
        right = loc - font.measure_w(label.split('\n')[0])/2

    for loc, label in ticks:
        size = font.measure_w(label)
        if left + size/2 <= loc <= right - size/2:
            canvas.write(loc, y-15, label, font=font, pos='.v', debug=debug)
        elif debug:
            canvas.write(loc, y-15, label, font=font, pos='.v', debug=True, col='r')


def draw_labels_perp(canvas, a, b, y, ticks: dict, col: Color, font: Font, debug=False):
    # labels
    ticks = [(loc, label) for loc, label in sorted(ticks.items()) if label is not None]
    left, right = a, b
    if len(ticks) > 0:
        # border ticks label
        # left tick
        (loc, label), *ticks = ticks
        canvas.write(loc, y-15, label, font=font, pos='v.', debug=debug)
        left = loc + font.max_h * 0.7

    if len(ticks) > 0:
        # right tick
        *ticks, (loc, label) = ticks
        canvas.write(loc, y-15, label, font=font, pos='v.', debug=debug)
        right = loc - font.max_h * 0.7

    for loc, label in ticks:
        if left <= loc <= right:
            canvas.write(loc, y-15, label, font=font, pos='v.', debug=debug)
        elif debug:
            canvas.write(loc, y-15, label, font=font, pos='v.', debug=True, col='r')


def draw_axis(canvas: Canvas, a, b, y, ticks: dict, col: Color, font: Font, point_right=True):
    """ for testing purposes """
    lines = [(loc, 4 if label is None else 7) for loc, label in ticks.items()]
    canvas.horizontal_arrow([a, b+15], y-6, col=col, ticks=lines)
    draw_labels(canvas, a, b, y, ticks, col, font)

def draw_axis_perp(canvas: Canvas, a, b, y, ticks: dict, col: Color, font: Font, point_right=True):
    """ for testing purposes """
    lines = [(loc, 4 if label is None else 7) for loc, label in ticks.items()]
    canvas.horizontal_arrow([a, b+15], y-6, col=col, ticks=lines)
    draw_labels_perp(canvas, a, b, y, ticks, col, font)



class Axis:

    ticks_font = FontDescriptor()
    text_font = FontDescriptor()
    col = ColorDescriptor()

    dimension: PixelDimension

    def __init__(self, dimension, text='', ticks=None,
                 col='axis', text_font='axis', ticks_font=('axis', '-', 'k'), font=None,
                 ticks_scale=None, arrow_type=None):
        self.dimension = dimension
        self.text = text
        self.user_ticks = ticks

        if font:
            self.ticks_font = font
            self.text_font = font
        else:
            self.ticks_font = ticks_font
            self.text_font = text_font

        self.ticks_scale = ticks_scale
        self.arrow_type = arrow_type

        self.col = col

    def __bool__(self):
        return True

    def __setattr__(self, key, value):
        """ prevent incorrect assignemnts """
        if key in ('label', 'caption', 'name'):
            raise AttributeError(f'Axis have no such attribute as "{key}". Did you mean "text" instead?')
        if key == 'font':
            super().__setattr__('ticks_font', value)
            super().__setattr__('text_font', value)
        super().__setattr__(key, value)

    def update(self, **kwargs):
        for key, value in kwargs.items():
            setattr(self, key, value)

    @property
    def pixel_w(self):
        return self.ticks_font.max_h
    @property
    def pixel_h(self):
        labels_h = max([self.ticks_font.measure_h(s) for s in self.ticks.values() if s is not None], default=10)
        if self.text:
            return 20 + labels_h + self.text_font.measure_h(self.text)
        else:
            return 15 + labels_h


    @property
    def ticks(self):
        return self.make_ticks(defaults=self.user_ticks)
    @ticks.setter
    def ticks(self, value):
        self.user_ticks = value

    def make_ticks(self, defaults=None) -> dict:
        min_interval = self.ticks_font.standard_w
        min_interval *= self.ticks_scale or self.dimension.mapping.suggested_ticks_scale

        return self.dimension.get_ticks(
            min_interval=min_interval,
            defaults=defaults,
            multiline=True)


    def draw(self, canvas, debug=False):
        a, b = self.dimension.pixel_domain
        ticks = self.ticks
        self.draw_arrow(canvas, a, b, ticks, debug=debug)
        self.draw_labels(canvas, a, b, ticks, debug=debug)
        if self.text:
            self.draw_caption(canvas, a, b, debug=debug)

    def draw_arrow(self, canvas, a, b, ticks, debug=False):
        arrow_type = self.arrow_type or self.dimension.mapping.suggested_arrow_type

        if arrow_type == 'normal':
            for x, label in ticks.items():
                if label is None:
                    canvas.rect([x, x-1], [-6, -10], self.col)
                else:
                    canvas.rect([x, x-1], [-6, -13], self.col)

            if self.dimension.k >= 0:
                canvas.horizontal_arrow([a, b+15], -6, col=self.col)
            else:
                canvas.horizontal_arrow([b, a-15], -6, col=self.col)

        if arrow_type == 'cat':
            for x, label in ticks.items():
                canvas.rect([x, x-1], [-6, -13], self.col)
                canvas.rect([x+6, x-7], [-6, -5], self.col)

        if arrow_type == 'bins':
            if self.dimension.k >= 0:
                canvas.horizontal_arrow([a, b+15], -6, col=self.col)
                for x, label in ticks.items():
                    if x != a:
                        canvas.rect([x+1, x+2], [-6, -13], self.col)
                        canvas.rect([x,   x-5], [-6, -7], (0, 0, 0, 0))
                       # canvas.rect([x-2, x-3], [-6, -9], self.col)
                    else:
                        canvas.rect([x, x-1], [-6, -13], self.col)
            else:
                canvas.horizontal_arrow([b, a-15], -6, col=self.col)
                for x, label in ticks.items():
                    if x != b:
                        canvas.rect([x+1, x+2], [-6, -9], self.col)
                        canvas.rect([x,   x-5], [-6, -7], (0, 0, 0, 0))
                       # canvas.rect([x-2, x-3], [-6, -13], self.col)
                    else:
                        canvas.rect([x, x-1], [-6, -13], self.col)


    def draw_labels(self, canvas, a, b, ticks, debug=False):
        draw_labels(canvas, a, b, y=0, ticks=ticks, col=self.col, font=self.ticks_font, debug=debug)

    def draw_caption(self, canvas, a, b, debug=False):
        canvas.write((a+b)//2, 5-self.pixel_h, self.text, font=self.text_font, pos='.^', debug=debug)


    def __repr__(self):
        return f'{self.__class__.__name__} {self.__dict__}'


class AxisOnlyCaption(Axis):

    def __bool__(self):
        return bool(self.text)

    @property
    def pixel_w(self):
        return self.ticks_font.max_h // 2
    @property
    def pixel_h(self):
        if self.text:
            return 10 + self.text_font.measure_h(self.text)
        else:
            return 0

    def draw(self, canvas, debug=False):
        a, b = self.dimension.pixel_domain
        if self.text:
            self.draw_caption(canvas, a, b, debug=debug)


class AxisWithPerpendicularLabels(Axis):

    @property
    def pixel_w(self):
        return 0
    @property
    def pixel_h(self):
        labels_w = max([self.ticks_font.measure_w(s) for s in self.ticks.values() if s is not None], default=10)

        if self.text:
            return 25 + labels_w + self.text_font.measure_h(self.text)
        else:
            return 15 + labels_w

    def make_ticks(self, defaults=None) -> dict:
        ticks_scale = self.ticks_scale or self.dimension.mapping.suggested_ticks_scale_perp
        if ticks_scale:
            min_interval = self.ticks_font.max_h * ticks_scale
        else:
            min_interval = self.ticks_font.standard_w
            min_interval *= self.dimension.mapping.suggested_ticks_scale

        return self.dimension.get_ticks(
            min_interval=min_interval,
            defaults=defaults,
            multiline=False)

    def draw_labels(self, canvas, a, b, ticks, debug=False):
        draw_labels_perp(canvas, a, b, y=0, ticks=ticks, col=self.col, font=self.ticks_font, debug=debug)

# ====================================



def make_axis(dimension, text, symbol):
    if symbol*2 in text:
        return AxisWithPerpendicularLabels(dimension)
    elif symbol in text:
        return Axis(dimension)
    else:
        return AxisOnlyCaption(dimension)


class CaptionDescriptor:
    def __set_name__(self, owner, name): self.name = name
    def __get__(self, obj, cls): return obj.__dict__[self.name]
    def __set__(self, obj, value):
        if isinstance(value, Caption):
            obj.__dict__[self.name] = value
        elif isinstance(value, str):
            obj.__dict__[self.name].text = value
        else:
            raise AttributeError("CaptionDescriptor can only be assigned Caption object or string")


class AxisDescriptor:
    def __set_name__(self, owner, name): self.name = name
    def __get__(self, obj, cls): return obj.__dict__[self.name]
    def __set__(self, obj, value):
        if isinstance(value, Axis):
            obj.__dict__[self.name] = value
            return

        axis = obj.__dict__[self.name]
        if isinstance(value, str):
            axis.text = value
        elif isinstance(value, (tuple, list, set, dict)):
            axis.ticks = value
        elif value is None:
            obj.__dict__[self.name] = AxisOnlyCaption(dimension=axis.dimension, text='', ticks=axis.user_ticks)
        elif value is False:
            obj.__dict__[self.name] = AxisOnlyCaption(dimension=axis.dimension, text=axis.text, ticks=axis.user_ticks)
        elif value is True:
            if isinstance(axis, AxisOnlyCaption):
                obj.__dict__[self.name] = Axis(dimension=axis.dimension, text=axis.text, ticks=axis.user_ticks)
        else:
            raise AttributeError("AxisDescriptor can only be assigned Axis object, str, tuple, list, set, dict, None, True or False")

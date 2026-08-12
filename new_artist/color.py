'''
Operations with color
'''

# *** BEST PLACE FOR STRUCTURAL PATTER MATCHING
# SPM
# *** Also place for postponed annotations

import typing
import colorsys
from math import isnan

from PIL import ImageColor
from new_artist.base import Number, Sequence


def _to_0_255(x) -> int:
    return 0 if x < 0 else 255 if x > 255 else int(x)


class Color(tuple):

    def __new__(cls, first_arg, *rest_args):
        if not rest_args:
            # simple copy
            if isinstance(first_arg, Color):
                return tuple.__new__(cls, first_arg)

            # in cases this is a string, use functions
            if isinstance(first_arg, str):
                return cls.from_function(first_arg)

            # in cases this is a tuple, open up
            if isinstance(first_arg, Sequence):
                return cls(*first_arg)

            # single number represent basic color sequence
            if isinstance(first_arg, Number):
                return basic_color_sequence(first_arg)

            # None
            elif first_arg is None:
                return None

        # color is represented in RGB (or RGBA) form
        if isinstance(first_arg, Number):
            return cls.from_RGB(first_arg, *rest_args)

        # color is either coming from Color library or from function library
        if isinstance(first_arg, str):
            return cls.from_function(first_arg, *rest_args)

        raise KeyError(f'wrong argument in Color(): {(first_arg, ) + rest_args}')

    @classmethod
    def from_RGB(cls, r, g, b, a=255) -> 'Color':
        r = _to_0_255(r)
        g = _to_0_255(g)
        b = _to_0_255(b)
        a = _to_0_255(a)
        return tuple.__new__(cls, (r, g, b, a))

    @classmethod
    def from_function(cls, func: str, *args) -> 'Color':
        if func in COLOR_LIBRARY:
            return cls.from_RGB(*COLOR_LIBRARY[func], *args)

        elif func in FUNCTION_LIBRARY:
            return FUNCTION_LIBRARY[func](*args)

        # modifications
        elif len(func) and func[0] in '+-^_=':
            if   func.startswith('+++'): return cls.from_function(func[3:], *args).to_white(0.9)
            elif func.startswith('++'):  return cls.from_function(func[2:], *args).to_white(0.5)
            elif func.startswith('+'):   return cls.from_function(func[1:], *args).to_white(0.25)

            elif func.startswith('---'): return cls.from_function(func[3:], *args).to_black(0.9)
            elif func.startswith('--'):  return cls.from_function(func[2:], *args).to_black(0.5)
            elif func.startswith('-'):   return cls.from_function(func[1:], *args).to_black(0.25)

            elif func.startswith('=='):  return cls.from_function(func[1:], *args).to_gray(0.9)
            elif func.startswith('='):   return cls.from_function(func[1:], *args).to_gray(0.5)

            elif func.startswith('___'): return cls.from_function(func[3:], *args).alpha(0.1)
            elif func.startswith('__'):  return cls.from_function(func[2:], *args).alpha(0.5)
            elif func.startswith('_'):   return cls.from_function(func[1:], *args).alpha(0.75)

        else:
            try:
                return cls.from_RGB(*ImageColor.getrgb(func))
            except:
                raise KeyError(f'wrong argument in Color(): {(func, ) + args}') from None

    def merge(self, other, fraction=0.5, alpha=None) -> 'Color':
        r0, g0, b0, a0 = self
        r1, g1, b1, a1 = Color(other)
        return Color.from_RGB(
            r1*fraction + r0*(1-fraction),
            g1*fraction + g0*(1-fraction),
            b1*fraction + b0*(1-fraction),
            a0*fraction + a1*(1-fraction) if alpha is None else alpha)

    def to_white(self, x) -> 'Color':
        return self.merge('white', x)
    def to_black(self, x) -> 'Color':
        return self.merge('black', x)
    def to_gray(self, x) -> 'Color':
        return self.merge('gray', x)

    def alpha(self, a=None) -> 'Color':
        r, g, b, old_a = self
        return Color.from_RGB(r, g, b, old_a if a is None else a*255)

    def power(self, x) -> 'Color':
        if x < 1:
            return self.alpha(x)
        else:
            return self.to_black(min(x-1, 0.3))

    def text_color(self) -> 'Color':
        if sum(self)<609:
            return Color.from_RGB(255, 255, 255)
        else:
            return Color.from_RGB(0, 0, 0)

    def opposite(self) -> 'Color':
        r, g, b, a = self
        return Color.from_RGB(255-r, 255-g, 255-b, a)

    def __repr__(self):
        r, g, b, a = self
        return f'Color({r}, {g}, {b}, {a})'


def merge(color0, color1, fraction, alpha=None) -> Color:
    return Color(color0).merge(color1, fraction, alpha)


# Color library
# ===================


# (list of aliases): Color
COLOR_LIBRARY = {
    ('transparent', 'a', 'A'):  (  0,   0,   0,   0),

    ('white',   'w', 'W'):  (255, 255, 255),
    ('gray',            ):  (128, 128, 128),
    ('black',   'k', 'K'):  (  0,   0,   0),

    ('red',          'r'):  (180,   0,   0),
    ('green',        'g'):  ( 30, 200,  30),
    ('blue',         'b'):  ( 10,  10, 170),
    ('yellow',       'y'):  (200, 170,  20),
    ('magenta',      'm'):  (160,   0, 170),
    ('cyan',         'c'):  (  0, 160, 170),
    ('orange',       'o'):  (242, 130,  55),
    ('purple',       'p'):  (100,   0, 200),

    ('pure red',     'R'):  (255,   0,   0),
    ('pure green',   'G'):  (  0, 255,   0),
    ('pure blue',    'B'):  (  0,   0, 255),
    ('pure yellow',  'Y'):  (255, 255,   0),
    ('pure magenta', 'M'):  (255,   0, 255),
    ('pure cyan',    'C'):  (  0, 255, 255),
    ('pure orange',  'O'):  (250, 100,   0),
    ('pure purple',  'P'):  (128,   0, 255),

    ('caption'):            (  0,   0,   0),
    ('label', 'l', 'L'):    ( 50,  50,  50),
    ('axis name'):          ( 50,  50,  50),
    ('axis', 'X', 'x'):     (150, 150, 150),
    ('ticks'):              (150, 150, 150),
    ('grid', '#'):          (205, 205, 205),

    ('background', 'bg'):   (255, 255, 255),

    '_debug':      (0, 20, 30),
    }

# open up aliases
COLOR_LIBRARY = {name: Color.from_RGB(*color) for aliases, color in COLOR_LIBRARY.items() for name in (aliases if isinstance(aliases, tuple) else [aliases]) }



# Color-generating Functions
# ==========================


# this is used to define the basic color sequence of 10 color
#                                           0 1 2 3 4 5 6 7 8 9
_BASIC_COLOR_SEQIENCE = [Color(c) for c in 'w k r b g m y c o p'.split()]
# note that here red is followed by blue, not green


def basic_color_sequence(x: Number) -> Color:
    """
         x < -1 : black
    -1 < x <  0 : shades of transparent black
     0 < x <  9 : different colors from the basic color sequence
     9 < x      : looping basic color sequence without white
          +inf  : white
    """
    if x < 0:
        return Color.from_RGB(0, 0, 0, -x*255)
    elif x < 1:
        gray = 255 - x*255
        return Color.from_RGB(gray, gray, gray)
    elif x == float('inf'):
        return Color.from_RGB(255, 255, 255)
    else:
        return _BASIC_COLOR_SEQIENCE[int(x-1) % 9 + 1].merge(_BASIC_COLOR_SEQIENCE[int(x) % 9 + 1], x % 1)


def hsv2rgb(h, s=255, v=255, alpha=255) -> Color:
    r, g, b = colorsys.hsv_to_rgb(h, s/255, v/255)
    return Color.from_RGB(r*255, g*255, b*255, alpha)


def hue2rgb(h, alpha=255) -> Color:
    return hsv2rgb(h, alpha=alpha)


def random_color(alpha=255) -> Color:
    import random
    return hsv2rgb(h=random.random(),
                   s=random.randint(0, 100) + 155,
                   v=random.randint(0, 100) + 155,
                   alpha=alpha)


def hash_color(x, alpha=255) -> Color:
    h = (hash(x)+hash(str(x)))**2
    return hsv2rgb(h=((634*h) % 1000) / 1000,
                   s=(932*h) % 100 + 155,
                   v=(421*h) % 100 + 155,
                   alpha=alpha)


def two_letters_hash_color(s, alpha=255) -> Color:
    c1, c2, *_ = s
    return merge(hash_color(c1), hash_color(c2), 0.7)


def make_gradient(*gradient_points) -> typing.Callable[[Number], Color]:
    """ Creates a functions, representing a gradient """
    gradient_points = [(k, Color(v)) for k, v in gradient_points]

    def gradient(x, alpha=None):
        if x is None or (isinstance(x, float) and isnan(x)):
            return None
        points = gradient_points[:]
        (x0, col0), *points = points
        if x <= x0:
            return col0.alpha(alpha)

        for x1, col1  in points:
            if x0 <= x <= x1:
                fraction = (x-x0)/(x1-x0)
                return col0.merge(col1, fraction, alpha=alpha)
            x0, col0 = x1, col1
        return col0.alpha(alpha)

    return gradient


FUNCTION_LIBRARY = {
    'basic_color_sequence': basic_color_sequence,
    'hsv': hsv2rgb,
    'hue': hue2rgb,
    'random': random_color,
    'hash': hash_color,
    '2hash': two_letters_hash_color,
    'sequence': basic_color_sequence,

    'alpha': lambda x: Color.from_RGB(0, 0, 0, x*255),
    'grayscale': make_gradient(
        (0, 'w'),
        (1, 'k')),
    'heat': make_gradient(
        (0.0, 'B'),
        (1/3, 'C'),
        (2/3, 'Y'),
        (1.0, 'R')),
    'night': make_gradient(
        (0.00, (255, 255, 255)),
        (0.25, (255, 100, 100)),
        (0.50, (200, 200,   0)),
        (0.75, (  0, 150, 150)),
        (1.00, (  0,   0, 50))),
    'temp': make_gradient(
        (-1, 'B'),
        ( 0, 'w'),
        ( 1, 'R')),
    'temp01': make_gradient(
        ( 0,   'B'),
        ( 1/2, 'w'),
        ( 1,   'R')),
    'corr': make_gradient(
        (-1, (100, 100, 255)),
        ( 0, (150, 150, 150)),
        ( 1, (255, 170, 10))),
    'corr01': make_gradient(
        (0.0, (100, 100, 255)),
        (0.5, (150, 150, 150)),
        (1.0, (255, 170, 10))),
    'black body': make_gradient(
        (0.0,            (255, 255, 255)),
        (0.142857142857, (233, 216,  57)),
        (0.285714285714, (245, 151,  48)),
        (0.428571428571, (235,  83,  60)),
        (0.571428571429, (198,   0, 116)),
        (0.714285714286, ( 93,   0, 200)),
        (0.857142857143, ( 43,  15, 107)),
        (1.0,            (  0,   0,   0))),
    'viridis': make_gradient(
        (0.00, (252, 229,  30)),
        (0.11, (171, 219,  32)),
        (0.22, (101, 202,  68)),
        (0.33, ( 52, 178,  98)),
        (0.44, ( 32, 148, 115)),
        (0.55, ( 31, 120, 122)),
        (0.66, ( 36,  93, 123)),
        (0.77, ( 44,  63, 121)),
        (0.88, ( 53,  37, 110)),
        (1.00, ( 52,   0,  66))),
    'batlow': make_gradient(
        (0.0, (251, 197, 232)),
        (0.1, (253, 180, 180)),
        (0.2, (247, 161, 124)),
        (0.3, (215, 148,  74)),
        (0.4, (168, 139,  47)),
        (0.5, (123, 128,  52)),
        (0.6, ( 84, 116,  72)),
        (0.7, ( 46, 100,  91)),
        (0.8, ( 23,  77,  97)),
        (0.9, ( 12,  51,  93)),
        (1.0, (  0,  26,  90))),
    'age': make_gradient(
        (0.0, (100, 255, 100)),
        (0.4, (150,  80,  40)),
        (0.8, (  0,   0, 150)),
        (1.0, (200, 200, 200))),
    'calendar': make_gradient(
        (1.5 / 12, (100, 100, 150)),
        (2.5 / 12, (100, 255, 100)),
        (4.5 / 12, (100, 255, 100)),
        (5.5 / 12, (100, 125, 20)),
        (7.5 / 12, (100, 125, 20)),
        (8.5 / 12, (240, 170,  20)),
        (10.5 / 12, (240, 170,  20)),
        (11.5 / 12, (100, 100, 150))),
    }


# Color Descriptor
# =================


class ColorDescriptor:
    def __set_name__(self, owner, name): self.name = name
    def __get__(self, obj, cls): return obj.__dict__[self.name]
    def __set__(self, obj, value):
        obj.__dict__[self.name] = Color(value)

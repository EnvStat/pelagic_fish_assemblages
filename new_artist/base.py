import math
from math import log, log10, floor, ceil, nan
from typing import Tuple


# Constants
# ================

VERY_LARGE_NUMBER = 10**6


# Type checking
# ================

from collections.abc import Sequence
from numbers import Integral, Number
from datetime import date


def is_integer(x):
    return isinstance(x, Integral) or x.is_integer()


# Representing number
# ================

def first_meaningfull_digit(x) -> int:
    return floor(log10(abs(x)))+1 if x else -100

def nice_string_format(value, meanigful_digits=3, resolution=None, unit='', round_to_5=False) -> str:
    if not isinstance(value, Number):
        return str(value)

    if value == 0:
        return '0'

    if resolution is None:
        resolution = -first_meaningfull_digit(value) + meanigful_digits

    if round_to_5:
        rounded = round(value*2, resolution)/2
    else:
        rounded = round(value, resolution)

    if is_integer(rounded) or resolution <= 0:
        return '{:_}'.format(int(rounded)).replace('_', ' ') + unit
    else:
        return str(rounded) + unit


def goodround(x, n=2):
    if x==0:
        return '0'
    h = math.log10(abs(x))
    x = round(x, n-1-int(h))
    if int(x) == x:
        return str(int(x))
    else:
        return str(x)


# Coords
# ================

def unpack_xy(*args):
    # *** pattern matching
    try:
        x, y = args
        return x, y
    except ValueError:
        pass

    try:
        ((x, y), ) = args
        return x, y
    except TypeError:
        pass

    raise ValueError(f'Expected 2 coordinates; received {args}')


def unpack_xyxy(*args):
    # *** pattern matching
    try:
        (x0, y0, x1, y1) = args
        return x0, y0, x1, y1
    except ValueError:
        pass

    try:
        (x0, x1), (y0, y1) = args
        return x0, y0, x1, y1
    except (ValueError, TypeError):
        pass

    try:
        (((x0, y0), (x1, y1)), ) = args
        return x0, y0, x1, y1
    except (ValueError, TypeError):
        pass

    try:
        ((x0, y0, x1, y1), ) = args
        return x0, y0, x1, y1
    except (ValueError, TypeError):
        pass

    raise ValueError(f'Expected 4 coordinates; received {args}')


def unpack_xxxyyy(X, Y=None):
    # *** pattern matching
    if Y is None:
        if isinstance(X, dict):
            return list(X.keys()), list(X.values())
        try:
            X, Y = zip(*X)
        except TypeError:
            X, Y = range(len(X)), X
    return list(X), list(Y)


def unpack_xyxy_or_wh(*args):
    # *** pattern matching
    try:
        x0, y0, x1, y1 = unpack_xyxy(*args)
        return x0, y0, x1, y1
    except ValueError:
        pass

    try:
        (x1, y1) = unpack_xy(*args)
        return 0, 0, x1-1, y1-1
    except ValueError:
        pass

    raise ValueError(f'Expected 4 or 2 coordinates; received {args}')


def unpack_xyxy_or_xyr(*args):
    # *** pattern matching
    try:
        ((x, y, r), ) = args
        return x-r, y-r, x+r, y+r
    except ValueError:
        pass

    try:
        (x, y, r, ) = args
        return x-r, y-r, x+r, y+r
    except ValueError:
        pass

    try:
        return unpack_xyxy(*args)
    except ValueError:
        pass

    raise ValueError(f'Expected 4 coordinates or 2 coordinates and radius; received {args}')


def unpack_matrix(M, default_step, x_borders=None, y_borders=None, x_vals=None, y_vals=None):
    h = len(M)
    w = len(M[0])
    linearize_data = [M[i][j] for j in range(w) for i in range(h)]
    if len(linearize_data) != h*w:
        raise ValueError(f'Wrong size of the matrix: expected {w}*{h}={w*h} elements, got {len(linearize_data)}')

    # there is two way to define image: with borders or with values
    # we need to unpack these

    if x_borders is not None and x_vals is not None:
        raise ValueError('Only x_borders or x_vals can be defined, not both')
    elif x_vals is not None:
        if len(x_vals) != w:
            raise ValueError(f'len(x_vals) should be equal to w, got {len(x_vals)} != {w}')
        data_x = x_vals
    elif x_borders is not None:
        if len(x_borders) != w+1:
            raise ValueError(f'len(x_borders) should be equal to w+1, got {len(x_borders)} != {w+1}')
        data_x = x_borders
    else:
        data_x = [i*default_step for i in range(w)]

    if y_borders is not None and y_vals is not None:
        raise ValueError('Only y_borders or y_vals can be defined, not both')
    elif y_vals is not None:
        if len(y_vals) != h:
            raise ValueError(f'len(y_vals) should be equal to h, got {len(y_vals)} != {h}')
        data_y = y_vals
    elif y_borders is not None:
        if len(y_borders) != h+1:
            raise ValueError(f'len(y_borders) should be equal to h+1, got {len(y_borders)} != {h+1}')
        data_y = y_borders
    else:
        data_y = [i*default_step for i in range(h-1, -1, -1)]

    return linearize_data, data_x, data_y


def pos_to_shift(w:int, h:int, pos:str) -> Tuple[int, int, bool]:  # *** replace Tuple with tuple
    dx, dy, rotated = {
        '<^': (w-1,  0,    False),
        '<.': (w-1,  h//2, False),
        '<v': (w-1,  h-1,  False),
        '.^': (w//2, 0,    False),
        '..': (w//2, h//2, False),
        '.v': (w//2, h-1,  False),
        '>^': (0,    0,    False),
        '>.': (0,    h//2, False),
        '>v': (0,    h-1,  False),

        '^<': (h-1,  0,    True),
        '.<': (h-1,  w//2, True),
        'v<': (h-1,  w-1,  True),
        '^.': (h//2, 0,    True),
        ':':  (h//2, w//2, True),
        'v.': (h//2, w-1,  True),
        '^>': (0,    0,    True),
        '.>': (0,    w//2, True),
        'v>': (0,    w-1,  True),

        '<':  (w-1,  h//2, False),
        '.':  (w//2, h//2, False),
        '>':  (0,    h//2, False),
        '^':  (h//2, 0,    True),
        'v':  (h//2, w-1,  True),
        }[pos]
    return -dx, -dy, rotated


def pos_to_alignment(pos:str) -> str:
    return {
        '<': 'right',
        'v': 'right',
        '.': 'center',
        ':': 'center',
        '>': 'left',
        '^': 'left'}[pos[0]]

def rotate_margins(margin:dir, pos:str) -> Tuple[dir, bool]:  # *** replace Tuple with tuple
    margin, x_y_swap = {
        '>^': ({'<': margin['<'],   'v': margin['v'],   '>': margin['>'],   '^': margin['^']},   False),
        '>v': ({'<': margin['<'],   'v': margin['^'],   '>': margin['>'],   '^': margin['v']},   False),
        '<^': ({'<': margin['>'],   'v': margin['v'],   '>': margin['<'],   '^': margin['^']},   False),
        '<v': ({'<': margin['>'],   'v': margin['^'],   '>': margin['<'],   '^': margin['v']},   False),
        '^>': ({'<': margin['v'],   'v': margin['<'],   '>': margin['^'],   '^': margin['>']},   True),
        'v>': ({'<': margin['v'],   'v': margin['>'],   '>': margin['^'],   '^': margin['<']},   True),
        '^<': ({'<': margin['^'],   'v': margin['<'],   '>': margin['v'],   '^': margin['>']},   True),
        'v<': ({'<': margin['^'],   'v': margin['>'],   '>': margin['v'],   '^': margin['<']},   True),
        }[pos]
    return margin, x_y_swap


class Direction():
    """
    Encodes the direction of drawing.
    """
    def __init__(self, string='>^'):
        self._matr = {
            '>^': [[ 1,  0], [ 0,  1]],
            '>v': [[ 1,  0], [ 0, -1]],
            '<^': [[-1,  0], [ 0,  1]],
            '<v': [[-1,  0], [ 0, -1]],
            '^>': [[ 0,  1], [ 1,  0]],
            'v>': [[ 0,  1], [-1,  0]],
            '^<': [[ 0, -1], [ 1,  0]],
            'v<': [[ 0, -1], [-1,  0]]
            }[string]

    def __getitem__(self, key):
        return self._matr[key[0]][key[1]]

    def __mul__(self, other):
        new = Direction.__new__(Direction)
        new._matr = [[self[0, 0]*other[0, 0] + self[0, 1]*other[1, 0],
                      self[0, 0]*other[0, 1] + self[0, 1]*other[1, 1]],
                     [self[1, 0]*other[0, 0] + self[1, 1]*other[1, 0],
                      self[1, 0]*other[0, 1] + self[1, 1]*other[1, 1]]]
        return new

    __imul__ = __mul__

    def __str__(self):
        return ({-1: '<', 0:'', 1: '>'}[self[0, 0]] + {-1: 'v', 0:'', 1: '^'}[self[1, 0]] +
                {-1: '<', 0:'', 1: '>'}[self[0, 1]] + {-1: 'v', 0:'', 1: '^'}[self[1, 1]])

    @property
    def vertical(self):
        return bool(self[1, 0])


# Histograms
# ================

def compute_bin_histogram(data, borders, precomputed=False, ensure_coverage=True):
    if precomputed:
        if isinstance(borders, Number):
            raise KeyError('precomputed histogram should have their borders defined')
        if len(borders)-1 != len(data):
            raise KeyError(f'In precomputed histogram len of data, len(borders)-1 = len(data), but len(borders) = {len(borders)} and len(data) = {len(data)}')
        return list(data), borders

    if borders is int:
        borders = [i-0.5 for i in range(min(data), max(data)+2)]
    elif isinstance(borders, Number):
        v_min, v_max = min(data), max(data)
        borders = [v_min + (i / borders) * (v_max - v_min) for i in range(borders+1)]
    else:
        borders = list(borders)

    if not data:
        return [0] * (len(borders)-1), borders

    data = list(sorted(data))
    if ensure_coverage:
        if data[0] < borders[0]:
            borders = [data[0]] + borders
        if data[-1] > borders[-1]:
            borders = borders + [data[-1]]

    # do the actual binning
    bins = list(zip(borders, borders[1:]))
    counts = [0] * len(bins)
    while data[0] < borders[0]:
        data = data[1:]

    for i, (a, b) in enumerate(bins):
        while data and a <= data[0] <= b:
            counts[i] += 1
            data = data[1:]

    return counts, borders

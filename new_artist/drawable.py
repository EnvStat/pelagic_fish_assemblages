from abc import ABC, abstractproperty, abstractclassmethod, abstractmethod
from typing import List

from new_artist.canvas import Canvas
from new_artist.color import Color
from new_artist import base


VERBOSE = False


# *** typing: replace List with list


class Drawable(ABC):
    """
    Abstact class to represent something drawable, i.e. something that can be turned into Canvas.

    Hierarchy of classes:

       [Drawable]
        |      |
      Plot    FloatingDrawable
               |            |
      DrawableCollection   Panel
               |
              Figure

    Each Drawable should have two sets of public coordinates: inner and outer. Outer coordinates describe the position and size of the whole drawable,
    while inner describe the "information-containing" parts, and can be used, for example, when aligning titles and captions.

    Attribures shift_x, shift_y and x describe the position of the Drawable, should it be places among other Drawables.
    """

    def __init__(self):
        self.__init_defaults__()

    def __init_defaults__(self):
        self.shift_x = 0
        self.shift_y = 0
        self.margin_left = 0
        self.margin_right = 0
        self.margin_bottom = 0
        self.margin_top = 0
        self.z = 0

    def move(self, dx, dy, dz=0):
        self.shift_x += dx
        self.shift_y += dy
        self.z += dz
        return self

    # inner coordinates refer to the pixel space where data is contained
    # they are abstract methods and will be defined in subclasses
    @abstractproperty
    def inner_x0(self): pass
    @abstractproperty
    def inner_x1(self): pass
    @abstractproperty
    def inner_y0(self): pass
    @abstractproperty
    def inner_y1(self): pass

    @property
    def inner_w(self):  return self.inner_x1 - self.inner_x0 + 1
    @property
    def inner_h(self):  return self.inner_y1 - self.inner_y0 + 1
    @property
    def inner_lower_left(self): return (self.inner_x0, self.inner_y0)
    @property
    def inner_box(self): return (self.inner_x0, self.inner_y0, self.inner_x1, self.inner_y1)
    @property
    def inner_xc(self):  return (self.inner_x1 + self.inner_x0) // 2
    @property
    def inner_yc(self):  return (self.inner_y1 + self.inner_y0) // 2


    # outer coordinates refer to the pixel space where drawing happens
    @property
    def outer_x0(self): return self.inner_x0 - self.margin_left
    @property
    def outer_x1(self): return self.inner_x1 + self.margin_right
    @property
    def outer_y0(self): return self.inner_y0 - self.margin_bottom
    @property
    def outer_y1(self): return self.inner_y1 + self.margin_top

    @property
    def outer_w(self):  return self.outer_x1 - self.outer_x0 + 1
    @property
    def outer_h(self):  return self.outer_y1 - self.outer_y0 + 1
    @property
    def outer_lower_left(self): return (self.outer_x0, self.outer_y0)
    @property
    def outer_box(self): return (self.outer_x0, self.outer_y0, self.outer_x1, self.outer_y1)
    @property
    def outer_xc(self):  return (self.outer_x1 + self.outer_x0) // 2
    @property
    def outer_yc(self):  return (self.outer_y1 + self.outer_y0) // 2

    @property
    def margins(self):
        return {'<': self.margin_left, 'v': self.margin_bottom, '>': self.margin_right, '^': self.margin_top}


    @abstractclassmethod
    def render(self, canvas):
        # self.draw(canvas)
        pass

    def make(self, bgcol: Color=(0, 0, 0, 0), margin: int=0, debug=False) -> Canvas:
        """ Creates a canvas with the image """
        canvas = Canvas(self.outer_box, bgcol, margin)
        self.render(canvas, debug=debug)
        if debug:
            canvas.add_debug_info(str(self))
        return canvas

    def show(self, bgcol: Color=(255, 255, 255), margin: int=10, debug=False, **kwargs) -> 'IPython.display.Image':
        """ Outputs the image to the IPython notebook"""
        return self.make(bgcol, margin, debug).show(**kwargs)

    def display(self, bgcol: Color=(255, 255, 255), margin: int=10, debug=False, **kwargs):
        """ Display the image"""
        return self.make(bgcol, margin, debug).display(**kwargs)

    def save(self, filename: str, bgcol: Color=(255, 255, 255), margin: int=10, debug=False):
        """ Save the image into file """
        self.make(bgcol, margin, debug).save(filename)
        if VERBOSE:
            print(filename, 'is ready')

    def __gt__(self, other):
        self.save(f'{other}.png')



class FloatingDrawable(Drawable):

    def __init__(self, items=()):
        self.__init_defaults__()

        self.margin_left = 0
        self.margin_right = 0
        self.margin_bottom = 0
        self.margin_top = 0

    def __init_defaults__(self):
        # dont initialize margins
        self.shift_x = 0
        self.shift_y = 0
        self.z = 0

        self.space_left = 0
        self.space_right = 0
        self.space_bottom = 0
        self.space_top = 0

    # This should be referencing to Figure, after Figure class would be declared
    _ref_to_Figure = None

    def _unpack(self):
        return [self]

    def __mul__(self, other) -> 'Figure':
        if isinstance(other, FloatingDrawable):
            return self._ref_to_Figure.from_stack(self, other)
        return NotImplemented

    def __add__(self, other) -> 'Figure':
        if isinstance(other, int):
            self.space_right += other
            return self
        if isinstance(other, FloatingDrawable):
            return self._ref_to_Figure.from_row([self, other])
        return NotImplemented

    def __radd__(self, other) -> 'Figure':
        if isinstance(other, int):
            self.space_left += other
            return self
        return NotImplemented

    def __floordiv__(self, other) -> 'Figure':
        if isinstance(other, int):
            self.space_bottom += other
            return self
        elif isinstance(other, FloatingDrawable):
            return self._ref_to_Figure.from_column([self, other])
        return NotImplemented

    def __truediv__(self, other) -> 'Figure':
        if isinstance(other, int):
            self.space_bottom += other
            return self
        elif isinstance(other, FloatingDrawable):
            return self._ref_to_Figure.from_column([self, other])
        return NotImplemented

    def __rfloordiv__(self, other) -> 'Figure':
        if isinstance(other, int):
            self.space_top += other
            return self
        return NotImplemented

    def __rtruediv__(self, other) -> 'Figure':
        if isinstance(other, int):
            self.space_top += other
            return self
        return NotImplemented

    __iadd__      = __add__
    __itruediv__  = __truediv__
    __ifloordiv__ = __floordiv__
    __imul__      = __mul__


# *** untested
class FloatingCanvas(Canvas, FloatingDrawable):

    def _init_coords(self, w, h, ox=0, oy=0):
        # dont initialize margins
        self.shift_x = 0
        self.shift_y = 0
        self.z = 0

        self.margin_left = 0
        self.margin_right = 0
        self.margin_bottom = 0
        self.margin_top = 0

        self.space_left = 0
        self.space_right = 0
        self.space_bottom = 0
        self.space_top = 0

        self.ox = ox
        self.oy = h - 1 - oy
        self.w = w
        self.h = h
        self.direction = base.Direction()

    @property
    def inner_x0(self): return -self.ox
    @property
    def inner_y0(self): return self.oy - self.h + 1
    @property
    def inner_x1(self): return -self.ox + self.w - 1
    @property
    def inner_y1(self): return self.oy

    def make(self):
        return self
    def render(self, canvas):
        pass

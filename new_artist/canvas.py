"""
Provide the interface with the basic drawing module:
    drawing
    image manipulation
In this case: Python Image Lib
"""

from math import isnan
from warnings import warn

from PIL import Image, ImageDraw, ImageShow

from new_artist.base import Direction, unpack_xyxy_or_wh, pos_to_shift, pos_to_alignment
from new_artist.font import Font
from new_artist.color import Color


MAX_IMAGE_SIZE = 30_000  # pixels


class Canvas():
    '''
    All the basic operations are performed throught this interface obsect
    '''
    def __init__(self, coords, bgcol=0, margin=0):
        x0, y0, x1, y1 = unpack_xyxy_or_wh(*coords)
        self._init_coords(
            w=x1 - x0 + 1 + margin*2,
            h=y1 - y0 + 1 + margin*2,
            ox=-x0 + margin,
            oy=-y0 + margin)

        w, h = self.w, self.h

        if w is None or h is None or isnan(w) or isnan(h) or w <= 0 or h <= 0:
            raise ValueError(f'Weird canvas size w="{w}" h="{h}"')
        if w > MAX_IMAGE_SIZE or h > MAX_IMAGE_SIZE:
            warn(f'Image size is too big! w={w} h={h}')
            self.w = w = min(MAX_IMAGE_SIZE, w)
            self.h = h = min(MAX_IMAGE_SIZE, h)

        self._init_img(Image.new('RGBA', (w, h), color=Color(bgcol)))

    def _init_coords(self, w, h, ox=0, oy=0):
        self.ox = ox
        self.oy = h - 1 - oy
        self.w = w
        self.h = h
        self.direction = Direction()

    def _init_img(self, img):
        self._img = img
        self._draw = ImageDraw.Draw(img)

    def inner_coords(self, x, y):
        """
        Transform x and y defined on the shifted axes, to x and y defined on Canvas' own axes
        """
        return (self.ox + self.direction[0, 0]*x + self.direction[0, 1]*y,
                self.oy - self.direction[1, 0]*x - self.direction[1, 1]*y)

    def inner_top_left(self, x, y, w, h):
        """
        For a given box, defined with a bottom-left corner in a shifted axes, width and height
        return coords of the top left corner on Canvas' own axes.
        """
        x, y = self.inner_coords(x, y)
        if self.direction[0, 0] == -1 or self.direction[0, 1] == -1: x -= w-1
        if self.direction[1, 0] ==  1 or self.direction[1, 1] ==  1: y -= h-1
        return x, y

    @property
    def x0(self): return -self.ox
    @property
    def y0(self): return self.oy - self.h + 1
    @property
    def x1(self): return -self.ox + self.w - 1
    @property
    def y1(self): return self.oy
    @property
    def size(self): return self.w, self.h

    def __repr__(self):
        return f'{self.__class__.__name__}(size={self.size}, origin={(self.ox, self.oy)})'

    # Alternative constructors
    # ========================

    @classmethod
    def load(cls, filename) -> 'Canvas':
        new = cls.__new__(cls)
        img = Image.open(filename)
        new._init_coords(w=img.size[0], h=img.size[1])
        new._init_img(img)
        return new

    @classmethod
    def _from_img(cls, img: Image) -> 'Canvas':
        new = cls.__new__(cls)
        new._init_coords(w=img.size[0], h=img.size[1])
        new._init_img(img)
        return new

    def view(self, dx, dy, rotation='>^') -> 'Canvas':
        new = self.__class__.__new__(self.__class__)
        new._init_img(self._img)
        new._init_coords(w=self.w, h=self.h, ox=self.ox+dx)
        new.oy = self.oy-dy
        new.direction = self.direction * Direction(rotation)
        return new


    # Modifications
    # =============

    def scaled(self, size) -> 'Canvas':
        return Canvas._from_img(self._img.thumbnail(size, Image.BICUBIC))

    def rotated(self, rotation):
        # >^ is considered to be standard
        if rotation == '>^':
            return self

        if rotation == '<^':
            transformed = self._img.transpose(Image.FLIP_LEFT_RIGHT)
        elif rotation == '>v':
            transformed = self._img.transpose(Image.FLIP_TOP_BOTTOM)
        elif rotation == '<v':
            transformed = self._img.transpose(Image.ROTATE_180)

        elif rotation == 'v<':
            transformed = self._img.transpose(Image.ROTATE_90).transpose(Image.FLIP_TOP_BOTTOM)
        elif rotation == '^<':
            transformed = self._img.transpose(Image.ROTATE_90)
        elif rotation == 'v>':
            transformed = self._img.transpose(Image.ROTATE_270)
        elif rotation == '^>':
            transformed = self._img.transpose(Image.ROTATE_270).transpose(Image.FLIP_TOP_BOTTOM)

        return Canvas._from_img(transformed)

    def to_bw(self) -> 'Canvas':
        return Canvas._from_img(self.img.convert('LA').convert('RGBA'))

    # Saving and showing
    # ===================

    def save(self, filename: str, debug=False):
        if filename.lower().endswith('.tiff'):
            self._img.save(filename, resolution=1200)
        elif filename.lower().endswith('.png'):
            self._img.save(filename, dpi=[150, 150])
        else:
            raise ValueError(f'Unknow resolution for the file: {filename}')

    def show(self, **kwargs) -> 'IPython.display.Image':
        from IPython.display import Image
        import io

        img_bytes = io.BytesIO()
        self._img.save(img_bytes, format='png')
        return Image(data=img_bytes.getvalue(), **kwargs)

    # *** after updating pillow:
    #def show(self, **kwargs) -> 'ImageShow.IPythonViewer':
        # return ImageShow.IPythonViewer(self._img, **kwargs)

    def display(self, **kwargs):
        return ImageShow.show(self._img)

    # Basic Drawing
    # =============
    # all following functions assume to recieve shifted coords, that are then transformed to actual coords

    def line(self, X, Y, col, p):
        if col and p:
            x0 = y0 = None
            for x1, y1 in zip(X, Y):
                if None not in (x1, y1):
                    x1, y1 = self.inner_coords(x1, y1)
                    if None not in (x0, y0):
                        self._draw.line((x0, y0, x1, y1), fill=col, width=p)
                x0, y0 = x1, y1

    def rect(self, X, Y, col: Color):
        if col:
            x0, x1 = X
            y0, y1 = Y
            x0, y0 = self.inner_coords(x0, y0)
            x1, y1 = self.inner_coords(x1, y1)
            self._draw.rectangle((x0, y0, x1, y1), fill=col)

    # *** uncomment after updating pillow
    #def box(self, x0, y0, x1, y1, col:Color, p:int=1):
        #x0, y0 = self.inner_coords(x0, y0)
        #x1, y1 = self.inner_coords(x1, y1)
        #if col and p:
            #self._draw.rectangle((x0, y0, x1, y1), outline=col, width=p)

    def box(self, X, Y, col: Color, p:int=1):
        x0, x1 = X
        y0, y1 = Y
        # *** joint="curve" in the next Pillow version
        self.line([x0, x0, x1, x1, x0], [y0, y1, y1, y0, y0], col, p=p)

    def ellipse(self, X, Y, col:Color):
        if col:
            x0, x1 = X
            y0, y1 = Y
            x0, y0 = self.inner_coords(x0, y0)
            x1, y1 = self.inner_coords(x1, y1)
            # these should be in the correct order
            x0, x1 = sorted([x0, x1])
            y0, y1 = sorted([y0, y1])
            self._draw.ellipse((x0, y0, x1, y1), fill=col)

    def circle(self, x, y, col:Color, r):
        if col:
            # *** allow for wid in the next Pillow version
            x, y = self.inner_coords(x, y)
            self._draw.ellipse((x-r, y-r, x+r, y+r), fill=col)

    def sector(self, X, Y, col:Color, start, end):
        if col:
            x0, x1 = X
            y0, y1 = Y
            x0, y0 = self.inner_coords(x0, y0)
            x1, y1 = self.inner_coords(x1, y1)
            # these should be in the correct order
            x0, x1 = sorted([x0, x1])
            y0, y1 = sorted([y0, y1])
            self._draw.pieslice((x0, y0, x1, y1), start, end, fill=col)

    def polygon(self, X, Y, col:Color):
        if col:
            self._draw.polygon([self.inner_coords(x, y) for x, y in zip(X, Y)], fill=col)

    def paste(self, x, y, canvas: 'Canvas', rotate: bool=True):
        if rotate:
            canvas = canvas.rotated(str(self.direction))
        img = canvas._img
        w, h = img.size
        xo, yo = self.inner_top_left(x, y, w, h)
        try:
            # this seems to be the only way to complitely replace "None" pixels
            # get pixels which are complitely transparent
            region = self._img.crop((xo, yo, xo+w, yo+h)).split()[3]
            if region.getbbox() is None:
                # region is complitely empty
                self._img.paste(img, (xo, yo))

            else:
                nones = region.point(lambda x: x==0, mode='1')

                # convert to RGB (remove alpha chanell) before pasting the image
                self._img.paste(img.convert('RGB'), (xo, yo), mask=img)

                # paste the image again, this time at the alpha=0 pixels
                self._img.paste(img, (xo, yo), mask=nones)

        except ValueError:
            self._img.paste(img, (xo, yo))

    # Writing
    # ==============

    def write(self, x, y, s, font, pos='>^', col=None, debug=False):
        if not s: return

        if not isinstance(font, Font):
            # create font
            font = Font(font)

        if col is None:
            col = font.col
        else:
            col = Color(col)

        w, h = font.measure(s)
        dx, dy, vertical = pos_to_shift(w, h, pos)
        align = pos_to_alignment(pos)

        x += dx
        y += dy

        if vertical == self.direction.vertical:
            # simply print the text
            xo, yo = self.inner_top_left(x, y, w, h)
            if debug:
                self._draw.rectangle((xo, yo, xo+w-1, yo+h-1), outline=col)
                self.box([x-2, x+2], [y-2, y+2], col)
            self._draw.text((xo, yo-font.vertical_correction), s, fill=col, font=font.font_obj, align=align)

        else:
            # using Pillow to write vertical test requires extra dependencies
            # so we print the text on a separate canvas and paste it with rotation
            label = Canvas((w, h), bgcol=col.alpha(0))
            if debug:
                label._draw.rectangle((0, 0, w-1, h-1), outline=col)
                label.box([-2, 2], [-2, 2], col)
            label._draw.text((0, -font.vertical_correction), s, fill=col, font=font.font_obj, align=align)
            self.paste(x, y, label.rotated('^<'), rotate=False)


    # Advanced Drawing
    # ================

    def pixel(self, x, y, col:Color):
        if col:
            x, y = self.inner_coords(x, y)
            self._draw.rectangle((x, y, x, y), fill=col)

    def fill(self, col:Color):
        if col:
            self._draw.rectangle((0, 0, self.w-1, self.h-1), fill=col)

    def border(self, col: Color, p:int=1):
        self.box([self.x0, self.x1], [self.y0, self.y1], col, p=p)

    def gradient(self, L, x=0, y=0):
        """
        Draw a serie of vertical lines, each with given height and color.
        Suitable for doing histograms or colored axes.
        """
        for i, (col, h) in enumerate(L):
            if h and col is not None:
                x0, y0 = self.inner_coords(x+i, y)
                x1, y1 = self.inner_coords(x+i, y+h-1)
                self._draw.line((x0, y0, x1, y1), fill=col, width=1)

    def horizontal_arrow(self, X, y, col, ticks=()):
        """
        Draw an arrow like this::

            ---------------------->

        or lke this

            <----------------------

        """
        self.rect(X, [y, y-1], col)
        x0, x1 = X
        if x1 >= x0:
            self.polygon([x1-2, x1-10, x1-6, x1-6, x1-10, x1-2], [y, y+4, y, y-1, y-5, y-1], col)
        else:
            self.polygon([x1+2, x1+10, x1+6, x1+6, x1+10, x1+2], [y, y+4, y, y-1, y-5, y-1], col)
        for x, length in ticks:
            self.rect([x, x-1], [y, y-length], col)

    def points(self, X, Y, C, p):
        r = p / 2
        for x, y, col in zip(X, Y, C):
            if None not in (x, y, col):
                self.circle(x, y, r=r, col=col)

    def recpoints(self, X, Y, C, p):
        ar = int(p / 2)
        br = int(p / 2 + 0.5)
        for x, y, col in zip(X, Y, C):
            if None not in (x, y, col):
                self.rect([x-ar, x+br], [y-ar, y+br], col=col)


    def symbol(self, x, y, symbol, size, col, font=None):
        """ draws a given symbol """
        #*** pattern matching?
        if symbol == '[]':
            self.rect([x, x+size], [y, y+size], col=col)
        elif symbol == '()':
            self.circle(x+size/2, y+size/2, r=size/2, col=col)
        elif symbol == '0':
            self.circle(x+size/2, y+size/2, r=size/3, col=col)
        elif symbol == 'O':
            self.circle(x+size/2, y+size/3, r=size/4, col=col)
        elif symbol == 'o':
            self.circle(x+size/2, y+size/3, r=size/5, col=col)
        elif symbol == '<>':
            self.polygon((x, x+size/2, x+size, x+size/2), (y+size/2, y, y+size/2, y+size), col=col)

        elif symbol == '-':
            self.rect([x, x+size], [y+size/4, y+size/2], col=col)
        elif symbol == '--':
            self.rect([x, x+size], [y+size/5*2, y+size/5*3], col=col)
        elif symbol == '|':
            self.rect([x+size/3, x+size/3*2], [y, y+size], col=col)
        elif symbol == '+':
            self.rect([x, x+size], [y+size/3, y+size/3*2], col=col)
            self.rect([x+size/3, x+size/3*2], [y, y+size], col=col)

        elif symbol == '^':
            self.polygon((x, x+size, x+size/2), (y, y, y+size), col=col)
        elif symbol == 'v':
            self.polygon((x, x+size, x+size/2), (y+size, y+size, y), col=col)
        elif symbol == '>':
            self.polygon((x, x, x+size), (y, y+size, y+size/2), col=col)
        elif symbol == '<':
            self.polygon((x+size, x+size, x), (y, y+size, y+size/2), col=col)

        elif font is not None:
            # symbolnot found; try to write it down
            self.write(x, y+size, str(symbol), font=font, col=col, pos='>v')
        else:
            raise KeyError(f'Unknown symbol "{symbol}" given')

    def add_debug_info(self, text):
        col = Color('_debug')
        self.border(col)
        self._draw.rectangle((0, 0, 4, 4), fill=col)
        self._draw.multiline_text((5, 0), text, fill=col)

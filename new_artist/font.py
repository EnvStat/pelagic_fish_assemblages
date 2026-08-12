import os

from PIL import ImageFont
from new_artist.color import Color, ColorDescriptor


FONT_PATH = os.path.dirname(__file__)+ '/fonts/'

DEFAULT_FONT_SIZE = 36
DEFAULT_FONT_NAME = 'cambria.ttf'
DEFAULT_FONT_COL = (0, 0, 0)

_LOADED_FONTS = {}

# string used to compute thestandard width and height of a font
_MODEL_STRING = '125%[- A'


def _load_font(path, size):
    """
    Loading the same font multiple times may create conflicts with files. Therefore, we are loading fonts into dictionary first
    """
    if (path, size) not in _LOADED_FONTS:
        try:
            font = ImageFont.truetype(path, size)
        except:
            raise TypeError(f'Unable to load Font with name {path} and size {size}')
        w, h = font.getsize(_MODEL_STRING)
        size_hash = {_MODEL_STRING: (w, h)}
        _LOADED_FONTS[path, size] = font, size_hash
    return _LOADED_FONTS[path, size]


class Font:
    """ Font object """

    col = ColorDescriptor()

    def __init__(self, size=DEFAULT_FONT_SIZE, name=DEFAULT_FONT_NAME, col=DEFAULT_FONT_COL):
        # *** Structural Patter matching could help here
        if isinstance(size, (tuple, list)):
            # unpack arguments, dont use keywords
            self.__init__(*size)
            return

        self._size = size
        self._font_name = name
        self.col = col
        self._set()

    def update(self, args):
        # *** Structural Patter matching could help here
        if isinstance(args, (tuple, list)):
            if len(args) == 2:
                self._size, self._font_name = args
            else:
                self._size, self._font_name, self.col = args
        else:
            self._size = args
        self._set()

    def copy(self):
        return Font(size=self._size, name=self._font_name, col=self.col)


    @property
    def font_name(self):
        return self._font_name
    @font_name.setter
    def font_name(self, value):
        self._font_name = value
        self._set()

    @property
    def size(self):
        return self._size
    @size.setter
    def size(self, value):
        self._size = value
        self._set()

    def _set(self):
        if self._size in FONT_SIZE_ALIASES:
            self._size = FONT_SIZE_ALIASES[self._size]

        if self._font_name == None or self._size == -1:
            # Font is None
            self._font_name = None
            self._size = -1
            self._size_hash = {}
            self.font_obj = None
            self.max_h = 9
            self.standard_w = 6 * len(_MODEL_STRING)
            self.vertical_correction = 2
            return

        if self._font_name == '-':
            self._font_name = DEFAULT_FONT_NAME

        self.font_obj, self._size_hash = _load_font(FONT_PATH+self._font_name, self.size)
        w, h = self._size_hash[_MODEL_STRING]
        self.max_h = h
        self.standard_w = w
        self.vertical_correction = int(h*0.1)

    def measure(self, s:str):
        if self.font_obj is None:
            w = 6 * max(len(ss) for ss in s.split('\n'))
            h = s.count('\n')*15 + 9
            return w, h
        else:
            # measuring the font size is time-demanding in pillow
            # for this reason, we hash for sizes
            if s not in self._size_hash:
                w = max(self.font_obj.getsize(ss)[0] for ss in s.split('\n'))
                h = self.max_h * (s.count('\n') + 1)
                self._size_hash[s] = w, h
            return self._size_hash[s]

    def measure_w(self, s:str):
        return self.measure(s)[0]

    def measure_h(self, s:str):
        return self.measure(s)[1]

    def __repr__(self):
        return f"Font(size={self._size}, name='{self._font_name}', col={self.col})"



class FontDescriptor:
    def __set_name__(self, owner, name): self.name = name
    def __get__(self, obj, cls): return obj.__dict__[self.name]
    def __set__(self, obj, value):
        if self.name not in obj.__dict__ or isinstance(value, Font):
            obj.__dict__[self.name] = Font(value)
        else:
            obj.__dict__[self.name].update(value)


#===================================================================================
# LIST OF FONTS SIZES AND THEIR ALIASES
# (list of aliases): Font size
FONT_SIZE_ALIASES = {
    (None, ):                     -1,
    ('s', 'small', 'axis'):       28,
    ('n', 'normal', 'label'):     36,
    ('b', 'big', 'caption'):      48,
    ('l', 'large', 'title'):      72,
    ('h', 'huge', 'panel name'):  92,
    }


# open up aliases
FONT_SIZE_ALIASES = {name: args for aliases, args in FONT_SIZE_ALIASES.items() for name in (aliases if isinstance(aliases, tuple) else [aliases]) }

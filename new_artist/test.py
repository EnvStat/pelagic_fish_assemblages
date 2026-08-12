import filecmp
import os
import unittest

from new_artist.canvas import Canvas
from new_artist.base import unpack_xyxy_or_wh, Direction
from new_artist.graph import Graph
from new_artist.dimension import PixelDimension, ColorDimension

from PIL import Image, ImageDraw


class TestSpace():
    """
    This dimension can be given to Plots
    """
    def __init__(self):
        self.X = PixelDimension('X')
        self.Y = PixelDimension('Y')
        self.C = ColorDimension('C')

        self._total_x0 = 0
        self._total_x1 = 0
        self._total_y0 = 0
        self._total_y1 = 0


class Dummy(Graph):
    """
    Plot substitute
    """
    def __init__(self, x):
        self.__init_defaults__()
        self._x = x
    def define(self):
        pass
    @property
    def inner_x0(self): return 0
    @property
    def inner_x1(self): return 0
    @property
    def inner_y0(self): return 0
    @property
    def inner_y1(self): return 0
    @staticmethod
    def draw(canvas, X, Y, C):
        pass
    def __repr__(self): return str(self._x)


class TestCasePicture(unittest.TestCase):
    def assertSameFigure(self, figure, filename, debug=False):
        figure.save(filename+'_test.png', debug=debug)

        if not os.path.exists(filename+'.png'):
            figure.save(filename+'.png', debug=debug)
            # test is passed automatically
            if os.path.exists(filename+'_z_err_.png'):
                os.remove(filename+'_z_err_.png')
            self.assertTrue(True)
        else:
            equal = filecmp.cmp(filename+'_test.png', filename+'.png')
            if not equal:
                A = Image.open(filename+'_test.png')
                B = Image.open(filename+'.png')
                wa, ha = A.size
                wb, hb = B.size
                if wa != wb or ha != hb:
                    diff = Image.new('RGB', (10, 10), color=(255, 0, 0))
                    diff.save(filename+'_z_err_.png')
                    self.assertTrue(False, msg=f'{filename} -- size is not correct -- w={wa}|{wb}, h={ha}|{hb}')
                diff = Image.new('RGB', (wa, ha), color=(200, 190, 190))
                #D = ImageDraw.Draw(C)
                A = A.load()
                B = B.load()
                C = diff.load()
                N = 0
                for x in range(wa):
                    for y in range(ha):
                        if A[x, y] !=  B[x, y]:
                            C[x, y] = (255, 0, 0)
                            N += 1
                diff.save(filename+'_z_err_.png')
                if N == 0:
                    # test is still correct, rewrite the file
                    figure.save(filename+'.png')
                    if os.path.exists(filename+'_z_err_.png'):
                        os.remove(filename+'_z_err_.png')
                    self.assertTrue(True)
                else:
                    self.assertTrue(False, msg=f'{filename} -- diff in {N} points')

            else:
                # test is passed
                if os.path.exists(filename+'_z_err_.png'):
                    os.remove(filename+'_z_err_.png')
                self.assertTrue(True)

from PIL import Image
import datetime
import random
from math import pi, log, tan

import new_artist as artist
from new_artist import base
from new_artist.graph import Graph
from new_artist.color import Color
from new_artist.canvas import Canvas
from new_artist.graphlib_shapes import *

from numpy import linspace


def fish_col(x):
    r, g, b, a = artist.color.FUNCTION_LIBRARY['batlow'](x)
    return artist.Color(b + 70*2*(x-0.5), g, r, a)


def SR_col(x):
    r, g, b, a = artist.color.FUNCTION_LIBRARY['black body'](x)
    return artist.Color(255-r, 255-g, 255-b, a)


artist.color.FUNCTION_LIBRARY['fish'] = fish_col
artist.color.FUNCTION_LIBRARY['richness'] = SR_col

artist.color.FUNCTION_LIBRARY['fish'] = artist.color.make_gradient(
    (0.0, (172, 217, 251)),
    (0.1, (82, 161, 247)),
    (0.2, (46, 148, 215)),
    (0.3, (33, 139, 168)),
    (0.4, (52, 128, 123)),
    (0.5, (86, 116, 84)),
    (0.6, (119, 100, 46)),
    (0.7, (139, 77, 23)),
    (0.8, (149, 51, 12)),
    (0.9, (160, 26, 0)),
    (1.0, (50, 26, 0)),
    )

artist.color.FUNCTION_LIBRARY['depth'] = artist.color.make_gradient(
        (0, (220, 255, 255)),
        (0.15, (88,  239,  239)),
        (0.25, (30, 161,  250)),
        (0.5, (0, 50, 250)),
        (0.7, (0, 0, 100)),
        (1, (200, 0, 100)))
artist.color.FUNCTION_LIBRARY['error'] = artist.color.make_gradient((0,    (  0,   0, 200)),
                                                                    (0.25, (  0, 200, 200)),
                                                                    (0.5,  (200, 200, 200)),
                                                                    (0.75, (200, 200,   0)),
                                                                    (1,    (200,   0,   0)))

artist.color.FUNCTION_LIBRARY['daytime'] = artist.color.make_gradient(
    (0,    (  0,   0, 200)),
    (2,    (  0,   0, 200)),
    (5,    (  0, 200, 100)),
    (7,    (100, 200, 100)),
    (10,   (250, 200, 0)),
    (14,   (250, 200, 0)),
    (17,   (200, 100, 0)),
    (19,   (100, 0, 100)),
    (22,   (0,   0,   200)),
    (24,   (0,   0,   200))
    )

artist.color.COLOR_LIBRARY['FI'] = artist.Color('+B')
artist.color.COLOR_LIBRARY['SE'] = artist.Color('y')
artist.color.COLOR_LIBRARY['DE'] = artist.Color('r')
artist.color.COLOR_LIBRARY['RU'] = artist.Color('k')
artist.color.COLOR_LIBRARY['PL'] = artist.Color('=G')
artist.color.COLOR_LIBRARY['LT'] = artist.Color('-o')
artist.color.COLOR_LIBRARY['LV'] = artist.Color('-c')
artist.color.COLOR_LIBRARY['EE'] = artist.Color('-=B')






class cpoints(points):
    """ Draw a scattergraph """
    def define(self, *xxxyyy, colors, p=3, legend=None):
        self.data_x, self.data_y = base.unpack_xxxyyy(*xxxyyy)
        self.data_c, self.data_x, self.data_y = zip(*sorted(zip(colors, self.data_x, self.data_y)))
        self.margins = (p+1)//2
        self.kwargs = {'p': p}


class piechart(circle):
    _single_col_arg = False

    def define(self, *xy, r=1, values=(), colors=()):
        x, y = base.unpack_xy(*xy)
        self.data_x = [x]
        self.data_y = [y]
        self.data_c = list(colors)
        self.margins = r
        self.kwargs = {'r': r, 'values': values}

    @staticmethod
    def draw(canvas: Canvas, x, y, C, r, values):
        tot = sum(values)
        cum = 0
        for c, v in zip(C, values):
            cur = v / tot * 360
            canvas.sector([x-r, x+r], [y-r, y+r], col=c, start=cum, end=cum+cur)
            cum += cur


class ScaledBitmap(Graph):
    def define(self, path, X, Y, crop=None):
        bmp = Canvas.load(path)
        self.data_x = X
        self.data_y = Y

        self.kwargs = {'bmp': bmp, 'crop': crop}

    @staticmethod
    def draw(canvas: Canvas, X, Y, _, bmp, crop):
        size = X[1] - X[0], Y[1] - Y[0]
        bmp._img.thumbnail(size, Image.BICUBIC)
        #bmp._img.transform(size, Image.Affine)
        canvas.paste(X[0], Y[0], bmp)


class Dpoints(Graph):
    """ Draw a scattergraph """
    def define(self, X, Y, colors, D, p=3, legend=None):
        self.data_x, self.data_y = X, Y
        self.data_c = list(colors)
        #self.data_c, self.data_x, self.data_y = zip(*sorted(zip(colors, self.data_x, self.data_y)))
        self.margins = (p+1)//2+100
        self.kwargs = {'p': p, 'Deep': D, 'vals': colors}

    @staticmethod
    def draw(canvas: Canvas, X, Y, C, p, Deep, vals):
        r = p / 2
        cx = 1000
        cy = 1000
        nn = 2000
        for x, y, col, d, val in zip(X, Y, C, Deep, vals):
            #canvas.circle(x+d/3, y+d/3, r=r, col=col)
           # if val == 0:
            #    continue
            canvas.circle((x*(nn-d)+cx*d)/nn, (y*(nn-d)+cy*d)/nn, r=r, col=col)



class randrect(Graph):

    def define(self, *xyxy, colors, p=4, m=5, legend=None):
        x0, y0, x1, y1 = base.unpack_xyxy(*xyxy)
        self.data_x = [x0, x1]
        self.data_y = [y0, y1]
        self.data_c = colors
        self.kwargs = {'p': p, 'm': m}

    @staticmethod
    def draw(canvas: Canvas, X, Y, col, p, m):
        dx = X[1] - X[0]-m
        dy = Y[1] - Y[0]-m
        canvas.points([X[0] + random.random()*dx+m/2 for _ in col], [Y[0] + random.random()*dy+m/2 for _ in col], col, p=p)





class DayTimeMapping(artist.mapping.DailyMapping, alias='dt'):
    @staticmethod
    def to_value(dt):
        return (dt.date() - datetime.date(2000, 1, 1)).days + dt.hour / 24 + dt.minute / 24 / 60
    @staticmethod
    def propose_ticks(a, b, min_interval):
        labelled_ticks = {datetime.datetime.combine(a.date() + datetime.timedelta(days=d), datetime.time()) for d in range(1, (b-a).days+1)}
        return {a} | labelled_ticks, {}

class HourMinuteMapping(artist.mapping.LinearMapping, alias='hm'):
    @staticmethod
    def to_value(dt):
        if isinstance(dt, datetime.datetime):
            return dt.hour + dt.minute / 60
        else:
            return dt

    @staticmethod
    def to_label(x, **_) -> str:
        if isinstance(x, datetime.datetime):
            return f'{x.hour}:{("0"+str(x.minute))[-2:]}'
        else:
            h = int(x)
            m = int((h-x)*60)
            return f'{h}:{("0"+str(m))[-2:]}'

    @staticmethod
    def propose_ticks(a, b, min_interval):
        return {a, b} | set(range(0, 25)), set()

class NoYearDailyMapping(artist.mapping.DailyMapping, alias='mdt'):
    @staticmethod
    def to_value(dt):
        return (dt.date() - datetime.date(dt.year, 9, 1)).days + dt.hour / 24 + dt.minute / 24 / 60

    @staticmethod
    def to_label(date, multiline=False, leading=False, **_) -> str:
        if leading or (date.day == 1 and date.month == 1):
            return f'{date:%d\n%b}' if multiline else f'{date:%b-%d}'
        elif date.day == 1:
            return f'{date:%d\n%b}'     if multiline else f'{date:%b-%d}'
        else:
            return f'{date:%d}'

    @staticmethod
    def propose_ticks(a, b, min_interval):
        labelled_ticks = {datetime.datetime.combine(a.date() + datetime.timedelta(days=d), datetime.time()) for d in range(1, 300)}
        return {a} | labelled_ticks, {}


class MercatorLinearMapping(artist.mapping.LinearMapping, alias='MercMap'):

    @staticmethod
    def to_value(latitude):
        # convert from degrees to radians
        latRad = (latitude * pi) / 180

        # get y value
        mercN = log(tan(pi / 4 + latRad / 2))
        return mercN


    @staticmethod
    def propose_ticks(a, b, min_interval):
        return {i/10 for i in range(500, 700, 5)}, {}


class LogWeightKgMapping(artist.mapping.LogMapping, alias='log_weight_kg'):

    @staticmethod
    def to_label(x, **_) -> str:
        if x >= 1000_000:
            return artist.mapping.nice_string_format(x/1000_000, unit='KT')
        if x >= 1000:
            return artist.mapping.nice_string_format(x/1000, unit='T')
        elif x < 1:
            return artist.mapping.nice_string_format(x*1000, unit='gr')
        else:
            return artist.mapping.nice_string_format(x, unit='kg')


class LogLenMMMapping(artist.mapping.LogMapping, alias='log_len_mm'):

    @staticmethod
    def to_label(x, **_) -> str:
        if x >= 1000:
            return artist.mapping.nice_string_format(x/1000, unit='m')
        elif x >= 10:
            return artist.mapping.nice_string_format(x/10, unit='cm')
        else:
            return artist.mapping.nice_string_format(x, unit='mm')


class LenMMMapping(artist.mapping.LinearMapping, alias='len_mm'):

    @staticmethod
    def to_label(x, **_) -> str:
        if x >= 1000:
            return artist.mapping.nice_string_format(x/1000, unit='m')
        elif x >= 10:
            return artist.mapping.nice_string_format(x/10, unit='cm')
        else:
            return artist.mapping.nice_string_format(x, unit='mm')




class nonoverlaping_labels(artist.graphlib_markup.GrapheWholeDataSpace):
    _single_col_arg = True

    def define(self, X, Y, labels, font, col=0.7, shift_y=0):
        self.data_x = list(X)
        self.data_y = list(Y)
        self.data_c = [col]

        self.kwargs = {'labels': labels, 'font': artist.font.Font(font), 'shift_y': shift_y}

    def draw(self, canvas, X, Y, C, labels, font, shift_y):
        occupied = {(i, j): 0 for i in range(canvas.x0, canvas.x1+1) for j in range(canvas.y0, canvas.y1+1)}
        for y0, x0, l in sorted(zip(Y, X, labels)):
            x = x0
            y = y0+shift_y
            w, h = font.measure(l)
            h *= 0.8
            h = int(h)

            x = min(canvas.x1-w, max(canvas.x0, x-w//2))
            y = min(canvas.y1-h, max(canvas.y0, y))

            while any(occupied[i, j] for i in range(x, x+w) for j in range(y, y+h)) and y+h < canvas.y1:
                y += 1

            canvas.write(x, y, l, font=font)

            for i in range(x, x+w):
                for j in range(y, y+h):
                    occupied[i, j] = 1

            if y > y0+shift_y:
                canvas.line([x0, x0], [y, y0], col=C, p=1)




def outliers_plot(LOWER, UPPER, DATA_VALS, func=None):
    if func:
        LOWER = func(LOWER)
        UPPER = func(UPPER)
        DATA_VALS = func(DATA_VALS)
    P1 = artist.Panel(700, 700, axes='<<v', C=1)
    P2 = artist.Panel(700, ('ilog', 700), axes='<<v', C=1)
    X = range(len(LOWER))
    for P in P1, P2:
        #P.lines(LOWER, col='o', p=1)
        #P.lines(UPPER, col='c', p=1)
        #P.points(DATA_VALS, col='k')
        P.area(X, LOWER, UPPER, col='___k')
        P.points(DATA_VALS, col='_k', p=1)
        L = [(i, DATA_VALS[i]) for i in X if DATA_VALS[i] < LOWER[i]]
        if L: P.points(L, col='c', p=5)
        U = [(i, DATA_VALS[i]) for i in X if DATA_VALS[i] > UPPER[i]]
        if U: P.points(U, col='o', p=5)

    return (P1+P2)


def Qplot(P, data, zero, scale=1, z=0):
    if  len(data)<10:
        P.points([(zero, x) for x in data], p=5, col='k')
        return
    elif len(data) < 50:
        scale *= 7
        quantiles = linspace(0, 1, 6)
    elif len(data) < 500:
        quantiles = linspace(0, 1, 11)
        scale *= 11
    elif len(data) < 5000:
        quantiles = linspace(0, 1, 21)
        scale *= 20
    else:
        quantiles = linspace(0, 1, 51)
        scale *= 50

    hist = [sum(a<=x<b for x in data) for a, b in zip(quantiles, quantiles[1:])]
    scale = (len(data) + 10) / max(hist)
    for i, h in enumerate(hist):
        if h:
            P.rect(
                [zero, zero+h*scale],
                [i/len(hist), (i+1)/len(hist)],
                col=('_viridis', h/len(data)*len(hist)*0.5),
                z=z)


def make_map():
    P = artist.Panel((9, 31, 2003), ('MercMap', 53.5, 64, 1860), '^<<')
    P.bitmap('map_23.png', 9, 53.5)

    P.top.font=40
    P.top = {i: f'{i}°E' for i in range(10, 40, 2)}
    P.left.font=40
    P.left = {i: f'{i}°N' for i in range(54, 65, 1)}

    return P

def make_map2():
    P = artist.Panel((13, 29, 1457), ('MercMap', 53.5, 64, 1860), '^<<')
    P.bitmap('map_24.png', 13, 53.5)

    P.top.font=40
    P.top = {i: f'{i}°E' for i in range(10, 40, 2)}
    P.left.font=40
    P.left = {i: f'{i}°N' for i in range(54, 65, 1)}

    return P

def broken_line(P, X, Y, breaks, **kwargs):
    X = list(X)
    Y = list(Y)
    breaks = list(breaks)[1:] + [True]
    while X:
        i = 0
        while not breaks[i]:
            i += 1
        i += 1
        P.lines(X[:i], Y[:i], **kwargs)
        X = X[i:]
        Y = Y[i:]
        breaks = breaks[i:]

class borders(artist.graphlib_shapes.points):
    def define(self, *xxxyyy, col=1, vals=None, p=3, res=3):
        super().define(*xxxyyy, col=col, p=p)
        self.kwargs['vals'] = vals
        self.kwargs['res'] = res

    @staticmethod
    def draw(canvas, X, Y, C, p, vals, res):
        coords = {}
        for x, y, c, v in zip(X, Y, C, vals):
            for i in (x+k for k in range(res)):
                for j in (y+k for k in range(res)):
                    if (i, j )in coords:
                        coords[i, j].add(v)
                    else:
                        coords[i, j] = {v}

        border_x = []
        border_y = []
        border_c = []
        for (i, j), vs in coords.items():
            if len(vs) > 1:
                border_x.append((i))
                border_y.append((j))
                border_c.append((C[0]))
        canvas.points(border_x, border_y, border_c, p)


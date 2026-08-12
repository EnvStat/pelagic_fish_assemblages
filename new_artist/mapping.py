from math import log10, floor, ceil
import calendar
import datetime
from abc import ABC, abstractmethod
from typing import Tuple  # *** remove this

from new_artist.base import nice_string_format, is_integer, first_meaningfull_digit


MAPPINGS_LIBRARY = {}


def linear_ticks(a, b, min_interval) -> Tuple[set, set]:
    if a==b: return {a}, set()
    resolution = ceil(log10(min_interval))
    labels_interval = 10 ** resolution
    ticks_interval = labels_interval / 10

    # can we make interval between labels smaller?
    if labels_interval/5 >= min_interval:
        labels_interval /= 5
    elif labels_interval/2 >= min_interval:
        labels_interval /= 2
    else:
        ticks_interval *= 2

    def _range(A, B, step):
        cur = h = round(A, -resolution)
        while cur >= A:
            yield cur
            cur = round(cur-step, 2-resolution)  # wee need extrarounding here to aboing accumulation of error
        cur = h + step
        while cur <= B:
            yield cur
            cur = round(cur+step, 2-resolution)

    labelled_ticks = set(_range(a, b, labels_interval))
    unlabelled_ticks = set(_range(a, b, ticks_interval))

    return {a, b} | labelled_ticks, unlabelled_ticks


class CoordinateMapping():

    suggested_ticks_scale = 1
    suggested_ticks_scale_perp = None
    suggested_arrow_type = 'normal'
    suggested_gradient_type = None

    def __init_subclass__(cls, alias=None):
        super().__init_subclass__()
        if alias:
            MAPPINGS_LIBRARY[alias] = cls

    @abstractmethod
    def to_value(self, x) -> float:
        return x

    @abstractmethod
    def to_label(self, x, **_) -> str:
        return str(x)

    @abstractmethod
    def propose_ticks(self, a, b, min_interval) -> Tuple[set, set]:
        return set(), set()

    def __repr__(self):
        if self.__dict__:
            return f'{self.__class__.__name__}({self.__dict__})'
        else:
            return f'{self.__class__.__name__}'


#------------------------------------------------


class LinearMapping(CoordinateMapping, alias='linear'):

    @staticmethod
    def to_value(x): return x

    @staticmethod
    def to_label(x, min_interval, **_) -> str:
        return nice_string_format(x, resolution=-first_meaningfull_digit(min_interval)+2)

    @staticmethod
    def propose_ticks(a, b, min_interval) -> Tuple[set, set]:
        return linear_ticks(a, b, min_interval=min_interval)


class LinearMappingPercent(LinearMapping, alias='%'):
    @staticmethod
    def to_label(x, min_interval, **_) -> str:
        return nice_string_format(x*100, resolution=-first_meaningfull_digit(min_interval), unit='%')

class LinearMappingThousand(LinearMapping, alias='K'):
    @staticmethod
    def to_label(x, min_interval, **_) -> str:
        return nice_string_format(x/1000, resolution=-first_meaningfull_digit(min_interval)+5, unit='K')

class LinearMappingMillion(LinearMapping, alias='M'):
    @staticmethod
    def to_label(x, min_interval, **_) -> str:
        return nice_string_format(x/1000_000, resolution=-first_meaningfull_digit(min_interval)+8, unit='M')


class IntegerLinearMapping(LinearMapping, alias='int'):
    """ linear mapping, but only integer ticks are used """
    @staticmethod
    def propose_ticks(a, b, min_interval) -> Tuple[set, set]:
        a, b = ceil(a), floor(b)
        labelled_ticks, unlabelled_ticks = linear_ticks(a, b, min_interval=min_interval)
        return {int(x) for x in labelled_ticks if is_integer(x)}, {int(x) for x in unlabelled_ticks if is_integer(x)}


#------------------------------------------------


class LogMapping(CoordinateMapping, alias='log'):

    @staticmethod
    def to_value(x): return log10(x)

    @staticmethod
    def to_label(x, **_) -> str:
        if x >= 10_000_000:
            return nice_string_format(x/1_000_000, unit='M')
        elif x >= 10_000:
            return nice_string_format(x/1_000, unit='K')
        else:
            return nice_string_format(x)

    @staticmethod
    def propose_ticks(a, b, min_interval) -> Tuple[set, set]:
        _a = int(ceil(log10(a)))
        _b = int(floor(log10(b)))
        labeled_ticks = {10**x for x in range(_a, _b+1)}
        unlabelled_ticks = {10**x * y for x in range(_a, _b+1) for y in range(1, 10)}
        return {a, b} | labeled_ticks, unlabelled_ticks


class LogMappingPercent(LogMapping, alias='log%'):
    @staticmethod
    def to_label(x, **_) -> str:
        return LogMapping.to_label(x*100, min_interval=None)+'%'


class IntegerLogMapping(LogMapping, alias='ilog'):
    """ Log mapping, suitable for count data """

    @staticmethod
    def to_value(x):
        return -1 if x < 1 else log10(x)

    @staticmethod
    def propose_ticks(a, b, min_interval) -> Tuple[set, set]:
        labeled_ticks, unlabelled_ticks = LogMapping.propose_ticks(a=1, b=b, min_interval=min_interval)
        return {0} | labeled_ticks, unlabelled_ticks


class SafeLogMapping(LogMapping, alias='slog'):

    def __init__(self, limit=0.1):
        self.zero = int(round(log10(limit)))
        self.limit = limit

    def to_value(self, x):
        return self.zero if x < self.limit else log10(x)

    def propose_ticks(self, a, b, min_interval):
        return LogMapping.propose_ticks(a=self.limit, b=b, min_interval=min_interval)


class SafeLogMappingPercent(SafeLogMapping, alias='slog%'):
    @staticmethod
    def to_label(x, **_) -> str:
        return SafeLogMapping.to_label(x*100)+'%'


#------------------------------------------------


class DailyMapping(CoordinateMapping, alias='day'):

    suggested_ticks_scale = 1/2
    suggested_ticks_scale_perp = 1.5
    suggested_gradient_type = 'bins'

    @staticmethod
    def to_value(date):
        return (date - datetime.date(2000, 1, 1)).days

    @staticmethod
    def to_label(date, multiline=False, leading=False, **_) -> str:
        if leading or (date.day == 1 and date.month == 1):
            return f'{date:%d\n%b\n%Y}' if multiline else f'{date:%Y-%b-%d}'
        elif date.day == 1:
            return f'{date:%d\n%b}'     if multiline else f'{date:%b-%d}'
        else:
            return f'{date:%d}'

    @staticmethod
    def propose_ticks(a, b, min_interval) -> Tuple[set, set]:
        labelled_ticks = {a + datetime.timedelta(days=d) for d in range(1, (b-a).days+1)}
        return {a} | labelled_ticks, {}


class WeeklyMapping(DailyMapping, alias='week'):

    @staticmethod
    def to_label(date, multiline=False, leading=False, **_) -> str:
        if leading or (date.day < 8 and date.month == 1):
            return f'{date:%d\n%b\n%Y}' if multiline else f'{date:%Y-%b-%d}'
        elif date.day < 8:
            return f'{date:%d\n%b}'     if multiline else f'{date:%b-%d}'
        else:
            return f'{date:%d}'

    @staticmethod
    def propose_ticks(a, b, min_interval) -> Tuple[set, set]:
        days = {a + datetime.timedelta(days=d) for d in range((b-a).days+1)}
        mondays = {d for d in days if d.weekday() == 0}
        return {a} | mondays, days


class MonthlyMapping(CoordinateMapping, alias='month'):

    suggested_ticks_scale = 1/2
    suggested_ticks_scale_perp = 1.5

    @staticmethod
    def to_value(date):
        return date.year*12 + date.month + (date.day-1)/calendar.monthrange(date.year, date.month)[1]

    @staticmethod
    def to_label(date, min_interval=0, multiline=False, leading=False) -> str:
        if min_interval > 0.3:
            if leading or date.month == 1:
                return f'{date:%b\n%Y}' if multiline else f'{date:%Y-%b}'
            else:
                return f'{date:%b}'
        else:
            if leading or date.month == 1:
                return f'{date:%B\n%Y}' if multiline else f'{date:%Y-%B}'
            else:
                return f'{date:%B}'

    @staticmethod
    def propose_ticks(a, b, min_interval) -> Tuple[set, set]:
        labelled_ticks = {datetime.date(y, m, 1) for y in range(a.year, b.year+1) for m in range(1, 13)}
        return {a} | labelled_ticks, {}


class AnnualMapping(CoordinateMapping, alias='year'):

    suggested_ticks_scale = 1/2
    suggested_ticks_scale_perp = 1.5

    @staticmethod
    def to_value(date):
        try:
            return date.year + (date.timetuple().tm_yday - 1) / (365 + calendar.isleap(date.year))
        except AttributeError:
            return float(date)

    @staticmethod
    def to_label(date, **_) -> str:
        try:
            return f'{date:%Y}'
        except ValueError:
            return str(date)

    @staticmethod
    def propose_ticks(a, b, min_interval) -> Tuple[set, set]:
        try:
            a = a.year
        except AttributeError:
            a = int(a)

        try:
            b = b.year
        except AttributeError:
            b = int(b)

        labelled_years, unlabelled_years = IntegerLinearMapping.propose_ticks(a, b, min_interval)
        if unlabelled_years - labelled_years:
            unlabelled_ticks = {datetime.date(y, 1, 1) for y in unlabelled_years}
        else:
            unlabelled_ticks = {datetime.date(y, m, 1) for y in range(a, b+1) for m in range(2, 13)}
        labelled_ticks = {datetime.date(y, 1, 1) for y in labelled_years}

        return labelled_ticks, unlabelled_ticks


class DateMapping(DailyMapping, alias='date'):

    @staticmethod
    def to_label(date, min_interval, multiline=False, leading=False) -> str:
        # min_interval correspond to year's label (e.g "2022"), i.e. it is twive as large as day label (e.g "22")
        if min_interval <= 1.5:
            return DailyMapping.to_label(date, multiline=multiline, leading=leading)
        elif min_interval <= 14:
            return WeeklyMapping.to_label(date, multiline=multiline, leading=leading)
        elif min_interval < 60:
            return MonthlyMapping.to_label(date, multiline=multiline, leading=leading, min_interval=1)
        else:
            return AnnualMapping.to_label(date)

    @staticmethod
    def propose_ticks(a, b, min_interval) -> Tuple[set, set]:
        # min_interval correspond to year's label (e.g "2022"), i.e. it is twive as large as day label (e.g "22")
        if min_interval <= 1.5:
            return DailyMapping.propose_ticks(a, b, min_interval)
        elif min_interval <= 14:
            return WeeklyMapping.propose_ticks(a, b, min_interval)
        elif min_interval < 60:
            return MonthlyMapping.propose_ticks(a, b, min_interval)
        else:
            return AnnualMapping.propose_ticks(a, b, min_interval/365)


#------------------------------------------------


class CategorialMapping(CoordinateMapping, alias='cat'):

    suggested_arrow_type = 'cat'
    suggested_gradient_type = 'cat'

    def __init__(self, categories):
        self.categories = list(categories)

    def to_value(self, x):
        return self.categories.index(x)

    def propose_ticks(self, a, b, min_interval) -> Tuple[set, set]:
        return set(self.categories), {}

class CategoriaBinMapping(CoordinateMapping, alias='catbin'):

    suggested_arrow_type = 'cat'
    suggested_gradient_type = 'cat'

    def __init__(self, borders):
        self.borders = list(borders)
        self._minus_inf = object()

    def to_value(self, x):
        i = -1
        if x is self._minus_inf:
            return -1
        for b in self.borders:
            if x < b: return i
            i += 1
        return i

    def to_label(self, x, **kwargs):
        if x is self._minus_inf or x < self.borders[0]:
            return f'(...{self.borders[0]})'
        for a, b in zip(self.borders, self.borders[1:]):
            if x < b: return f'[{a}, {b})'
        return f'[{self.borders[-1]}...)'

    def propose_ticks(self, a, b, min_interval) -> Tuple[set, set]:
        return set(self.borders) | {self._minus_inf}, {}


#------------------------------------------------


class BinMapping(CoordinateMapping, alias='bin'):

    suggested_arrow_type = 'bins'
    suggested_gradient_type = 'bins'

    def __init__(self, borders):
        self.borders = list(borders)

    def to_value(self, x):
        i = -1
        for b in self.borders:
            if x < b: return i
            i += 1
        return i

    def to_label(self, x, **kwargs):
        for b in self.borders[::-1]:
            if x >= b: return str(b)
        return None

    def propose_ticks(self, a, b, min_interval) -> Tuple[set, set]:
        return set(self.borders), {}


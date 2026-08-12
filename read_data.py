import re
import pandas
import datetime
import numpy
import math
import netCDF4
import suntime

import data_pers


def name_recrangle(Longitude, Latitude):
    x = int(Longitude)
    y = int(Latitude * 2) - 71
    if x >= 30:
        return f'{y}J{x-30}'
    elif x >= 20:
        return f'{y}H{x-20}'
    elif x < 10:
        return f'{y}F{x}'
    else:
        return f'{y}G{x-10}'


def name_to_xy(n):
    if 'H' in n:
        x, y = n.split('H')
        x, y = int(y)+20, int(x)
    elif 'F' in n:
        x, y = n.split('F')
        x, y = int(y), int(x)
    elif 'G' in n:
        x, y = n.split('G')
        x, y = int(y)+10, int(x)
    elif 'J' in n:
        x, y = n.split('J')
        x, y = int(y)+30, int(x)
    else:
        x = y = 0
    return x, y


def name_to_ll(n):
    x, y = name_to_xy(n)
    return x+0.5, (y + 71) / 2 + 0.25


name_to_coords = name_to_ll


def ll_to_region(x, y):

    if y > 63.5:
        return None

    elif y > 60.5 and x < 26:
        return 30

    elif x > 23 and y > 59:
        return 32

    elif (x > 19 and y > 58.5) or y > 60:
        return 29

    elif y > 56.5 and x > 14:
        if (y< 58 and x - 0.5*y > -7) or x>22.2:
            return None
        if  (x > 18 and y < 57) or (x > 18.3 and y < 57.75) or (x > 19):
            return 28
        else:
            return 27

    elif x > 18:
        return 26

    elif x < 14 and (x + 5.5*y > 328.125 or x - 2*y < -104.9) :
        return None

    elif x > 15 or (x > 14.8 and y > 55.1) or (x > 14 and y*5+x > 291.2):
        return 25

    elif x > 12 and x-6*y > -319.5:
        return 24

    elif (x < 11.6 or (x <= 12 and y < 55.5)) and x+y*3 < 179.2:
        return 22

    elif (x*0.3 - y/4 < -10.34) or (y < 56 and x < 12.2):
        return 21

    else:
        return 23

    raise Exception


def name_to_region(n):
    x, y = name_to_ll(n)
    return ll_to_region(x, y)

def closest_in_list(x, ind, L):
    if len(L) < 2:
        return ind
    if len(L) == 2:
        if abs(L[0]-x) < abs(L[1]-x):
            return ind
        else:
            return ind+1

    sep = len(L)//2
    if L[sep] > x:
        return closest_in_list(x, ind, L[:sep+1])
    elif L[sep] < x:
        return closest_in_list(x, ind+sep, L[sep:])
    else:
        return ind+sep


def read_path_var(year, name, path):
    MAPS, TIME, LAT, LON = read_variable_raw(year, name)
    res = []
    for _, row in path.iterrows():
        if row.LogTime.date() in TIME:
            time = TIME.index(row.LogTime.date())
        elif row.LogTime.date() < TIME[0]:
            time = 0
        else:
            time = len(TIME)-1
        lat = closest_in_list(row.LogLatitude, 0, LAT)
        lon = closest_in_list(row.LogLongitude, 0, LON)
        res.append(float(MAPS[time, lat, lon]))
    return res

def read_path_var_mean(year, name, path):
    MAP, LAT, LON = read_variable_raw_mean(year, name)
    res = []
    for _, row in path.iterrows():
        lat = closest_in_list(row.LogLatitude, 0, LAT)
        lon = closest_in_list(row.LogLongitude, 0, LON)
        res.append(float(MAP[lat, lon]))
    return res




def to_sunset_time(x_lon, y_lat, test_date):
    sun = suntime.Sun(y_lat, x_lon)
    time = sun.get_sunset_time(test_date)
    return time.hour + time.minute/60

def to_sunrise_time(x_lon, y_lat, test_date):
    sun = suntime.Sun(y_lat, x_lon)
    time = sun.get_sunrise_time(test_date)
    return time.hour + time.minute/60


def standartise_time(time, sunrise, sunset):
    if sunrise <= time <= sunset:
        return  (time-sunrise) / (sunset-sunrise) * 12 + 6
    else:
        return  (((time-sunset) % 24) / (24+sunrise-sunset) * 12 + 18) % 24




def haversine(point1, point2):
    lat1, lon1 = point1
    lat2, lon2 = point2

    dLat = (lat2 - lat1)
    dLon = (lon2 - lon1)

    a = math.sin(dLat/2)**2 + math.cos(lat1)*math.cos(lat2)*math.sin(dLon/2)**2
    c = 2*math.asin(math.sqrt(a))

    R = 6372.8 # this is in km
    return R * c

def haversine_deg(point1, point2):
    lat1, lon1 = point1
    lat2, lon2 = point2
    return haversine((math.radians(lat1), math.radians(lon1)), (math.radians(lat2), math.radians(lon2)))



class SpeciesSynonyms():
    def __repr__(self):
        return f'{self.short}\t{self.code}\t{self.name}'


class DictOfUsedFish(dict):
    _instance = None
    _inited = False

    def __new__(cls):
        if cls._instance is None:
            cls._instance = super().__new__(cls)
        return cls._instance

    def __init__(self):
        if self.__class__._inited:
            return

        sp = pandas.read_csv('input_data/species_list.csv', sep='\t')
        sp = sp[sp.include == 'X']
        self.name = list(sp['colloquial name'])
        self.short = list(sp['short'])
        self.code = list(sp['code'])
        self.scode = list(sp['code'].apply(str))
        self.entries = []

        for _, row in sp.iterrows():
            s = SpeciesSynonyms()
            self[row.code] = s
            self[str(row.code)] = s
            self[row['scientific name']] = s
            self[row['colloquial name']] = s
            self[row['short scientific name']] = s
            self[row.short] = s
            s.code = row.code
            s.scode = str(row.code)
            s.short = row.short
            s.latin = row['scientific name']
            s.name = row['colloquial name']
            s.shlatin = row['short scientific name']
            self[s] = s
            self.entries.append(s)

        self.__class__._inited = True

    def __iter__(self):
        return self.entries.__iter__()

    def __len__(self):
        return len(self.name)




def load_models(H, n, MODEL, **kwargs):
    subsample = H[::max(1, len(H)//n)]
    simulations = [MODEL(**kwargs) for i in range(len(subsample))]
    [sim.load(row) for sim, (_, row) in zip(simulations, subsample.iterrows())]
    return simulations


def to_natural(H):
    N = [sim.transformed_pars() for sim in load_models(H, len(H))]
    N = pandas.DataFrame(N)
    return pandas.concat([H, N], axis=1)


def load_samples_into_models(experiment_name, n_models_per_species, model_defining_func):
    M = {}
    SL = DictOfUsedFish()
    print('today is', datetime.date.today().strftime('%d-%m-%Y'))
    for i, s in enumerate(SL):
        TRIAL_N = f'samples/{experiment_name}_{s.name}'
        H = data_pers.Load(TRIAL_N, files=[1])
        print(i, len(H), TRIAL_N)
        M[s] = load_models(H, n_models_per_species, model_defining_func(s))
    return M


if __name__ == '__main__':
    #_, path = read_year_acc(2020, all_data=False)
    #path = path[path.LogLatitude > 60.5].reset_index()
    #print(to_sunset_time(21.01,  51.21, datetime.datetime(2020, 10, 1, 10, 10)))
    read_variable_raw(2021, 'oxygen')


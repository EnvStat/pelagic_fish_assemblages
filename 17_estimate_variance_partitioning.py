#!/usr/bin/env python
# coding: utf-8

# In[1]:


import resource

import numpy

import model
from load_data import *
import data_pers
from useful import logistic
import read_data



EN = '5'
N = 1000
RESOLUTION = '5x5'
#RESOLUTION = '3x3'
#RESOLUTION = '1x1'



M = read_data.load_samples_into_models(
    experiment_name=EN,
    n_models_per_species=N,
    model_defining_func=model.define_model)


def print_memory():
    print('memory use:', int(resource.getrusage(resource.RUSAGE_SELF).ru_maxrss/1024))

SPECIES_LIST = read_data.DictOfUsedFish()

print_memory()



## Loading map to make predictions
# constant map, for depth and distance to short
CM = pandas.read_csv('data/prediction_area_map_'+RESOLUTION+'.csv')

# annual map, for oxygen and visibility
AM = pandas.read_csv('data/annual_map_'+RESOLUTION+'.csv')
AM = AM[AM.exclude == 0].reset_index(drop=True)
print('done')
print_memory()

assert len(CM) == len(AM) // 17
assert list(CM.x_lon) == list(AM[AM.year == 2007].x_lon)
assert list(CM.y_lat) == list(AM[AM.year == 2007].y_lat)



print('# add depth info to the annual map')
AM = AM.merge(CM[['x_lon', 'y_lat', 'depth']], on=['x_lon', 'y_lat'])



print('# flattening the map')
def parse_array(s):
    return list(map(float, s[1:-1].split()))

DLAYERS = [0.5016462, 1.5159924, 2.548084, 3.6022985, 4.684081,  5.8002,    6.959055,
 8.171057, 9.449085,  10.809036,  12.27047,   13.857369,  15.5990095, 17.530924,
 19.695944,  22.145256, 24.939384, 28.148958, 31.85507,  36.148987, 41.130913, 46.907536, 53.588184,
 61.27954, 70.079216,  80.06874,   91.30695,  103.82471 ]

# layers that are later saved to the separater file
SAVED_LAYERS = [9, 18, 22, 24, 26]
[print(f'{round(DLAYERS[i-1], 2)}--{round(DLAYERS[i], 2)}') for i in SAVED_LAYERS]
SAVED_LAYERS_NAMES = [f'{round(DLAYERS[i-1], 2)}--{round(DLAYERS[i], 2)}' if i in SAVED_LAYERS else '' for i in range(len(DLAYERS))]

DLAYERS_SIZE = [DLAYERS[0]] + [b-a for a, b in zip(DLAYERS, DLAYERS[1:])]
DLAYERS_SIZE = array(DLAYERS_SIZE)

# flatten the map
NEW = {p:[] for p in ['year', 'x_lon', 'y_lat', 'salinity', 'temperature', 'weight', 'dl', 'max_depth', 'layer']}
for _, row in AM.iterrows():
    salt = parse_array(row.salinity)
    temp = parse_array(row.temperature)

    n = len(salt)
    assert n == len(temp)
    n = min(n, 28)
    #assert n <= 28  # len(DLAYERS)

    if row.depth < DLAYERS[n-1] -10:
        print(row.depth, DLAYERS[n-1])

    NEW['salinity'] += salt[:n]
    NEW['temperature'] += temp[:n]
    NEW['x_lon'] += [row.x_lon]*n
    NEW['y_lat'] += [row.y_lat]*n
    NEW['year'] += [row.year]*n
    NEW['max_depth'] += [row.depth]*n

    NEW['dl'] += DLAYERS[:n]
    NEW['weight'] += list(DLAYERS_SIZE[:n] / DLAYERS[n-1])

    NEW['layer'] += SAVED_LAYERS_NAMES[:n]


print('FLATTENING MAP - DONE')



print('# make a single huge layered map')
LM = pandas.DataFrame(NEW)
print('CONVERTED FLAT MAP INTO DATAFRAME - DONE')


print('computing distance from anchor points')
CM['distance_vector'] = CM.apply(get_distance_vector, axis=1)
print('DONE')



print("-----Preparations")

LM1 = LM[LM.year == 2007]
LM1 = LM1.merge(CM[['x_lon', 'y_lat', 'depth', 'dts', 'distance_vector']], on=['x_lon', 'y_lat'])
LM = LM.merge(AM[['x_lon', 'y_lat', 'year', 'transparency', 'bottom_oxygen']], on=['x_lon', 'y_lat', 'year'])
if RESOLUTION == '5x5':
    # this would be saved as well, so we need all the variables
    LM = LM.merge(CM[['x_lon', 'y_lat', 'depth', 'dts']], on=['x_lon', 'y_lat'])

# spatial effects
A_DEPTH = make_data_array(LM1.depth, U_DEPTH)
A_DTS   = make_data_array(LM1.dts, U_DTS)
A_TD    = make_data_array(LM1.dl, U_TD)
A_DFB   = make_data_array((LM1.max_depth - LM1.dl), U_DFB)
print_memory()

# spatio-temporal effects
A_TURB  = make_data_array(LM.transparency, U_TURB)
A_OXYG  = make_data_array(LM.bottom_oxygen, U_OXYG)
A_SALT  = make_data_array(LM.salinity, U_SALT)
A_TEMP  = make_data_array(LM.temperature, U_TEMP)

SCALE_DL = array(LM.weight)

print_memory()
print('MAKING ARRAYS - DONE')


def make_pred(mod):
    # spatial effects
    S_depth = A_DEPTH @ mod.depth_f_s
    S_dts   = A_DTS @ mod.dts_f_s
    S_geo   = LM1.distance_vector.apply(lambda x: x @ mod.geo_f_s)
    S_ts    = A_TD  @ mod.td_f_s
    S_dfb   = A_DFB @ mod.dfb_f_s

    # temporal effects
    T_year = mod.year_f_s

    # spatio-temporal effects
    ST_turb = A_TURB @ mod.turb_f_s
    ST_oxyg = A_OXYG @ mod.oxyg_f_s
    ST_salt = A_SALT @ mod.salt_f_s
    ST_temp = A_TEMP @ mod.temp_f_s

    # summary
    S = S_depth + S_dts + S_geo + S_ts + S_dfb
    T = T_year
    ST = ST_turb + ST_oxyg + ST_salt + ST_temp

    PRED = numpy.tile(S, 17) + numpy.repeat(T, len(LM1)) + ST
    v = PRED.var()

    rand = numpy.tile(S_geo, 17) + numpy.repeat(T, len(LM1))
    env = PRED - rand

    res = {
        'total': v,

        'depth': S_depth.var(),
        'dts': S_dts.var() ,
        'td': S_ts.var(),
        'dfb': S_dfb.var(),
        'geo': S_geo.var(),

        'year': T_year.var(),

        'turb': ST_turb.var(),
        'oxyg': ST_oxyg.var(),
        'salt': ST_salt.var(),
        'temp': ST_temp.var(),

        'a_rand': rand.var(),
        'a_env': env.var(),
        }

    for t in range(17):
        a, b = t*len(LM1), (t+1)*len(LM1)
        res[f'salt_{t}'] = ST_salt[a:b].var()
        res[f'temp_{t}'] = ST_temp[a:b].var()
        res[f'oxyg_{t}'] = ST_oxyg[a:b].var()
        res[f'turb_{t}'] = ST_turb[a:b].var()

    return res


print_memory()


## Make predictons
print("-----Making Predictions")

VP = []
for i, s in enumerate(SPECIES_LIST):
    print('\n', i, s.name)

    for j, mod in enumerate(M[s]):
        print(N-j, end=' ')
        vp = make_pred(mod)
        vp['Species'] = s.name
        VP.append(vp)

    print()
    print_memory()


VP = pandas.DataFrame(VP)
VP.to_csv(f'internal_results/variance_partition_{EN}_avg.csv', index=False)
print('DONE!')

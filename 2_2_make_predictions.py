"""
Step 2.2

loads the samples, and produces the prediction map for a given resolution

"""

import resource

import numpy

import model
from load_data import *
import data_pers
from useful import logistic
import read_data



EN = '5'
N = 100
RESOLUTION = '5x5'
RESOLUTION = '3x3'
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
SAVED_LAYERS_IND = [i if i in SAVED_LAYERS else '' for i in range(len(DLAYERS))]
SAVED_LAYERS_NAMES = {i: f'{round(DLAYERS[i-1], 2)}--{round(DLAYERS[i], 2)}' if i in SAVED_LAYERS else '' for i in range(len(DLAYERS))}

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

    NEW['salinity'] += salt[:n]
    NEW['temperature'] += temp[:n]
    NEW['x_lon'] += [row.x_lon]*n
    NEW['y_lat'] += [row.y_lat]*n
    NEW['year'] += [row.year]*n
    NEW['max_depth'] += [row.depth]*n

    NEW['dl'] += DLAYERS[:n]
    NEW['weight'] += list(DLAYERS_SIZE[:n] / DLAYERS[n-1])

    NEW['layer'] += SAVED_LAYERS_IND[:n]


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
    # baseline
    B = mod.logit_base

    # spatial effects
    S = zeros([len(LM1)])
    S += A_DEPTH @ mod.depth_f_s
    S += A_DTS @ mod.dts_f_s
    S += LM1.distance_vector.apply(lambda x: x @ mod.geo_f_s)
    S += A_TD  @ mod.td_f_s
    S += A_DFB @ mod.dfb_f_s

    # temporal effects
    T = mod.year_f_s

    # spatio-temporal effects
    ST = zeros([len(LM)])
    ST += A_TURB @ mod.turb_f_s
    ST += A_OXYG @ mod.oxyg_f_s
    ST += A_SALT @ mod.salt_f_s
    ST += A_TEMP @ mod.temp_f_s


    return logistic(B + numpy.tile(S, 17) + numpy.repeat(T, len(LM1)) + ST)


print_memory()


## Make predictons
print("-----Making Predictions")

# temporal dataframe for unagregated predictions
PML = LM[['x_lon', 'y_lat', 'year', 'weight', 'layer']].copy()

# dataframe for layer-agregated predictions
PM = AM[['x_lon', 'y_lat', 'year']].copy()

# dataframe for year-agregated predictions, for a subset of layers
PL = LM1[['x_lon', 'y_lat', 'layer']].copy()
PL = PL[PL.layer != ''].reset_index(drop=True)


for i, s in enumerate(SPECIES_LIST):
    print('\n', i, s.name)

    PRED = numpy.zeros([len(LM)])
    for j, mod in enumerate(M[s]):
        print(N-j, end=' ')
        PRED += make_pred(mod)

    # take the average prediction for all layers
    PML['pred'] = PRED / len(M[s])
    if RESOLUTION == '5x5':
        # collect all the results in the lowest resolution
        LM[s.code] = PML['pred']


    # aggredate over years, and save some layers
    PRED = PML[PML.layer != ''].groupby(['y_lat', 'x_lon', 'layer']).pred.mean()
    PL[s.code] = array(PRED)

    # take the weighted average across all layers
    PML['pred'] = PML['pred'] * PML.weight
    PRED = PML.groupby(['year', 'y_lat', 'x_lon']).pred.sum()
    PM[s.code] = array(PRED)



    print()
    print_memory()


print("-----Saving Files")
# annual map
PM.to_csv(f'result_files/annual_map_{RESOLUTION}.csv', index=False)
PM.to_csv(f'internal_results/annual_map_{RESOLUTION}_{EN}_avg.csv', index=False)

# map with selected layers
# give layers a better names
PL.layer = PL.layer.replace(SAVED_LAYERS_NAMES)
PL.to_csv(f'result_files/layer_map_{RESOLUTION}.csv', index=False)
PL.to_csv(f'internal_results/layer_map_{RESOLUTION}_{EN}_avg.csv', index=False)

CM = PM.groupby(['y_lat', 'x_lon']).mean().reset_index().drop(columns='year')
CM.to_csv(f'result_files/map_{RESOLUTION}.csv', index=False)
CM.to_csv(f'internal_results/map_{RESOLUTION}_{EN}_avg.csv', index=False)

if RESOLUTION == '5x5':
    LM.to_csv(f'result_files/whole_map_{RESOLUTION}.csv', index=False)
    LM.to_csv(f'internal_results/whole_map_{RESOLUTION}_{EN}.csv', index=False)


print('DONE!')

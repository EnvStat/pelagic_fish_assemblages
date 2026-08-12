from read_data import *
from numpy import log, exp, array, mean, matrix, zeros
from scipy.sparse import csc_array, csr_array, csc_matrix, csr_matrix
from anchor_points import anchors

data = pandas.read_csv('data/data.csv')
N = len(data)

log_trawl_time = array(log(data.trawl_dur / 30))
log_trawl_net = array(log(data.trawl_net / 20))
log_efford = log_trawl_time + log_trawl_net


# the first and the last values are ignored
U_YEAR = [2007, 2008, 2009, 2010, 2011, 2012, 2013, 2014, 2015, 2016, 2017, 2018, 2019, 2020, 2021, 2022, 2023, 2024]

U_DTS = [10, 20, 30, 40, 50, 60, 70, 80, 90, 100, 120]

U_DEPTH = [20, 30, 40, 50, 60, 70, 80, 90, 100, 120, 140, 160, 180, 200, 250]
U_TD = [0, 10, 20, 30, 40, 50, 60, 70, 80, 100]
U_DFB = [0, 5, 10, 15, 20, 25, 30, 35, 40, 45, 50, 55]

U_SALT = [3.5, 4.0, 4.5, 5.0, 5.5, 6.0, 6.5, 7.0, 7.5, 8.0, 9.0, 10.0, 11.0, 12.0, 13.0, 14.0, 15.0, 16.0, 17.0, 18.0, 19.0, 20.0, 22.0, 24.0, 26.0, 28.0, 30]
U_TEMP = [2, 3, 4, 5, 6, 7, 8, 9, 10, 11, 12, 13, 14, 15, 16, 17]
U_TURB =  [5.3, 5.9, 6.4, 7.0, 7.6, 8.1, 8.7, 9.3, 9.9, 10.4, 11.0, 11.6, 12.2, 12.7, 13.4, 14]
U_OXYG = [0, 26, 53, 80, 107, 134, 161, 188, 214, 241, 268, 295, 322, 349, 377, 400]


def make_discretize_func(milestones):
    def df(x):
        for i, m in enumerate(milestones):
            if x < m:
                return i
        return i+1

    return df

"""
17 [2007, 2008, 2009, 2010, 2011, 2012, 2013, 2014, 2015, 2016, 2017, 2018, 2019, 2020, 2021, 2022, 2023, 2024]
14 [20, 30, 40, 50, 60, 70, 80, 90, 100, 120, 140, 160, 180, 200, 250]
10 [10, 20, 30, 40, 50, 60, 70, 80, 90, 100, 120]
26 [3.5, 4.0, 4.5, 5.0, 5.5, 6.0, 6.5, 7.0, 7.5, 8.0, 9.0, 10.0, 11.0, 12.0, 13.0, 14.0, 15.0, 16.0, 17.0, 18.0, 19.0, 20.0, 22.0, 24.0, 26.0, 28.0, 30]
15 [2, 3, 4, 5, 6, 7, 8, 9, 10, 11, 12, 13, 14, 15, 16, 17]
15 [5.3, 5.9, 6.4, 7.0, 7.6, 8.1, 8.7, 9.3, 9.9, 10.4, 11.0, 11.6, 12.2, 12.7, 13.4, 14]
2537

0.46582454588819633
A_DEPTH.shape
(2537, 14)
A_DEPTH.sum(0)
array([472, 179, 201, 227, 308, 267, 237, 158, 221, 121,  72,  24,  26,
        24])

"""

def make_data_array(L, milestones):
    df = make_discretize_func(milestones[1:-1])
    N = len(L)
    M = len(milestones) - 1
    I = L.apply(df)
    return csc_array(([1]*N, (range(N), I)), shape=(N, M))


def make_data_vectors(data, milestones):
    n = len(milestones) + 1
    a_data = make_data_array(data, milestones)
    repr_data = a_data.sum(0) / N
    return a_data, a_data.shape[1], repr_data


A_YEAR, Ny, REPR_YEAR = make_data_vectors(data.year, U_YEAR)

A_DTS, Ndts, REPR_DTS = make_data_vectors(data.dts, U_DTS)

A_DEPTH, Nd, REPR_DEPTH = make_data_vectors(data.depth, U_DEPTH)
A_TD, Ntd, REPR_TD = make_data_vectors(data.trawl_depth, U_TD)
A_DFB, Ndfb, REPR_DFB = make_data_vectors(data.dfb, U_DFB)

A_SALT, Nsalt, REPR_SALT = make_data_vectors(data.salinity, U_SALT)
A_TEMP, Ntemp, REPR_TEMP = make_data_vectors(data.temperature, U_TEMP)
A_TURB, Nturb, REPR_TURB = make_data_vectors(data.transparency, U_TURB)
A_OXYG, Noxyg, REPR_OXYG = make_data_vectors(data.bottom_oxygen, U_OXYG)


# add the arrays for the day/night factors
day_factor = array(data.ntd)[:, None]
# 1=day, -1=night, 0=twilight

A_TD_NTD = A_TD.copy() * day_factor
A_DFB_NTD = A_DFB.copy() * day_factor

REPR_TD_NTD = A_TD_NTD.sum(0) / N
REPR_DFB_NTD = A_DFB_NTD.sum(0) / N

# geo data

def get_distance_vector(row):
    L = [haversine_deg((row.y_lat, row.x_lon), (y, x)) for x, y in anchors]
    L = array(L)
    L = exp(-L/50)
    L[L<0.001] = 0
    L = L / L.sum()
    return L

Ngeo = len(anchors)
A_GEO = array(list(data.apply(get_distance_vector, axis=1)))


if __name__ == '__main__':
    print(Ny, U_YEAR)
    print(Nd, U_DEPTH)
    print(Ndts, U_DTS)
    print(Nsalt, U_SALT)
    print(Ntemp, U_TEMP)
    print(Nturb, U_TURB)
    print(N)
    print()
    print(A_GEO.max())
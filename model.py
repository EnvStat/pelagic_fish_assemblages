"""
This file contains the model description
"""

import numba

from useful import dlmultivariate_norm_unnormalized, rnorm, logistic, logit

from probabilistic_programming.dec_mod import derived_quantity, prior, basic_transformation, likelihood_factor, ModelParameter, Indexer, Constant
from probabilistic_programming.dec_mod import Model2 as Model
from load_data import *

from numpy import array, log, exp, mean, cos, pi, cumsum
import numpy
from scipy import stats, linalg
from scipy.special import loggamma


def ssq(X):
    return X@X

def normp(x):
    return -x**2/2

def mnormp(X):
    return -ssq(X)/2  -  X.sum()**2/2


ENV_COVARIATE_LIST = 'depth dts   dfb td   dfb_ntd  td_ntd  salt temp turb oxyg   year'.split()
COVARIATE_LIST = ENV_COVARIATE_LIST + ['geo']


def define_model(SPECIE):
    CODE = str(DictOfUsedFish()[SPECIE].code)
    DATA = array(data[CODE])
    DATA_PM = DATA*2 - 1
    naive_estimate = sum(DATA) / N

    class MyModel(Model):

        # BASE VAL
        logit_base: ModelParameter(term_of='logit_expected') = logit(naive_estimate)

        # ENVORINMENTAL COVARIATES
        ECOV: Indexer(ENV_COVARIATE_LIST)
        ACOV: Indexer(COVARIATE_LIST)

        derof_depth_f: ModelParameter = rnorm(0, 0.001, Nd-1)
        derof_dts_f:   ModelParameter = rnorm(0, 0.001, Ndts-1)

        derof_dfb_f:   ModelParameter = rnorm(0, 0.001, Ndfb-1)
        derof_td_f:    ModelParameter = rnorm(0, 0.001, Ntd-1)
        derof_dfb_ntd_f:   ModelParameter = rnorm(0, 0.001, Ndfb-1)
        derof_td_ntd_f:    ModelParameter = rnorm(0, 0.001, Ntd-1)

        derof_salt_f:  ModelParameter = rnorm(0, 0.001, Nsalt-1)
        derof_temp_f:  ModelParameter = rnorm(0, 0.001, Ntemp-1)
        derof_turb_f:  ModelParameter = rnorm(0, 0.001, Nturb-1)
        derof_oxyg_f:  ModelParameter = rnorm(0, 0.001, Noxyg-1)

        derof_year_f:  ModelParameter = rnorm(0, 0.001, Ny-1)

        #

        _array_depth: Constant = A_DEPTH
        _array_dts:   Constant = A_DTS

        _array_dfb:   Constant = A_DFB
        _array_td:    Constant = A_TD

        _array_dfb_ntd:   Constant = A_DFB_NTD
        _array_td_ntd:    Constant = A_TD_NTD

        _array_salt:  Constant = A_SALT
        _array_temp:  Constant = A_TEMP
        _array_turb:  Constant = A_TURB
        _array_oxyg:  Constant = A_OXYG

        _array_year:  Constant = A_YEAR

        #

        _repr_depth: Constant = REPR_DEPTH
        _repr_dts:   Constant = REPR_DTS

        _repr_dfb:   Constant = REPR_DFB
        _repr_td:    Constant = REPR_TD

        _repr_dfb_ntd:   Constant = REPR_DFB_NTD
        _repr_td_ntd:    Constant = REPR_TD_NTD

        _repr_salt:  Constant = REPR_SALT
        _repr_temp:  Constant = REPR_TEMP
        _repr_turb:  Constant = REPR_TURB
        _repr_oxyg:  Constant = REPR_OXYG

        _repr_year:  Constant = REPR_YEAR


        # PRIORS
        log_factor_std_ECOV:   lambda x: x - exp(x)*10 = -5
        logit_factor_smt_ECOV: lambda x: 10*x - log(1+exp(x))*11 = 5


        @prior
        def prior_pen_ECOV(derof_ECOV_f, factor_smt_ECOV):
            X = derof_ECOV_f
            s = factor_smt_ECOV
            penalty =  -(X[0]**2 + X[-1]**2) - ssq(X[1:-1])*(1+s**2) + (X[1:]@X[:-1])*2*s
            penalty = penalty / (1-s**2) / 2
            return penalty
        @prior
        def prior_det_ECOV(_array_ECOV, factor_smt_ECOV):
            s = factor_smt_ECOV
            n = _array_ECOV.shape[1]
            # substract 1 from n because of the determinant formula. Substract another 1 because derof_ECOV matrix is smaller by 1
            return - log(1-s**2)*(n-2) / 2


        @basic_transformation
        def ECOV_f(derof_ECOV_f, _repr_ECOV):
            S = derof_ECOV_f
            S = numpy.append(0, cumsum(S))
            return S - sum(S * _repr_ECOV)


        @derived_quantity(term_of='logit_expected')
        def ECOV_factor(_array_ECOV, ECOV_f, factor_std_ECOV):
            return _array_ECOV @ ECOV_f * factor_std_ECOV


        # SPATIAL FACTOR
        geo_f: lambda Y: -ssq(Y)/2 = rnorm(0, 0.001, Ngeo)
        log_factor_std_geo:   lambda x: x - exp(x)*10 = -5

        @derived_quantity(term_of='logit_expected')
        def geo_factor(geo_f, factor_std_geo):
            return A_GEO @ (geo_f - geo_f.mean()) * factor_std_geo


        # TRAWL EFFORT
        log_ttscale: normp = 0

        @derived_quantity(term_of='logit_expected')
        def trawltime_factor(ttscale):
            return log_trawl_time * ttscale


        # LIKELIHOOD
        @derived_quantity
        def termsof_likelihood(expected):
            return log(expected * DATA_PM + (1-DATA))

        @likelihood_factor
        def likelihood(termsof_likelihood):
            return termsof_likelihood.sum()
            #return termsof_likelihood[:1923].sum()  # only till 2020 (inclusive)


        # OTHER
        # scaled factors
        @derived_quantity
        def ECOV_f_s(ECOV_f, factor_std_ECOV):
            return ECOV_f * factor_std_ECOV
        @derived_quantity
        def geo_f_s(geo_f, factor_std_geo):
            return (geo_f - geo_f.mean()) * factor_std_geo

        @derived_quantity
        def tdn_f_s(td_f_s, td_ntd_f_s):
            return td_f_s - td_ntd_f_s
        @derived_quantity
        def tdd_f_s(td_f_s, td_ntd_f_s):
            return td_f_s + td_ntd_f_s

        @derived_quantity
        def dfbn_f_s(dfb_f_s, dfb_ntd_f_s):
            return dfb_f_s - dfb_ntd_f_s
        @derived_quantity
        def dfbd_f_s(dfb_f_s, dfb_ntd_f_s):
            return dfb_f_s + dfb_ntd_f_s


    return MyModel


if __name__ == '__main__':
    M = define_model('lumpf')()
    print(M.expected)
    print(M.Prior)
    print(M.Likelihood)

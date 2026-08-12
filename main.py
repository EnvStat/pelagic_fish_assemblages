import os
import datetime

import pandas

import model
import gen_MCMC
import read_data

from random import shuffle


NAMES = read_data.DictOfUsedFish()
SPECIES_LIST = list(NAMES)

def run_MCMC_for_species(SPECIE, profiling=False):

    MCMC_UPDATE_BATCHES = tuple([]
      + [(f'derof_{cov}_f', 'logit_base', f'log_factor_std_{cov}') for cov in model.ENV_COVARIATE_LIST]
      + [('geo_f', 'logit_base', 'log_factor_std_geo')]
      + [(f'logit_factor_smt_{cov}', ) for cov in model.ENV_COVARIATE_LIST]
      + [tuple(f'log_factor_std_{cov}' for cov in model.COVARIATE_LIST)]
      + [('log_ttscale', )]
        )

    if profiling:
        gen_MCMC.MCMC(
            trial_name='samples/profiling',
            model_class=model.define_model(SPECIE),
            batches=MCMC_UPDATE_BATCHES,
            warmup=0,
            iterations_n=1_000,
            thinning=1,
            verbosity=True
        )
        return

    print('#'*80)
    print(SPECIES_LIST.index(SPECIE), SPECIE)
    print(datetime.datetime.now())
    print('#'*80)

    gen_MCMC.MCMC(
        trial_name='samples/'+NUMBER+'_'+SPECIE.name,
        model_class=model.define_model(SPECIE),
        batches=MCMC_UPDATE_BATCHES,
        warmup=100_000,
        iterations_n=300_000,
        thinning=10,
        verbosity=len(SPECIES_LIST) == 1  # print more info when working with one species
    )

NUMBER = '5'

rewrite = False

shuffle(SPECIES_LIST)


if __name__ == '__main__':
    for SPECIE in SPECIES_LIST:
        if rewrite or not os.path.exists('samples/'+NUMBER+'_'+SPECIE.name+'/data_1.pik'):
            run_MCMC_for_species(SPECIE)
        else:
            print(SPECIE, 'is done')

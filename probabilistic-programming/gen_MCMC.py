"""
Generic MC-MC
"""

from datetime import datetime

from numpy import exp, isnan, isinf

import ram
import data_pers
from pb_utils import rexp, runif, format_timedelta, CumulativeStopwatch



def MCMC_verbose(
         trial_name,
         model_class,
         batches,
         warmup=10_000,
         iterations_n=300_000,
         thinning=10):
    """
    Markov chain Monte Carlo.

    Chain would contain `warmup` + `iterations_n`.
    Output would be saved to `trial_name` folder as two files, corresponding to warmup and main iterations.
    Only every `thinning` iteration is recorded.
    """
    # prepare files to record MCMC output
    H = data_pers.ParallelDataWriter(trial_name, key='n')
    print()
    print(trial_name)
    print()

    # set up
    model = model_class()
    print('started with Likelihood', model.Likelihood)
    print('and Prior', model.Prior)
    print('and Posterior', model.Posterior)
    if isnan(model.Likelihood) or isinf(model.Likelihood):
        raise Exception('Starting with zero Likelihood')
    if isnan(model.Prior) or isinf(model.Prior):
        raise Exception('Starting with zero Prior')

    # check batches
    MCMC_UPDATE_BATCHES = [tuple(l) for l in batches]

    # initialize proposal variance
    jump = {}
    for batch in MCMC_UPDATE_BATCHES:
        jump[batch] = ram.RobustAdaptiveMetropolis(len(model.get_params(batch)))

    # initialize timer
    milestones =  sum([[1*10**i, 2*10**i, 5*10**i] for i in range(1, 7)], [80000])
    batch_times = {batch: CumulativeStopwatch() for batch in MCMC_UPDATE_BATCHES}
    batch_times['_computaion'] = CumulativeStopwatch()
    batch_times['_adapting'] = CumulativeStopwatch()
    batch_times['_hessian'] = CumulativeStopwatch()
    batch_times['_jumping'] = CumulativeStopwatch()
    batch_times['_sampling'] = CumulativeStopwatch()
    batch_times['_parameter_reading'] = CumulativeStopwatch()
    batch_times['_parameter_writing'] = CumulativeStopwatch()
    batch_times['_bookkeeping'] = CumulativeStopwatch()

    def print_total_time():
        total_time = datetime.now() - time_start
        time_per_iter = total_time / (iteration + 1)
        print('total time:', format_timedelta(total_time))
        print('time per iter:', format_timedelta(time_per_iter))
        print('job times:')
        for k, v in batch_times.items():
            print(f'{v}:\t{100*v.total/total_time:.2f}% --\t{k}')
        print()
        print()

    def print_intermediate_time():
        time_now = datetime.now()
        total_time = time_now - time_start
        time_per_iter = total_time / (iteration + 1)
        if iteration < warmup:
            time_end = time_now + time_per_iter*(warmup - iteration - 1)
        else:
            time_end = time_now + time_per_iter*(iterations_n + warmup - iteration - 1)
        msg = f'{time_now:%H:%M} -- iter {iteration+1} -- expected in {time_end:%H:%M} (+{format_timedelta(time_end-time_now)}) -- {format_timedelta(time_per_iter)}/i'
        print(msg, f'{model.Likelihood=}')

    time_start = time_last_note = datetime.now()
    print(f'ready at {time_start:%Y-%m-%d %H:%M}')

    for iteration in range(iterations_n + warmup):

        ####################
        ##   MCMC sample  ##
        ####################
        for batch in MCMC_UPDATE_BATCHES:
            with batch_times[batch]:
                with batch_times['_hessian']:
                    if iteration < warmup and iteration % 1000 == 0:
                        hess = model.measure_hessian(batch, 'Posterior')
                        jump[batch].set_prec(-hess)


                with batch_times['_parameter_reading']:
                    old_vals = model.get_params(batch)
                with batch_times['_sampling']:
                    new_vals = old_vals + jump[batch].draw()
                with batch_times['_parameter_writing']:
                    model.set_params(batch, new_vals)

                with batch_times['_computaion']:
                    jump_prob = exp(model.measure_change('Posterior'))

                if isnan(jump_prob):
                    jump_prob = 0

                with batch_times['_adapting']:
                    if jump_prob < 0.134 or jump_prob > 0.334:
                        jump[batch].adapt(min(1, jump_prob), iteration)

                with batch_times['_jumping']:
                    if jump_prob > runif():
                        # jump is succesfull! replase current values
                        model.drop_records()
                    else:
                        model.reverse_change()


        ####################
        ## SAVE ITERATION ##
        ####################

        if iteration == warmup:
            # when warmup is over, start writing into a new file
            H.new_file()
            print('started main iterations with Likelihood', model.Likelihood)
            print('and Prior', model.Prior)
            print_total_time()
            time_last_note = datetime.now()

        with batch_times['_bookkeeping']:
            if iteration % thinning == 0:
                # save MCMC sample and some additional quantities
                H.writerow(
                    Prior=model.Prior,
                    Likelihood=model.Likelihood,
                    Posterior=model.Posterior,

                    **model.parameters,
                    )

        if iteration == warmup  or  iteration+1 in milestones  or  (datetime.now() - time_last_note).seconds > 600:
            print_intermediate_time()
            time_last_note = datetime.now()

    print_total_time()
    print('done!')



def MCMC_non_verbose(
         trial_name,
         model_class,
         batches,
         warmup=10_000,
         iterations_n=300_000,
         thinning=10):
    """
    Markov chain Monte Carlo.

    Chain would contain `warmup` + `iterations_n`.
    Output would be saved to `trial_name` folder as two files, corresponding to warmup and main iterations.
    Only every `thinning` iteration is recorded.
    """
    # prepare files to record MCMC output
    H = data_pers.ParallelDataWriter(trial_name, key='n')

    # set up
    model = model_class()
    print('started with Posterior', model.Posterior)
    if isnan(model.Likelihood) or isinf(model.Likelihood):
        raise Exception('Starting with zero Likelihood')
    if isnan(model.Prior) or isinf(model.Prior):
        raise Exception('Starting with zero Prior')

    # check batches
    MCMC_UPDATE_BATCHES = [tuple(l) for l in batches]

    # initialize proposal variance
    jump = {}
    for batch in MCMC_UPDATE_BATCHES:
        jump[batch] = ram.RobustAdaptiveMetropolis(len(model.get_params(batch)))

    # initialize timer
    milestones =  [1*10**i for i in range(1, 7)]

    def print_total_time():
        total_time = datetime.now() - time_start
        time_per_iter = total_time / (iteration + 1)
        print('total time:', format_timedelta(total_time))
        print('time per iter:', format_timedelta(time_per_iter))
        print()

    def print_intermediate_time():
        time_now = datetime.now()
        total_time = time_now - time_start
        time_per_iter = total_time / (iteration + 1)
        if iteration < warmup:
            time_end = time_now + time_per_iter*(warmup - iteration - 1)
        else:
            time_end = time_now + time_per_iter*(iterations_n + warmup - iteration - 1)
        msg = f'{time_now:%H:%M} -- iter {iteration+1} -- expected in {time_end:%H:%M} (+{format_timedelta(time_end-time_now)}) -- {format_timedelta(time_per_iter)}/i'
        print(msg, f'{model.Posterior=}')

    time_start = time_last_note = datetime.now()
    print(f'ready at {time_start:%Y-%m-%d %H:%M}')

    for iteration in range(iterations_n + warmup):

        ####################
        ##   MCMC sample  ##
        ####################
        for batch in MCMC_UPDATE_BATCHES:

            if iteration < warmup and iteration % 1000 == 0:
                hess = model.measure_hessian(batch, 'Posterior')
                jump[batch].set_prec(-hess)

            old_vals = model.get_params(batch)
            new_vals = old_vals + jump[batch].draw()
            model.set_params(batch, new_vals)

            jump_prob = exp(model.measure_change('Posterior'))

            if isnan(jump_prob):
                jump_prob = 0

            if jump_prob < 0.134 or jump_prob > 0.334:
                jump[batch].adapt(min(1, jump_prob), iteration)

            if jump_prob > runif():
                # jump is succesfull! replase current values
                model.drop_records()
            else:
                model.reverse_change()


        ####################
        ## SAVE ITERATION ##
        ####################

        if iteration == warmup:
            # when warmup is over, start writing into a new file
            H.new_file()
            print_total_time()
            time_last_note = datetime.now()

        if iteration % thinning == 0:
            # save MCMC sample and some additional quantities
            H.writerow(
                Prior=model.Prior,
                Likelihood=model.Likelihood,
                Posterior=model.Posterior,

                **model.parameters,
                )

        if iteration == warmup  or  iteration+1 in milestones  or  (datetime.now() - time_last_note).seconds > 600:
            print_intermediate_time()
            time_last_note = datetime.now()

    print_total_time()
    print('done!')


def MCMC(*args,
         verbosity=False,
         **kwargs):
    if verbosity:
        MCMC_verbose(*args, **kwargs)
    else:
        MCMC_non_verbose(*args, **kwargs)



def optimize(
         model_class,
         batches,
         iterations_n=100,
         epsilon=0.001):
    # set up
    model = model_class()
    print('started with Posterior', model.Posterior)
    if isnan(model.Likelihood) or isinf(model.Likelihood):
        raise Exception('Starting with zero Likelihood')
    if isnan(model.Prior) or isinf(model.Prior):
        raise Exception('Starting with zero Prior')

    for iteration in range(iterations_n):

        A = model.measure_hessian(batch, 'Posterior')
        A = -hess

        jump[batch].set_prec(-hess)

        old_vals = model.get_params(batch)
        new_vals = old_vals + jump[batch].draw()
        model.set_params(batch, new_vals)

        jump_prob = exp(model.measure_change('Posterior'))

        if isnan(jump_prob):
            jump_prob = 0

        if jump_prob < 0.134 or jump_prob > 0.334:
            jump[batch].adapt(min(1, jump_prob), iteration)

        if jump_prob > runif():
            # jump is succesfull! replase current values
            model.drop_records()
        else:
            model.reverse_change()


        ####################
        ## SAVE ITERATION ##
        ####################

        if iteration == warmup:
            # when warmup is over, start writing into a new file
            H.new_file()
            print_total_time()
            time_last_note = datetime.now()

        if iteration % thinning == 0:
            # save MCMC sample and some additional quantities
            H.writerow(
                Prior=model.Prior,
                Likelihood=model.Likelihood,
                Posterior=model.Posterior,

                **model.parameters,
                )

        if iteration == warmup  or  iteration+1 in milestones  or  (datetime.now() - time_last_note).seconds > 600:
            print_intermediate_time()
            time_last_note = datetime.now()

    print_total_time()
    print('done!')


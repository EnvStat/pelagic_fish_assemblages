if 1:  # standard profiling

    from main import run_MCMC_for_species as MCMC
    import cProfile as prf
    import pstats


    #MCMC.MAIN(warmup=0, iterations_n=1000, trial_name="profiling")

    prf.run('MCMC("cod", profiling=True)', 'profiling_output')

    p = pstats.Stats('profiling_output')

    p.sort_stats('cumulative').print_stats(50)
    p.sort_stats('tottime').print_stats(50)

    p.sort_stats('tottime').print_stats('useful.py:')
    p.sort_stats('tottime').print_stats('dec_mod.py:')
    p.sort_stats('tottime').print_stats('numpy')
    p.sort_stats('tottime').print_stats('ram.py:')
    p.sort_stats('tottime').print_stats('copy')
    p.sort_stats('tottime').print_stats('gen_MCMC.py')


else:  # self-made profiling for model components

    from datetime import datetime
    #import prob_prog
    #prob_prog._PROFILING = True
    import dec_mod
    dec_mod._PROFILING = True

    from main import run_MCMC_for_species as MCMC
    from model import COVARIATE_LIST
    total_start = datetime.now()
    MCMC("cod", profiling=True)

    total = (datetime.now() - total_start)
    total_rec = sum(prf['recompute_time'].total_seconds() for prf in dec_mod._PROFILING_RESULTS.values())
    time_per_cov = {k: 0 for k in COVARIATE_LIST}
    time_for_prior = 0
    print()
    print('Total Execution Time', total.total_seconds(), 'sec')
    print('Total Recompute Time', total_rec, 'sec')
    print('''% - percent of computing in total execution
tt(s) - total time spend computing the function in seconds
ct(ms) - average time spend computing the function in milliseconds
Ccalls - compute calls, i.e. number of times the function had to be computed
Scalls - saved calls, i.e. number of time the function was called but not computed
att(s) - argument time, total - time spend computing the arguments of this fuction
leak(s) - leaked time: time spend on this fuction, excluding its computation and computation of its arguments''')
    print()
    print('                                   %    %  tt(s)   ct(ms)  Rcalls  Scalls    att(s)  leak(s)')
    for name, prf in sorted(dec_mod._PROFILING_RESULTS.items(), key=lambda item: item[1]['recompute_time'].total, reverse=True):
        if prf['recompute_calls'] == 0:
            #print(f'{name:>30}     -')
            continue

        if 'prior' in name: time_for_prior += prf['recompute_time'].total_seconds()
        for cov in COVARIATE_LIST:
            if cov in name: time_per_cov[cov] += prf['recompute_time'].total_seconds()

        prf['ct'] = '{:.4f}'.format(prf['recompute_time'].total_seconds()/prf['recompute_calls'] * 1000)
        prf['percent'] = '{:.1f}'.format(prf['recompute_time'].total_seconds()/total.total_seconds() * 100)
        prf['percent_rec'] = '{:.1f}'.format(prf['recompute_time'].total_seconds()/total_rec * 100)
        prf['saved_calls'] = prf['total_calls'] - prf['recompute_calls']
        prf['rest_time'] = prf['total_time'].total - prf['recompute_time'].total - prf['arguments_time'].total

        prf['recompute_time'] = prf['recompute_time'].total_seconds()
        prf['arguments_time'] = prf['arguments_time'].total_seconds()
        prf['rest_time'] = prf['rest_time'].total_seconds()

        print('{name:>30}: {percent:>4} {percent_rec:>4}  {recompute_time:.3f} {ct:>8}  {recompute_calls:>7} {saved_calls:>7}    {arguments_time:.3f}   {rest_time:.3f}'.format(name=name, **prf))

    print()
    for cov, recompute_time in time_per_cov.items():
        percent = '{:.1f}'.format(recompute_time/total.total_seconds()*100)
        percent_rec = '{:.1f}'.format(recompute_time/total_rec*100)
        print(f'{cov:>30}: {percent:>4} {percent_rec:>4}  {recompute_time:.3f}')

    print()
    percent = '{:.1f}'.format(time_for_prior/total.total_seconds()*100)
    percent_rec = '{:.1f}'.format(time_for_prior/total_rec*100)
    print(f'{"prior":>30}: {percent:>4} {percent_rec:>4}  {recompute_time:.3f}')



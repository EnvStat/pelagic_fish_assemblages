import copy
from datetime import datetime, timedelta
from math import inf

import numpy
from numpy import pi
from numpy import log, exp, mean, std, cov
from numpy import matrix, identity, array
from numpy import random
from numpy.linalg import cholesky, slogdet

import numba

from scipy.special import gammaln


@numba.vectorize([numba.float64(numba.float64)])
def logit(x):
    return log(x/(1-x))


@numba.vectorize([numba.float64(numba.float64)])
def logistic(x):
    return 1/(1+exp(-x))


def logsum(L):
    L = list(L)
    h = max(L)
    return h + log(sum(exp(x-h) for x in L))


class ZeroLikelihood(BaseException):
    pass


# -----------------------------------------
# -- matrixes
# -----------------------------------------

def invert_with_cholesky(M):
    chol = cholesky(M)
    inv = chol.I
    return inv.T * inv


def largest_eigenvalue(matrix):
    w, v = numpy.linalg.eig(array(matrix))
    # eigenvalues and eigenvectors are recieved unordered
    # take the largest ones
    return max(w).real


def largest_l_eigenvector(matrix):
    """
    Input matrix in the form of M[source][sink]:
    for the formula  I @ NGM
    """
    # matrix is transposed for the purpose of counting left eigenvectors
    w, v = numpy.linalg.eig(array(matrix).T)
    # eigenvalues and eigenvectors are recieved unordered
    # take the largest ones
    w, v = max(zip(w, v.T))
    if all(v < 0):
        v *= -1
    return w.real, v.real


def largest_r_eigenvector(matrix):
    """
    Input matrix in the form of M[sink][source]:
    for the formula  NGM @ I
    """
    w, v = numpy.linalg.eig(array(matrix))
    # eigenvalues and eigenvectors are recieved unordered
    # take the largest ones
    w, v = max(zip(w, v.T))
    if all(v < 0):
        v *= -1
    return w.real, v.real


def compute_unit_NGM(NGM):
    unit_R0 = largest_eigenvalue(NGM)
    return array(NGM) / unit_R0


# -----------------------------------------
# -- density and logdensities
# -----------------------------------------

_DLNORM_CONSTANT = -0.5*log(2*pi)
LOG_FACTORIAL = tuple([gammaln(x+1) for x in range(100)])
def lf(x):
    if x < 100:
        return LOG_FACTORIAL[x]
    else:
        return gammaln(x+1)


def dlpois(x, p):
    if x==0:
        return -p
    elif p==0:
        return -inf
    else:
        return x*log(p)-lf(x)-p


def dlpois_un(x, p):
    if x==0:
        return -p
    elif p==0:
        return -inf
    else:
        return x*log(p)-p


def dlbinom(x, N, p):
    if x==N==0:
        return 0
    elif p==x==0:
        return 0
    elif p==1 and x==N:
        return 0
    elif p in (0, 1):
        return -inf
    else:
        return lf(N) - lf(x) - lf(N-x) + x*log(p) + (N-x)*log(1-p)


def dlpolya(x, mean, over):
    """
    overdispersed poisson aka negative binomial aka Polya

    nbinom.pmf(x) = choose(x+n-1, n-1) * p**n * (1-p)**x
    """
    if mean == x == 0:
        return 0
    elif x > 0 and mean == 0:
        return -inf
    n = 1 / over
    p = n / (mean+n)
    return gammaln(x+n) - gammaln(n) - lf(x) + n*log(p) + x*log(1-p)


def dlmultinom_unnormalized(X, P):
    s = sum(P)
    P = [p/s for p in P]
    return sum(log(p)*x for x, p in zip(X, P))


def dlimproper_1x(x):
    if x == 0:
        return 0
    return -log(x)


def dlnorm(x, m, std):
    return _DLNORM_CONSTANT -log(std) - (x-m)**2 / (2*std**2)


def dllognorm(x, m, std):
    if x == 0: return -inf
    return _DLNORM_CONSTANT -log(std)-log(x) - (log(x)-log(m))**2 / (2*std**2)


def dllogitnorm(x, m, std):
    if x in (0, 1): return -inf
    return _DLNORM_CONSTANT -log(std)-log(x)-log(1-x) - (logit(x)-logit(m))**2 / (2*std**2)


def dlbeta(x, a, b):
    return (a-1)*log(x) + (b-1)*log(1-x)


def dlgamma(x, a, b):
    if x==0 and a>0:
        return float('-inf')
    return (a-1)*log(x) - b*x


def dlexp(x, l):
    return - l*x


def dlU01(x):
    return -1


def dlmultivariate_norm_unnormalized(x, inverse):
    ''' no normalizing constant'''
    x_T = matrix([[h] for h in x])
    return -0.5 * (x @ inverse @ x_T)[0, 0]


def dlmultivariate_norm(x, covariance):
    """ no dimention-dependent constant here, only factor dependent on covariance """
    (sign, logdet) = slogdet(covariance)
    return -0.5 * logdet + dlmultivariate_norm_unnormalized(x, covariance.I)


def dlgamma_unnormalized(x, mean, var):
    beta = mean / var
    alpha = mean * beta
    return alpha*log(beta) + (alpha-1)*log(x) - beta*x


def d_gamma_unnormalized(x, mean, var):
    beta = mean / var
    alpha = mean * beta
    return beta**alpha * x**(alpha-1) * exp(-beta*x)


# -----------------------------------------
# -- sampling
# -----------------------------------------

rexp = random.exponential
rpois = random.poisson
rnorm = random.normal
rbeta = random.beta
rbinom = random.binomial
runif = random.uniform


def rpolya(m, over):
    n = 1 / over
    p = n / (m+n)
    return random.negative_binomial(n, p)


def rmulnorm_cov(x, cov):
    """ sample multivaruate normal using covariance """
    return random.multivariate_normal(x, cov).tolist()


def rmulnorm_cholesky(mean, cholesky):
    """ sample multivaruate normal using cholesky """
    X = random.normal(size=len(mean))
    return (cholesky @ X + mean).A1.tolist()


def rmultinom(n, P):
    s = sum(P)
    P = [p/s for p in P]
    return list(random.multinomial(n, P))


def rgamma(alpha, beta):
    return random.gamma(alpha, 1/beta)

def rbeta_kN(k, N):
    """ Beta distribution, defined thought k=alpha and N=alpha+beta. If N<k, returns 1 """
    if N < k:
        return 1
    return rbeta(k, N-k)


# -----------------------------------------
# -- logging and time
# -----------------------------------------

MILESTONES = [0, 1] + sum([[1*10**i, 2*10**i, 5*10**i] for i in range(1, 7)], [])


START_TIME = None
LAST_TIME = None
LAST_ITER = None
def progress_str(i, n):
    global START_TIME, LAST_ITER, LAST_TIME
    time_now = datetime.now()

    if i == 0:
        START_TIME = time_now
        msg = f'{time_now:%Y-%m-%d %H:%M} -- starting'
    elif i == n:
        iteration = (time_now - START_TIME) / i
        total_time = time_now - START_TIME
        msg = f'fin -- iter {i} {iteration}/i --  total time {total_time}'
    else:
        iteration = (time_now - LAST_TIME) / (i - LAST_ITER)
        time_end = time_now + iteration*(n-i)
        day_diff = (time_end.date() - time_now.date()).days
        diff_str = f' (+{day_diff})' if day_diff else ''
        msg = f'{time_now:%Y-%m-%d %H:%M} -- iter {i} -- expected in {time_end:%H:%M}{diff_str} -- {iteration}/i'

    LAST_TIME = time_now
    LAST_ITER = i
    return msg


def print_progress(i, n):
    if i in MILESTONES or i == n:
        print(progress_str(i, n), end='\r')


def format_timedelta(td):
    seconds = int(td.total_seconds())
    days = seconds // 60 // 60 // 24
    hours = seconds // 60 // 60 % 24
    if days: return f'{days}d-{hours}h'

    minut = seconds // 60 % 60
    if hours: return f'{hours}h-{minut}m'
    if minut > 10: return f'{minut}m'

    seconds = seconds % 60
    if minut: return f'{minut}m-{seconds}sec'
    if seconds > 10: return f'{seconds}sec'

    microsec = td.total_seconds() % 60
    if seconds: return f'{microsec:0.2f}sec'
    return f'{1000*microsec:4.2f}ms'


class CumulativeStopwatch():
    def __init__(self):
        self.total = timedelta()

    def start(self):
        self.start_time = datetime.now()

    def stop(self):
        self.total += (datetime.now() - self.start_time)

    def __enter__(self): self.start()
    def __exit__(self, exc_type, exc_value, traceback): self.stop()

    def __str__(self):
        return format_timedelta(self.total)

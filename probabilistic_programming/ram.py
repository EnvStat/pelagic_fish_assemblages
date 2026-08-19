from math import sqrt, exp
import tensorflow_probability as tfp
import numpy as np

# This is a generic 'adaptive proposal', which is instantiated
# for each 'sampling block':
class RobustAdaptiveMetropolis:
    """Simple implementation of the Robust Adaptive Metropolis sampler.

    Building blocks for the Robust Adaptive Metropolis sampler
    (doi:10.1007/s11222-011-9269-5).

    The module provides two methods, 'draw' and 'adapt', which draw
    random samples from the proposal, and adapt the proposal, respectively.
    They should be applied consecutively ('adapt' uses auxiliary variables
    stored in 'draw').
    """

    # Constructor: d is the dimension of the proposal:
    def __init__(self, d, alpha_opt=0.234, gamma=0.66):
        """Initialise the adaptive proposal distribution.

        :param d: state-space dimension
        :param alpha_opt: desired acceptance rate (default: 0.234)
        :param gamma: step size decay rate (default: 0.66)
        """

        self.d = d                 # Dimension
        self.z = np.zeros(d)       # Independent N(0,I) rv's
        self.chol = np.identity(d) # Proposal Cholesky factor
        self.alpha_opt = alpha_opt # Desired accept rate
        self.gamma = gamma         # Step size decay rate

    def draw(self):
        """Draw proposal increment."""

        # Draw a proposal (increment) z ~ N(0,I), output ~ N(0, chol*chol')
        # NB: It is important that 'z' is saved in the state (used in adapt)
        self.z = np.random.randn(self.d)
        return self.chol @ self.z

    # Adapt the proposal covariance:
    def adapt(self, alpha, j):
        """Adapt the proposal.

        :param alpha: acceptance probability of the last proposal.
        :param j: number of current iteration.
        """

        # Difference of acceptance prob vs. desired:
        dalpha = alpha - 0.234
        # Step size (as in the paper):
        step = min(1, self.d*pow(j+1, -self.gamma))


        # Calculate normalised 'innovation', avoiding division by zero:
        sz2 = sqrt(np.inner(self.z, self.z))
        normalised_z = self.chol @ (self.z/sz2 if sz2 > 0 else self.z)

        # Calculate new proposal covariance:
        self.cov = self.chol @ self.chol.transpose()
        self.cov += step * dalpha * np.outer(normalised_z, normalised_z)
        # ...and its Cholesky factor:
        self.chol = np.linalg.cholesky(self.cov)
        # (NB: This could also be done by a rank-1 Cholesky update/downdate,
        # which saves computations if d >> 1)

    def set_prec(self, prec):
        try:
            chol = np.linalg.cholesky(np.linalg.inv(prec))
        except:
            n = prec.shape[0]
            for i in range(n):
                prec[i, i] = abs(prec[i, i])
            for i in range(1, n):
                for j in range(i):
                    threshold  = (prec[i, i] * prec[j, j])**0.5 / (n-0.99)
                    if prec[i, j] > threshold:
                        prec[j, i] = prec[i, j] = -threshold
                    elif prec[i, j] < -threshold:
                        prec[j, i] = prec[i, j] = threshold
            try:
                chol = np.linalg.cholesky(np.linalg.inv(prec))
            except:
                for i in range(1, n):
                    for j in range(i):
                        prec[j, i] = prec[i, j] = 0
                h = prec.max()
                for i in range(n):
                    prec[i, i] += h
                try:
                    chol = np.linalg.cholesky(np.linalg.inv(prec))
                except:
                    print(prec)
                    raise

        self.chol = chol * (np.e / np.log(self.d+1)**2)


    def diagonalize(self):
        self.chol *= np.identity(self.d)


class RobustAdaptiveMetropolis_zerosum(RobustAdaptiveMetropolis):
    # Mikhail Shubin, 2024
    def __init__(self, d, *args, **kwargs):
        super().__init__(*args, d=d-1, **kwargs)

    def draw(self):
        res = super().draw()
        return np.concatenate((res, [-sum(res)]))

    def set_prec(self, prec):
        prec = prec[:-1, :-1]
        super().set_prec(prec)

class RobustAdaptiveMetropolis_upd(RobustAdaptiveMetropolis):
    # Mikhail Shubin, 2024
    def adapt(self, alpha, j):
        """Adapt the proposal.

        :param alpha: acceptance probability of the last proposal.
        :param j: number of current iteration.
        """

        # Step size (as in the paper):
        step = min(1, self.d*pow(j+1, -self.gamma))

        # Difference of acceptance prob vs. desired:
        dalpha = alpha - self.alpha_opt

        # Calculate normalised 'innovation', avoiding division by zero:
        sz2 = sqrt(np.inner(self.z, self.z))
        normalised_z = self.chol @ (self.z/sz2 if sz2 > 0 else self.z)

        # Calculate new proposal covariance:
        update(self.chol, (step * dalpha)**0.5 * normalised_z)
        #tfp.math.cholesky_update(self.chol, normalised_z, multiplier=step * dalpha)


def cholupdate(R, x):
    p = np.size(x)
    diag = np.array([R[k,k] for k in range(p)])
    r = np.sqrt(diag**2 + x**2)
    c = r / diag
    s = x / diag
    for k in range(p):
        R[k,k] = r[k]
        R[k,k+1:p] = (R[k,k+1:p] + s[k]*x[k+1:p]) / c[k]
        x[k+1:p]= c[k] * x[k+1:p] - s[k] * R[k, k+1:p]

import scipy
from scipy import linalg

def update(L: np.ndarray, v: np.ndarray) -> None:
    """Python implementation of the rank-1 update algorithm from section 2 in [1]_.

    Warning: The validity of the arguments will not be checked by this method, so
    passing invalid argument will result in undefined behavior.

    Parameters
    ----------
    L : (N, N) numpy.ndarray, dtype=numpy.double
        The lower-triangular Cholesky factor of the matrix to be updated.
        Must have shape `(N, N)` and dtype `np.double`.
        Must not contain zeros on the diagonal.
        The entries in the strict upper triangular part of :code:`L` can contain
        arbitrary values, since the algorithm neither reads from nor writes to this part
        of the matrix
        Will be overridden with the Cholesky factor of the matrix to be updated.
    v : (N,) numpy.ndarray, dtype=numpy.double
        The vector :math:`v` with shape :code:`(N, N)` and dtype :class:`numpy.double`
        defining the symmetric rank-1 update :math:`v v^T`.
        Will be reused as an internal memory buffer to store intermediate results, and
        thus modified.

    References
    ----------
    .. [1] M. Seeger, "Low Rank Updates for the Cholesky Decomposition", 2008.
    """

    N = L.shape[0]

    blas_rotg, blas_rot = scipy.linalg.get_blas_funcs(("rotg", "rot"), (L, v))

    # Generate a contiguous view of the underling memory buffer of L, emulating raw
    # pointer access
    L_buf = L.ravel(order="K")

    assert np.may_share_memory(L, L_buf)

    if L.flags.f_contiguous:
        # In column-major memory layout, moving to the next row means moving the pointer
        # by 1 entry, while moving to the next column means moving the pointer by N
        # entries, i.e. the number of entries per column
        row_inc = 1
        column_inc = N
    else:
        assert L.flags.c_contiguous

        # In row-major memory layout, moving to the next column means moving the pointer
        # by 1 entry, while moving to the next row means moving the pointer by N
        # entries, i.e. the number of entries per row
        row_inc = N
        column_inc = 1

    # Create a "pointer" into the contiguous view of L's memory buffer
    # Points to the k-th diagonal entry of L at the beginning of the loop body
    L_buf_off = 0

    for k in range(N):
        # At this point the first k entries of v are zeros

        # Generate Givens rotation which eliminates the k-th entry of v by rotating onto
        # the k-th diagonal entry of L and apply it only to these entries of (L|v)
        # Note: The following two operations will be performed by a single call to
        # `rotg` in C/Fortran. However, Python can not modify `Float` arguments.
        c, s = blas_rotg(L_buf[L_buf_off], v[k])
        L_buf[L_buf_off], v[k] = blas_rot(L_buf[L_buf_off], v[k], c, s)

        # Givens rotations generated by BLAS' `rotg` might rotate the diagonal entry to
        # a negative value. However, by convention, the diagonal entries of a Cholesky
        # factor are positive. As a remedy, we add another 180 degree rotation to the
        # Givens rotation matrix. This flips the sign of the diagonal entry while
        # ensuring that the resulting transformation is still a Givens rotation.
        if L_buf[L_buf_off] < 0.0:
            L_buf[L_buf_off] = -L_buf[L_buf_off]
            c = -c
            s = -s

        # Apply (modified) Givens rotation to the remaining entries in the k-th column
        # of L and the remaining entries in v

        # We only operate on the lower triangular part of L, and we pretend that the
        # strict upper triangular part contains zeros.
        # Moreover, the first k - 1 entries of v are zeros.
        # Since we already applied the Givens rotation to the k-th diagonal element of L
        # and the k-th element of v, it suffices to apply it to the slices
        # L[(k + 1):, k] and v[(k + 1):] here
        i = k + 1

        if i < N:
            # Move the pointer to the entry of L at index (i, k)
            L_buf_off += row_inc

            blas_rot(
                # We only need to rotate the last N - i entries
                n=N - i,
                # This constructs the memory adresses of the last N - i entries of the
                # k-th column in L
                x=L_buf,
                offx=L_buf_off,
                incx=row_inc,
                # This constructs the memory adresses of the last N - i entries of v
                y=v,
                offy=i,
                incy=1,
                c=c,
                s=s,
                overwrite_x=True,
                overwrite_y=True,
            )

            # In the beginning of the next iteration, the buffer offset must point to
            # the (k + 1)-th diagonal entry of L
            L_buf_off += column_inc


blas_rotg, blas_rot = scipy.linalg.get_blas_funcs(("rotg", "rot"))


def update(L: np.ndarray, v: np.ndarray) -> None:
    N = L.shape[0]
   # blas_rotg, blas_rot = scipy.linalg.get_blas_funcs(("rotg", "rot"), (L, v))
    L_buf = L.ravel(order="K")
    #assert np.may_share_memory(L, L_buf)
    if L.flags.f_contiguous:
        row_inc = 1
        column_inc = N
    else:
        assert L.flags.c_contiguous
        row_inc = N
        column_inc = 1

    L_buf_off = 0
    for k in range(N):
        c, s = blas_rotg(L_buf[L_buf_off], v[k])
        L_buf[L_buf_off], v[k] = blas_rot(L_buf[L_buf_off], v[k], c, s)

        if L_buf[L_buf_off] < 0.0:
            L_buf[L_buf_off] = -L_buf[L_buf_off]
            c = -c
            s = -s

        i = k + 1

        if i < N:
            # Move the pointer to the entry of L at index (i, k)
            L_buf_off += row_inc

            blas_rot(
                # We only need to rotate the last N - i entries
                n=N - i,
                # This constructs the memory adresses of the last N - i entries of the
                # k-th column in L
                x=L_buf,
                offx=L_buf_off,
                incx=row_inc,
                # This constructs the memory adresses of the last N - i entries of v
                y=v,
                offy=i,
                incy=1,
                c=c,
                s=s,
                overwrite_x=True,
                overwrite_y=True,
            )

            L_buf_off += column_inc




if __name__ == '__main__':
    import timeit

    for i in 1, 2, 5, 20, 50, 100, 200:
        print(i)
        A = RobustAdaptiveMetropolis(i)
        t = timeit.timeit('A.draw(); A.adapt(0.5, 10000)', globals={'A': A}, number=100000//i)
        print(t)
        #print(t/i)
        #print(t/i**2)
        A = RobustAdaptiveMetropolis_upd(i)
        t = timeit.timeit('A.draw(); A.adapt(0.5, 10000)', globals={'A': A}, number=100000//i)
        print(t)
        #print(t/i)
        print()

    #for i in 2, 5, 20, 50, 100, 200, 500, 1000:
        #print(i)
        #A = RobustAdaptiveMetropolis(i)
        #t = timeit.timeit('A.draw()', globals={'A': A}, number=10000)
        #print(t, t/i)
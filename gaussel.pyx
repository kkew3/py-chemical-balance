import numpy as np
cimport numpy as np
cimport cython

np.import_array()


cdef void swap(np.ndarray[np.int_t, ndim=1] p, int i, int j):
    cdef np.int_t tmp
    if i != j:
        tmp = p[i]
        p[i] = p[j]
        p[j] = tmp


cdef np.double_t select_pivot(np.ndarray[np.double_t, ndim=2] A, int i,
                              np.ndarray[np.int_t, ndim=1] p,
                              np.ndarray[np.int_t, ndim=1] q):
    cdef:
        int ii, jj
        m = A.shape[0]
        n = A.shape[1]
        np.double_t maxvalue = np.abs(A[p[i], q[i]])
        int s = i, t = i
    for ii in range(i, m):
        for jj in range(i, n):
            if np.abs(A[p[ii], q[jj]]) > maxvalue:
                s = ii
                t = jj
                maxvalue = np.abs(A[p[ii], q[jj]])
    swap(p, i, s)
    swap(q, i, t)
    return maxvalue


@cython.boundscheck(False)
@cython.wraparound(False)
def gaussian_elimination(np.ndarray[np.double_t, ndim=2] A,
                         np.ndarray[np.int_t, ndim=1] p,
                         np.ndarray[np.int_t, ndim=1] q):
    """
    Perform complete pivoting Gaussian elimination on matrix ``A``.

    :param A: the matrix to solve
    :param p: row permutation vector, of shape (A.shape[0],)
    :param q: column permutation vector, of shape (A.shape[1],)

    ``A``, ``p``, ``q`` are modified in-place.
    """
    cdef:
        int m = A.shape[0]
        int n = A.shape[1]
        int h, i, j, k, rank
        np.double_t v, l
    assert p.shape[0] == m and q.shape[0] == n
    for i in range(m):
        p[i] = i
    for i in range(n):
        q[i] = i

    for i in range(m):
        v = select_pivot(A, i, p, q)
        if np.isclose(v, 0.0):
            i -= 1
            break
        for k in range(i + 1, m):
            l = A[p[k], q[i]] / A[p[i], q[i]]
            for j in range(i, n):
                A[p[k], q[j]] -= l * A[p[i], q[j]]
    rank = i + 1
    for j in range(rank - 1, -1, -1):
        for k in range(j):
            l = A[p[k], q[j]] / A[p[j], q[j]]
            for h in range(j, n):
                A[p[k], q[h]] -= l * A[p[j], q[h]]
    return rank

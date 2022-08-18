from fractions import Fraction
import math
import argparse

import numpy as np

import ext
import parseeq


def nullspace_basis(A: np.ndarray, p: np.ndarray, q: np.ndarray, rank: int):
    pp = p[:rank]
    qp = q[:rank]

    j = np.argsort(pp)
    pp = pp[j]
    qp = qp[j]
    A[pp] /= A[pp, qp][:, np.newaxis]
    AL = -A[:, np.sort(q[rank:])]

    j = np.argsort(qp)
    pp = pp[j]
    qp = qp[j]

    nullity = A.shape[1] - rank
    B = np.eye(nullity)
    for j in range(rank):
        B = np.insert(B, qp[j], AL[pp[j]], axis=0)
    return B


def proc_basis(b: list[float]) -> list[int]:
    b = [Fraction(x).limit_denominator(10000) for x in b]
    m = math.lcm(*[x.denominator for x in b])
    b = [x * m for x in b]
    d = math.gcd(*[x.numerator for x in b])
    b = [x / d for x in b]
    return [x.numerator for x in b]


def solveeq(string: str, N: int, allow_decimal: bool):
    A = parseeq.form_coef_mat(parseeq.parseeq(parseeq.preprocesseq(string)))
    p = np.arange(A.shape[0])
    q = np.arange(A.shape[1])
    rank = ext.gaussian_elimination(A, p, q)
    B = nullspace_basis(A, p, q, rank)
    Q = ext.find_opt_basis_transform(B, N)
    B = np.matmul(Q, B.T).T
    B = [B[:, j].tolist() for j in range(B.shape[1])]
    if not allow_decimal:
        B = [proc_basis(b) for b in B]
    return B


def make_parser():
    parser = argparse.ArgumentParser()
    parser.add_argument(
        '--decimal', action='store_true', help='allow decimal coefficient')
    parser.add_argument(
        '-N',
        type=int,
        default=10000,
        help=('try N times before stopping finding legal basis; default '
              '%(default)s'))
    parser.add_argument('eq', nargs='+', help='the equation')
    return parser


def main():
    args = make_parser().parse_args()
    line = ' '.join(args.eq)
    sols = solveeq(line, args.N, args.decimal)
    for row in sols:
        print(*row)


if __name__ == '__main__':
    main()

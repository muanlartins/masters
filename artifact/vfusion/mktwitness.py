"""Exact integer witness for the MKT circuit.

Every auxiliary signal the circuit checks is produced here with integer
arithmetic at scale SC=2^16, so the Python reference and circuit agree bit for
bit. Reciprocal divisions round down and carry a constrained nonnegative
remainder; the logarithm witness is the greatest fixed-point integer whose
degree-12 polynomial does not exceed the accumulated value.
"""
from fractions import Fraction

SC = 1 << 16
D = 12
VOFF = 32768
TCOFF = VOFF - 27315
SC1E6 = SC * 1_000_000
T_LO_C, T_HI_C = 0, 3500          # policy temperature band, centi-Celsius
T_LO_POS, T_HI_POS = T_LO_C + VOFF, T_HI_C + VOFF


def xref():
    lo = Fraction(SC1E6, T_HI_C + 27315)
    hi = Fraction(SC1E6, T_LO_C + 27315)
    return int((lo + hi) / 2)


XREF = xref()
UMIN = XREF - (SC1E6 // (T_LO_C + 27315))
UMAX = XREF - (SC1E6 // (T_HI_C + 27315))


def _cf():
    cf = [0] * (D + 1)
    cf[D] = 1
    for j in range(D - 1, -1, -1):
        cf[j] = cf[j + 1] * (j + 1)
    return cf


def _scp():
    scp = [0] * (D + 1)
    scp[D] = 1
    for j in range(D - 1, -1, -1):
        scp[j] = scp[j + 1] * SC
    return scp


CF, SCP = _cf(), _scp()


def poly_num(u):
    """N(u) = sum_j (D!/j!) * u^j * SC^(D-j), the series times its denominator."""
    return sum(CF[j] * SCP[j] * (u ** j) for j in range(D + 1))


def rbits(n):
    delta = CF[0] * SCP[1] * 9      # D! * SC^(D-1) * max exp(u)
    return (n * delta).bit_length()


def witness(vpos_list):
    n = len(vpos_list)
    X, Xrem, snum = [], [], 0
    for vp in vpos_list:
        tc = vp - TCOFF
        x = SC1E6 // tc
        X.append(x)
        Xrem.append(SC1E6 - x * tc)
        snum += poly_num(XREF - x)
    # Largest L with n*N(L) <= snum, found by bisection on a monotone function.
    lo, hi = UMIN, UMAX
    while lo < hi:
        mid = (lo + hi + 1) // 2
        if n * poly_num(mid) <= snum:
            lo = mid
        else:
            hi = mid - 1
    L = lo
    Lrem = snum - n * poly_num(L)
    W = XREF - L
    TcMkt = SC1E6 // W
    Trem = SC1E6 - TcMkt * W
    return {"v": vpos_list, "X": X, "Xrem": Xrem, "L": L, "Lrem": Lrem,
            "TcMkt": TcMkt, "Trem": Trem}, TcMkt

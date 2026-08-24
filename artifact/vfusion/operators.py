"""Fusion operators F, in the float reference and the fixed-point form the
circuits implement.

Mean kinetic temperature follows USP <1079.2>: with dH the activation energy and
R the gas constant,
    T_MKT = (dH/R) / ( -ln( (1/n) * sum_i exp(-(dH/R)/T_i) ) ).
The circuits use the shifted form in circuits/fusion.circom to keep every
intermediate inside a fixed-point range.
"""
import math

DH_OVER_R = 10000.0        # dH = 83.144 kJ/mol, R = 8.3144 J/(mol K)
T_REF_K = 298.15           # 25 C, the shift point
KELVIN0 = 273.15
def to_kelvin(centi_c):
    return centi_c / 100.0 + KELVIN0


def mean(values, params=None):
    return sum(to_kelvin(v) for v in values) / len(values)


def wmean(values, params):
    w = params["weights"]
    tot = sum(w[i % len(w)] for i in range(len(values)))
    return sum(to_kelvin(v) * w[i % len(w)] for i, v in enumerate(values)) / tot


def excursion(values, params):
    """Number of readings strictly above the policy threshold."""
    thr = params["threshold"]
    return float(sum(1 for v in values if v > thr))


def mkt(values, params=None):
    s = sum(math.exp(-DH_OVER_R / to_kelvin(v)) for v in values) / len(values)
    return DH_OVER_R / (-math.log(s))


def mkt_shifted(values, params=None):
    """Numerically identical to `mkt`, in the form the circuit evaluates."""
    x_ref = DH_OVER_R / T_REF_K
    s = sum(math.exp(x_ref - DH_OVER_R / to_kelvin(v)) for v in values) / len(values)
    return DH_OVER_R / (x_ref - math.log(s))


OPERATORS = {"mean": mean, "wmean": wmean, "excursion": excursion, "mkt": mkt}

# Degree of the polynomial the circuits use for exp on the shifted range.
EXP_DEGREE = 12


def exp_poly(u, degree=EXP_DEGREE):
    """Truncated series for exp(u) on u in [-3, 1]; what the circuit computes."""
    term, acc = 1.0, 1.0
    for i in range(1, degree + 1):
        term *= u / i
        acc += term
    return acc


def apply(policy, values):
    return OPERATORS[policy.operator](values, policy.params)

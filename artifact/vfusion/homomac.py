"""Linearly homomorphic MAC (Agrawal-Boneh style) over a 127-bit prime field.

For labels tau_i and values v_i, a device holding (K_d, alpha) emits
    t_i = (v_i - PRF_{K_d}(tau_i)) * alpha^{-1}  mod p.
The aggregator combines t = sum_i c_i t_i.  The designated auditor, who can
derive every K_d and alpha, accepts y = sum_i c_i v_i iff
    alpha * t + sum_i c_i PRF_{K_d(i)}(tau_i) == y   (mod p).

The label set the auditor sums over comes from the policy, so a missing term
makes the aggregate equation fail for linear F. A combined tag does not retain
an auditable per-record manifest, however, and therefore does not discharge the
paper's cumulative recording and attribution goals.
"""
import hmac
import hashlib

P = (1 << 127) - 1          # Mersenne prime
TAG_BYTES = 16


def _prf(key, msg):
    return int.from_bytes(hmac.new(key, msg, hashlib.sha256).digest(), "big") % P


def device_key(master, device):
    return hmac.new(master, b"dev%d" % device, hashlib.sha256).digest()


def alpha_for(master, epoch):
    a = _prf(master, b"alpha%d" % epoch)
    return a if a else 1


def tag(master, device, label, value, meter=None):
    if meter:
        meter.mul(1)
    k = device_key(master, device)
    alpha = alpha_for(master, _EPOCH[0])
    return ((value - _prf(k, label)) * pow(alpha, P - 2, P)) % P


_EPOCH = [0]


def set_epoch(e):
    _EPOCH[0] = e


def combine(tags, coeffs, meter=None):
    acc = 0
    for t, c in zip(tags, coeffs):
        if meter:
            meter.mul(1)
        acc = (acc + c * t) % P
    return acc


def verify(master, epoch, labels_devices, coeffs, combined_tag, y, meter=None):
    alpha = alpha_for(master, epoch)
    acc = 0
    for (label, dev), c in zip(labels_devices, coeffs):
        if meter:
            meter.hash()
            meter.mul(1)
        acc = (acc + c * _prf(device_key(master, dev), label)) % P
    if meter:
        meter.mul(1)
    return (alpha * combined_tag + acc) % P == y % P

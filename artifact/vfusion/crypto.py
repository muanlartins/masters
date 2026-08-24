"""Primitives, each wired to a Meter so that every call is counted.

SHA-256 and Ed25519 come from `cryptography` (OpenSSL).  BLS12-381 aggregate
signatures come from `py_ecc`.  Poseidon is evaluated by circomlibjs through
node so that the Python manifest commitment is bit-identical to the one the
circuit recomputes.
"""
import hashlib
import json
import struct
import subprocess
from pathlib import Path

from cryptography.hazmat.primitives.asymmetric.ed25519 import (
    Ed25519PrivateKey, Ed25519PublicKey)
from cryptography.hazmat.primitives import serialization

ROOT = Path(__file__).resolve().parent.parent

HASH_OUT = 32
ED25519_SIG = 64
ED25519_PK = 32
BLS_SIG = 96          # G2 point, compressed
BLS_PK = 48           # G1 point, compressed


# --------------------------------------------------------------- hashing ----
def H(*parts, meter=None):
    if meter:
        meter.hash()
    h = hashlib.sha256()
    for p in parts:
        h.update(p)
    return h.digest()


def commit(value, salt, meter=None):
    """Binding (and hiding) commitment to one observation value."""
    return H(salt, struct.pack(">h", value), meter=meter)


def rid_bytes(rid):
    return struct.pack(">HH", rid[0], rid[1])


# --------------------------------------------------------------- ed25519 ----
def ed_keygen(seed_int):
    return Ed25519PrivateKey.from_private_bytes(
        hashlib.sha256(b"vfusion-device-%d" % seed_int).digest())


def ed_public_bytes(pk):
    return pk.public_bytes(serialization.Encoding.Raw,
                           serialization.PublicFormat.Raw)


def ed_public_from_bytes(data):
    return Ed25519PublicKey.from_public_bytes(data)


def ed_sign(sk, msg, meter=None):
    if meter:
        meter.sign()
    return sk.sign(msg)


def ed_verify(pk, sig, msg, meter=None):
    if meter:
        meter.verify()
    try:
        pk.verify(sig, msg)
        return True
    except Exception:
        return False


# ------------------------------------------------------------------- BLS ----
_BLS = None


def _bls():
    global _BLS
    if _BLS is None:
        from py_ecc.bls import G2ProofOfPossession as B
        _BLS = B
    return _BLS


def bls_keygen(seed_int):
    return int.from_bytes(hashlib.sha256(b"vfusion-bls-%d" % seed_int).digest(), "big") % (
        0x73EDA753299D7D483339D80809A1D80553BDA402FFFE5BFEFFFFFFFF00000001)


def bls_public(sk):
    return _bls().SkToPk(sk)


def bls_sign(sk, msg, meter=None):
    if meter:
        meter.sign()
    return _bls().Sign(sk, msg)


def bls_aggregate(sigs, meter=None):
    if meter:
        meter.agg(len(sigs) - 1)
    return _bls().Aggregate(sigs)


def bls_aggregate_verify(pks, msgs, sig, meter=None):
    """One pairing per distinct message, plus one for the aggregate."""
    if meter:
        meter.pairing(len(msgs) + 1)
    return _bls().AggregateVerify(pks, msgs, sig)


# -------------------------------------------------------------- poseidon ----
_POSEIDON_JS = ROOT / "scripts" / "poseidon.js"


def poseidon_many(batches):
    """Evaluate Poseidon on a list of input lists; returns decimal strings."""
    proc = subprocess.run(
        ["node", str(_POSEIDON_JS)],
        input=json.dumps([[str(x) for x in b] for b in batches]),
        capture_output=True, text=True, check=True)
    return json.loads(proc.stdout)

"""Seeded synthetic cold-chain traces.

A transport window at 2-8 C with a warm-up excursion in the second half, which
is the event an aggregator has a motive to suppress.  Seeded so that every
number in the paper is reproducible from the seed alone.
"""
import hashlib
import random
import struct
from . import crypto as C
from .policy import Observation, Policy, Run

DEFAULT_SEED = 20260904


def make_policy(m=4, k=15, operator="mkt", params=None, epoch=1762300800):
    pubkeys = {
        d: {
            "bls12-381": C.bls_public(C.bls_keygen(d)),
            "ed25519": C.ed_public_bytes(C.ed_keygen(d).public_key()),
        }
        for d in range(1, m + 1)
    }
    service_keys = {
        "anchor-ed25519": C.ed_public_bytes(C.ed_keygen(0).public_key()),
        "attestation-ed25519": C.ed_public_bytes(C.ed_keygen(4242).public_key()),
    }
    return Policy(epoch=epoch, m=m, k=k, operator=operator, params=params or {},
                  pubkeys=pubkeys, service_keys=service_keys)


def make_run(policy, seed=DEFAULT_SEED, excursion_frac=0.25, excursion_peak=1850,
             run_id=None, auditor_state=None):
    """Build a full, honest run: every required identifier is present exactly once."""
    rng = random.Random(seed)
    obs, salts = [], {}
    ids = policy.required_ids()
    n_exc = int(len(ids) * excursion_frac)
    start_exc = len(ids) - n_exc
    for idx, (d, q) in enumerate(ids):
        base = 500 + rng.randint(-120, 120)          # 5.00 C nominal, +/- 1.2 C
        if idx >= start_exc:                          # ramped excursion at the tail
            ramp = (idx - start_exc + 1) / max(n_exc, 1)
            base += int(ramp * (excursion_peak - 500))
        obs.append(Observation(device=d, seq=q, value=base))
        salts[(d, q)] = rng.randbytes(16)
    # Real deployments obtain both values from fresh external state. These
    # deterministic fixtures preserve reproducibility while exercising the
    # same signed fields and judge-state boundary.
    context = policy.digest() + struct.pack(">Q", seed)
    run_id = run_id or hashlib.sha256(b"vfusion-run-id\x00" + context).digest()[:16]
    auditor_state = auditor_state or hashlib.sha256(
        b"vfusion-auditor-state\x00" + context).digest()
    if len(run_id) != 16 or len(auditor_state) != C.HASH_OUT:
        raise ValueError("run_id must be 16 bytes and auditor_state must be 32 bytes")
    return Run(policy=policy, obs=obs, salts=salts, run_id=run_id,
               auditor_state=auditor_state)

"""Protocol-level cost accounting.

The paper reports cost(S, n, m, F) = <N_P, N_J, B_ev, M_P, M_J>. Primitive
counts and serialized byte counts are exact for the serialization declared by
each stack. M_P and M_J are *streaming-state models*: protocol bytes retained
between records under the stated online schedule. They are not process-RSS or
cryptographic-library working-memory measurements.
"""
from contextlib import contextmanager
from dataclasses import dataclass, field

PRIMITIVES = ("hash", "sign", "verify", "agg", "pairing", "mul", "cmp", "fuse")


@dataclass
class Meter:
    """Counts primitives and tracks peak declared working state, in bytes."""
    counts: dict = field(default_factory=lambda: {p: 0 for p in PRIMITIVES})
    live: int = 0
    peak: int = 0

    def bump(self, prim, k=1):
        self.counts[prim] += k

    hash = lambda self, k=1: self.bump("hash", k)
    sign = lambda self, k=1: self.bump("sign", k)
    verify = lambda self, k=1: self.bump("verify", k)
    agg = lambda self, k=1: self.bump("agg", k)
    pairing = lambda self, k=1: self.bump("pairing", k)
    mul = lambda self, k=1: self.bump("mul", k)
    cmp = lambda self, k=1: self.bump("cmp", k)
    fuse = lambda self, k=1: self.bump("fuse", k)

    @contextmanager
    def hold(self, nbytes):
        """Declare protocol state retained for the duration of a streaming phase."""
        self.live += nbytes
        self.peak = max(self.peak, self.live)
        try:
            yield
        finally:
            self.live -= nbytes

    def touch(self, nbytes):
        """Declare retained state reached by an online algorithm."""
        self.peak = max(self.peak, self.live + nbytes)

    def nonzero(self):
        return {k: v for k, v in self.counts.items() if v}

    def as_dict(self):
        return {"counts": self.nonzero(), "peak_state_bytes": self.peak}


class Evidence:
    """A serialized judge-view object, tracked field by field.

    B_ev is the complete online verification transcript beyond pre-provisioned
    policy P and claimed output y. Device public keys live in P's roster and
    are therefore not counted. Challenges, observations, commitments,
    signatures, proofs, and openings are counted.
    """

    def __init__(self):
        self.parts = []

    def add(self, name, blob, count=1):
        n = len(blob) if isinstance(blob, (bytes, bytearray)) else int(blob)
        self.parts.append((name, n, count))
        return self

    def total(self):
        return sum(n * c for _, n, c in self.parts)

    def breakdown(self):
        out = {}
        for name, n, c in self.parts:
            out[name] = out.get(name, 0) + n * c
        return out

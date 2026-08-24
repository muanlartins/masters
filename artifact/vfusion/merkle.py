"""Merkle tree (RFC 6962) and hash chain, both in streaming form.

RFC 6962 is used rather than a padded binary tree because it is defined for
every n, not only powers of two, and because its leaf/node domain separation
blocks the second-preimage confusion between a leaf and an internal node.

Both structures are written so that M_P -- peak state the producer cannot
stream out -- is honest: the hash chain holds one digest, the Merkle frontier
holds at most ceil(log2 n) + 1 digests.
"""
from .crypto import H, HASH_OUT

LEAF = b"\x00"
NODE = b"\x01"


def leaf_hash(payload, meter=None):
    return H(LEAF, payload, meter=meter)


def _node(left, right, meter=None):
    return H(NODE, left, right, meter=meter)


def _split(n):
    """Largest power of two strictly less than n (RFC 6962 k)."""
    k = 1
    while k * 2 < n:
        k *= 2
    return k


def mth(leaves, meter=None):
    if not leaves:
        return bytes(HASH_OUT)
    if len(leaves) == 1:
        return leaves[0]
    k = _split(len(leaves))
    return _node(mth(leaves[:k], meter=meter), mth(leaves[k:], meter=meter), meter=meter)


class StreamingMerkle:
    """Frontier of complete subtrees; identical root to `mth`."""

    def __init__(self, meter=None):
        self.stack = []             # (size, digest), sizes strictly decreasing
        self.n = 0
        self.meter = meter

    def add(self, leaf):
        self.n += 1
        size, dig = 1, leaf
        while self.stack and self.stack[-1][0] == size:
            psize, pdig = self.stack.pop()
            dig = _node(pdig, dig, meter=self.meter)
            size *= 2
        self.stack.append((size, dig))
        if self.meter:
            self.meter.touch(self.peak_state())
        return self

    def peak_state(self):
        return HASH_OUT * max(len(self.stack), 1)

    def root(self):
        if not self.stack:
            return bytes(HASH_OUT)
        _, acc = self.stack[-1]
        for _, dig in reversed(self.stack[:-1]):
            acc = _node(dig, acc, meter=self.meter)
        return acc


def merkle_root(leaves, meter=None):
    t = StreamingMerkle(meter=meter)
    for lf in leaves:
        t.add(lf)
    return t.root(), t.peak_state()


def merkle_path(leaves, index, meter=None):
    """RFC 6962 audit path for `index`."""
    n = len(leaves)
    if n == 1:
        return []
    k = _split(n)
    if index < k:
        return merkle_path(leaves[:k], index, meter=meter) + [mth(leaves[k:], meter=meter)]
    return merkle_path(leaves[k:], index - k, meter=meter) + [mth(leaves[:k], meter=meter)]


def merkle_verify(leaf, index, path, n, root, meter=None):
    """Recompute the root from an audit path; `n` fixes the tree shape."""
    def rec(idx, size, p):
        if size == 1:
            return leaf, p
        k = _split(size)
        sib, rest = p[-1], p[:-1]
        if idx < k:
            acc, rest = rec(idx, k, rest)
            return _node(acc, sib, meter=meter), rest
        acc, rest = rec(idx - k, size - k, rest)
        return _node(sib, acc, meter=meter), rest

    got, rest = rec(index, n, list(path))
    return got == root and not rest


def chain_head(leaves, meter=None):
    acc = bytes(HASH_OUT)
    for lf in leaves:
        acc = _node(acc, lf, meter=meter)
    return acc, HASH_OUT

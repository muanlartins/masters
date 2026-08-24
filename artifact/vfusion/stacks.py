"""Mechanism stacks and one intentionally incomplete baseline.

Every V-labeled stack carries evidence for all conjuncts up to its level, and
its judge checks all of them. The partial homomorphic-MAC row demonstrates why
an aggregate authenticator must not be priced as a cumulative V4 stack.

B_ev counts what the aggregator must transmit beyond the public policy P and
the claimed output y.  Device verification keys live in P's roster and are
therefore not charged.

M_P is protocol state retained between record arrivals under an online
schedule. A per-record signature can be emitted as it is made, so it costs no
retained state; a Merkle frontier cannot.
"""
import struct
from dataclasses import dataclass, field

from . import crypto as C
from . import homomac as HM
from . import operators as OPS
from .merkle import (StreamingMerkle, chain_head, leaf_hash, merkle_path,
                     merkle_verify, mth)
from .meter import Evidence, Meter
from .policy import B_OBS, Entry, EPOCH_FMT

B_ENTRY = 2 + 2 + C.HASH_OUT          # device, seq, commitment = 36 bytes
ANCHOR_DEV = 0                        # external anchoring authority
B_RUN_ID = 16
B_AUDITOR_STATE = C.HASH_OUT
ANCHOR_DOMAIN = b"vfusion-anchor-v1\x00"


# ------------------------------------------------------------------ proof ----
@dataclass
class Proof:
    y: float
    n: int
    root: bytes = b""
    anchor: bytes = b""
    run_id: bytes = b""
    entries: list = field(default_factory=list)
    raw: list = field(default_factory=list)
    extra: dict = field(default_factory=dict)


def anchor_message(policy, root, run_id, auditor_state):
    if len(run_id) != B_RUN_ID or len(auditor_state) != B_AUDITOR_STATE:
        raise ValueError("invalid run identifier or auditor state")
    return ANCHOR_DOMAIN + policy.digest() + run_id + auditor_state + root


def anchor_sign(run, root, meter=None):
    sk = C.ed_keygen(ANCHOR_DEV)
    return C.ed_sign(sk, anchor_message(run.policy, root, run.run_id,
                                       run.auditor_state), meter=meter)


def anchor_verify(policy, root, sig, run_id, auditor_state, meter=None):
    try:
        pk = C.ed_public_from_bytes(policy.service_key("anchor-ed25519"))
        msg = anchor_message(policy, root, run_id, auditor_state)
    except (TypeError, ValueError):
        return False
    return C.ed_verify(pk, sig, msg, meter=meter)


def add_anchor_context(ev, run):
    """Charge freshness/order fields in the full online transcript."""
    return (ev.add("run id", run.run_id)
              .add("auditor anchor state", run.auditor_state))


def build_entries(run, meter=None):
    """Devices commit to their values and sign the commitments."""
    out = []
    for o in run.obs:
        c = C.commit(o.value, run.salts[o.rid], meter=meter)
        out.append(Entry(o.device, o.seq, c))
    return out


def sign_entries(run, entries, meter=None, forged=()):
    for e in entries:
        signer = 9999 if e.rid in forged else e.device
        sk = C.ed_keygen(signer)
        e.sig = C.ed_sign(sk, e.preimage(run.policy.epoch), meter=meter)
    return entries


# ------------------------------------------------------------------ base ----
class Stack:
    name = "?"
    level = 0
    profile = "rho_soft"
    mechanism = "?"
    public = True
    delta = 0.0
    operators = ("mean", "wmean", "excursion", "mkt")
    complete = True
    modeled = False

    def supports(self, policy):
        return policy.operator in self.operators

    def prove(self, run, tamper=None):
        raise NotImplementedError

    def judge(self, policy, proof, auditor_state=None):
        raise NotImplementedError


# -------------------------------------------------------------------- V0 ----
class V0None(Stack):
    name, level, mechanism = "v0-none", 0, "no evidence"

    def prove(self, run, tamper=None):
        m = Meter()
        vals = [o.value for o in run.obs]
        y = tamper.output(OPS.apply(run.policy, vals)) if tamper else OPS.apply(run.policy, vals)
        return Proof(y=y, n=len(run.obs)), Evidence(), m

    def judge(self, policy, proof, auditor_state=None):
        return True, Meter()


# ---------------------------------------------------------- V1 mechanisms ----
class _V1(Stack):
    level, profile = 1, "rho_soft"
    streaming = True

    def _commit(self, leaves, meter):
        raise NotImplementedError

    def prove(self, run, tamper=None):
        m = Meter()
        obs = [o for o in run.obs if not tamper or tamper.keeps(o.rid)]
        vals = {o.rid: o.value for o in obs}
        if tamper:
            vals.update(tamper.fabricate)
        entries = []
        for o in obs:
            entries.append(Entry(o.device, o.seq,
                                 C.commit(vals[o.rid], run.salts[o.rid], meter=m)))
        leaves = [leaf_hash(struct.pack(">HH", e.device, e.seq) + e.commit, meter=m)
                  for e in entries]
        root, state = self._commit(leaves, m)
        with m.hold(state):
            anchor = anchor_sign(run, root, meter=m)
        # Values changed after binding: the transmitted manifest carries the new
        # commitment while the anchored root still covers the old one.
        if tamper and tamper.post_alter:
            for e in entries:
                if e.rid in tamper.post_alter:
                    vals[e.rid] = tamper.post_alter[e.rid]
                    e.commit = C.commit(vals[e.rid], run.salts[e.rid], meter=m)
        y = OPS.apply(run.policy, [vals[o.rid] for o in obs])
        if tamper:
            y = tamper.output(y)
        ev = add_anchor_context(
            Evidence().add("manifest", B_ENTRY, len(entries)).add("root", root), run
        ).add("anchor", anchor)
        p = Proof(y=y, n=len(entries), root=root, anchor=anchor,
                  run_id=run.run_id, entries=entries)
        p.extra["values"] = vals
        p.extra["leaves"] = leaves          # the leaf set the anchored root covers
        return p, ev, m

    def judge(self, policy, proof, auditor_state=None):
        m = Meter()
        if not anchor_verify(policy, proof.root, proof.anchor, proof.run_id,
                             auditor_state, meter=m):
            return False, m
        leaves = [leaf_hash(struct.pack(">HH", e.device, e.seq) + e.commit, meter=m)
                  for e in proof.entries]
        root, state = self._commit(leaves, m)
        m.touch(state)
        return root == proof.root, m

class V1Merkle(_V1):
    name, mechanism = "v1-merkle", "anchored RFC 6962 Merkle root"

    def _commit(self, leaves, meter):
        t = StreamingMerkle(meter=meter)
        for lf in leaves:
            t.add(lf)
        return t.root(), t.peak_state()


class V1Chain(_V1):
    name, mechanism = "v1-chain", "anchored hash chain"

    def _commit(self, leaves, meter):
        return chain_head(leaves, meter=meter)


# ---------------------------------------------------------- V2 mechanisms ----
class V2Ed25519(V1Merkle):
    name, level = "v2-ed25519", 2
    mechanism = "per-record Ed25519 signature"

    def prove(self, run, tamper=None):
        proof, ev, m = V1Merkle.prove(self, run, tamper)
        forged = tamper.forged if tamper else frozenset()
        sign_entries(run, proof.entries, meter=m, forged=forged)
        ev.add("record sigs", C.ED25519_SIG, len(proof.entries))
        return proof, ev, m

    def judge(self, policy, proof, auditor_state=None):
        ok, m = V1Merkle.judge(self, policy, proof, auditor_state)
        if not ok:
            return False, m
        for e in proof.entries:
            try:
                pk = C.ed_public_from_bytes(policy.credential(e.device, "ed25519"))
            except (TypeError, ValueError):
                return False, m
            if not C.ed_verify(pk, e.sig, e.preimage(policy.epoch), meter=m):
                return False, m
        return True, m


class V2BLS(V1Merkle):
    name, level = "v2-bls", 2
    mechanism = "BLS12-381 aggregate signature"

    def prove(self, run, tamper=None):
        proof, ev, m = V1Merkle.prove(self, run, tamper)
        forged = tamper.forged if tamper else frozenset()
        sigs = []
        with m.hold(C.BLS_SIG):
            for e in proof.entries:
                signer = 9999 if e.rid in forged else e.device
                sigs.append(C.bls_sign(C.bls_keygen(signer),
                                       e.preimage(run.policy.epoch), meter=m))
            agg = C.bls_aggregate(sigs, meter=m)
        proof.extra["bls"] = agg
        ev.add("aggregate sig", C.BLS_SIG)
        return proof, ev, m

    def judge(self, policy, proof, auditor_state=None):
        ok, m = V1Merkle.judge(self, policy, proof, auditor_state)
        if not ok:
            return False, m
        try:
            pubs = [policy.credential(e.device, "bls12-381")
                    for e in proof.entries]
        except ValueError:
            return False, m
        msgs = [e.preimage(policy.epoch) for e in proof.entries]
        return C.bls_aggregate_verify(pubs, msgs, proof.extra["bls"], meter=m), m


# ---------------------------------------------------------- V3 mechanisms ----
class V3Manifest(V2Ed25519):
    name, level = "v3-manifest", 3
    mechanism = "policy-order check on the transmitted manifest"

    def judge(self, policy, proof, auditor_state=None):
        ok, m = V2Ed25519.judge(self, policy, proof, auditor_state)
        if not ok:
            return False, m
        got = [e.rid for e in proof.entries]
        want = policy.required_ids()
        m.hash(len(want))
        return got == want, m


class V3PolicySample(V2Ed25519):
    """Sample policy positions after an externally anchored root.

    The verifier challenge is supplied as judge state, not copied from the
    producer's proof object. It must be issued after the root is anchored;
    otherwise a producer that controls commitment salts can grind roots until
    the defective position is not sampled.
    """
    name, level = "v3-policy-sample", 3
    mechanism = "policy-position sampling with k openings"
    k = 20

    def commit(self, run, tamper=None):
        """Phase 1: bind and externally anchor the manifest root."""
        proof, _ev, m = V2Ed25519.prove(self, run, tamper)
        return proof, m

    def respond(self, proof, m, verifier_challenge, auditor_state):
        """Phase 2: open positions selected by the later verifier challenge."""
        if not isinstance(verifier_challenge, bytes) or len(verifier_challenge) != C.HASH_OUT:
            raise ValueError("a 32-byte verifier-held challenge is required")
        if not isinstance(auditor_state, bytes) or len(auditor_state) != B_AUDITOR_STATE:
            raise ValueError("the 32-byte auditor-held anchor state is required")
        leaves = proof.extra["leaves"]
        idxs = challenge_indices(proof.root, len(proof.entries), self.k,
                                 verifier_challenge)
        proof.extra["openings"] = [(i, proof.entries[i], merkle_path(leaves, i, meter=m))
                                   for i in idxs]
        depth = max(1, (len(proof.entries) - 1).bit_length())
        ev = (Evidence().add("root", proof.root).add("run id", proof.run_id)
              .add("auditor anchor state", auditor_state)
              .add("anchor", proof.anchor)
              .add("verifier challenge", verifier_challenge))
        ev.add("openings", B_ENTRY + C.ED25519_SIG + C.HASH_OUT * depth, len(idxs))
        n = len(proof.entries)
        self.delta = 1 - min(self.k, n) / max(n, 1)
        return proof, ev, m

    def prove(self, run, tamper=None):
        raise RuntimeError("sampled V3 is two-phase: call commit(), then respond()")

    def judge(self, policy, proof, verifier_challenge=None, auditor_state=None):
        m = Meter()
        if not anchor_verify(policy, proof.root, proof.anchor, proof.run_id,
                             auditor_state, meter=m):
            return False, m
        required = policy.required_ids()
        if proof.n != len(required):
            return False, m
        if not isinstance(verifier_challenge, bytes) or len(verifier_challenge) != C.HASH_OUT:
            return False, m
        expected = challenge_indices(proof.root, proof.n, self.k, verifier_challenge)
        openings = proof.extra.get("openings", [])
        if [item[0] for item in openings] != expected:
            return False, m
        for i, e, path in openings:
            if e.rid != required[i]:
                return False, m
            lf = leaf_hash(struct.pack(">HH", e.device, e.seq) + e.commit, meter=m)
            if not merkle_verify(lf, i, path, proof.n, proof.root, meter=m):
                return False, m
            try:
                pk = C.ed_public_from_bytes(policy.credential(e.device, "ed25519"))
            except (TypeError, ValueError):
                return False, m
            if not C.ed_verify(pk, e.sig, e.preimage(policy.epoch), meter=m):
                return False, m
        return True, m


def challenge_indices(root, n, k, challenge):
    """Unique positions derived from an anchored root and verifier challenge."""
    out, ctr = [], 0
    while len(out) < min(k, n):
        d = C.H(b"challenge", root, challenge, struct.pack(">I", ctr))
        idx = _uniform_index(d[:4], n)
        if idx is None:
            ctr += 1
            continue
        if idx not in out:
            out.append(idx)
        ctr += 1
    return out


def _uniform_index(draw, n):
    """Map a 32-bit draw uniformly to [0,n), rejecting the biased tail."""
    if n <= 0 or n > (1 << 32):
        raise ValueError("n must be in [1, 2^32]")
    x = int.from_bytes(draw, "big")
    limit = (1 << 32) - ((1 << 32) % n)
    return None if x >= limit else x % n


# ---------------------------------------------------------- V4 mechanisms ----
class V4Raw(Stack):
    name, level = "v4-raw", 4
    mechanism = "ship raw observations, judge recomputes F"

    def prove(self, run, tamper=None):
        m = Meter()
        obs = [o for o in run.obs if not tamper or tamper.keeps(o.rid)]
        vals = {o.rid: o.value for o in obs}
        if tamper:
            vals.update(tamper.fabricate)
        forged = tamper.forged if tamper else frozenset()
        sigs = {}
        for o in obs:
            signer = 9999 if o.rid in forged else o.device
            wire = struct.pack(">HHh", o.device, o.seq, vals[o.rid])
            sigs[o.rid] = C.ed_sign(C.ed_keygen(signer),
                                    struct.pack(EPOCH_FMT, run.policy.epoch) + wire, meter=m)
        leaves = [leaf_hash(struct.pack(EPOCH_FMT, run.policy.epoch)
                            + struct.pack(">HHh", o.device, o.seq, vals[o.rid]), meter=m)
                  for o in obs]
        tree = StreamingMerkle(meter=m)
        for leaf in leaves:
            tree.add(leaf)
        root = tree.root()
        anchor = anchor_sign(run, root, meter=m)
        if tamper:
            vals.update(tamper.post_alter)      # changed after the record was signed
        y = OPS.apply(run.policy, [vals[o.rid] for o in obs])
        if tamper:
            y = tamper.output(y)
        ev = add_anchor_context(
            Evidence().add("observations", B_OBS, len(obs))
            .add("record sigs", C.ED25519_SIG, len(obs)).add("root", root), run
        ).add("anchor", anchor)
        pr = Proof(y=y, n=len(obs), root=root, anchor=anchor,
                   run_id=run.run_id,
                   raw=[(o.device, o.seq, vals[o.rid]) for o in obs])
        pr.extra["sigs"] = sigs
        return pr, ev, m

    def judge(self, policy, proof, auditor_state=None):
        m = Meter()
        if not anchor_verify(policy, proof.root, proof.anchor, proof.run_id,
                             auditor_state, meter=m):
            return False, m
        if [(d, q) for d, q, _ in proof.raw] != policy.required_ids():
            return False, m
        tree = StreamingMerkle(meter=m)
        for d, q, v in proof.raw:
            msg = struct.pack(EPOCH_FMT, policy.epoch) + struct.pack(">HHh", d, q, v)
            try:
                pk = C.ed_public_from_bytes(policy.credential(d, "ed25519"))
            except (TypeError, ValueError):
                return False, m
            if not C.ed_verify(pk, proof.extra["sigs"][(d, q)], msg, meter=m):
                return False, m
            tree.add(leaf_hash(msg, meter=m))
        if tree.root() != proof.root:
            return False, m
        y = OPS.apply(policy, [v for _, _, v in proof.raw])
        m.fuse()
        return abs(y - proof.y) < 1e-9, m


class V4Attested(Stack):
    name, level, profile = "v4-attested", 4, "rho_iso"
    mechanism = "modeled attested execution report"
    modeled = True

    ROT = 4242

    def prove(self, run, tamper=None):
        m = Meter()
        obs = [o for o in run.obs if not tamper or tamper.keeps(o.rid)]
        acquired = {o.rid: o.value for o in obs}
        if tamper:
            acquired.update(tamper.fabricate)
        # This is a cost model for an isolated acquisition path. The expected
        # binary measurement and attestation key are pre-provisioned in P. A
        # real deployment must establish that the path admits only enrolled
        # inputs and enforces the policy before issuing the report.
        leaves = [leaf_hash(struct.pack(EPOCH_FMT, run.policy.epoch)
                            + struct.pack(">HHh", o.device, o.seq, acquired[o.rid]), meter=m)
                  for o in obs]
        root, state = chain_head(leaves, meter=m)
        m.touch(state)
        # The root is witnessed by an external authority before y is accepted.
        # This anchor is distinct from the device/root-of-trust report below.
        anchor = anchor_sign(run, root, meter=m)
        attested_y = OPS.apply(run.policy, [acquired[o.rid] for o in obs])
        admissible = (not (tamper.forged if tamper else frozenset())
                      and [o.rid for o in obs] == run.policy.required_ids())
        signer = self.ROT if admissible else 9999
        report = C.ed_sign(C.ed_keygen(signer), run.policy.digest() + root
                           + struct.pack(">d", attested_y), meter=m)
        presented = dict(acquired)
        if tamper:
            presented.update(tamper.post_alter)   # changed after attestation
        y = OPS.apply(run.policy, [presented[o.rid] for o in obs])
        if tamper:
            y = tamper.output(y)
        pr = Proof(y=y, n=len(obs), root=root, anchor=anchor, run_id=run.run_id)
        pr.extra["report"] = report
        ev = add_anchor_context(Evidence().add("manifest root", root), run)
        ev.add("external anchor", anchor).add("report", C.ED25519_SIG)
        return pr, ev, m

    def judge(self, policy, proof, auditor_state=None):
        m = Meter()
        if not anchor_verify(policy, proof.root, proof.anchor, proof.run_id,
                             auditor_state, meter=m):
            return False, m
        try:
            pk = C.ed_public_from_bytes(policy.service_key("attestation-ed25519"))
        except (TypeError, ValueError):
            return False, m
        ok = C.ed_verify(pk, proof.extra["report"], policy.digest() + proof.root
                         + struct.pack(">d", proof.y), meter=m)
        return ok, m


class V4HomoMAC(Stack):
    name, level = "partial-homomac", 0
    mechanism = "aggregate-only linearly homomorphic MAC"
    complete = False
    public = False
    operators = ("mean", "wmean")

    MASTER = b"auditor-master-key-32-bytes----!"

    def prove(self, run, tamper=None):
        m = Meter()
        HM.set_epoch(run.policy.epoch)
        obs = [o for o in run.obs if not tamper or tamper.keeps(o.rid)]
        acquired = {o.rid: o.value for o in obs}
        if tamper:
            acquired.update(tamper.fabricate)
        forged = tamper.forged if tamper else frozenset()
        coeffs = _coeffs(run.policy, obs)
        with m.hold(HM.TAG_BYTES):
            tags = []
            for o in obs:
                key = b"adversary-key-32-bytes--------!!" if o.rid in forged else self.MASTER
                m.hash()
                tags.append(HM.tag(key, o.device, C.rid_bytes(o.rid),
                                   acquired[o.rid], meter=m))
            t = HM.combine(tags, coeffs, meter=m)
        presented = dict(acquired)
        if tamper:
            presented.update(tamper.post_alter)
        ylin = sum(c * presented[o.rid] for c, o in zip(coeffs, obs))
        y = _relin(run.policy, ylin, len(obs))
        if tamper and tamper.dy:
            y = tamper.output(y)
            ylin = _delin(run.policy, y, obs, coeffs)
        pr = Proof(y=y, n=len(obs))
        pr.extra["tag"] = t
        return pr, Evidence().add("combined tag", HM.TAG_BYTES), m

    def judge(self, policy, proof, auditor_state=None):
        m = Meter()
        req = policy.required_ids()
        coeffs = _coeffs_ids(policy, req)
        ld = [(C.rid_bytes(r), r[0]) for r in req]
        ylin = round(_delin(policy, proof.y, req, coeffs))
        if not HM.verify(self.MASTER, policy.epoch, ld, coeffs,
                         proof.extra["tag"], ylin, meter=m):
            return False, m
        return abs(_relin(policy, ylin, len(req)) - proof.y) < 1e-9, m


def _coeffs(policy, kept):
    if policy.operator == "wmean":
        w = policy.params["weights"]
        return [w[i % len(w)] for i in range(len(kept))]
    return [1] * len(kept)


def _coeffs_ids(policy, ids):
    if policy.operator == "wmean":
        w = policy.params["weights"]
        return [w[i % len(w)] for i in range(len(ids))]
    return [1] * len(ids)


def _relin(policy, ylin, n):
    """Recover the operator's value from the linear form the MAC certifies."""
    if policy.operator == "wmean":
        w = policy.params["weights"]
        tot = sum(w[i % len(w)] for i in range(n))
        return ylin / 100.0 / tot + OPS.KELVIN0
    return ylin / 100.0 / n + OPS.KELVIN0


def _delin(policy, y, kept, coeffs):
    n = len(kept)
    tot = sum(coeffs) if policy.operator == "wmean" else n
    return (y - OPS.KELVIN0) * 100.0 * tot


ALL = [V0None, V1Merkle, V1Chain, V2Ed25519, V2BLS, V3Manifest, V3PolicySample,
       V4Raw, V4Attested, V4HomoMAC]

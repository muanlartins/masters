"""Adversarial proof-object and public-signal checks beyond numeric matching."""
from copy import deepcopy
import json
import sys

sys.path.insert(0, ".")

from vfusion import crypto as C
from vfusion.stacks import (V2Ed25519, V3PolicySample, V4Attested,
                            V4HomoMAC, V4Raw, _uniform_index)
from vfusion.trace import make_policy, make_run


def check(name, condition):
    if not condition:
        raise AssertionError(name)
    print("PASS ", name)


def main():
    policy = make_policy(m=4, k=15, operator="mean")
    run = make_run(policy)

    sampled = V3PolicySample()
    challenge = bytes.fromhex("42" * 32)
    pending, meter = sampled.commit(run)
    check("sampled root is anchored before challenge response",
          bool(pending.root and pending.anchor) and "openings" not in pending.extra)
    proof, _, _ = sampled.respond(pending, meter, challenge, run.auditor_state)
    check("sampled honest proof",
          sampled.judge(policy, proof, verifier_challenge=challenge,
                        auditor_state=run.auditor_state)[0])
    check("sampled challenge is verifier state, not proof data",
          "challenge" not in proof.extra)
    check("sampled response is bound to verifier state",
          not sampled.judge(policy, proof,
                            verifier_challenge=bytes.fromhex("43" * 32),
                            auditor_state=run.auditor_state)[0])
    check("anchor requires independently held auditor state",
          not sampled.judge(policy, proof, verifier_challenge=challenge)[0])
    check("anchor is bound to the exact auditor state",
          not sampled.judge(policy, proof, verifier_challenge=challenge,
                            auditor_state=bytes.fromhex("41" * 32))[0])
    saved = proof.extra["openings"]
    proof.extra["openings"] = []
    check("sampled empty opening set rejected",
          not sampled.judge(policy, proof, verifier_challenge=challenge,
                            auditor_state=run.auditor_state)[0])
    proof.extra["openings"] = saved[1:] + saved[:1]
    check("sampled reordered challenges rejected",
          not sampled.judge(policy, proof, verifier_challenge=challenge,
                            auditor_state=run.auditor_state)[0])

    check("32-bit modulo tail is rejected",
          _uniform_index(bytes.fromhex("ff" * 4), 60) is None)

    enrolled = V2Ed25519()
    enrolled_proof, _, _ = enrolled.prove(run)
    check("generated policy carries both enrolled device suites",
          len(policy.pubkeys) == policy.m and
          all(set(s) == {"bls12-381", "ed25519"}
              for s in policy.pubkeys.values()))
    reordered = deepcopy(policy)
    reordered.pubkeys = dict(reversed(list(reordered.pubkeys.items())))
    reordered.service_keys = dict(reversed(list(reordered.service_keys.items())))
    check("canonical roster order does not change the policy digest",
          policy.digest() == reordered.digest())
    wrong_enrollment = deepcopy(policy)
    wrong_enrollment.pubkeys[1]["ed25519"] = C.ed_public_bytes(
        C.ed_keygen(9999).public_key())
    wrong_run = make_run(wrong_enrollment)
    wrong_proof, _, _ = enrolled.prove(wrong_run)
    check("record signed outside the policy enrollment is rejected",
          not enrolled.judge(wrong_enrollment, wrong_proof,
                             auditor_state=wrong_run.auditor_state)[0])
    check("roster substitution changes the bound policy digest",
          policy.digest() != wrong_enrollment.digest())
    check("post-anchor roster substitution is rejected",
          not enrolled.judge(wrong_enrollment, enrolled_proof,
                             auditor_state=run.auditor_state)[0])

    raw = V4Raw()
    raw_proof, _, _ = raw.prove(run)
    check("raw honest proof",
          raw.judge(policy, raw_proof, auditor_state=run.auditor_state)[0])
    raw_proof.raw[0] = (*raw_proof.raw[0][:2], raw_proof.raw[0][2] + 1)
    check("raw value is bound to root and signature",
          not raw.judge(policy, raw_proof, auditor_state=run.auditor_state)[0])

    attested = V4Attested()
    report, ev, _ = attested.prove(run)
    check("attested honest report",
          attested.judge(policy, report, auditor_state=run.auditor_state)[0])
    check("attested report has no uncharged id list or flag",
          set(report.extra) == {"report"} and ev.total() == 208)
    saved_anchor = report.anchor
    report.anchor = bytes(len(saved_anchor))
    check("attested report requires an external anchor",
          not attested.judge(policy, report,
                             auditor_state=run.auditor_state)[0])

    mac = V4HomoMAC()
    check("aggregate MAC is marked incomplete", not mac.complete)

    snark = json.load(open("results/snark.json"))
    executed = [r for r in snark["results"] if "public_signals" in r]
    check("all executed circuits match independent public claims",
          len(executed) == 5 and all(r.get("checked") for r in executed))


if __name__ == "__main__":
    main()

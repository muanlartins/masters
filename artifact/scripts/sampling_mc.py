"""Measure the sampled stack against its exact one-defect probability.

A short manifest is rejected deterministically because policy fixes n. An
omission padded with an authentic duplicate preserves n and is the harder
case: only the substituted policy position reveals the coverage defect.
"""
import json
import math
import sys
sys.path.insert(0, ".")
from vfusion.attacks import Tamper
from vfusion.stacks import V3PolicySample, challenge_indices
from vfusion.policy import Run
from vfusion.trace import make_policy, make_run

TRIALS = 2000


def challenge(nonce):
    return nonce.to_bytes(32, "big")


def selected_rate(root, n, bad_index, k):
    """Rate at which the exact judge challenge includes one defective index."""
    hit = sum(bad_index in challenge_indices(root, n, k, challenge(nonce))
              for nonce in range(TRIALS))
    return hit / TRIALS


def wilson95(hits, trials):
    """Two-sided Wilson interval with z=1.96."""
    z = 1.96
    p = hits / trials
    den = 1 + z * z / trials
    centre = (p + z * z / (2 * trials)) / den
    half = z * math.sqrt(p * (1 - p) / trials + z * z / (4 * trials * trials)) / den
    return [round(centre - half, 4), round(centre + half, 4)]


if __name__ == "__main__":
    pol = make_policy(m=4, k=15, operator="mean")
    run = make_run(pol)
    n = pol.n
    alter = Tamper("A1", 1, post_alter={(2, 3): 400})
    omit = Tamper("A3", 3, omit=frozenset({(4, 15)}))
    # Preserve n while omitting (4,15): duplicate an authentic first record at
    # the final policy position. Attribution still holds for the duplicate,
    # while exact policy coverage does not.
    replaced_obs = list(run.obs[:-1]) + [run.obs[0]]
    replaced = Run(policy=pol, obs=replaced_obs, salts=run.salts,
                   run_id=run.run_id, auditor_state=run.auditor_state)
    fixture = V3PolicySample()
    fixed_challenge = challenge(0)
    pending, meter = fixture.commit(run, tamper=alter)
    alter_proof, _, _ = fixture.respond(pending, meter, fixed_challenge,
                                         run.auditor_state)
    pending, meter = fixture.commit(replaced)
    replace_proof, _, _ = fixture.respond(pending, meter, fixed_challenge,
                                           run.auditor_state)
    pending, meter = fixture.commit(run, tamper=omit)
    short_proof, _, _ = fixture.respond(pending, meter, fixed_challenge,
                                         run.auditor_state)
    short_rejected = not fixture.judge(
        pol, short_proof, verifier_challenge=fixed_challenge,
        auditor_state=run.auditor_state)[0]
    alter_index = pol.required_ids().index((2, 3))
    replace_index = n - 1
    out = {"n": n, "trials": TRIALS, "rows": []}
    for k in (1, 5, 10, 20, 30, 60):
        meas = selected_rate(alter_proof.root, n, alter_index, k)
        bound = min(k, n) / n      # k distinct draws, one defective record
        om_short = float(short_rejected)
        om_replace = selected_rate(replace_proof.root, n, replace_index, k)
        hits = round(meas * TRIALS)
        replace_hits = round(om_replace * TRIALS)
        out["rows"].append({"k": k, "measured_A1": meas, "bound_A1": bound,
                            "ci95_A1": wilson95(hits, TRIALS),
                            "measured_A3_short": om_short,
                            "measured_A3_replace": om_replace,
                            "ci95_A3_replace": wilson95(replace_hits, TRIALS)})
        print(f"k={k:3d}  A1 detected {meas:.3f}  (bound {bound:.3f})   "
              f"A3-short {om_short:.3f}  A3-replace {om_replace:.3f}")
    json.dump(out, open("results/sampling.json", "w"), indent=1)

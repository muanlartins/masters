"""Evaluate every stack over two operators and a range of window sizes.

Emits results/stacks.json. Primitive counts and byte counts are exact for the
declared protocol and serialization. Streaming-state coordinates are modeled
from each online schedule; the attestation row is explicitly a cost model. No
wall clock is recorded because pure-Python timing would misrepresent a device.
"""
import json
import sys
sys.path.insert(0, ".")

from vfusion.attacks import traces
from vfusion.trace import make_policy, make_run
import vfusion.stacks as S

SWEEP = [12, 20, 60, 120, 240, 480, 960]
HEADLINE = 60
SLOW = {"v2-bls"}                 # pure-Python pairings; exact counts, slow clock
SLOW_MAX = 60
PARAMS = {"mkt": {}, "mean": {}, "excursion": {"threshold": 800},
          "wmean": {"weights": [1, 2, 3, 1]}}
VERIFIER_CHALLENGE = bytes.fromhex("42" * 32)


def prove(st, run, tamper=None):
    """Run the interactive sampled stack with verifier-owned challenge state."""
    if isinstance(st, S.V3PolicySample):
        pending, meter = st.commit(run, tamper=tamper)
        # The verifier issues this reproducible fixture only after commit()
        # returns the externally anchored root.
        return st.respond(pending, meter, VERIFIER_CHALLENGE, run.auditor_state)
    return st.prove(run, tamper=tamper)


def judge(st, policy, proof, auditor_state):
    if isinstance(st, S.V3PolicySample):
        return st.judge(policy, proof,
                        verifier_challenge=VERIFIER_CHALLENGE,
                        auditor_state=auditor_state)
    return st.judge(policy, proof, auditor_state=auditor_state)


def measure(pol, run, cls):
    st = cls()
    if not st.supports(pol):
        return None
    pr, ev, mp = prove(st, run)
    ok, mj = judge(st, pol, pr, run.auditor_state)
    return {
        "stack": st.name, "level": st.level, "profile": st.profile,
        "mechanism": st.mechanism, "public": st.public, "delta": st.delta,
        "complete": st.complete, "modeled": st.modeled,
        "accept": ok, "y": pr.y,
        "B_ev": ev.total(), "B_breakdown": ev.breakdown(),
        "N_P": mp.nonzero(), "M_P": mp.peak,
        "N_J": mj.nonzero(), "M_J": mj.peak,
    }


def separation(pol, run):
    rows = []
    for cls in S.ALL:
        st = cls()
        if not st.supports(pol) or st.name in SLOW:
            continue
        row = {"stack": st.name, "level": st.level, "results": {}}
        for t in traces(pol):
            pr, _, _ = prove(st, run, tamper=t)
            ok, _ = judge(st, pol, pr, run.auditor_state)
            row["results"][t.name] = {
                "detected": not ok,
                "expected": st.level >= t.rejects_at if st.complete else None,
            }
        rows.append(row)
    return rows


if __name__ == "__main__":
    out = {"sweep": SWEEP, "headline_n": HEADLINE, "operators": {}, "separation": {}}
    for op in ("mkt", "mean"):
        out["operators"][op] = {}
        for n in SWEEP:
            pol = make_policy(m=4, k=n // 4, operator=op, params=PARAMS[op])
            run = make_run(pol)
            rows = []
            for cls in S.ALL:
                if cls().name in SLOW and n > SLOW_MAX:
                    continue
                r = measure(pol, run, cls)
                if r:
                    rows.append(r)
            out["operators"][op][str(n)] = rows
            print(f"{op:10s} n={n:4d}  " +
                  "  ".join(f"{r['stack'].split('-',1)[1][:7]}:{r['B_ev']}" for r in rows),
                  flush=True)
    pol = make_policy(m=4, k=HEADLINE // 4, operator="mean", params={})
    out["separation"]["mean"] = separation(pol, make_run(pol))
    json.dump(out, open("results/stacks.json", "w"), indent=1)
    print("written results/stacks.json")

"""BLS separation, run apart because pure-Python pairings are slow.

Only the wall clock is slow: the primitive counts and byte counts this stack
reports are exact and independent of the implementation's speed.
"""
import json
import sys
sys.path.insert(0, ".")
from vfusion.attacks import traces
from vfusion.stacks import V2BLS
from vfusion.trace import make_policy, make_run

pol = make_policy(m=4, k=15, operator="mean")
run = make_run(pol)
st = V2BLS()
row = {"stack": st.name, "level": st.level, "results": {}}
for t in traces(pol):
    pr, _, _ = st.prove(run, tamper=t)
    ok, _ = st.judge(pol, pr, auditor_state=run.auditor_state)
    row["results"][t.name] = {"detected": not ok,
                              "expected": st.level >= t.rejects_at if st.complete else None}
    print(t.name, "detected" if not ok else "accepted",
          "(expected", "reject)" if st.level >= t.rejects_at else "accept)", flush=True)

d = json.load(open("results/stacks.json"))
d["separation"]["mean"] = [r for r in d["separation"]["mean"] if r["stack"] != st.name]
d["separation"]["mean"].append(row)
order = ["v0-none", "v1-merkle", "v1-chain", "v2-ed25519", "v2-bls",
         "v3-manifest", "v3-policy-sample", "v4-raw", "v4-attested", "partial-homomac"]
d["separation"]["mean"].sort(key=lambda r: order.index(r["stack"]))
json.dump(d, open("results/stacks.json", "w"), indent=1)
print("merged into results/stacks.json")

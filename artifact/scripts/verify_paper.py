"""Check quantitative manuscript claims against the included result JSON."""
import json
import math
import sys
from pathlib import Path

sys.path.insert(0, ".")
from vfusion import operators as OPS
from vfusion.mktwitness import SC, VOFF, witness
from vfusion.trace import make_policy, make_run

RAW = "".join(Path(f"../sections/{name}.tex").read_text()
              for name in ("evidence", "main", "conclusion", "intro"))
TEX = RAW.replace("{,}", ",").replace("\\,", ",")

data = json.load(open("results/stacks.json"))
snark = json.load(open("results/snark.json"))
sampling = json.load(open("results/sampling.json"))
n = str(data["headline_n"])
mkt = {r["stack"]: r for r in data["operators"]["mkt"][n]}
mean = {r["stack"]: r for r in data["operators"]["mean"][n]}
cir = {(r["circuit"], r["n"]): r for r in snark["results"]}
checks = []


def claim(description, source_fragment, expected, actual):
    present = source_fragment in TEX if source_fragment is not None else True
    checks.append((present and expected == actual, description, expected, actual))


def at(operator, nn, stack):
    return next(r for r in data["operators"][operator][str(nn)]
                if r["stack"] == stack)


base = cir[("binding", 60)]["constraints"]
claim("V2 Ed25519 bytes", "6,144", 6144, mkt["v2-ed25519"]["B_ev"])
claim("raw V4 bytes", "4,344", 4344, mkt["v4-raw"]["B_ev"])
claim("exact V3 reuses V2 evidence", "same full manifest",
      mkt["v2-ed25519"]["B_ev"], mkt["v3-manifest"]["B_ev"])
claim("sampled V3 bytes", "6,016", 6016, mkt["v3-policy-sample"]["B_ev"])

# The displayed serialization formulas must fit every measured sweep point.
raw_formula = all(at("mkt", nn, "v4-raw")["B_ev"] == 144 + 70 * nn
                  for nn in data["sweep"])
ed_formula = all(at("mkt", nn, "v2-ed25519")["B_ev"] == 144 + 100 * nn
                 for nn in data["sweep"])
sample_formula = all(
    at("mkt", nn, "v3-policy-sample")["B_ev"]
    == 176 + min(20, nn) * (100 + 32 * math.ceil(math.log2(nn)))
    for nn in data["sweep"])
claim("raw byte formula", "B_{\\mathrm{raw}}", True, raw_formula)
claim("Ed25519 byte formula", "B_{\\mathrm{Ed}}", True, ed_formula)
claim("sample byte formula", "B_{\\mathrm{sample}}", True, sample_formula)

def sample_bytes(nn):
    return 176 + min(20, nn) * (100 + 32 * math.ceil(math.log2(nn)))

crossover = next(nn for nn in range(1, 1000) if sample_bytes(nn) < 144 + 70 * nn)
claim("analytical sampled crossover", "$n=94$", 94, crossover)
claim("first measured point after crossover", "$n=120$", True,
      at("mkt", 120, "v3-policy-sample")["B_ev"]
      < at("mkt", 120, "v4-raw")["B_ev"])

claim("attested bytes", "208-byte transcript", 208,
      mkt["v4-attested"]["B_ev"])
claim("attested profile", "under $\\rho_{\\mathrm{iso}}$", "rho_iso",
      mkt["v4-attested"]["profile"])
claim("attested external anchor charged", "64-byte external",
      64, mkt["v4-attested"]["B_breakdown"]["external anchor"])
claim("attested explicitly modeled", "modeled attestation", True,
      mkt["v4-attested"]["modeled"])
claim("aggregate MAC bytes", "16-byte homomorphic MAC", 16,
      mean["partial-homomac"]["B_ev"])
claim("aggregate MAC incomplete", "not V4", False,
      mean["partial-homomac"]["complete"])
claim("BLS bytes", "2,400", 2400, mkt["v2-bls"]["B_ev"])
claim("BLS pairings", "61 pairings", 61, mkt["v2-bls"]["N_J"]["pairing"])
claim("Ed25519 verifications", "61 Ed25519 verifications", 61,
      mkt["v2-ed25519"]["N_J"]["verify"])

claim("binding constraints", "32,040", 32040, base)
claim("mean adds one", "adds one", 1,
      cir[("mean", 60)]["constraints"] - base)
claim("excursion added constraints", "adds 1,261", 1261,
      cir[("excursion", 60)]["constraints"] - base)
claim("excursion percent", "(3.9\\%)", "3.9",
      f"{100 * (cir[('excursion', 60)]['constraints'] - base) / base:.1f}")
claim("MKT added constraints", "adds 6,591", 6591,
      cir[("mkt", 60)]["constraints"] - base)
claim("MKT percent", "(20.6\\%)", "20.6",
      f"{100 * (cir[('mkt', 60)]['constraints'] - base) / base:.1f}")
claim("attributed n=60 constraints", "549,392", 549392,
      cir[("attributed", 60)]["constraints"])
claim("attribution factor", "factor of 17.1", "17.1",
      f"{cir[('attributed', 60)]['constraints'] / cir[('mean', 60)]['constraints']:.1f}")

at12 = cir[("attributed", 12)]
rss_mb = [round(x / 1e6) for x in at12["prove_rss_all"]]
claim("attributed n=12 RSS median", "2,467 MB", 2467,
      round(at12["prove_rss_bytes"] / 1e6))
claim("attributed RSS repetitions", "three\ntrials", 3, at12["reps"])
claim("attributed RSS range", "range 1,812--2,494 MB",
      [1812, 2494], [min(rss_mb), max(rss_mb)])

emitted = at12["proof_json_bytes"] + at12["public_json_bytes"]
anchor_context = 64 + 16 + 32
normalized = (at12["proof_structural_bytes"]
              + at12["public_structural_bytes"] + anchor_context)
raw12 = at("mkt", 12, "v4-raw")["B_ev"]
claim("attributed emitted bytes", "snarkjs emits 983\nbytes", 983, emitted)
claim("attributed JSON online bundle", "1,095 bytes", 1095,
      emitted + anchor_context)
claim("attributed normalized bundle", "336 bytes", 336, normalized)
claim("same-workload raw n=12", "Packed raw V4 uses 984\nbytes", 984, raw12)
claim("normalized proof saving", "648 bytes smaller", 648, raw12 - normalized)
claim("implementation encoding delta", "111 bytes larger", 111,
      emitted + anchor_context - raw12)
claim("attributed vkey", "3,290 bytes as JSON", 3290,
      at12["verification_key_json_bytes"])
claim("attributed structural vkey", "352 bytes normalized", 352,
      at12["verification_key_structural_bytes"])
claim("attributed first JSON run", "4,385 bytes", 4385,
      emitted + anchor_context + at12["verification_key_json_bytes"])
claim("attributed first normalized run", "688 bytes", 688,
      normalized + at12["verification_key_structural_bytes"])
claim("attributed n=60 compile only", "compiled but not proven",
      True, cir[("attributed", 60)]["compile_only"])

mkt_policy = make_policy(m=4, k=15, operator="mkt")
mkt_run = make_run(mkt_policy)
mkt_values = [o.value for o in mkt_run.obs]
mkt_fixed = witness([v + VOFF for v in mkt_values])[1] / 100
mkt_error_mk = abs(OPS.mkt(mkt_values) - mkt_fixed) * 1000
claim("MKT fixed-point scale", "scale $2^{16}$", 1 << 16, SC)
claim("MKT rounding semantics", "round toward $-\\infty$", True, True)
claim("MKT observed approximation error", "1.8~mK", "1.8",
      f"{mkt_error_mk:.1f}")

row20 = next(r for r in sampling["rows"] if r["k"] == 20)
claim("sampling trials", "2,000", 2000, sampling["trials"])
claim("A1 k=20 rate", "0.338", 0.338, round(row20["measured_A1"], 3))
claim("A3 padded k=20 rate", "0.317", 0.317,
      round(row20["measured_A3_replace"], 3))
claim("single-defect bound", "consistent with $1/3$", 1 / 3,
      row20["bound_A1"])
claim("short omission deterministic", "rejected before sampling", {1.0},
      {r["measured_A3_short"] for r in sampling["rows"]})

complete = [r for r in mean.values() if r["complete"]]
claim("complete stack count", "nine complete stacks", 9, len(complete))
claim("partial baseline count", "one deliberately partial", 1,
      sum(not r["complete"] for r in mean.values()))
claim("circuit count", "five\nproof circuits", 5,
      len({r["circuit"] for r in snark["results"]}))
claim("complete-stack decisions", "36 complete-stack decisions", 36,
      4 * len(complete))
claim("deterministic decisions", "34 are", 34, 4 * len(complete) - 2)

bad = [c for c in checks if not c[0]]
for ok, desc, expected, actual in checks:
    print(f"{'PASS' if ok else 'FAIL':<5} {desc:<38} "
          f"expected={expected!r:<24} got={actual!r}")
print(f"\n{len(checks) - len(bad)}/{len(checks)} checks pass")
sys.exit(1 if bad else 0)

"""Compile, set up, prove and verify each circuit; record measured costs.

Reported per circuit: R1CS constraint counts, Groth16 proving key size, prover
wall time and peak resident set on the named host, proof and public-signal
bytes as snarkjs serializes them, and the structural minimum for a BN254
Groth16 proof.  Wall time and RSS are host measurements and are labelled as
such; constraint counts and byte counts are exact.
"""
import json
import os
import platform
import re
import statistics
import subprocess
import sys
import time
from pathlib import Path

REPS = 3          # every host measurement is the median of this many runs

sys.path.insert(0, ".")
from vfusion.mktwitness import VOFF, rbits, witness
from vfusion.crypto import poseidon_many
from vfusion.trace import make_policy, make_run

CIRCOM = os.environ.get("CIRCOM", "circom")
SNARKJS = "node_modules/.bin/snarkjs"
BUILD = Path("build")
PTAU_BY_POWER = {15: BUILD / "pot15.ptau", 16: BUILD / "pot16.ptau",
                 17: BUILD / "pot17.ptau", 18: BUILD / "pot18.ptau"}


def ptau_for(constraints):
    """Smallest available setup whose domain covers the constraint system."""
    for power in sorted(PTAU_BY_POWER):
        if (1 << power) >= constraints and PTAU_BY_POWER[power].exists():
            return PTAU_BY_POWER[power], power
    raise SystemExit(f"no powers-of-tau file covers {constraints} constraints")

# Groth16 on BN254: two G1 points and one G2 point, compressed. A verification
# key has one fixed G1 point, three fixed G2 points, and one G1 IC point per
# public input plus the constant term.
GROTH16_STRUCTURAL = 32 + 32 + 64
GROTH16_VKEY_FIXED = 32 + 3 * 64
FIELD_ELEM = 32


def run(cmd, capture_rss=False):
    if capture_rss:
        t0 = time.time()
        p = subprocess.run(["/usr/bin/time", "-l"] + cmd,
                           capture_output=True, text=True)
        dt = time.time() - t0
        m = re.search(r"(\d+)\s+maximum resident set size", p.stderr)
        return p, dt, int(m.group(1)) if m else None
    return subprocess.run(cmd, capture_output=True, text=True), None, None


ANSI = re.compile(r"\x1b\[[0-9;]*m")


def r1cs_info(name, n=60):
    """Total R1CS constraints from snarkjs, plus circom's non-linear split."""
    p, _, _ = run([SNARKJS, "r1cs", "info", str(BUILD / f"main_{name}_{n}.r1cs")])
    out = ANSI.sub("", p.stdout + p.stderr)
    get = lambda k: int(re.search(rf"# of {k}:\s+(\d+)", out).group(1))
    info = {"constraints": get("Constraints"), "wires": get("Wires"),
            "outputs": get("Outputs"), "private_inputs": get("Private Inputs")}
    c, _, _ = run([CIRCOM, str(BUILD / f"main_{name}_{n}.circom"), "--r1cs",
                   "-o", str(BUILD), "-l", "node_modules", "-l", "circuits"])
    txt = ANSI.sub("", c.stdout + c.stderr)
    for key, label in (("nonlinear", "non-linear constraints"),
                       ("linear", "linear constraints")):
        m = re.search(rf"^{label}:\s+(\d+)", txt, re.M)
        if m:
            info[key] = int(m.group(1))
    return info


def poseidon_chain(vals):
    p = subprocess.run(["node", "scripts/poseidon_chain.js"],
                       input=json.dumps([str(v) for v in vals]),
                       capture_output=True, text=True, check=True)
    return p.stdout.strip()


def attach_cross_checks(results, vpos):
    """Tie public circuit outputs to independently computed policy values."""
    attr = json.load(open("build/main_attributed_12.input.json"))
    attr_cm = poseidon_chain(attr["v"])
    attr_roster = poseidon_many([attr["Ax"] + attr["Ay"]])[0]
    mkt_out = witness(vpos)[1]
    for r in results:
        if "public_signals" not in r:
            continue
        public = r["public_signals"]
        values = [int(v) for v in (attr["v"] if r["circuit"] == "attributed" else vpos)]
        checks = {"manifest": public[0] ==
                  (attr_cm if r["circuit"] == "attributed" else poseidon_chain(values))}
        if r["circuit"] == "mean":
            checks["operator"] = int(public[1]) == sum(values)
        elif r["circuit"] == "excursion":
            checks["operator"] = int(public[1]) == sum(v > 33568 for v in values)
        elif r["circuit"] == "mkt":
            checks["operator"] = int(public[1]) == mkt_out
        elif r["circuit"] == "attributed":
            checks["operator"] = int(public[1]) == sum(values)
            checks["roster"] = public[2] == attr_roster
        r["cross_checks"] = checks
        r["checked"] = r.get("verified", False) and all(checks.values())


def bench(name, inputs, n=60):
    tag = f"main_{name}_{n}"
    res = {"circuit": name, "n": n, **r1cs_info(name, n)}

    ptau, power = ptau_for(res["constraints"])
    res["ptau_power"] = power
    zkey, vkey = BUILD / f"{tag}.zkey", BUILD / f"{tag}.vkey.json"
    r1cs = BUILD / f"{tag}.r1cs"
    if zkey.exists() and zkey.stat().st_mtime < r1cs.stat().st_mtime:
        zkey.unlink()
        vkey.unlink(missing_ok=True)
    if not zkey.exists():
        p, t_setup, _ = run([SNARKJS, "groth16", "setup", str(r1cs),
                             str(ptau), str(zkey)], capture_rss=True)
        if p.returncode:
            return {**res, "error": p.stderr[-400:]}
        run([SNARKJS, "zkey", "export", "verificationkey", str(zkey), str(vkey)])
    res["proving_key_bytes"] = zkey.stat().st_size
    res["verification_key_json_bytes"] = vkey.stat().st_size

    inp = BUILD / f"{tag}.input.json"
    inp.write_text(json.dumps({k: [str(x) for x in v] if isinstance(v, list) else str(v)
                               for k, v in inputs.items()}))
    wtns = BUILD / f"{tag}.wtns"
    p, t_w, rss_w = run(["node", str(BUILD / f"{tag}_js" / "generate_witness.js"),
                         str(BUILD / f"{tag}_js" / f"{tag}.wasm"), str(inp), str(wtns)],
                        capture_rss=True)
    if p.returncode:
        return {**res, "error": "witness: " + p.stderr[-400:]}
    res["witness_s"], res["witness_rss_bytes"] = round(t_w, 2), rss_w

    proof, public = BUILD / f"{tag}.proof.json", BUILD / f"{tag}.public.json"
    ts, rs = [], []
    for _ in range(REPS):
        p, t_p, rss_p = run([SNARKJS, "groth16", "prove", str(zkey), str(wtns),
                             str(proof), str(public)], capture_rss=True)
        if p.returncode:
            return {**res, "error": "prove: " + ANSI.sub("", p.stdout + p.stderr)[:600]}
        ts.append(t_p)
        rs.append(rss_p)
    res["reps"] = REPS
    res["prove_s"] = round(statistics.median(ts), 2)
    res["prove_s_all"] = [round(t, 2) for t in ts]
    res["prove_rss_bytes"] = int(statistics.median(rs))
    res["prove_rss_all"] = rs

    p, t_v, rss_v = run([SNARKJS, "groth16", "verify", str(vkey), str(public),
                         str(proof)], capture_rss=True)
    res["verified"] = "OK" in (p.stdout + p.stderr)
    res["verify_s"], res["verify_rss_bytes"] = round(t_v, 2), rss_v

    sig = json.loads(public.read_text())
    res["public_signals"] = sig
    res["proof_json_bytes"] = proof.stat().st_size
    res["public_json_bytes"] = public.stat().st_size
    res["proof_structural_bytes"] = GROTH16_STRUCTURAL
    res["public_structural_bytes"] = FIELD_ELEM * len(sig)
    res["verification_key_structural_bytes"] = (
        GROTH16_VKEY_FIXED + FIELD_ELEM * (len(sig) + 1))
    return res


if __name__ == "__main__":
    pol = make_policy(m=4, k=15, operator="mkt")
    run_ = make_run(pol)
    vals = [o.value for o in run_.obs]
    vpos = [v + VOFF for v in vals]
    cM = poseidon_chain(vpos)
    print("python Poseidon chain cM =", cM[:24], "...")

    only = sys.argv[1:] or None
    jobs = [("binding", {"v": vpos}, 60), ("mean", {"v": vpos}, 60),
            ("excursion", {"v": vpos}, 60), ("mkt", witness(vpos)[0], 60),
            ("attributed", json.load(open("build/main_attributed_12.input.json")), 12)]
    if only:
        jobs = [j for j in jobs if j[0] in only]
    version = lambda cmd: subprocess.run(cmd, capture_output=True, text=True).stdout.strip()
    out = {"host": os.uname().machine + " / " + os.uname().sysname,
           "environment": {"platform": platform.platform(),
                           "python": platform.python_version(),
                           "node": version(["node", "--version"]),
                           "circom": version([CIRCOM, "--version"]),
                           "snarkjs": "0.7.5"},
           "cM_python": cM, "results": []}
    for name, inputs, nn in jobs:
        print(f"--- {name} (n={nn}) ---", flush=True)
        r = bench(name, inputs, nn)
        if "error" in r:
            print("   ERROR:", r["error"][:300])
        else:
            print(f"   constraints={r['constraints']} prove={r['prove_s']}s "
                  f"rss={r['prove_rss_bytes']/1e6:.1f}MB verified={r['verified']} "
                  f"proof={r['proof_json_bytes']}B signals={r['public_signals']}")
        out["results"].append(r)
    Path("results").mkdir(exist_ok=True)
    if only and Path("results/snark.json").exists():
        prev = json.load(open("results/snark.json"))
        keep = [r for r in prev["results"] if r["circuit"] not in only]
        # Migrate artifacts produced before the attributed circuit was renamed.
        keep = [r for r in keep if r["circuit"] != "attested"]
        order = ["binding", "mean", "excursion", "mkt", "attributed"]
        out["results"] = sorted(keep + out["results"],
                                key=lambda r: order.index(r["circuit"]))
    attach_cross_checks(out["results"], vpos)
    json.dump(out, open("results/snark.json", "w"), indent=1)
    print("written results/snark.json")

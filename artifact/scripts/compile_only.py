"""Record exact constraint counts for circuits too large to prove here.

Constraint counts come from compilation and are exact; no proving run is
implied, and nothing derived from a proving run is recorded for these rows.
"""
import json
import os
import re
import subprocess
import sys
from pathlib import Path

CIRCOM = os.environ.get("CIRCOM", "circom")
ANSI = re.compile(r"\x1b\[[0-9;]*m")

if __name__ == "__main__":
    name, n = sys.argv[1], int(sys.argv[2])
    p = subprocess.run([CIRCOM, f"build/main_{name}_{n}.circom", "--r1cs",
                        "-o", "build", "-l", "node_modules", "-l", "circuits"],
                       capture_output=True, text=True)
    txt = ANSI.sub("", p.stdout + p.stderr)
    nl = int(re.search(r"^non-linear constraints:\s+(\d+)", txt, re.M).group(1))
    li = int(re.search(r"^linear constraints:\s+(\d+)", txt, re.M).group(1))
    d = json.load(open("results/snark.json"))
    d["results"] = [r for r in d["results"]
                    if not (r["circuit"] == name and r["n"] == n)]
    d["results"].append({"circuit": name, "n": n, "constraints": nl + li,
                         "nonlinear": nl, "linear": li, "compile_only": True})
    order = ["binding", "mean", "excursion", "mkt", "attributed"]
    d["results"].sort(key=lambda r: (order.index(r["circuit"]), r["n"]))
    json.dump(d, open("results/snark.json", "w"), indent=1)
    print(f"{name} n={n}: {nl+li} constraints ({nl} non-linear, {li} linear)")

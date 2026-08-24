"""Generate reproducible main components and the attributed n=12 witness.

Generated files live under build/ and are intentionally not archived. Keeping
this generator in the artifact makes `make all` work from a clean extraction.
"""
import json
import subprocess
import sys
from pathlib import Path

sys.path.insert(0, ".")

from vfusion.mktwitness import (D, SC, T_HI_POS, T_LO_POS, UMAX, UMIN,
                                VOFF, XREF, rbits)
from vfusion.trace import make_policy, make_run


BUILD = Path("build")


def write(name, body):
    (BUILD / name).write_text("pragma circom 2.1.6;\ninclude \"fusion.circom\";\n" + body)


def attributed_input(n, m, k):
    policy = make_policy(m=m, k=k, operator="mean")
    values = [o.value + VOFF for o in make_run(policy).obs]
    proc = subprocess.run(
        ["node", "scripts/eddsa_sign.js"],
        input=json.dumps({"vpos": values, "m": m, "k": k}),
        capture_output=True, text=True, check=True)
    return {"v": values, **json.loads(proc.stdout)}


def main():
    BUILD.mkdir(exist_ok=True)
    write("main_binding_60.circom", """
template BindingOnly(n) {
    signal input v[n];
    signal output cM;
    component b = Binding(n);
    component rc[n];
    for (var i = 0; i < n; i++) {
        rc[i] = Num2Bits(16);
        rc[i].in <== v[i];
        b.v[i] <== v[i];
    }
    cM <== b.cM;
}
component main = BindingOnly(60);
""")
    write("main_mean_60.circom", "component main = MeanFusion(60);\n")
    write("main_excursion_60.circom",
          "component main = ExcursionFusion(60, 33568);\n")
    write("main_mkt_60.circom",
          f"component main = MktFusion(60, {SC}, {XREF}, {D}, {rbits(60)}, "
          f"{T_LO_POS}, {T_HI_POS}, {UMIN}, {UMAX});\n")
    write("main_attributed_60.circom",
          "component main = AttributedMeanFusion(60, 4, 15);\n")
    write("main_attributed_12.circom",
          "component main = AttributedMeanFusion(12, 4, 3);\n")
    (BUILD / "main_attributed_12.input.json").write_text(
        json.dumps(attributed_input(12, 4, 3)))
    print("prepared circuit entry points and attributed n=12 input")


if __name__ == "__main__":
    main()

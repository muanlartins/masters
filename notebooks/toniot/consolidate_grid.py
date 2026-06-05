"""Consolidate the big-grid shards (run_wisard_grid.py) into analysis tables.

Reads results/_consolidado/grid/wisard_grid_*.jsonl (per-cfg schema with
cv_{f1,f1_macro,f1_weighted}(+std) and holdout_{...}) and produces:
  - best config per (model, base) by cv_f1_weighted  -> per-device table
  - per-thermometer best (3 thermometer models)       -> thermometer sensitivity
  - synthesis: per-model per-device mean + combined    -> final table
Safe to run mid-sweep (works on partial shards).

Usage: python consolidate_grid.py
"""
from __future__ import annotations
import json, collections
from pathlib import Path
import numpy as np

GRID = Path("/Users/muanlartins/repos/masters/notebooks/toniot/results/_consolidado/grid")
BASES = ["Fridge", "Garage_Door", "GPS_Tracker", "Modbus", "Motion_Light", "Thermostat", "Weather"]
WMODELS = ["wisard", "cluswisard", "bloomwisard", "bthowen", "uleen"]
DISP = {"wisard": "WiSARD", "cluswisard": "ClusWiSARD", "bloomwisard": "BloomWiSARD",
        "bthowen": "BTHOWeN", "uleen": "ULEEN"}
THERMO_MODELS = {"wisard", "cluswisard", "bloomwisard"}


def load():
    rows = []
    for shard in sorted(GRID.glob("wisard_grid_*.jsonl")):
        for ln in shard.read_text().splitlines():
            if ln.strip():
                rows.append(json.loads(ln))
    return rows


def best_per(rows, model, base, task="binary", metric="cv_f1_weighted"):
    cand = [r for r in rows if r["model"] == model and r["base"] == base and r["task"] == task]
    return max(cand, key=lambda r: r[metric]) if cand else None


def main():
    rows = load()
    n_by = collections.Counter((r["model"], r["base"]) for r in rows if r["task"] == "binary")
    print(f"loaded {len(rows)} records\n")

    # ---- per-device best (cv + holdout) ----
    print("=== Best cv_f1_weighted per (model, base)  [holdout in brackets] ===")
    hdr = f"{'model':12}" + "".join(f"{b[:9]:>11}" for b in BASES) + f"{'mean':>8}"
    print(hdr)
    synth = {}
    for m in WMODELS:
        cells, cvs, hos = [], [], []
        for b in BASES:
            r = best_per(rows, m, b)
            if r:
                cells.append(f"{r['cv_f1_weighted']:.3f}[{r['holdout_f1_weighted']:.2f}]")
                cvs.append(r["cv_f1_weighted"]); hos.append(r["holdout_f1_weighted"])
            else:
                cells.append("    -      ")
        mean_cv = np.mean(cvs) if cvs else float("nan")
        synth[m] = {"per_dev_cv": mean_cv, "per_dev_ho": np.mean(hos) if hos else float("nan")}
        print(f"{DISP[m]:12}" + "".join(f"{c:>11}" for c in cells) + f"{mean_cv:8.3f}")

    # ---- thermometer sensitivity (3 thermometer models) ----
    print("\n=== Best cv_f1_weighted by thermometer (mean over bases, thermometer models) ===")
    thermos = ["linear", "distributive", "gaussian", "exponential", "logarithmic", "non-uniform"]
    print(f"{'thermometer':14}" + "".join(f"{DISP[m]:>13}" for m in ['wisard','cluswisard','bloomwisard']))
    for th in thermos:
        line = f"{th:14}"
        for m in ["wisard", "cluswisard", "bloomwisard"]:
            per_base = []
            for b in BASES:
                cand = [r for r in rows if r["model"] == m and r["base"] == b
                        and r["task"] == "binary" and r["cfg"].get("thermometer") == th]
                if cand:
                    per_base.append(max(c["cv_f1_weighted"] for c in cand))
            line += f"{np.mean(per_base):13.3f}" if per_base else f"{'-':>13}"
        print(line)

    # ---- combined ----
    print("\n=== Combined (cv_f1_weighted [holdout]) ===")
    for m in WMODELS:
        rb = best_per(rows, m, "combined", "binary")
        rm = best_per(rows, m, "combined", "multiclass")
        b = f"{rb['cv_f1_weighted']:.3f}[{rb['holdout_f1_weighted']:.2f}]" if rb else "-"
        mc = f"{rm['cv_f1_weighted']:.3f}[{rm['holdout_f1_weighted']:.2f}]" if rm else "-"
        print(f"{DISP[m]:12} bin={b:18} multi={mc}")

    # ---- coverage ----
    print("\n=== coverage (configs evaluated per model×base, binary) ===")
    for m in WMODELS:
        print(f"  {DISP[m]:12}", {b: n_by.get((m, b), 0) for b in BASES})


if __name__ == "__main__":
    main()

"""Boundary-extension PILOT: does pushing the swept grid past its current ceilings
buy F1 for the WiSARD family? Re-runs each model's grid-best cfg plus configs that
extend the binding capacity axes, under the IDENTICAL CV protocol (k=4 StratifiedKFold,
seed 42, on the 80% StratifiedShuffleSplit train). Writes incrementally.

Run from notebooks/toniot with the repo venv:  ../../venv/bin/python3 pilot_boundary.py
"""
import json, time, itertools, sys
from pathlib import Path
import numpy as np
from sklearn.model_selection import StratifiedShuffleSplit, StratifiedKFold

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE))
import run_wisard_grid as g
import run_wisard_family as rwf

SEED, TEST_SIZE, N_FOLDS = 42, 0.20, 4
OUT = HERE / "results" / "_consolidado" / "pilot_boundary.json"
DIFF_BASES = ["Modbus", "Weather", "GPS_Tracker", "Thermostat"]

# current grid-best cfg per (model, base)
def load_best():
    best = {}
    for f in (HERE / "results/_consolidado/grid").glob("wisard_grid_*.jsonl"):
        if "combined" in f.name:
            continue
        for line in f.read_text().splitlines():
            if not line.strip():
                continue
            d = json.loads(line)
            k = (d["model"], d["base"])
            if k not in best or d["cv_f1_weighted"] > best[k]["cv_f1_weighted"]:
                best[k] = d
    return best

BEST = load_best()

# extension cfg-lists per model: list of override dicts (merged onto the base cfg)
def wisard_exts(b):
    out = []
    for th in ["distributive", "gaussian"]:
        for bits in [32, 48, 64]:
            for addr in [16, 32, 48, 64]:
                out.append({"thermometer": th, "bits": bits, "address_size": addr,
                            "ignore_zero": b["cfg"]["ignore_zero"]})
    return out

def clus_exts(b):
    c = b["cfg"]
    return [{"thermometer": "distributive", "bits": bits, "address_size": addr,
             "min_score": c["min_score"], "threshold": c["threshold"], "limit": c["limit"]}
            for bits in [32, 48, 64] for addr in [16, 24, 32]]

def bloom_exts(b):
    c = b["cfg"]
    return [{"thermometer": "distributive", "bits": bits, "address_size": addr,
             "filter_size": c["filter_size"], "num_hashes": h}
            for bits in [32, 48, 64] for addr in [24, 32, 48] for h in [3, 4]]

def bthowen_exts(b):
    return [{"address_size": a, "num_bits": nb, "num_hashes": h, "bits_per_input": bpi}
            for a in [16, 20, 24] for nb in [2048, 4096] for h in [4] for bpi in [24, 32, 48]]

def uleen_exts(b):
    c = b["cfg"]
    return [{"bits_per_input": bpi, "filter_inputs": fi, "filter_entries": fe,
             "filter_hash_functions": 2, "n_submodels": ns, "epochs": ep,
             "batch_size": 64, "lr": c.get("lr", 0.01)}
            for bpi in [24, 32] for fi in [12] for fe in [128, 256]
            for ns in [3, 5] for ep in [20, 30]]

EXT = {"wisard": wisard_exts, "cluswisard": clus_exts, "bloomwisard": bloom_exts,
       "bthowen": bthowen_exts, "uleen": uleen_exts}
THERMO_TRIO = {"wisard", "cluswisard", "bloomwisard"}

def cv_f1w(model, base, cfg, X_df, y, folds, enc_cache):
    """Mean cv_f1_weighted over folds for one cfg (identical to grid path)."""
    preds_scores = []
    if model in THERMO_TRIO:
        key = (cfg["thermometer"], cfg["bits"])
        if key not in enc_cache:
            Xtr_full = X_df  # already the train matrix
            per = []
            for (ftr, fva) in folds:
                t = g.make_thermometer(cfg["thermometer"], cfg["bits"], Xtr_full[ftr])
                Xb = g.encode_matrix(t, Xtr_full)
                per.append((Xb, ftr, fva))
            enc_cache[key] = per
        per = enc_cache[key]
        f1s = []
        for (Xb, ftr, fva) in per:
            if cfg["address_size"] > Xb.shape[1]:
                return None  # invalid
            yp = rwf.fit_predict(model, Xb[ftr], y[ftr], Xb[fva], cfg)
            f1s.append(rwf.metrics(y[fva], yp, "binary")["f1_weighted"])
        return float(np.mean(f1s))
    else:
        X = X_df.astype(float)
        f1s = []
        for (ftr, fva) in folds:
            if model == "bthowen":
                yp = rwf.fit_predict_bthowen(X[ftr], y[ftr], X[fva], cfg)
            else:
                yp = rwf.fit_predict_uleen(X[ftr], y[ftr], X[fva], cfg)
            f1s.append(rwf.metrics(y[fva], yp, "binary")["f1_weighted"])
        return float(np.mean(f1s))

def append(row):
    data = json.loads(OUT.read_text()) if OUT.exists() else []
    data.append(row)
    OUT.write_text(json.dumps(data, indent=1))

def main():
    order = ["wisard", "cluswisard", "bloomwisard", "bthowen", "uleen"]
    bases_for = {m: (["Modbus", "Weather"] if m == "uleen" else DIFF_BASES) for m in order}
    for model in order:
        for base in bases_for[model]:
            b = BEST.get((model, base))
            if not b:
                continue
            X_df, y = rwf.prepare(base, "binary")
            Xall = X_df.values.astype(float)
            sss = StratifiedShuffleSplit(n_splits=1, test_size=TEST_SIZE, random_state=SEED)
            tr_full, _ = next(sss.split(Xall, y))
            Xtr, ytr = Xall[tr_full], y[tr_full]
            skf = StratifiedKFold(N_FOLDS, shuffle=True, random_state=SEED)
            folds = list(skf.split(Xtr, ytr))
            enc_cache = {}
            grid_best = b["cv_f1_weighted"]
            best_ext = {"f1": -1, "cfg": None}
            cfgs = EXT[model](b)
            t0 = time.time()
            for cfg in cfgs:
                try:
                    f1 = cv_f1w(model, base, cfg, Xtr, ytr, folds, enc_cache)
                except Exception as e:
                    print(f"  ! {model}/{base} {cfg}: {e}", flush=True)
                    continue
                if f1 is None:
                    continue
                if f1 > best_ext["f1"]:
                    best_ext = {"f1": f1, "cfg": cfg}
            row = {"model": model, "base": base, "grid_best_f1": round(grid_best, 4),
                   "grid_best_cfg": b["cfg"],
                   "ext_best_f1": round(best_ext["f1"], 4), "ext_best_cfg": best_ext["cfg"],
                   "delta": round(best_ext["f1"] - grid_best, 4),
                   "n_ext_cfgs": len(cfgs), "secs": round(time.time() - t0, 1)}
            append(row)
            print(f"{model:11s} {base:13s} grid={grid_best:.3f} -> ext={best_ext['f1']:.3f} "
                  f"(Δ{row['delta']:+.3f})  best_ext={best_ext['cfg']}  [{row['secs']}s]", flush=True)
    print("DONE", flush=True)

if __name__ == "__main__":
    main()

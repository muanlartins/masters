"""BIG grid search — WiSARD-family, paper-faithful protocol, expanded & harmonized.

Changes vs run_wisard_paper.py:
  * 6 UNSUPERVISED thermometers, uniform across the 3 thermometer models
    (WiSARD/ClusWiSARD/BloomWiSARD):
        linear (=SimpleThermometer), distributive, gaussian, exponential,
        logarithmic, non-uniform (=DynamicThermometer, per-feature bit budget
        allocated by dispersion, floor 2 bits).
    Dropped: stochastic (was distributive-without-optimize, a duplicate) and
    supervised (label-aware — breaks the unsupervised consistency of the set).
  * bits/feature swept ∈ {8,16,32} for all 3 thermometer models.
  * expanded + harmonized internal grids (address/min_score/threshold/limit/
    filter_size/num_hashes; BTHOWeN/ULEEN internal grids expanded).
  * ENCODING CACHE: the binary matrix for a given (thermometer,bits,fold) is
    built once and reused across every address/internal config AND across the
    3 thermometer models — the encoding (the expensive step) is amortized.
  * HELD-OUT TEST: besides the 4-fold CV mean, each config is also retrained on
    the full 80% train and evaluated on the untouched 20% test split.
  * one row PER CONFIG (not per fold): cv_{f1,f1_macro,f1_weighted}(+std) and
    holdout_{...}. Per-base shard files for safe parallel runs.

Protocol (identical to baselines_paper / wisard_paper):
  80/20 StratifiedShuffleSplit(seed=42) → k=4 StratifiedKFold on train.
  drop_temporal_leak always; NO clean_df (paper-faithful).

Usage:  python run_wisard_grid.py --base Fridge [--models wisard ...] [--quick]
Output: results/_consolidado/grid/wisard_grid_<base>.jsonl
"""
from __future__ import annotations

import os
# single-threaded math so N base-processes map cleanly to N cores (no oversubscription)
for _v in ("OMP_NUM_THREADS", "MKL_NUM_THREADS", "OPENBLAS_NUM_THREADS",
           "NUMEXPR_NUM_THREADS", "VECLIB_MAXIMUM_THREADS"):
    os.environ.setdefault(_v, "1")

import argparse, gc, json, sys, time, warnings
from pathlib import Path
from itertools import product

import numpy as np
from sklearn.model_selection import StratifiedKFold, StratifiedShuffleSplit

warnings.filterwarnings("ignore")

PROJ = Path("/Users/muanlartins/repos/masters")
OUT_DIR = PROJ / "notebooks" / "toniot" / "results" / "_consolidado" / "grid"
OUT_DIR.mkdir(parents=True, exist_ok=True)

sys.path.insert(0, str(PROJ / "notebooks" / "toniot"))
import consolidado_utils as cu
import wisardpkg as wp
import run_wisard_family as rwf  # prepare, fit_predict, fit_predict_bthowen/uleen, metrics
try:
    import torch; torch.set_num_threads(1)
except Exception:
    pass

SEED = 42
N_FOLDS = 4
TEST_SIZE = 0.20

THERMOS = ["linear", "distributive", "gaussian", "exponential", "logarithmic", "non-uniform"]
# Extended bits range (2026-06: boundary-fair re-sweep). The original [8,16,32]
# left F1 on the table on structured bases (best configs hit bits=32); 48/64
# add resolution. See pilot_boundary.py.
THERMO_BITS = [8, 16, 32, 48, 64]

# ---- internal grids (thermo/bits handled separately) -----------------------
# Address-size ceilings UNIFIED to 64 across the thermometer trio (was 32/16/24
# for wisard/clus/bloom — an inconsistent cap that handicapped ClusWiSARD; see
# the boundary pilot, ClusWiSARD Modbus 0.603->0.879 once raised to 32). The
# address<=n_bits guard prunes invalid combos naturally.
WISARD_INTERNAL = {"address_size": [2, 4, 8, 16, 32, 48, 64], "ignore_zero": [True, False]}
CLUS_INTERNAL   = {"address_size": [4, 8, 16, 24, 32, 48, 64], "min_score": [0.1, 0.2],
                   "threshold": [10, 100], "limit": [5, 20]}
BLOOM_INTERNAL  = {"address_size": [8, 16, 24, 32, 48, 64], "filter_size": [256, 1024, 4096],
                   "num_hashes": [2, 3, 4]}
# raw-X models (own internal encoder; no external thermometer)
BTHOWEN_GRID = {"address_size": [6, 12, 16, 20, 24], "num_bits": [128, 256, 512, 1024, 2048, 4096],
                "num_hashes": [2, 4, 6], "bits_per_input": [4, 8, 16, 24, 32, 48]}
ULEEN_GRID   = {"bits_per_input": [4, 8, 16, 24, 32], "filter_inputs": [3, 6, 12],
                "filter_entries": [16, 64, 128, 256], "filter_hash_functions": [2],
                "n_submodels": [1, 3, 5], "epochs": [5, 10, 20], "lr": [0.001, 0.01],
                "batch_size": [64]}

THERMO_MODELS = {"wisard": WISARD_INTERNAL, "cluswisard": CLUS_INTERNAL,
                 "bloomwisard": BLOOM_INTERNAL}
RAW_MODELS = {"bthowen": BTHOWEN_GRID, "uleen": ULEEN_GRID}

# guard: skip ClusWiSARD configs in the known-explosive region (minutes/fit)
def _too_expensive(model, cfg):
    return model == "cluswisard" and cfg.get("address_size", 0) >= 16 and cfg.get("limit", 0) >= 20


def _grid(d):
    keys = list(d)
    for vals in product(*[d[k] for k in keys]):
        yield dict(zip(keys, vals))


# ---- thermometer construction (renamed + non-uniform) ----------------------

def _allocate_nonuniform(X_fit, base_bits):
    """Per-feature bit budget ∝ dispersion (std), floor 2, total = base_bits*n_feat."""
    nfeat = X_fit.shape[1]
    budget = base_bits * nfeat
    floor = min(2, base_bits)
    w = X_fit.std(axis=0)
    if not np.isfinite(w).all() or w.sum() <= 0:
        w = np.ones(nfeat)
    w = w + 1e-9
    extra = budget - floor * nfeat
    if extra <= 0:
        return [max(1, base_bits)] * nfeat
    alloc = floor + np.floor(extra * w / w.sum()).astype(int)
    rem = int(budget - alloc.sum())
    order = np.argsort(-w)
    for i in range(max(rem, 0)):
        alloc[order[i % nfeat]] += 1
    return [int(a) for a in alloc]


def make_thermometer(kind, bits, X_fit):
    """X_fit: 2D ndarray of TRAIN rows only (thermometer fit on train)."""
    if kind == "linear":
        lo, hi = float(X_fit.min()), float(X_fit.max())
        if hi <= lo:
            hi = lo + 1e-6
        return wp.SimpleThermometer(bits, lo, hi)
    if kind == "distributive":
        t = wp.DistributiveThermometer(bits); t.fit(X_fit.tolist()); return t
    if kind == "gaussian":
        t = wp.GaussianThermometer(bits); t.fit(X_fit.tolist()); return t
    if kind == "exponential":
        t = wp.ExponentialThermometer(bits); t.fit(X_fit.tolist()); return t
    if kind == "logarithmic":
        t = wp.LogarithmicThermometer(bits); t.fit(X_fit.tolist()); return t
    if kind == "non-uniform":
        sizes = _allocate_nonuniform(X_fit, bits)
        lo = X_fit.min(axis=0).astype(float)
        hi = X_fit.max(axis=0).astype(float)
        hi = np.where(hi <= lo, lo + 1e-6, hi)
        return wp.DynamicThermometer(sizes, lo.tolist(), hi.tolist())
    raise ValueError(kind)


def encode_matrix(t, X):
    """Transform every row of X (2D ndarray) with fitted thermometer t -> int8 matrix."""
    rows = []
    for i in range(len(X)):
        out = t.transform(X[i].tolist())
        rows.append([int(out[j]) for j in range(out.size())])
    return np.array(rows, dtype=np.int8)


# ---- per-base driver -------------------------------------------------------

def done_keys(shard):
    if not shard.exists():
        return set()
    ks = set()
    for ln in shard.read_text().splitlines():
        if ln.strip():
            d = json.loads(ln)
            ks.add((d["model"], d["task"], json.dumps(d["cfg"], sort_keys=True)))
    return ks


def cv_holdout_metrics(cv_preds, ho_pred, y, cv_va_idx, ho_te_y, task):
    """Aggregate per-fold preds into cv mean/std + holdout metrics."""
    keys = ["f1", "f1_macro", "f1_weighted"]
    per = {k: [] for k in keys}
    for pred, va in zip(cv_preds, cv_va_idx):
        m = rwf.metrics(y[va], pred, task)
        for k in keys:
            per[k].append(m[k])
    out = {}
    for k in keys:
        out[f"cv_{k}"] = float(np.mean(per[k]))
        out[f"cv_{k}_std"] = float(np.std(per[k]))
    hm = rwf.metrics(ho_te_y, ho_pred, task)
    for k in keys:
        out[f"holdout_{k}"] = float(hm[k])
    return out


def run_base(base, models, quick=False):
    shard = OUT_DIR / f"wisard_grid_{base}.jsonl"
    done = done_keys(shard)
    print(f"[{base}] resuming, {len(done)} done", flush=True)

    X_df, y = rwf.prepare(base, "binary")
    Xall = X_df.values.astype(float)
    sss = StratifiedShuffleSplit(n_splits=1, test_size=TEST_SIZE, random_state=SEED)
    tr_full, te_ho = next(sss.split(Xall, y))
    Xtr_full, ytr_full = Xall[tr_full], y[tr_full]
    Xte_ho, yte_ho = Xall[te_ho], y[te_ho]
    skf = StratifiedKFold(N_FOLDS, shuffle=True, random_state=SEED)
    folds = list(skf.split(Xtr_full, ytr_full))

    therm_models = [m for m in models if m in THERMO_MODELS]
    raw_models = [m for m in models if m in RAW_MODELS]

    with shard.open("a") as f_out:
        # ---- thermometer models: cache encoding per (thermo,bits,fold) ----
        for thermo in (THERMOS if not quick else THERMOS[:2]):
            for bits in (THERMO_BITS if not quick else [16]):
                t0 = time.time()
                # encode each fold (fit on fold-train) + holdout (fit on full train)
                fold_enc = []
                for (ftr, fva) in folds:
                    t = make_thermometer(thermo, bits, Xtr_full[ftr])
                    Xb = encode_matrix(t, Xtr_full)
                    fold_enc.append((Xb, ftr, fva))
                t_ho = make_thermometer(thermo, bits, Xtr_full)
                Xb_tr_ho = encode_matrix(t_ho, Xtr_full)
                Xb_te_ho = encode_matrix(t_ho, Xte_ho)
                enc_s = time.time() - t0
                for model in therm_models:
                    for ic in _grid(THERMO_MODELS[model]):
                        cfg = {"thermometer": thermo, "bits": bits, **ic}
                        ck = (model, "binary", json.dumps(cfg, sort_keys=True))
                        if ck in done or _too_expensive(model, cfg):
                            continue
                        try:
                            t0 = time.time()
                            cv_preds = []
                            ok = True
                            for (Xb, ftr, fva) in fold_enc:
                                if cfg["address_size"] > Xb.shape[1]:
                                    ok = False; break
                                cv_preds.append(rwf.fit_predict(model, Xb[ftr], ytr_full[ftr], Xb[fva], cfg))
                            if not ok:
                                continue  # invalid (address>n_bits)
                            ho_pred = rwf.fit_predict(model, Xb_tr_ho, ytr_full, Xb_te_ho, cfg)
                            mets = cv_holdout_metrics(cv_preds, ho_pred, ytr_full,
                                                       [fva for (_, _, fva) in fold_enc], yte_ho, "binary")
                            rec = {"model": model, "base": base, "task": "binary", "cfg": cfg,
                                   "n_bits": int(fold_enc[0][0].shape[1]),
                                   "elapsed_s": round(time.time() - t0, 3), **mets}
                            f_out.write(json.dumps(rec) + "\n"); f_out.flush()
                        except Exception as e:
                            print(f"FAIL {model}/{base}/{cfg}: {e}", flush=True)
                        finally:
                            gc.collect()
                print(f"  [{base}] {thermo}/{bits}b encoded in {enc_s:.1f}s, models done", flush=True)
                del fold_enc, Xb_tr_ho, Xb_te_ho; gc.collect()

        # ---- raw-X models (bthowen/uleen) ----
        for model in raw_models:
            grid = list(_grid(RAW_MODELS[model]))
            if quick:
                grid = grid[:4]
            print(f"  [{base}] {model}: {len(grid)} cfgs", flush=True)
            fp = rwf.fit_predict_bthowen if model == "bthowen" else rwf.fit_predict_uleen
            for cfg in grid:
                ck = (model, "binary", json.dumps(cfg, sort_keys=True))
                if ck in done:
                    continue
                try:
                    t0 = time.time()
                    cv_preds = []
                    for (ftr, fva) in folds:
                        cv_preds.append(fp(Xtr_full[ftr], ytr_full[ftr], Xtr_full[fva], cfg))
                    ho_pred = fp(Xtr_full, ytr_full, Xte_ho, cfg)
                    mets = cv_holdout_metrics(cv_preds, ho_pred, ytr_full,
                                               [fva for (_, fva) in folds], yte_ho, "binary")
                    rec = {"model": model, "base": base, "task": "binary", "cfg": cfg,
                           "n_bits": None, "elapsed_s": round(time.time() - t0, 3), **mets}
                    f_out.write(json.dumps(rec) + "\n"); f_out.flush()
                except Exception as e:
                    print(f"FAIL {model}/{base}/{cfg}: {e}", flush=True)
                finally:
                    gc.collect()
    print(f"[{base}] done.", flush=True)


def best_cfg_per_model(models):
    """From per-device shards, pick each model's cfg with the highest mean
    cv_f1_weighted averaged over the bases in which it appears."""
    import collections
    agg = collections.defaultdict(lambda: collections.defaultdict(list))  # model -> cfgkey -> [f1]
    cfgmap = {}
    for shard in OUT_DIR.glob("wisard_grid_*.jsonl"):
        if "combined" in shard.name:
            continue
        for ln in shard.read_text().splitlines():
            if not ln.strip():
                continue
            d = json.loads(ln)
            if d["model"] not in models or d["task"] != "binary":
                continue
            ck = json.dumps(d["cfg"], sort_keys=True)
            agg[d["model"]][ck].append(d["cv_f1_weighted"])
            cfgmap[ck] = d["cfg"]
    best = {}
    for model, cfgs in agg.items():
        # require coverage of most bases to avoid a fluke on one base
        ranked = sorted(cfgs.items(), key=lambda kv: (len(kv[1]) >= 5, np.mean(kv[1])), reverse=True)
        best[model] = cfgmap[ranked[0][0]]
    return best


def run_combined(models):
    """Combined binary + multiclass using each model's per-device best cfg."""
    shard = OUT_DIR / "wisard_grid_combined.jsonl"
    done = done_keys(shard)
    best = best_cfg_per_model(models)
    print(f"[combined] best cfgs: { {m: best[m] for m in best} }", flush=True)
    with shard.open("a") as f_out:
        for task in ("binary", "multiclass"):
            X_df, y = rwf.prepare("combined", task)
            Xall = X_df.values.astype(float)
            sss = StratifiedShuffleSplit(n_splits=1, test_size=TEST_SIZE, random_state=SEED)
            tr_full, te_ho = next(sss.split(Xall, y))
            Xtr_full, ytr_full = Xall[tr_full], y[tr_full]
            Xte_ho, yte_ho = Xall[te_ho], y[te_ho]
            folds = list(StratifiedKFold(N_FOLDS, shuffle=True, random_state=SEED).split(Xtr_full, ytr_full))
            for model in models:
                cfg = best[model]
                ck = (model, task, json.dumps(cfg, sort_keys=True))
                if ck in done:
                    continue
                try:
                    t0 = time.time()
                    if model in THERMO_MODELS:
                        cv_preds = []
                        for (ftr, fva) in folds:
                            t = make_thermometer(cfg["thermometer"], cfg["bits"], Xtr_full[ftr])
                            Xb = encode_matrix(t, Xtr_full)
                            cv_preds.append(rwf.fit_predict(model, Xb[ftr], ytr_full[ftr], Xb[fva], cfg))
                        t = make_thermometer(cfg["thermometer"], cfg["bits"], Xtr_full)
                        ho_pred = rwf.fit_predict(model, encode_matrix(t, Xtr_full), ytr_full,
                                                  encode_matrix(t, Xte_ho), cfg)
                    else:
                        fp = rwf.fit_predict_bthowen if model == "bthowen" else rwf.fit_predict_uleen
                        cv_preds = [fp(Xtr_full[ftr], ytr_full[ftr], Xtr_full[fva], cfg) for (ftr, fva) in folds]
                        ho_pred = fp(Xtr_full, ytr_full, Xte_ho, cfg)
                    mets = cv_holdout_metrics(cv_preds, ho_pred, ytr_full,
                                               [fva for (_, fva) in folds], yte_ho, task)
                    rec = {"model": model, "base": "combined", "task": task, "cfg": cfg,
                           "n_bits": None, "elapsed_s": round(time.time() - t0, 3), **mets}
                    f_out.write(json.dumps(rec) + "\n"); f_out.flush()
                    print(f"  combined {model:11s} {task[:5]} cv_w={mets['cv_f1_weighted']:.3f} "
                          f"ho_w={mets['holdout_f1_weighted']:.3f} t={rec['elapsed_s']}s", flush=True)
                except Exception as e:
                    print(f"FAIL combined/{model}/{task}: {e}", flush=True)
                finally:
                    gc.collect()
    print("[combined] done.", flush=True)


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--base", help="per-device base name")
    ap.add_argument("--combined", action="store_true", help="run combined from per-device best cfgs")
    ap.add_argument("--models", nargs="+",
                    default=["wisard", "cluswisard", "bloomwisard", "bthowen", "uleen"])
    ap.add_argument("--quick", action="store_true", help="tiny grid for smoke test")
    args = ap.parse_args()
    if args.combined:
        run_combined(args.models)
    else:
        run_base(args.base, args.models, quick=args.quick)


if __name__ == "__main__":
    main()

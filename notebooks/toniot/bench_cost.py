"""Cost micro-benchmark — consistent time + memory for the cost/Pareto story.

Motivation: the big grid's `elapsed_s` is NOT a per-fit time (it sums 4 CV
folds + 1 holdout fit-predict per config) and EXCLUDES the cached thermometer
encoding for the trio while INCLUDING it for BTHOWeN/ULEEN. The baselines'
`elapsed_s` is a single fold's fit. So neither the within-family nor the
cross-baseline time comparison is apples-to-apples. This script re-measures
everything under ONE harness.

For each model at its SELECTED best cfg (per-device best from the grid, via
best_cfg_per_model) it measures, per base, on the SAME 80/20 split (seed 42):
  * train_time_s    — single fit on the full 80% train, INCLUDING encoding
  * infer_us_sample — inference latency per held-out sample, INCLUDING encoding
  * mem_bytes        — trained-model footprint (see mem_metric for the definition)

Memory metric — UNIFIED deployed-state yardstick (deployedSizeBytes, 2026-06):
  * wisard/cluswisard : deployedSizeBytes() = sum over RAMs of (#distinct seen
                        addresses) * ceil(tupleSize/8) — the minimal lossless
                        seen-set (no false positives). getsizeof() kept as audit.
  * bloomwisard       : deployedSizeBytes() = numRAMs*numBits/8 — deployed bit-table.
  * bthowen           : model_size_bytes()    — deployed bit-table.
  * uleen             : deployed_size_bytes() — deployed bit-table.
  All five WiSARD-family rows are now the deployable learned state on one
  comparable axis. sklearn baselines: len(pickle.dumps(clf)) (serialized);
  LSTM: param_count*4 (float32) — these stay separate (different representation).
The `impl` field records C++ vs pure-Python so the time/latency caveat (BTHOWeN/
ULEEN are pure-Python reference impls) is backed by the data.

Baselines (LR/LDA/kNN/RF/CART/NB/SVM/LSTM) are timed too so the cross-family
"N x faster than LSTM" claim rests on identically-measured numbers.

Usage:  python bench_cost.py            # all bases, all models
Output: results/_consolidado/bench_cost.json   (list of per (model,base) rows)
"""
from __future__ import annotations

import os
for _v in ("OMP_NUM_THREADS", "MKL_NUM_THREADS", "OPENBLAS_NUM_THREADS",
           "NUMEXPR_NUM_THREADS", "VECLIB_MAXIMUM_THREADS"):
    os.environ.setdefault(_v, "1")

import json, pickle, sys, time, warnings
from pathlib import Path

import numpy as np
from sklearn.model_selection import StratifiedShuffleSplit

warnings.filterwarnings("ignore")

PROJ = Path("/Users/muanlartins/repos/masters")
TONIOT = PROJ / "notebooks" / "toniot"
OUT = TONIOT / "results" / "_consolidado" / "bench_cost.json"

sys.path.insert(0, str(TONIOT))
import consolidado_utils as cu
import wisardpkg as wp
import run_wisard_grid as g
import run_wisard_family as rwf
import run_baselines_paper as bp
try:
    import torch; torch.set_num_threads(1)
except Exception:
    pass

SEED = 42
TEST_SIZE = 0.20
WISARD_MODELS = ["wisard", "cluswisard", "bloomwisard", "bthowen", "uleen"]
BASELINES = ["LR", "LDA", "kNN", "RF", "CART", "NB", "SVM", "LSTM"]


def split(X, y):
    sss = StratifiedShuffleSplit(n_splits=1, test_size=TEST_SIZE, random_state=SEED)
    tr, te = next(sss.split(X, y))
    return X[tr], y[tr], X[te], y[te]


# ---- WiSARD-family ---------------------------------------------------------

def _ds(Xb, y=None):
    ds = wp.DataSet()
    if y is None:
        for row in Xb.tolist():
            ds.add(row)
    else:
        for row, lab in zip(Xb.tolist(), y):
            ds.add(row, str(int(lab)))
    return ds


def bench_trio(model, cfg, Xtr, ytr, Xte):
    """Train time includes thermo-fit + encode_train + clf.train.
    Inference time includes encode_test + classify."""
    t0 = time.time()
    t = g.make_thermometer(cfg["thermometer"], cfg["bits"], Xtr)
    Xb_tr = g.encode_matrix(t, Xtr)
    if model == "wisard":
        clf = wp.Wisard(cfg["address_size"], ignoreZero=cfg["ignore_zero"], bleachingActivated=True)
    elif model == "cluswisard":
        clf = wp.ClusWisard(cfg["address_size"], cfg["min_score"], cfg["threshold"], cfg["limit"])
    else:
        clf = wp.BloomWisard(addressSize=cfg["address_size"], capacity=cfg["filter_size"],
                             numberOfHashes=cfg["num_hashes"], bleachingActivated=True)
    clf.train(_ds(Xb_tr, ytr))
    train_s = time.time() - t0

    t1 = time.time()
    Xb_te = g.encode_matrix(t, Xte)
    pred = clf.classify(_ds(Xb_te))
    infer_s = time.time() - t1
    pred = np.array([int(p) for p in pred])

    if model == "bloomwisard":
        # Unified deployed metric: numRAMs*numBits/8 (the Bloom bit-table).
        # getsizeof() (the in-memory counting filter) kept for audit.
        row = {"mem_bytes": int(clf.deployedSizeBytes()),
               "mem_metric": "deployed bit-table",
               "mem_getsizeof": int(clf.getsizeof()),
               "num_rams": int(clf.getNumberOfRAMS()), "num_bits": int(clf.getNumBits()),
               "impl": "C++"}
    else:
        # Wisard/ClusWisard: deployedSizeBytes() = the minimal lossless seen-set,
        # sum over RAMs of (#distinct seen addresses) * ceil(tupleSize/8). On the
        # SAME yardstick as the Bloom/BTHOWeN/ULEEN bit-table. getsizeof() (the
        # in-memory sparse footprint, with std::map overhead) kept for audit.
        row = {"mem_bytes": int(clf.deployedSizeBytes()),
               "mem_metric": "deployed seen-set",
               "mem_getsizeof": int(clf.getsizeof()), "impl": "C++"}
    return train_s, infer_s, pred, row


def bench_bthowen(cfg, Xtr, ytr, Xte):
    from wisardpkg.models import BTHOWeN
    t0 = time.time()
    clf = BTHOWeN(addressSize=cfg["address_size"], numBits=cfg["num_bits"],
                  numHashes=cfg["num_hashes"], bitsPerInput=cfg["bits_per_input"])
    clf.fit(Xtr.tolist(), [int(v) for v in ytr])
    train_s = time.time() - t0
    t1 = time.time()
    pred = np.array([int(p) for p in clf.predict(Xte.tolist())])
    infer_s = time.time() - t1
    return train_s, infer_s, pred, {"mem_bytes": int(clf.model_size_bytes()),
                                    "mem_metric": "deployed bit-table", "impl": "Python"}


def bench_uleen(cfg, Xtr, ytr, Xte):
    from wisardpkg.models import ULEENClassifier
    t0 = time.time()
    clf = ULEENClassifier(bits_per_input=cfg["bits_per_input"], filter_inputs=cfg["filter_inputs"],
                          filter_entries=cfg["filter_entries"],
                          filter_hash_functions=cfg["filter_hash_functions"],
                          n_submodels=cfg["n_submodels"], epochs=cfg["epochs"],
                          batch_size=cfg["batch_size"], lr=cfg.get("lr", 0.01))
    clf.fit(Xtr, ytr)
    train_s = time.time() - t0
    t1 = time.time()
    pred = np.array([int(p) for p in clf.predict(Xte)])
    infer_s = time.time() - t1
    return train_s, infer_s, pred, {"mem_bytes": int(clf.deployed_size_bytes()),
                                    "mem_metric": "deployed bit-table", "impl": "Python"}


# ---- baselines -------------------------------------------------------------

def bench_baseline(name, Xtr, ytr, Xte):
    if name == "LSTM":
        import torch
        t0 = time.time()
        pred = bp.fit_predict_lstm(Xtr, ytr, Xte, int(max(ytr)) + 1, "binary")
        train_infer_s = time.time() - t0
        # LSTM time is reported as a single train+infer block (dominated by train)
        return train_infer_s, None, pred, {"mem_bytes": None, "mem_metric": "n/a", "impl": "PyTorch"}
    eff = "SVM_LINEAR" if (name == "SVM" and len(Xtr) > 50_000) else name
    clf = bp.build_model(eff, "binary")
    t0 = time.time(); clf.fit(Xtr, ytr); train_s = time.time() - t0
    t1 = time.time(); pred = clf.predict(Xte); infer_s = time.time() - t1
    try:
        mem = len(pickle.dumps(clf))
    except Exception:
        mem = None
    return train_s, infer_s, pred, {"mem_bytes": mem, "mem_metric": "pickle (serialized)", "impl": "sklearn"}


def f1w(y_true, y_pred):
    from sklearn.metrics import f1_score
    return float(f1_score(y_true, y_pred, average="weighted", zero_division=0))


def main():
    best = g.best_cfg_per_model(WISARD_MODELS)
    print("best cfgs:", json.dumps(best), flush=True)
    rows = []
    for base in cu.CSVS:
        # WiSARD-family on the grid's prepare()
        Xdf, y = rwf.prepare(base, "binary")
        Xtr, ytr, Xte, yte = split(Xdf.values.astype(float), y)
        for model in WISARD_MODELS:
            cfg = best[model]
            try:
                if model in ("wisard", "cluswisard", "bloomwisard"):
                    tr_s, inf_s, pred, mem = bench_trio(model, cfg, Xtr, ytr, Xte)
                elif model == "bthowen":
                    tr_s, inf_s, pred, mem = bench_bthowen(cfg, Xtr, ytr, Xte)
                else:
                    tr_s, inf_s, pred, mem = bench_uleen(cfg, Xtr, ytr, Xte)
                rows.append({"model": model, "base": base, "family": "wisard",
                             "train_s": round(tr_s, 4),
                             "infer_us_sample": round(inf_s / len(Xte) * 1e6, 2) if inf_s else None,
                             "f1_holdout": round(f1w(yte, pred), 4),
                             "n_train": int(len(Xtr)), "n_test": int(len(Xte)),
                             "cfg": cfg, **mem})
                print(f"  {base:13s} {model:11s} train={tr_s:7.3f}s mem={mem['mem_bytes']} ({mem['mem_metric']})", flush=True)
            except Exception as e:
                print(f"FAIL {model}/{base}: {e}", flush=True)

        # baselines on the baseline prepare()
        Xb, yb = bp.prepare_per_device(base)
        Xtrb, ytrb, Xteb, yteb = split(Xb, yb)
        for name in BASELINES:
            try:
                tr_s, inf_s, pred, mem = bench_baseline(name, Xtrb, ytrb, Xteb)
                rows.append({"model": name, "base": base, "family": "baseline",
                             "train_s": round(tr_s, 4),
                             "infer_us_sample": round(inf_s / len(Xteb) * 1e6, 2) if inf_s else None,
                             "f1_holdout": round(f1w(yteb, pred), 4),
                             "n_train": int(len(Xtrb)), "n_test": int(len(Xteb)),
                             "cfg": None, **mem})
                print(f"  {base:13s} {name:11s} train={tr_s:7.3f}s mem={mem['mem_bytes']} ({mem['mem_metric']})", flush=True)
            except Exception as e:
                print(f"FAIL {name}/{base}: {e}", flush=True)

    OUT.write_text(json.dumps(rows, indent=1))
    print(f"\nwrote {len(rows)} rows -> {OUT}", flush=True)


if __name__ == "__main__":
    main()

"""Sweep dos 5 modelos WiSARD-family — k-fold 5.

Modelos: WiSARD, ClusWiSARD, BloomWiSARD, BTHOWeN, ULEEN.

Tarefas:
  - per-device BINÁRIO (7 bases × normal vs ataque) — grid moderado
  - combined MULTI-CLASSE (combined_IoT_dataset × 9 classes) — config única
    por modelo (combined é GRANDE: 261k rows × 17 features)

Cleaning: clean_df unificado SEMPRE (foco em comparação honesta).
Sem-cleaning fica como contrafactual nos baselines (§3 do notebook).

Resultados em: results/_consolidado/wisard_family.jsonl
"""
from __future__ import annotations

import argparse, gc, json, sys, time, warnings
from pathlib import Path
from itertools import product

import numpy as np
import pandas as pd
from sklearn.model_selection import StratifiedKFold
from sklearn.preprocessing import LabelEncoder, MinMaxScaler

warnings.filterwarnings("ignore")

PROJ = Path("/Users/muanlartins/repos/masters")
DATA_DIR = PROJ / "data" / "toniot"
OUT_DIR = PROJ / "notebooks" / "toniot" / "results" / "_consolidado"
OUT_DIR.mkdir(parents=True, exist_ok=True)
OUT_FILE = OUT_DIR / "wisard_family.jsonl"

sys.path.insert(0, str(PROJ / "notebooks" / "toniot"))
import consolidado_utils as cu
import wisardpkg as wp
from wisardpkg.models import BTHOWeN, ULEENClassifier

SEED = 42
N_FOLDS = 5

# ---- per-device binary grids -----------------------------------------------

WISARD_GRID = {
    # 7 termômetros: 4 da wisardpkg padrão (simple, distributive, gaussian, exponential) +
    # 2 nossos (logarithmic, stochastic) + 1 supervisionado (uses labels)
    "thermometer": ["simple", "distributive", "gaussian", "logarithmic",
                     "exponential", "stochastic", "supervised"],
    "bits": [16],
    "address_size": [2, 4, 8, 16],
    "ignore_zero": [True, False],
}
CLUS_GRID = {
    # 3 termômetros (distributive, gaussian, logarithmic) — orçamento contido
    "thermometer": ["distributive", "gaussian", "logarithmic"],
    "bits": [16],
    "address_size": [4, 8],
    "min_score": [0.1, 0.15],
    "threshold": [10, 100],
    "limit": [10, 20],
}
BLOOM_GRID = {
    # 3 termômetros (distributive, gaussian, logarithmic) — orçamento contido
    "thermometer": ["distributive", "gaussian", "logarithmic"],
    "bits": [16, 32],
    "address_size": [8, 16, 24],
    "filter_size": [256, 1024],
    "num_hashes": [2, 3],
}
BTHOWEN_GRID = {
    # G2 ∪ G3 ∪ G1: cobertura completa de bits_per_input (G2: 4-32)
    "address_size": [6, 12],
    "num_bits": [128, 256, 512, 1024],
    "num_hashes": [2, 4],
    "bits_per_input": [4, 8, 16, 24],
}
ULEEN_GRID = {
    # G2 dispatch device-specific: bits_per_input ∈ {8, 16, 24}. Cobertura completa
    # [4, 8, 16, 24]. filter_inputs / filter_entries / lr de G2.
    "bits_per_input": [4, 8, 16, 24],
    "filter_inputs": [3, 12],
    "filter_entries": [16, 128],
    "filter_hash_functions": [2],
    "n_submodels": [3],
    "epochs": [10],
    "lr": [0.001, 0.01],
    "batch_size": [64],
}

# ---- G2's per-device ULEEN dispatch (BITS_RESOLUTION) ---------------------
G2_ULEEN_DEVICE_BITS = {
    "Fridge": 8, "Thermostat": 8,
    "Weather": 16, "Modbus": 16,
    "GPS_Tracker": 24, "Motion_Light": 24, "Garage_Door": 24,
}

# ---- single-cfg recipes for combined multi-class (expensive) ---------------

COMBINED_CFGS = {
    "wisard":      {"thermometer":"distributive", "bits":16, "address_size":8,  "ignore_zero":True},
    "cluswisard":  {"thermometer":"distributive", "bits":16, "address_size":8,
                    "min_score":0.1, "threshold":10, "limit":10},
    "bloomwisard": {"thermometer":"distributive", "bits":16, "address_size":8,
                    "filter_size":1024, "num_hashes":2},
    "bthowen":     {"address_size":6, "num_bits":256, "num_hashes":2, "bits_per_input":8},
    "uleen":       {"bits_per_input":4, "filter_inputs":12, "filter_entries":128,
                    "filter_hash_functions":2, "n_submodels":1, "epochs":5, "batch_size":128},
}


def prepare(base: str, task: str):
    """Retorna X_df, y. base in CSVS or 'combined'. task in {binary, multiclass}.

    Pipeline paper-faithful: apenas drop_temporal + LabelEncoder cru.
    Sem clean_df (que mistura '0'/'false' indevidamente — ver §3.5 do notebook).
    """
    if base == "combined":
        df = cu.build_combined_dataset(apply_cleaning=False, drop_temporal=True)
    else:
        df = pd.read_csv(DATA_DIR / cu.CSVS[base])
        df = cu.drop_temporal_leak(df)
    if task == "binary":
        y = df["label"].astype(int).values
    else:
        y = LabelEncoder().fit_transform(df["type"].astype(str))
    X_df = df.drop(columns=["label", "type"])
    for col in X_df.columns:
        if not pd.api.types.is_numeric_dtype(X_df[col]):
            X_df[col] = LabelEncoder().fit_transform(X_df[col].astype(str))
    X_df = X_df.fillna(0).astype(float)
    X_df.iloc[:, :] = MinMaxScaler().fit_transform(X_df.values)
    return X_df, y


def encode_X(X_df, fit_idx, thermo_kind, bits, y_fit=None):
    """Codifica X via termômetro escolhido.

    Suporta: distributive, gaussian, logarithmic, exponential (precisam fit),
    simple (precisa min/max do fit_data), stochastic (precisa fit),
    supervised (precisa fit + labels via y_fit).
    """
    fit_data = X_df.iloc[fit_idx]
    if thermo_kind == "distributive":
        t = wp.DistributiveThermometer(bits)
        t.fit(fit_data.values.tolist())
    elif thermo_kind == "gaussian":
        t = wp.GaussianThermometer(bits)
        t.fit(fit_data.values.tolist())
    elif thermo_kind == "logarithmic":
        t = wp.LogarithmicThermometer(bits)
        t.fit(fit_data.values.tolist())
    elif thermo_kind == "exponential":
        t = wp.ExponentialThermometer(bits)
        t.fit(fit_data.values.tolist())
    elif thermo_kind == "simple":
        # SimpleThermometer precisa (n_bits, min, max) — usa range global do fit_data
        lo = float(fit_data.values.min()); hi = float(fit_data.values.max())
        if hi == lo: hi = lo + 1e-6
        t = wp.SimpleThermometer(bits, lo, hi)
        # no .fit() needed
    elif thermo_kind == "stochastic":
        t = wp.StochasticThermometer(bits)
        t.fit(fit_data.values.tolist())
    elif thermo_kind == "supervised":
        if y_fit is None:
            raise ValueError("supervised thermometer requires y_fit (labels)")
        t = wp.SupervisedThermometer(bits)
        t.fit(fit_data.values.tolist(), [str(int(yi)) for yi in y_fit])
    else:
        raise ValueError(thermo_kind)
    rows = []
    size = bits * X_df.shape[1]
    for i in range(len(X_df)):
        out = t.transform(list(X_df.iloc[i].values))
        rows.append([int(out[j]) for j in range(size)])
    return np.array(rows, dtype=np.int8), size


def _make_dataset(Xb, y=None):
    ds = wp.DataSet()
    rows = Xb.tolist()
    if y is None:
        for row in rows: ds.add(row)
    else:
        for row, label in zip(rows, y): ds.add(row, str(int(label)))
    return ds


def fit_predict(model_name, Xb_tr, y_tr, Xb_te, cfg):
    if model_name == "wisard":
        clf = wp.Wisard(cfg["address_size"], ignoreZero=cfg["ignore_zero"],
                        bleachingActivated=True)
    elif model_name == "cluswisard":
        clf = wp.ClusWisard(cfg["address_size"], cfg["min_score"],
                            cfg["threshold"], cfg["limit"])
    elif model_name == "bloomwisard":
        clf = wp.BloomWisard(addressSize=cfg["address_size"], capacity=cfg["filter_size"],
                             numberOfHashes=cfg["num_hashes"], bleachingActivated=True)
    else:
        raise ValueError(model_name)
    clf.train(_make_dataset(Xb_tr, y_tr))
    pred = clf.classify(_make_dataset(Xb_te))
    return np.array([int(p) for p in pred])


def fit_predict_bthowen(X_tr, y_tr, X_te, cfg):
    clf = BTHOWeN(addressSize=cfg["address_size"], numBits=cfg["num_bits"],
                  numHashes=cfg["num_hashes"], bitsPerInput=cfg["bits_per_input"])
    clf.fit(X_tr.tolist(), [int(v) for v in y_tr])
    pred = clf.predict(X_te.tolist())
    return np.array([int(p) for p in pred])


def fit_predict_uleen(X_tr, y_tr, X_te, cfg):
    clf = ULEENClassifier(
        bits_per_input=cfg["bits_per_input"],
        filter_inputs=cfg["filter_inputs"],
        filter_entries=cfg["filter_entries"],
        filter_hash_functions=cfg["filter_hash_functions"],
        n_submodels=cfg["n_submodels"],
        epochs=cfg["epochs"],
        batch_size=cfg["batch_size"],
        lr=cfg.get("lr", 0.01),
    )
    clf.fit(X_tr, y_tr)
    pred = clf.predict(X_te)
    return np.array([int(p) for p in pred])


def metrics(y_true, y_pred, task):
    from sklearn.metrics import accuracy_score, f1_score
    avg = "binary" if task == "binary" else "weighted"
    kw = {"average": avg, "zero_division": 0}
    if task == "binary": kw["pos_label"] = 1
    return {
        "accuracy": float(accuracy_score(y_true, y_pred)),
        "f1": float(f1_score(y_true, y_pred, **kw)),
        "f1_macro": float(f1_score(y_true, y_pred, average="macro", zero_division=0)),
        "f1_weighted": float(f1_score(y_true, y_pred, average="weighted", zero_division=0)),
    }


def grid_iter(model):
    G = {"wisard": WISARD_GRID, "cluswisard": CLUS_GRID, "bloomwisard": BLOOM_GRID,
         "bthowen": BTHOWEN_GRID, "uleen": ULEEN_GRID}[model]
    keys = list(G.keys())
    for vals in product(*[G[k] for k in keys]):
        yield dict(zip(keys, vals))


def run_one_fit(model, base, task, fold, cfg, tr_idx, te_idx, X_df, y):
    t0 = time.time()
    # encode for shallow wisards; raw X for bthowen/uleen
    if model in ("wisard", "cluswisard", "bloomwisard"):
        Xb, n_bits = encode_X(X_df, tr_idx, cfg["thermometer"], cfg["bits"],
                                y_fit=y[tr_idx] if cfg["thermometer"] == "supervised" else None)
        if cfg["address_size"] > n_bits:
            return None  # skip invalid
        y_pred = fit_predict(model, Xb[tr_idx], y[tr_idx], Xb[te_idx], cfg)
    elif model == "bthowen":
        X = X_df.values.astype(float)
        y_pred = fit_predict_bthowen(X[tr_idx], y[tr_idx], X[te_idx], cfg)
        n_bits = None
    elif model == "uleen":
        X = X_df.values.astype(float)
        y_pred = fit_predict_uleen(X[tr_idx], y[tr_idx], X[te_idx], cfg)
        n_bits = None
    else:
        raise ValueError(model)
    elapsed = time.time() - t0
    m = metrics(y[te_idx], y_pred, task)
    return {"model": model, "base": base, "task": task, "fold": fold,
            "cfg": cfg, "n_bits": n_bits, "elapsed_s": round(elapsed, 3), **m}


def load_done():
    if not OUT_FILE.exists(): return set()
    done = set()
    for ln in OUT_FILE.read_text().splitlines():
        if not ln.strip(): continue
        d = json.loads(ln)
        done.add((d["model"], d["base"], d["task"], d["fold"],
                  json.dumps(d["cfg"], sort_keys=True)))
    return done


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--models", nargs="+",
                    default=["wisard","cluswisard","bloomwisard","bthowen","uleen"])
    ap.add_argument("--bases", nargs="+", default=list(cu.CSVS.keys()))
    ap.add_argument("--combined", action="store_true",
                    help="rodar combined MULTI-CLASSE (1 config por modelo)")
    args = ap.parse_args()

    done = load_done()
    print(f"Resuming, {len(done)} already done.", flush=True)

    with OUT_FILE.open("a") as f_out:
        # --- per-device binário (grid) ---
        for base in args.bases:
            try:
                X_df, y = prepare(base, "binary")
            except Exception as e:
                print(f"PREPARE FAIL {base}/binary: {e}", flush=True); continue
            skf = StratifiedKFold(N_FOLDS, shuffle=True, random_state=SEED)
            splits = list(skf.split(X_df.values, y))
            for model in args.models:
                cfgs = list(grid_iter(model))
                print(f"[{model}] {base}/binary: {len(cfgs)} cfgs × {N_FOLDS} folds",
                      flush=True)
                for cfg in cfgs:
                    cfg_key = json.dumps(cfg, sort_keys=True)
                    for fold, (tr, te) in enumerate(splits):
                        key = (model, base, "binary", fold, cfg_key)
                        if key in done: continue
                        try:
                            rec = run_one_fit(model, base, "binary", fold, cfg,
                                              tr, te, X_df, y)
                            if rec is None: continue
                            f_out.write(json.dumps(rec) + "\n"); f_out.flush()
                            print(f"  {model:11s} {base:13s} bin f{fold} "
                                  f"cfg={cfg} f1={rec['f1']:.3f} t={rec['elapsed_s']:.1f}s",
                                  flush=True)
                        except Exception as e:
                            print(f"FAIL {model}/{base}/bin/f{fold} cfg={cfg}: {e}",
                                  flush=True)
                        finally:
                            gc.collect()

        # --- combined: BINÁRIO (Tab 12) + MULTI-CLASSE (Tab 13) ---
        if args.combined:
            for task in ("binary", "multiclass"):
                try:
                    X_df, y = prepare("combined", task)
                except Exception as e:
                    print(f"PREPARE FAIL combined/{task}: {e}", flush=True); continue
                skf = StratifiedKFold(N_FOLDS, shuffle=True, random_state=SEED)
                splits = list(skf.split(X_df.values, y))
                for model in args.models:
                    cfg = COMBINED_CFGS[model]
                    cfg_key = json.dumps(cfg, sort_keys=True)
                    for fold, (tr, te) in enumerate(splits):
                        key = (model, "combined", task, fold, cfg_key)
                        if key in done: continue
                        try:
                            rec = run_one_fit(model, "combined", task, fold, cfg,
                                              tr, te, X_df, y)
                            if rec is None: continue
                            f_out.write(json.dumps(rec) + "\n"); f_out.flush()
                            print(f"  {model:11s} combined      {task[:5]} f{fold} "
                                  f"f1={rec['f1']:.3f} t={rec['elapsed_s']:.1f}s",
                                  flush=True)
                        except Exception as e:
                            print(f"FAIL {model}/combined/{task}/f{fold}: {e}", flush=True)
                        finally:
                            gc.collect()

    print("Done.", flush=True)


if __name__ == "__main__":
    main()

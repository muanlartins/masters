"""Unified WiSARD-family sweep with StratifiedKFold(5).

Models: WiSARD, ClusWiSARD, BloomWiSARD (BTHOWeN/ULEEN handled separately
because their Python ports have their own train loops).

For each (model, base, cleaning, task, cfg) — and 5 folds — record:
    f1_binary/f1_macro, accuracy, train_time_s, n_bits, memory.

Resumable via the existing JSONL.  Designed to run in background.
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

sys.path.insert(0, str(PROJ / "notebooks" / "toniot"))
import consolidado_utils as cu
import wisardpkg as wp

CSVS = {
    "Weather":      "Train_Test_IoT_Weather.csv",
    "Modbus":       "Train_Test_IoT_Modbus.csv",
    "GPS_Tracker":  "Train_Test_IoT_GPS_Tracker.csv",
    "Fridge":       "Train_Test_IoT_Fridge.csv",
    "Thermostat":   "Train_Test_IoT_Thermostat.csv",
    "Motion_Light": "Train_Test_IoT_Motion_Light.csv",
    "Garage_Door":  "Train_Test_IoT_Garage_Door.csv",
}
SEED = 42

# Reduced union grid (compute-bounded).  Keep address_size compatible with
# bit budgets per encoder; large addrs need many bits.
WISARD_GRID = {
    # Reduced grid for tractable runtime — covers the new thermometers but doesn't sweep exhaustively
    "thermometer": ["distributive", "gaussian", "logarithmic", "dispatch"],
    "bits_per_feature": [16],
    "address_size": [4, 8, 16],
    "ignore_zero": [True],
}
CLUS_GRID = {
    "thermometer": ["distributive", "logarithmic"],
    "bits_per_feature": [16],
    "address_size": [4, 8, 16],
    "min_score": [0.1, 0.3],
    "threshold": [10, 100],
    "limit": [10, 20],
}
BLOOM_GRID = {
    "thermometer": ["distributive", "logarithmic"],
    "bits_per_feature": [16, 32],
    "address_size": [8, 16, 24, 32],
    "filter_size": [256, 1024, 4096],
    "num_hashes": [2, 3],
}


def prepare_features(base: str, cleaning: str, task: str):
    df = pd.read_csv(DATA_DIR / CSVS[base])
    if cleaning == "with_cleaning":
        df = cu.clean_df_g1(df)
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
    # MinMaxScale just to give consistent ranges to the thermometer
    X_df.iloc[:, :] = MinMaxScaler().fit_transform(X_df.values)
    return X_df, y


def encode_X(X_df, fit_idx, thermo_kind, bits):
    """Encode X using the chosen thermometer family (fit on train slice)."""
    fit_data = X_df.iloc[fit_idx]
    if thermo_kind == "dispatch":
        therms, _ = cu.build_per_feature_thermometer(X_df, base_bits=bits, fit_on=fit_data)
        # transform per-feature
        rows = []
        for i in range(len(X_df)):
            bits_row = []
            for t, col in zip(therms, X_df.columns):
                v = float(X_df[col].iloc[i])
                out = t.transform([v])
                for j in range(t.getSize()):
                    bits_row.append(int(out[j]))
            rows.append(bits_row)
        return np.array(rows, dtype=np.int8), len(rows[0])
    else:
        if thermo_kind == "distributive":
            t = wp.DistributiveThermometer(bits)
        elif thermo_kind == "gaussian":
            t = wp.GaussianThermometer(bits)
        elif thermo_kind == "exponential":
            t = wp.ExponentialThermometer(bits)
        elif thermo_kind == "logarithmic":
            t = wp.LogarithmicThermometer(bits)
        else:
            raise ValueError(f"unknown thermometer {thermo_kind!r}")
        t.fit(fit_data.values.tolist())
        # batch transform
        rows = []
        size = bits * X_df.shape[1]
        for i in range(len(X_df)):
            out = t.transform(list(X_df.iloc[i].values))
            rows.append([int(out[j]) for j in range(size)])
        return np.array(rows, dtype=np.int8), size


def _make_dataset(Xb, y=None):
    """Build wp.DataSet. y=None → unlabeled (for classify)."""
    ds = wp.DataSet()
    rows = Xb.tolist()
    if y is None:
        for row in rows:
            ds.add(row)
    else:
        for row, label in zip(rows, y):
            ds.add(row, str(int(label)))
    return ds


def wisard_fit_predict(Xb_tr, y_tr, Xb_te, addr, ignore_zero):
    clf = wp.Wisard(addr, ignoreZero=ignore_zero, bleachingActivated=True)
    clf.train(_make_dataset(Xb_tr, y_tr))
    pred = clf.classify(_make_dataset(Xb_te))
    return np.array([int(p) for p in pred])


def cluswisard_fit_predict(Xb_tr, y_tr, Xb_te, addr, min_score, threshold, limit):
    clf = wp.ClusWisard(addr, min_score, threshold, limit)
    clf.train(_make_dataset(Xb_tr, y_tr))
    pred = clf.classify(_make_dataset(Xb_te))
    return np.array([int(p) for p in pred])


def bloom_fit_predict(Xb_tr, y_tr, Xb_te, addr, filter_size, num_hashes):
    clf = wp.BloomWisard(addressSize=addr, capacity=filter_size, numberOfHashes=num_hashes,
                         bleachingActivated=True)
    clf.train(_make_dataset(Xb_tr, y_tr))
    pred = clf.classify(_make_dataset(Xb_te))
    return np.array([int(p) for p in pred])


def metrics(y_true, y_pred, task):
    from sklearn.metrics import accuracy_score, f1_score
    avg_macro = "binary" if task == "binary" else "macro"
    kw = {"average": avg_macro}
    if task == "binary": kw["pos_label"] = 1
    return {
        "accuracy": float(accuracy_score(y_true, y_pred)),
        "f1": float(f1_score(y_true, y_pred, zero_division=0, **kw)),
        "f1_weighted": float(f1_score(y_true, y_pred, average="weighted", zero_division=0)),
    }


def grid_iter(model):
    if model == "wisard":
        for thermo, bits, addr, ig in product(*[WISARD_GRID[k]
                                                for k in ["thermometer","bits_per_feature","address_size","ignore_zero"]]):
            yield {"thermometer":thermo, "bits":bits, "address_size":addr, "ignore_zero":ig}
    elif model == "cluswisard":
        for thermo, bits, addr, ms, th, lim in product(*[CLUS_GRID[k]
                                                          for k in ["thermometer","bits_per_feature","address_size","min_score","threshold","limit"]]):
            yield {"thermometer":thermo, "bits":bits, "address_size":addr,
                   "min_score":ms, "threshold":th, "limit":lim}
    elif model == "bloomwisard":
        for thermo, bits, addr, fs, nh in product(*[BLOOM_GRID[k]
                                                     for k in ["thermometer","bits_per_feature","address_size","filter_size","num_hashes"]]):
            yield {"thermometer":thermo, "bits":bits, "address_size":addr,
                   "filter_size":fs, "num_hashes":nh}
    else:
        raise ValueError(model)


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("model", choices=["wisard", "cluswisard", "bloomwisard"])
    ap.add_argument("--bases", nargs="*", default=list(CSVS.keys()))
    ap.add_argument("--tasks", nargs="*", default=["binary", "multiclass"])
    ap.add_argument("--cleanings", nargs="*", default=["with_cleaning"])
    args = ap.parse_args()

    OUT_FILE = OUT_DIR / f"{args.model}_kfold5.jsonl"
    done = set()
    if OUT_FILE.exists():
        for ln in OUT_FILE.read_text().splitlines():
            if ln.strip():
                d = json.loads(ln)
                done.add((d["base"], d["cleaning"], d["task"], d["fold"],
                          json.dumps(d["cfg"], sort_keys=True)))
    print(f"[{args.model}] resuming, {len(done)} runs already in {OUT_FILE.name}", flush=True)

    written = 0
    with OUT_FILE.open("a") as f_out:
        for base in args.bases:
            for cleaning in args.cleanings:
                for task in args.tasks:
                    try:
                        X_df, y = prepare_features(base, cleaning, task)
                    except Exception as e:
                        print(f"PREPARE FAIL {base}/{cleaning}/{task}: {e}", flush=True)
                        continue
                    if int(max(y)) + 1 < 2:
                        continue
                    skf = StratifiedKFold(n_splits=5, shuffle=True, random_state=SEED)
                    splits = list(skf.split(X_df.values, y))
                    cfgs = list(grid_iter(args.model))
                    print(f"[{args.model}] {base}/{cleaning}/{task}: {len(cfgs)} cfgs × 5 folds", flush=True)
                    for cfg in cfgs:
                        cfg_key = json.dumps(cfg, sort_keys=True)
                        # encode bits ONCE per (cfg-thermo, all folds use same thermo refit)
                        for fold, (tr_idx, te_idx) in enumerate(splits):
                            key = (base, cleaning, task, fold, cfg_key)
                            if key in done:
                                continue
                            try:
                                t0 = time.time()
                                Xb, n_bits = encode_X(X_df, tr_idx, cfg["thermometer"], cfg["bits"])
                                if cfg["address_size"] > n_bits:
                                    print(f"  skip addr>{n_bits} for cfg {cfg}", flush=True)
                                    continue
                                if args.model == "wisard":
                                    y_pred = wisard_fit_predict(Xb[tr_idx], y[tr_idx], Xb[te_idx],
                                                                cfg["address_size"], cfg["ignore_zero"])
                                elif args.model == "cluswisard":
                                    y_pred = cluswisard_fit_predict(Xb[tr_idx], y[tr_idx], Xb[te_idx],
                                                                    cfg["address_size"], cfg["min_score"],
                                                                    cfg["threshold"], cfg["limit"])
                                elif args.model == "bloomwisard":
                                    y_pred = bloom_fit_predict(Xb[tr_idx], y[tr_idx], Xb[te_idx],
                                                               cfg["address_size"], cfg["filter_size"],
                                                               cfg["num_hashes"])
                                elapsed = time.time() - t0
                                m = metrics(y[te_idx], y_pred, task)
                                rec = {"model": args.model, "base": base, "cleaning": cleaning,
                                       "task": task, "fold": fold, "cfg": cfg,
                                       "n_bits": n_bits, "elapsed_s": round(elapsed, 3), **m}
                                f_out.write(json.dumps(rec) + "\n"); f_out.flush()
                                written += 1
                                if written % 20 == 0:
                                    print(f"  [{written}] {base}/{task}/f{fold} cfg={cfg} f1={m['f1']:.3f} t={elapsed:.1f}s", flush=True)
                            except Exception as e:
                                print(f"FAIL {base}/{cleaning}/{task}/{fold} cfg={cfg}: {e}", flush=True)
                            finally:
                                gc.collect()
    print(f"[{args.model}] done. wrote {written} new rows.", flush=True)


if __name__ == "__main__":
    main()

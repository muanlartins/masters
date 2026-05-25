"""Reprodução PAPER-FAITHFUL para WiSARD-family — 5 modelos × tarefas.

Protocolo idêntico ao baselines_paper.py:
  1. Split 80/20 train/test (StratifiedShuffleSplit, random_state=42)
  2. k=4 StratifiedKFold no TRAIN
  3. F1 final = média sobre os 4 folds do CV
  4. drop_temporal_leak SEMPRE; NÃO aplicamos clean_df (ver §6.3 do notebook)

Reusa toda a infra de modelos do run_wisard_family.py (encode_X, fit_predict,
grids, etc).

Resultados em: results/_consolidado/wisard_paper.jsonl
"""
from __future__ import annotations

import argparse, gc, json, sys, time, warnings
from pathlib import Path

import numpy as np
import pandas as pd
from sklearn.model_selection import StratifiedKFold, StratifiedShuffleSplit
from sklearn.preprocessing import LabelEncoder, MinMaxScaler

warnings.filterwarnings("ignore")

PROJ = Path("/Users/muanlartins/repos/masters")
OUT_DIR = PROJ / "notebooks" / "toniot" / "results" / "_consolidado"
OUT_FILE = OUT_DIR / "wisard_paper.jsonl"

sys.path.insert(0, str(PROJ / "notebooks" / "toniot"))
import consolidado_utils as cu
import run_wisard_family as rwf  # reuse encode_X, grids, fit_predict_*

SEED = 42
N_FOLDS = 4
TEST_SIZE = 0.20


def load_done():
    if not OUT_FILE.exists():
        return set()
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
    ap.add_argument("--combined", action="store_true")
    args = ap.parse_args()

    done = load_done()
    print(f"Resuming, {len(done)} already done.", flush=True)
    print(f"Protocol: 80/20 split + k={N_FOLDS} CV on train (paper-faithful)", flush=True)

    with OUT_FILE.open("a") as f_out:
        # --- per-device binary ---
        for base in args.bases:
            try:
                X_df, y = rwf.prepare(base, "binary")
            except Exception as e:
                print(f"PREPARE FAIL {base}/binary: {e}", flush=True); continue

            # 80/20 split
            sss = StratifiedShuffleSplit(n_splits=1, test_size=TEST_SIZE, random_state=SEED)
            train_idx_full, _test = next(sss.split(X_df.values, y))
            X_tr_full = X_df.iloc[train_idx_full].reset_index(drop=True)
            y_tr_full = y[train_idx_full]

            # k=4 CV on train
            skf = StratifiedKFold(n_splits=N_FOLDS, shuffle=True, random_state=SEED)
            cv_splits = list(skf.split(X_tr_full.values, y_tr_full))

            for model in args.models:
                cfgs = list(rwf.grid_iter(model))
                print(f"[{model}] {base}/binary: {len(cfgs)} cfgs × {N_FOLDS} folds",
                      flush=True)
                for cfg in cfgs:
                    cfg_key = json.dumps(cfg, sort_keys=True)
                    for fold, (rel_tr, rel_te) in enumerate(cv_splits):
                        key = (model, base, "binary", fold, cfg_key)
                        if key in done: continue
                        try:
                            rec = rwf.run_one_fit(model, base, "binary", fold, cfg,
                                                   rel_tr, rel_te, X_tr_full, y_tr_full)
                            if rec is None: continue
                            f_out.write(json.dumps(rec) + "\n"); f_out.flush()
                            print(f"  {model:11s} {base:13s} bin f{fold} "
                                  f"f1={rec['f1']:.3f} t={rec['elapsed_s']:.1f}s",
                                  flush=True)
                        except Exception as e:
                            print(f"FAIL {model}/{base}/bin/f{fold} cfg={cfg}: {e}",
                                  flush=True)
                        finally:
                            gc.collect()

        # --- combined (binary + multiclass) — single cfg per model ---
        if args.combined:
            for task in ("binary", "multiclass"):
                try:
                    X_df, y = rwf.prepare("combined", task)
                except Exception as e:
                    print(f"PREPARE FAIL combined/{task}: {e}", flush=True); continue
                sss = StratifiedShuffleSplit(n_splits=1, test_size=TEST_SIZE, random_state=SEED)
                train_idx_full, _test = next(sss.split(X_df.values, y))
                X_tr_full = X_df.iloc[train_idx_full].reset_index(drop=True)
                y_tr_full = y[train_idx_full]
                skf = StratifiedKFold(n_splits=N_FOLDS, shuffle=True, random_state=SEED)
                cv_splits = list(skf.split(X_tr_full.values, y_tr_full))
                for model in args.models:
                    cfg = rwf.COMBINED_CFGS[model]
                    cfg_key = json.dumps(cfg, sort_keys=True)
                    for fold, (rel_tr, rel_te) in enumerate(cv_splits):
                        key = (model, "combined", task, fold, cfg_key)
                        if key in done: continue
                        try:
                            rec = rwf.run_one_fit(model, "combined", task, fold, cfg,
                                                   rel_tr, rel_te, X_tr_full, y_tr_full)
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

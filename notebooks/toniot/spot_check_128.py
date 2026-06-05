"""Does pushing WiSARD/ClusWiSARD past the new 64 ceiling (to 96/128 bits & address)
buy materially more F1? If not, 64 is the honest practical ceiling and the fair
within-family comparison stands. Identical CV protocol (k=4, seed 42)."""
import json, sys
from pathlib import Path
import numpy as np
from sklearn.model_selection import StratifiedShuffleSplit, StratifiedKFold
HERE = Path(__file__).resolve().parent; sys.path.insert(0, str(HERE))
import run_wisard_grid as g, run_wisard_family as rwf
SEED, TS, NF = 42, 0.20, 4

def cvf1(model, cfg, Xtr, ytr, folds, enc):
    key = (cfg["thermometer"], cfg["bits"])
    if key not in enc:
        enc[key] = [(g.encode_matrix(g.make_thermometer(cfg["thermometer"], cfg["bits"], Xtr[ftr]), Xtr), ftr, fva)
                    for (ftr, fva) in folds]
    f1 = []
    for (Xb, ftr, fva) in enc[key]:
        if cfg["address_size"] > Xb.shape[1]:
            return None
        yp = rwf.fit_predict(model, Xb[ftr], ytr[ftr], Xb[fva], cfg)
        f1.append(rwf.metrics(ytr[fva], yp, "binary")["f1_weighted"])
    return float(np.mean(f1))

BASE_BEST = {  # the extended-grid 64/64 winners, for reference
 ("wisard","Modbus"):0.953, ("wisard","Weather"):0.932,
 ("cluswisard","Modbus"):0.954, ("cluswisard","Weather"):0.934,
}
for model in ["wisard", "cluswisard"]:
    for base in ["Modbus", "Weather"]:
        X_df, y = rwf.prepare(base, "binary")
        Xall = X_df.values.astype(float)
        tr, _ = next(StratifiedShuffleSplit(1, test_size=TS, random_state=SEED).split(Xall, y))
        Xtr, ytr = Xall[tr], y[tr]
        folds = list(StratifiedKFold(NF, shuffle=True, random_state=SEED).split(Xtr, ytr))
        enc = {}
        best = {"f1": -1, "cfg": None}
        for bits in [64, 96, 128]:
            for addr in [64, 96, 128]:
                if model == "wisard":
                    cfg = {"thermometer": "distributive", "bits": bits, "address_size": addr, "ignore_zero": False}
                else:
                    cfg = {"thermometer": "distributive", "bits": bits, "address_size": addr,
                           "min_score": 0.2, "threshold": 100, "limit": 5}
                f = cvf1(model, cfg, Xtr, ytr, folds, enc)
                if f is not None and f > best["f1"]:
                    best = {"f1": f, "cfg": {"bits": bits, "addr": addr}}
        ref = BASE_BEST[(model, base)]
        print(f"{model:11s} {base:8s} 64/64-grid={ref:.3f}  best@>=64={best['f1']:.3f} "
              f"({best['cfg']})  Δ={best['f1']-ref:+.3f}", flush=True)

"""Reprodução PAPER-FAITHFUL do Alsaedi 2020 — 8 baselines × 3 tarefas.

Protocolo (alinhado §VI-A2 do paper):
  1. Split 80/20 train/test (StratifiedShuffleSplit, random_state=42)
  2. k=4 StratifiedKFold no TRAIN para avaliação (paper: "average of all folds
     was used as the final result")
  3. F1 final = média sobre os 4 folds do CV
  4. NÃO aplicamos clean_df — preserva o leak de encoding (variantes whitespace
     em Fridge/Garage_Door) que provavelmente também existia nos dados do paper.
     Ver §6.3 do notebook 06_consolidado_grupos.ipynb para detalhes.
  5. drop_temporal_leak SEMPRE (paper: drop date/time/timestamp)
  6. F1 reportado em três averages (binary/macro/weighted); notebook usa weighted
     por melhor ajuste empírico ao paper (§6.2).

Hiperparâmetros (§V do paper):
  - LR: defaults + multi_class='ovr' (paper §VI-D3)
  - LDA: defaults
  - kNN: k=5, Euclidean
  - RF: n_estimators=10, criterion=gini
  - CART: criterion=gini
  - NB: GaussianNB
  - SVM: RBF kernel='rbf', gamma='auto'  (auto-substituído por LinearSVC quando n>50k)
  - LSTM: 3 camadas (128/100/64), tanh, dropout 0.2, batch=64, epochs=35, Adam

Tarefas:
  - per-device BINÁRIO (Tabs 10-11): 7 bases × normal vs ataque
  - combined BINÁRIO (Tab 12): combined_IoT_dataset × normal vs ataque
  - combined MULTI-CLASSE (Tab 13): combined_IoT_dataset × 9 sub-classes

Resultados em: results/_consolidado/baselines_paper.jsonl
"""
from __future__ import annotations

import json
import sys
import time
import warnings
from pathlib import Path

import numpy as np
import pandas as pd

warnings.filterwarnings("ignore")

PROJ = Path("/Users/muanlartins/repos/masters")
DATA_DIR = PROJ / "data" / "toniot"
OUT_DIR = PROJ / "notebooks" / "toniot" / "results" / "_consolidado"
OUT_DIR.mkdir(parents=True, exist_ok=True)
OUT_FILE = OUT_DIR / "baselines_paper.jsonl"

sys.path.insert(0, str(PROJ / "notebooks" / "toniot"))
import consolidado_utils as cu

SEED = 42
N_FOLDS = 4   # paper §VI-A2: "k value was set to 4"
TEST_SIZE = 0.20  # paper §VI-A2: "20% held back for testing"


def load_existing_keys() -> set:
    if not OUT_FILE.exists():
        return set()
    keys = set()
    for ln in OUT_FILE.read_text().splitlines():
        if not ln.strip():
            continue
        d = json.loads(ln)
        keys.add((d["model"], d["base"], d["task"], d["fold"]))
    return keys


def prepare_per_device(base: str):
    """Per-device binary. Apenas drop_temporal + LabelEncoder cru.

    NÃO aplicamos clean_df porque o paper não tinha as variantes whitespace dos
    CSVs públicos atuais. LabelEncoder sobre raw strings preserva o que era um
    feature 'limpo' no CSV original do paper (paper §VI-A1: high→1, low→0).
    """
    from sklearn.preprocessing import LabelEncoder, MinMaxScaler
    df = pd.read_csv(DATA_DIR / cu.CSVS[base])
    df = cu.drop_temporal_leak(df)
    y = df["label"].astype(int).values
    X = df.drop(columns=["label", "type"])
    for col in X.columns:
        if not pd.api.types.is_numeric_dtype(X[col]):
            X[col] = LabelEncoder().fit_transform(X[col].astype(str))
    X = X.fillna(0).astype(float).values
    X = MinMaxScaler().fit_transform(X)
    return X, y


def prepare_combined(task: str):
    """Combined dataset. task in {binary, multiclass}. Sem clean_df."""
    from sklearn.preprocessing import LabelEncoder, MinMaxScaler
    df = cu.build_combined_dataset(apply_cleaning=False, drop_temporal=True)
    if task == "binary":
        y = df["label"].astype(int).values
    else:
        y = LabelEncoder().fit_transform(df["type"].astype(str))
    X = df.drop(columns=["label", "type"])
    for col in X.columns:
        if not pd.api.types.is_numeric_dtype(X[col]):
            X[col] = LabelEncoder().fit_transform(X[col].astype(str))
    X = X.fillna(0).astype(float).values
    X = MinMaxScaler().fit_transform(X)
    return X, y


def build_model(name: str, task: str):
    """Paper §V hyperparams. LR multi-class usa OvR (paper §VI-D3)."""
    from sklearn.linear_model import LogisticRegression
    from sklearn.discriminant_analysis import LinearDiscriminantAnalysis
    from sklearn.neighbors import KNeighborsClassifier
    from sklearn.ensemble import RandomForestClassifier
    from sklearn.tree import DecisionTreeClassifier
    from sklearn.naive_bayes import GaussianNB
    from sklearn.svm import SVC
    from sklearn.multiclass import OneVsRestClassifier

    if name == "LR":
        if task == "multiclass":
            # paper §VI-D3: "Logistic Regression (LR) is usually used for a binary
            # classification ... Therefore, LR is implemented with the one-vs-rest (OvR)"
            return OneVsRestClassifier(LogisticRegression(max_iter=500, random_state=SEED))
        return LogisticRegression(max_iter=500, random_state=SEED, n_jobs=-1)
    if name == "LDA":  return LinearDiscriminantAnalysis()
    if name == "kNN":  return KNeighborsClassifier(n_neighbors=5, metric="euclidean", n_jobs=-1)
    if name == "RF":   return RandomForestClassifier(n_estimators=10, criterion="gini",
                                                       random_state=SEED, n_jobs=-1)
    if name == "CART": return DecisionTreeClassifier(criterion="gini", random_state=SEED)
    if name == "NB":   return GaussianNB()
    if name == "SVM":  return SVC(kernel="rbf", gamma="auto", random_state=SEED)
    if name == "SVM_LINEAR":
        from sklearn.svm import LinearSVC
        return LinearSVC(random_state=SEED, max_iter=2000, dual="auto")
    raise ValueError(name)


def fit_predict_lstm(X_tr, y_tr, X_te, n_classes, task):
    """LSTM Alsaedi Table 9 — 3-layer 128/100/64, dropout 0.2, batch=64,
    epochs=35 (paper-faithful), Adam, tanh."""
    import torch
    import torch.nn as nn

    torch.manual_seed(SEED)
    device = torch.device("mps" if torch.backends.mps.is_available() else "cpu")
    Xt = torch.tensor(X_tr, dtype=torch.float32).unsqueeze(1).to(device)
    Xs = torch.tensor(X_te, dtype=torch.float32).unsqueeze(1).to(device)
    yt = torch.tensor(y_tr, dtype=torch.long).to(device)

    class LSTMClf(nn.Module):
        def __init__(self, n_features, n_classes):
            super().__init__()
            self.lstm1 = nn.LSTM(n_features, 128, batch_first=True)
            self.drop1 = nn.Dropout(0.2)
            self.lstm2 = nn.LSTM(128, 100, batch_first=True)
            self.drop2 = nn.Dropout(0.2)
            self.lstm3 = nn.LSTM(100, 64, batch_first=True)
            self.drop3 = nn.Dropout(0.2)
            self.fc = nn.Linear(64, n_classes)
        def forward(self, x):
            x, _ = self.lstm1(x); x = self.drop1(torch.tanh(x))
            x, _ = self.lstm2(x); x = self.drop2(torch.tanh(x))
            _, (h, _) = self.lstm3(x); h = self.drop3(torch.tanh(h[-1]))
            return self.fc(h)

    model = LSTMClf(X_tr.shape[1], n_classes).to(device)
    opt = torch.optim.Adam(model.parameters(), lr=1e-3)
    loss_fn = nn.CrossEntropyLoss()
    batch = 64
    n_epochs = 35  # PAPER §VI: epochs=35
    model.train()
    for epoch in range(n_epochs):
        idx = torch.randperm(len(Xt))
        for i in range(0, len(idx), batch):
            sel = idx[i:i+batch]
            opt.zero_grad()
            loss = loss_fn(model(Xt[sel]), yt[sel])
            loss.backward(); opt.step()
    model.eval()
    with torch.no_grad():
        preds = []
        for i in range(0, len(Xs), 1024):
            preds.append(model(Xs[i:i+1024]).argmax(dim=1).cpu().numpy())
        return np.concatenate(preds)


def metrics(y_true, y_pred, task):
    """Reporta accuracy + F1 em MÚLTIPLOS averages.

    Paper §VI-B1 mostra apenas a fórmula F-Score = 2*P*R/(P+R), sem dizer qual
    average para multi-class. Tabelas têm valores incompatíveis com binary F1
    quando classe é majoritária (e.g. Motion_Light paper=0.43 mas predict-majority
    binary F1 = 0.77). MACRO F1 de predict-majority Motion_Light = 0.385, bem
    mais próximo. Por isso reportamos AMBOS para o reader decidir.
    """
    from sklearn.metrics import accuracy_score, f1_score, precision_score, recall_score
    out = {"accuracy": float(accuracy_score(y_true, y_pred))}
    if task == "binary":
        # Paper-faithful binary metric (assuming pos_label=1 = attack)
        kw = {"average": "binary", "pos_label": 1, "zero_division": 0}
        out["f1"] = float(f1_score(y_true, y_pred, **kw))
        out["precision"] = float(precision_score(y_true, y_pred, **kw))
        out["recall"] = float(recall_score(y_true, y_pred, **kw))
    else:
        kw = {"average": "weighted", "zero_division": 0}
        out["f1"] = float(f1_score(y_true, y_pred, **kw))
        out["precision"] = float(precision_score(y_true, y_pred, **kw))
        out["recall"] = float(recall_score(y_true, y_pred, **kw))
    # ALSO macro F1 (paper might have used this; see Motion_Light)
    out["f1_macro"] = float(f1_score(y_true, y_pred, average="macro", zero_division=0))
    out["f1_weighted"] = float(f1_score(y_true, y_pred, average="weighted", zero_division=0))
    return out


def run_one(model_name, base, task, fold, train_idx, test_idx, X, y):
    t0 = time.time()
    X_tr, X_te = X[train_idx], X[test_idx]
    y_tr, y_te = y[train_idx], y[test_idx]
    if model_name == "LSTM":
        n_classes = int(max(y) + 1)
        y_pred = fit_predict_lstm(X_tr, y_tr, X_te, n_classes, task)
        eff_model = "LSTM"
    else:
        eff_model = model_name
        # SVM RBF on combined (260k+) is O(n²) — substitui por LinearSVC
        if model_name == "SVM" and len(X) > 50_000:
            eff_model = "SVM_LINEAR"
        clf = build_model(eff_model, task)
        clf.fit(X_tr, y_tr)
        y_pred = clf.predict(X_te)
    elapsed = time.time() - t0
    m = metrics(y_te, y_pred, task)
    return {
        "model": model_name, "effective_model": eff_model,
        "base": base, "task": task, "fold": fold,
        "n_train": int(len(train_idx)), "n_test": int(len(test_idx)),
        "elapsed_s": round(elapsed, 3), **m,
    }


def main():
    from sklearn.model_selection import StratifiedKFold, StratifiedShuffleSplit

    MODELS = ["LR", "LDA", "kNN", "RF", "CART", "NB", "SVM", "LSTM"]
    JOBS = [(b, "binary") for b in cu.CSVS]
    JOBS += [("combined", "binary"), ("combined", "multiclass")]

    done = load_existing_keys()
    print(f"Resuming, {len(done)} already done.", flush=True)
    print(f"Protocol: 80/20 split + k={N_FOLDS} CV on train", flush=True)

    with OUT_FILE.open("a") as f_out:
        for base, task in JOBS:
            try:
                if base == "combined":
                    X, y = prepare_combined(task)
                else:
                    X, y = prepare_per_device(base)
            except Exception as e:
                print(f"PREPARE FAIL {base}/{task}: {e}", flush=True)
                continue
            if int(max(y)) + 1 < 2:
                continue

            # PAPER §VI-A2: split 80/20 first
            sss = StratifiedShuffleSplit(n_splits=1, test_size=TEST_SIZE, random_state=SEED)
            train_idx_full, _test_idx = next(sss.split(X, y))
            # PAPER §VI-A2: k=4 CV on the 80% training portion
            skf = StratifiedKFold(n_splits=N_FOLDS, shuffle=True, random_state=SEED)
            X_tr_full = X[train_idx_full]
            y_tr_full = y[train_idx_full]
            cv_splits = list(skf.split(X_tr_full, y_tr_full))

            for model_name in MODELS:
                for fold, (rel_tr, rel_te) in enumerate(cv_splits):
                    if (model_name, base, task, fold) in done:
                        continue
                    # Map relative indices back to absolute (within original X)
                    abs_tr = train_idx_full[rel_tr]
                    abs_te = train_idx_full[rel_te]
                    try:
                        rec = run_one(model_name, base, task, fold,
                                      abs_tr, abs_te, X, y)
                        f_out.write(json.dumps(rec) + "\n"); f_out.flush()
                        print(f"  {model_name:5s} {base:13s} {task:10s} f{fold} "
                              f"f1={rec['f1']:.3f} t={rec['elapsed_s']:.1f}s", flush=True)
                    except Exception as e:
                        print(f"FAIL {model_name}/{base}/{task}/{fold}: {e}", flush=True)
    print("Done.", flush=True)


if __name__ == "__main__":
    main()

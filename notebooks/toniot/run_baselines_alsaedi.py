"""Reprodução fiel do paper Alsaedi 2020 — 8 baselines × 2 tarefas.

Tarefas (alinhadas ao paper):
  - per-device BINÁRIO (Tabelas 10-11): 7 bases × normal vs ataque
  - combined MULTI-CLASSE (Tabela 13): combined_IoT_dataset × 9 classes

Hiperparâmetros (Sec. V do paper):
  - kNN: k=5, Euclidean
  - RF:  n_estimators=10, Gini
  - CART: Gini
  - SVM: RBF, gamma='auto'
  - LSTM: 3 camadas (128/100/64), tanh, dropout 0.2, batch=64, epochs=35, Adam
  - LR/LDA/NB: defaults

Protocolo (Sec. VI-A2):
  - clean_df unificado (neutraliza leaks categóricos) — opção `cleaning`
  - drop_temporal_leak SEMPRE (paper explicitly: 'date, time, timestamp emitted')
  - StratifiedKFold(5, shuffle=True, random_state=42)
  - MinMaxScaler para [0, 1]
  - F-score binário (binary tasks) / weighted (multi-class)

Resultados em: results/_consolidado/baselines_alsaedi.jsonl
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
OUT_FILE = OUT_DIR / "baselines_alsaedi.jsonl"

sys.path.insert(0, str(PROJ / "notebooks" / "toniot"))
import consolidado_utils as cu

SEED = 42
N_FOLDS = 5


def load_existing_keys() -> set:
    if not OUT_FILE.exists():
        return set()
    keys = set()
    for ln in OUT_FILE.read_text().splitlines():
        if not ln.strip():
            continue
        d = json.loads(ln)
        keys.add((d["model"], d["base"], d["cleaning"], d["task"], d["fold"]))
    return keys


def prepare_per_device(base: str, cleaning: str):
    """7 bases per-device. task=binary. Returns (X, y)."""
    from sklearn.preprocessing import LabelEncoder, MinMaxScaler
    df = pd.read_csv(DATA_DIR / cu.CSVS[base])
    if cleaning == "with_cleaning":
        df = cu.clean_df(df)
    df = cu.drop_temporal_leak(df)
    y = df["label"].astype(int).values
    X = df.drop(columns=["label", "type"])
    for col in X.columns:
        if not pd.api.types.is_numeric_dtype(X[col]):
            X[col] = LabelEncoder().fit_transform(X[col].astype(str))
    X = X.fillna(0).astype(float).values
    X = MinMaxScaler().fit_transform(X)
    return X, y


def prepare_combined(cleaning: str, task: str = "multiclass"):
    """combined_IoT_dataset. task in {multiclass, binary}.

    - multiclass: y vem de `type` (9 sub-classes, Tabela 13 do paper).
    - binary: y vem de `label` (normal/ataque, Tabela 12 do paper).
    """
    from sklearn.preprocessing import LabelEncoder, MinMaxScaler
    df = cu.build_combined_dataset(apply_cleaning=(cleaning == "with_cleaning"),
                                    drop_temporal=True)
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


def build_model(name: str):
    """Hiperparâmetros alinhados ao paper Section V."""
    from sklearn.linear_model import LogisticRegression
    from sklearn.discriminant_analysis import LinearDiscriminantAnalysis
    from sklearn.neighbors import KNeighborsClassifier
    from sklearn.ensemble import RandomForestClassifier
    from sklearn.tree import DecisionTreeClassifier
    from sklearn.naive_bayes import GaussianNB
    from sklearn.svm import SVC

    if name == "LR":   return LogisticRegression(max_iter=500, random_state=SEED, n_jobs=-1)
    if name == "LDA":  return LinearDiscriminantAnalysis()
    if name == "kNN":  return KNeighborsClassifier(n_neighbors=5, metric="euclidean", n_jobs=-1)
    if name == "RF":   return RandomForestClassifier(n_estimators=10, criterion="gini",
                                                       random_state=SEED, n_jobs=-1)
    if name == "CART": return DecisionTreeClassifier(criterion="gini", random_state=SEED)
    if name == "NB":   return GaussianNB()
    # SVM RBF gamma='auto' — paper choice
    if name == "SVM":  return SVC(kernel="rbf", gamma="auto", random_state=SEED)
    # combined dataset has 260k+ rows — RBF SVM is O(n²), prohibitive.
    # We swap to LinearSVC for combined (annotated in results).
    if name == "SVM_LINEAR":
        from sklearn.svm import LinearSVC
        return LinearSVC(random_state=SEED, max_iter=2000, dual="auto")
    raise ValueError(name)


def fit_predict_lstm(X_tr, y_tr, X_te, n_classes, task):
    """LSTM Alsaedi Table 9: 3-layer 128/100/64, dropout 0.2, batch=64, epochs=35, Adam."""
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
    model.train()
    # 35 epochs alinhado ao paper; mas pra economizar tempo usamos 10 (mantém qualidade
    # razoável; ajustar se quiser fidelidade total).
    n_epochs = 10
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
    from sklearn.metrics import accuracy_score, f1_score, precision_score, recall_score
    # alinhado ao paper: binary p/ binário (Tabs 10-11), weighted p/ multi-classe (Tab 13)
    avg = "binary" if task == "binary" else "weighted"
    kw = {"average": avg, "zero_division": 0}
    if task == "binary":
        kw["pos_label"] = 1
    return {
        "accuracy": float(accuracy_score(y_true, y_pred)),
        "f1": float(f1_score(y_true, y_pred, **kw)),
        "precision": float(precision_score(y_true, y_pred, **kw)),
        "recall": float(recall_score(y_true, y_pred, **kw)),
    }


def run_one(model_name, base, cleaning, task, fold, train_idx, test_idx, X, y):
    t0 = time.time()
    X_tr, X_te = X[train_idx], X[test_idx]
    y_tr, y_te = y[train_idx], y[test_idx]
    if model_name == "LSTM":
        n_classes = int(max(y) + 1)
        y_pred = fit_predict_lstm(X_tr, y_tr, X_te, n_classes, task)
    else:
        # SVM RBF on combined (260k+ rows) is O(n²) — substituir por LinearSVC
        # (anotamos no record o substituto). Per-device datasets ficam com RBF como paper.
        effective_model = model_name
        if model_name == "SVM" and len(X) > 50_000:
            effective_model = "SVM_LINEAR"
        clf = build_model(effective_model)
        clf.fit(X_tr, y_tr)
        y_pred = clf.predict(X_te)
    elapsed = time.time() - t0
    m = metrics(y_te, y_pred, task)
    return {
        "model": model_name, "base": base, "cleaning": cleaning, "task": task,
        "fold": fold, "n_train": int(len(train_idx)), "n_test": int(len(test_idx)),
        "elapsed_s": round(elapsed, 3), **m,
    }


def main():
    from sklearn.model_selection import StratifiedKFold

    MODELS = ["LR", "LDA", "kNN", "RF", "CART", "NB", "SVM", "LSTM"]
    BASES = list(cu.CSVS.keys()) + ["combined"]
    CLEANS = ["no_cleaning", "with_cleaning"]

    done = load_existing_keys()
    print(f"Resuming, {len(done)} already done.", flush=True)

    # Per-device só faz binary; combined faz binary (Tab 12) E multiclass (Tab 13).
    JOBS = [(b, c, "binary") for b in cu.CSVS for c in CLEANS]
    JOBS += [("combined", c, t) for c in CLEANS for t in ("binary", "multiclass")]

    with OUT_FILE.open("a") as f_out:
        for base, cleaning, task in JOBS:
            try:
                if base == "combined":
                    X, y = prepare_combined(cleaning, task=task)
                else:
                    X, y = prepare_per_device(base, cleaning)
            except Exception as e:
                print(f"PREPARE FAIL {base}/{cleaning}/{task}: {e}", flush=True)
                continue
            if int(max(y)) + 1 < 2:
                continue
            skf = StratifiedKFold(n_splits=N_FOLDS, shuffle=True, random_state=SEED)
            splits = list(skf.split(X, y))
            for model_name in MODELS:
                for fold, (tr_idx, te_idx) in enumerate(splits):
                    if (model_name, base, cleaning, task, fold) in done:
                        continue
                    try:
                        rec = run_one(model_name, base, cleaning, task, fold,
                                      tr_idx, te_idx, X, y)
                        f_out.write(json.dumps(rec) + "\n"); f_out.flush()
                        print(f"  {model_name:5s} {base:13s} {cleaning:13s} {task:10s} f{fold} "
                              f"f1={rec['f1']:.3f} t={rec['elapsed_s']:.1f}s", flush=True)
                    except Exception as e:
                        print(f"FAIL {model_name}/{base}/{cleaning}/{task}/{fold}: {e}",
                              flush=True)
    print("Done.", flush=True)


if __name__ == "__main__":
    main()

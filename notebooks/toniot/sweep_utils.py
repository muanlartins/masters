"""Utilitários de leitura/normalização das entregas de sweep do T1.

Cada integrante salva resultados sob `results/<modelo>/.../*.json`.
O schema "oficial" está na §4 do `PLANO.md`, mas algumas entregas usam
schema flat alternativo. Esse módulo lê as duas variantes e devolve um
DataFrame único com colunas canônicas — pronto pra agregação,
ranking e Pareto.

Uso típico:

    from sweep_utils import load_all_results
    df = load_all_results("notebooks/toniot/results")
    df.groupby(["model", "base", "task"])["f1_macro"].max()
"""
from __future__ import annotations

import json
import math
import time
from pathlib import Path

import numpy as np
import pandas as pd

# Colunas canônicas que todo loader devolve. Manter sincronizado com o
# DataFrame consumido pelo notebook comparativo.
CANONICAL_COLS = [
    "model", "submission", "base", "task",
    "encoder_type", "encoder_size", "address_size",
    "bits_total", "n_features_num", "n_features_cat", "cat_bits",
    "skipped", "skipped_reason",
    "accuracy",
    "precision_macro", "precision_weighted",
    "recall_macro", "recall_weighted",
    "f1_macro", "f1_weighted",
    "auc_roc",
    "memory_bytes_serialized", "memory_bytes_theoretical",
    "train_time_s", "inference_latency_us",
    "model_hyperparams",
    "confusion_matrix", "labels",
    "machine", "timestamp", "source_file",
]


# --------------------------------------------------------------------------- #
# Loaders por integrante                                                       #
# --------------------------------------------------------------------------- #

def _read_records(path: Path) -> list[dict]:
    """Lê `.json` (objeto ou lista) ou `.jsonl` (1 objeto por linha)."""
    with path.open() as fh:
        if path.suffix == ".jsonl":
            return [json.loads(ln) for ln in fh if ln.strip()]
        raw = json.load(fh)
        return raw if isinstance(raw, list) else [raw]


def _load_plano_schema(path: Path, model_name: str, submission: str) -> list[dict]:
    """Lê schema oficial (PLANO §4) — `.json` ou `.jsonl`.

    Usado por BTHOWeN (json), WiSARD/ULEEN (jsonl) e pelos gabaritos."""
    raw = _read_records(path)
    out = []
    for r in raw:
        enc = r.get("encoder", {}) or {}
        inp = r.get("input", {}) or {}
        mtr = r.get("metrics", {}) or {}
        mh = r.get("model_hyperparams", {}) or {}
        # BTHOWeN VsCode duplica filter_entries/filter_hashes top-level;
        # mesclar dentro de model_hyperparams pra ficar uniforme.
        for k in ("filter_entries", "filter_hashes"):
            if k in r and k not in mh:
                mh[k] = r[k]
        out.append({
            "model": r.get("model", model_name),
            "submission": submission,
            "base": r.get("base"),
            "task": r.get("task"),
            "encoder_type": enc.get("type"),
            "encoder_size": enc.get("size"),
            "address_size": r.get("addressSize"),
            "bits_total": inp.get("bits_total"),
            "n_features_num": inp.get("n_features_num"),
            "n_features_cat": inp.get("n_features_cat"),
            "cat_bits": inp.get("cat_bits"),
            "skipped": bool(r.get("skipped", False)),
            "skipped_reason": r.get("skipped_reason"),
            "accuracy": mtr.get("accuracy"),
            "precision_macro": mtr.get("precision_macro"),
            "precision_weighted": mtr.get("precision_weighted"),
            "recall_macro": mtr.get("recall_macro"),
            "recall_weighted": mtr.get("recall_weighted"),
            "f1_macro": mtr.get("f1_macro"),
            "f1_weighted": mtr.get("f1_weighted"),
            "auc_roc": mtr.get("auc_roc"),
            "memory_bytes_serialized": mtr.get("memory_bytes_serialized"),
            "memory_bytes_theoretical": mtr.get("memory_bytes_theoretical"),
            "train_time_s": mtr.get("train_time_s"),
            "inference_latency_us": mtr.get("inference_latency_us"),
            "model_hyperparams": mh,
            "confusion_matrix": r.get("confusion_matrix"),
            "labels": r.get("labels"),
            "machine": r.get("machine"),
            "timestamp": r.get("timestamp"),
            "source_file": str(path),
        })
    return out


# Campos flat (não-canônicos) que viram model_hyperparams por modelo.
_FLAT_HP_FIELDS = {
    "ClusWiSARD":   ("min_score", "threshold", "discriminators_limit"),
    "BloomWiSARD":  ("hash_mode", "num_hashes", "filter_size"),
}


def _load_flat_schema(path: Path, model_name: str, submission: str) -> list[dict]:
    """Schema flat sem aninhamento (ClusWiSARD pure-Python e BloomWiSARD).

    Métricas de tempo dessas entregas NÃO são comparáveis às outras
    (pure-Python ~10-50× mais lento que o C++ fork).
    """
    raw = _read_records(path)
    hp_fields = _FLAT_HP_FIELDS.get(model_name, ())
    out = []
    for r in raw:
        out.append({
            "model": model_name,
            "submission": submission,
            "base": r.get("dataset"),
            "task": r.get("task"),
            "encoder_type": r.get("thermometer_type"),
            "encoder_size": r.get("thermometer_size"),
            "address_size": r.get("address_size"),
            "bits_total": r.get("total_input_bits"),
            "n_features_num": None,
            "n_features_cat": None,
            "cat_bits": None,
            "skipped": False,                     # entrega não tracka skipped
            "skipped_reason": None,
            "accuracy": r.get("accuracy"),
            "precision_macro": r.get("precision_macro"),
            "precision_weighted": r.get("precision_weighted"),
            "recall_macro": r.get("recall_macro"),
            "recall_weighted": r.get("recall_weighted"),
            "f1_macro": r.get("f1_macro"),
            "f1_weighted": r.get("f1_weighted"),
            "auc_roc": r.get("auc_roc"),
            "memory_bytes_serialized": r.get("memory_bytes"),
            "memory_bytes_theoretical": None,
            "train_time_s": r.get("train_time_s"),
            "inference_latency_us": r.get("infer_latency_us"),
            "model_hyperparams": {k: r.get(k) for k in hp_fields},
            "confusion_matrix": r.get("confusion_matrix"),
            "labels": r.get("confusion_matrix_labels"),
            "machine": None,                       # entrega não declara
            "timestamp": None,
            "source_file": str(path),
        })
    return out


# --------------------------------------------------------------------------- #
# Dispatch + agregação                                                         #
# --------------------------------------------------------------------------- #

# Pasta -> (loader, model_name, submission_id)
SUBMISSION_SPECS = {
    "cluswisard":     (_load_flat_schema,  "ClusWiSARD",  "cluswisard_purepython"),
    "bloomwisard":    (_load_flat_schema,  "BloomWiSARD", "bloomwisard_purepython"),
    "bthowen/colab":  (_load_plano_schema, "BTHOWeN",     "bthowen_colab"),
    "bthowen/vscode": (_load_plano_schema, "BTHOWeN",     "bthowen_vscode"),
    "wisard":         (_load_plano_schema, "WiSARD",      "wisard"),
    "uleen":          (_load_plano_schema, "ULEEN",       "uleen"),
}

# JSONs especiais que NÃO são entradas por-config (ex: agregadores).
_SKIP_JSON_NAMES = {"all_results.json"}


# Mapeia o nome de pasta sob _reference/ pro nome canônico do modelo.
_REFERENCE_MODEL_NAMES = {
    "wisard": "WiSARD", "cluswisard": "ClusWiSARD",
    "bloomwisard": "BloomWiSARD", "bthowen": "BTHOWeN", "uleen": "ULEEN",
}


def load_all_results(root: str | Path = "notebooks/toniot/results") -> pd.DataFrame:
    """Lê todas as entregas conhecidas + as do gabarito (`_reference/<modelo>/`)."""
    root = Path(root)
    rows: list[dict] = []

    def _iter_files(sub_dir: Path):
        for pat in ("*__*.json", "*__*.jsonl"):
            yield from sub_dir.glob(pat)

    # Entregas dos integrantes
    for rel_path, (loader, model_name, submission) in SUBMISSION_SPECS.items():
        sub_dir = root / rel_path
        if not sub_dir.exists():
            continue
        for fp in sorted(_iter_files(sub_dir)):
            if fp.name in _SKIP_JSON_NAMES:
                continue
            rows.extend(loader(fp, model_name, submission))

    # Gabarito: results/_reference/<modelo>/<base>__<task>.json[l]
    ref_root = root / "_reference"
    if ref_root.exists():
        for sub_dir in sorted(ref_root.iterdir()):
            if not sub_dir.is_dir():
                continue
            model_pretty = _REFERENCE_MODEL_NAMES.get(sub_dir.name, sub_dir.name.capitalize())
            submission = f"{sub_dir.name}_reference"
            for fp in sorted(_iter_files(sub_dir)):
                rows.extend(_load_plano_schema(fp, model_pretty, submission))

    df = pd.DataFrame(rows, columns=CANONICAL_COLS)
    for col in ("encoder_size", "address_size", "bits_total"):
        df[col] = pd.to_numeric(df[col], errors="coerce").astype("Int64")
    return df


def coverage_summary(df: pd.DataFrame) -> pd.DataFrame:
    """Resumo: por (modelo, submissão, base, task), # configs totais e válidas."""
    g = df.groupby(["model", "submission", "base", "task"])
    out = g.agg(
        n_total=("skipped", "size"),
        n_skipped=("skipped", "sum"),
    )
    out["n_valid"] = out["n_total"] - out["n_skipped"]
    return out.reset_index()


def best_per_base(df: pd.DataFrame, metric: str = "f1_macro",
                  group_by_submission: bool = False) -> pd.DataFrame:
    """Pra cada (modelo[, submissão], base, task), devolve a config com maior `metric`.

    Por padrão agrupa só por `model` (BTHOWeN: as 2 submissões disputam
    como uma só). Passe `group_by_submission=True` pra quebrar por
    submissão (usado na auditoria de timing cross-environment).
    """
    sub = df[~df["skipped"]].dropna(subset=[metric])
    if sub.empty:
        return sub
    keys = ["model", "base", "task"]
    if group_by_submission:
        keys = ["model", "submission", "base", "task"]
    idx = sub.groupby(keys)[metric].idxmax()
    return sub.loc[idx].sort_values(["base", "task", "model"])


def axes_summary(df: pd.DataFrame) -> pd.DataFrame:
    """Mostra TODOS os eixos efetivamente variados por (modelo, submissão).

    Inclui termômetro/size/address (comum) + tudo dentro de
    `model_hyperparams` que tenha mais de 1 valor único.
    Útil pra explicar por que duas submissões com "menos eixos" podem ter
    mais configs (ex.: BTHOWeN VsCode tem `addr_sizes` = 3 valores, mas
    `filter_entries × filter_hashes` adicionam outros eixos)."""
    rows = []
    for (model, submission), g in df.groupby(["model", "submission"]):
        row = {
            "model": model,
            "submission": submission,
            "n_configs": len(g),
            "thermo_types": sorted(g["encoder_type"].dropna().unique().tolist()),
            "thermo_sizes": sorted(g["encoder_size"].dropna().unique().tolist()),
            "addr_sizes":   sorted(g["address_size"].dropna().unique().tolist()),
        }
        # Eixos model-specific: varrer chaves de model_hyperparams.
        hyper_axes: dict[str, set] = {}
        for mh in g["model_hyperparams"].dropna():
            if not isinstance(mh, dict):
                continue
            for k, v in mh.items():
                if v is None or isinstance(v, (list, dict)):
                    continue
                hyper_axes.setdefault(k, set()).add(v)
        for k, vals in sorted(hyper_axes.items()):
            if len(vals) > 1:                  # só os REALMENTE variados
                row[k] = sorted(vals)
        rows.append(row)
    return pd.DataFrame(rows)


# =========================================================================== #
# Pipeline de execução (gabarito): preparação de dados, encoders, métricas    #
# =========================================================================== #

# Features por base — derivadas do PLANO §3.4.
FEATURE_COLS: dict[str, tuple[list[str], list[str]]] = {
    # base: (numericas, categoricas-binarias)
    "Fridge":       (["fridge_temperature"],                                  ["temp_condition"]),
    "Garage_Door":  (["sphone_signal"],                                       ["door_state"]),
    "GPS_Tracker":  (["latitude", "longitude"],                               []),
    "Modbus":       (["fc1_read_input_register", "fc2_read_discrete_value",
                      "fc3_read_holding_register", "fc4_read_coil"],          []),
    "Motion_Light": (["motion_status"],                                       ["light_status"]),
    "Thermostat":   (["current_temperature", "thermostat_status"],            []),
    "Weather":      (["temperature", "pressure", "humidity"],                 []),
}

META_COLS = ["date", "time", "label", "type"]


def clean_df(df: pd.DataFrame) -> pd.DataFrame:
    """Padroniza dtypes/strings: lowercase, trim, normaliza sphone_signal, label int."""
    df = df.copy()
    df.columns = [c.lower().strip() for c in df.columns]
    for c in df.columns:
        if not pd.api.types.is_numeric_dtype(df[c]):
            df[c] = df[c].astype(str).str.strip().str.lower()
    if "sphone_signal" in df.columns:
        # após lowercasing/strip: 'true'/'false'/'1'/'0'
        df["sphone_signal"] = (df["sphone_signal"]
                                .map({"true": 1, "false": 0, "1": 1, "0": 0})
                                .astype("Int64"))
    if "label" in df.columns:
        df["label"] = pd.to_numeric(df["label"], errors="coerce").astype("Int64")
    return df


def cat_encoded_bits(df: pd.DataFrame, cat_cols: list[str]) -> int:
    """1 bit por categórica binária; k bits one-hot pra k>2."""
    total = 0
    for c in cat_cols:
        k = df[c].nunique()
        total += 1 if k == 2 else k
    return total


def encode_categoricals(df: pd.DataFrame, cat_cols: list[str]) -> np.ndarray:
    """Codifica categóricas conforme PLANO §3.3 (binária = 1 bit, k-ária = k bits)."""
    if not cat_cols:
        return np.zeros((len(df), 0), dtype=int)
    out_cols = []
    for c in cat_cols:
        vals = sorted(df[c].dropna().unique().tolist())
        if len(vals) == 2:
            out_cols.append((df[c] == vals[1]).astype(int).values[:, None])
        else:
            for v in vals:
                out_cols.append((df[c] == v).astype(int).values[:, None])
    return np.concatenate(out_cols, axis=1)


def _fit_thermometer(thermo_kind: str, thermo_size: int, X_num_train: np.ndarray):
    """Fita UM termômetro multi-feature. API wisardpkg:
    `fit(matrix_n_samples × n_feat)` então `transform(sample_n_feat)` por amostra.
    SimpleThermometer não tem fit; usa min/max por feature."""
    import wisardpkg as wp
    kind = thermo_kind.lower()
    if kind in ("simple", "simples"):
        therms = []
        for j in range(X_num_train.shape[1]):
            mn = float(X_num_train[:, j].min())
            mx = float(X_num_train[:, j].max())
            if mn == mx:
                mx = mn + 1e-9
            therms.append(wp.SimpleThermometer(thermo_size, mn, mx))
        return ("simple", therms)
    cls = {
        "distributive": wp.DistributiveThermometer,
        "distributivo": wp.DistributiveThermometer,
        "gaussian": wp.GaussianThermometer,
        "exponential": wp.ExponentialThermometer,
    }[kind]
    t = cls(thermo_size)
    t.fit(X_num_train.tolist())
    return ("multi", t)


def _transform_thermometer(handle, X_num: np.ndarray, thermo_size: int) -> np.ndarray:
    mode, payload = handle
    n, nf = X_num.shape
    if mode == "simple":
        cols = []
        for j, th in enumerate(payload):
            # SimpleThermometer.transform: aceita Sequence[float] (1 amostra de 1 feature).
            sub = np.empty((n, thermo_size), dtype=int)
            for i in range(n):
                sub[i] = np.array(th.transform([float(X_num[i, j])]).list(), dtype=int)
            cols.append(sub)
        return np.concatenate(cols, axis=1)
    out = np.empty((n, nf * thermo_size), dtype=int)
    for i in range(n):
        out[i] = np.array(payload.transform(X_num[i].tolist()).list(), dtype=int)
    return out


_ENCODE_CACHE: dict[tuple, tuple] = {}

def encode_dataset(df_train: pd.DataFrame, df_test: pd.DataFrame, base: str,
                   thermo_kind: str, thermo_size: int):
    """Termômetro fittado APENAS no train; aplicado nos dois.
    Categóricas codificadas com a política PLANO §3.3 (binária = 1 bit).
    Cacheia por (base, thermo_kind, thermo_size, len(train), len(test)) —
    o mesmo encoding é reusado em N configs de address_size do mesmo modelo."""
    cache_key = (base, thermo_kind.lower(), int(thermo_size), len(df_train), len(df_test))
    if cache_key in _ENCODE_CACHE:
        return _ENCODE_CACHE[cache_key]
    num_cols, cat_cols = FEATURE_COLS[base]
    if num_cols:
        X_num_tr = df_train[num_cols].astype(float).values
        X_num_te = df_test[num_cols].astype(float).values
        handle = _fit_thermometer(thermo_kind, thermo_size, X_num_tr)
        num_tr = _transform_thermometer(handle, X_num_tr, thermo_size)
        num_te = _transform_thermometer(handle, X_num_te, thermo_size)
    else:
        num_tr = np.zeros((len(df_train), 0), dtype=int)
        num_te = np.zeros((len(df_test), 0), dtype=int)
    cat_tr = encode_categoricals(df_train, cat_cols)
    cat_te = encode_categoricals(df_test, cat_cols)
    X_tr = np.concatenate([num_tr, cat_tr], axis=1).astype(int)
    X_te = np.concatenate([num_te, cat_te], axis=1).astype(int)
    info = {
        "n_features_num": len(num_cols),
        "n_features_cat": len(cat_cols),
        "cat_bits": cat_tr.shape[1],
        "bits_total": X_tr.shape[1],
    }
    _ENCODE_CACHE[cache_key] = (X_tr, X_te, info)
    return X_tr, X_te, info


def make_split(df: pd.DataFrame, target_col: str, test_size: float = 0.3, seed: int = 0):
    """Split estratificado por `type`. Devolve (df_train, df_test) — encoders
    fitados depois no train apenas. PLANO §3.3."""
    from sklearn.model_selection import train_test_split
    idx_train, idx_test = train_test_split(
        np.arange(len(df)),
        test_size=test_size, random_state=seed, stratify=df["type"].values,
    )
    return df.iloc[idx_train].reset_index(drop=True), df.iloc[idx_test].reset_index(drop=True)


def ranks_to_score_matrix(ranks: list[dict], class_order: list) -> np.ndarray:
    """Converte saída de m.rank() (lista de dicts {classe: votos}) → matriz
    [n_samples, n_classes] normalizada por linha (proxy de prob)."""
    M = np.zeros((len(ranks), len(class_order)), dtype=float)
    cls_idx = {c: i for i, c in enumerate(class_order)}
    for i, d in enumerate(ranks):
        for cls, v in d.items():
            if cls in cls_idx:
                M[i, cls_idx[cls]] = v
    row_sum = M.sum(axis=1, keepdims=True)
    row_sum[row_sum == 0] = 1.0
    return M / row_sum


def compute_metrics(y_true, y_pred, score_matrix=None, class_order=None) -> dict:
    """Métricas conforme PLANO §2.1."""
    from sklearn.metrics import (
        accuracy_score, precision_score, recall_score, f1_score,
        roc_auc_score, confusion_matrix
    )
    # Normaliza tipos: wisardpkg devolve string, BTHOWeN/ULEEN devolvem int — força string.
    y_true = np.array([str(v) for v in y_true])
    y_pred = np.array([str(v) for v in y_pred])
    if class_order is not None:
        class_order = [str(c) for c in class_order]
    out = {
        "accuracy": accuracy_score(y_true, y_pred),
        "precision_macro": precision_score(y_true, y_pred, average="macro", zero_division=0),
        "precision_weighted": precision_score(y_true, y_pred, average="weighted", zero_division=0),
        "recall_macro": recall_score(y_true, y_pred, average="macro", zero_division=0),
        "recall_weighted": recall_score(y_true, y_pred, average="weighted", zero_division=0),
        "f1_macro": f1_score(y_true, y_pred, average="macro", zero_division=0),
        "f1_weighted": f1_score(y_true, y_pred, average="weighted", zero_division=0),
    }
    auc = None
    if score_matrix is not None and class_order is not None:
        try:
            if len(class_order) == 2:
                pos = class_order[-1]
                pos_idx = class_order.index(pos)
                auc = roc_auc_score((y_true == pos).astype(int), score_matrix[:, pos_idx])
            else:
                # Multi-classe OvR: y_true vs score_matrix [n × n_classes]
                auc = roc_auc_score(y_true, score_matrix, multi_class="ovr",
                                    average="macro", labels=class_order)
        except ValueError:
            auc = None
    out["auc_roc"] = auc
    labels = list(class_order) if class_order is not None else sorted(np.unique(y_true).tolist())
    out["confusion_matrix"] = confusion_matrix(y_true, y_pred, labels=labels).tolist()
    out["labels"] = [str(c) for c in labels]
    return out


def measure_serialized_size(model) -> int | None:
    """Tamanho de serialização *real* do modelo: o que ocupa em disco."""
    # 1. C++ wisardpkg: .json() é a serialização nativa (string JSON)
    if hasattr(model, "json"):
        try:
            s = model.json()
            if isinstance(s, str):
                return len(s.encode("utf-8"))
        except Exception:
            pass
    # 2. Fallback geral: pickle.
    try:
        import pickle
        return len(pickle.dumps(model))
    except Exception:
        return None


def measure_theoretical_size(model) -> int | None:
    """Tamanho 'lógico' do modelo: número de bytes que ele OCUPA pós-deploy.

    BTHOWeN/ULEEN expõem isso (BTHOWeN: filtros Bloom alocados; ULEEN:
    pesos pós-binarização). Outros modelos: None — caller pode usar o
    cálculo manual (# RAMs × #endereços × bytes_por_contador)."""
    for attr in ("model_size_bytes", "deployed_size_bytes"):
        if hasattr(model, attr):
            try:
                return int(getattr(model, attr)())
            except Exception:
                pass
    return None


def measure_inference_latency(predict_one_fn, X_pool: np.ndarray,
                              n_iters: int = 200, n_warmup: int = 20) -> float:
    """Mediana de latência batch=1 em µs. `predict_one_fn` recebe X[i:i+1] e devolve algo."""
    n = len(X_pool)
    if n == 0:
        return 0.0
    # warmup
    for k in range(n_warmup):
        predict_one_fn(X_pool[k % n: k % n + 1])
    times_us = []
    for k in range(n_iters):
        idx = k % n
        t0 = time.perf_counter()
        predict_one_fn(X_pool[idx: idx + 1])
        dt = (time.perf_counter() - t0) * 1e6
        times_us.append(dt)
    return float(np.median(times_us))


def result_dict(*, model: str, base: str, task: str, encoder_type: str,
                encoder_size: int, address_size: int,
                model_hyperparams: dict, input_info: dict,
                metrics: dict | None, skipped: bool, skipped_reason: str | None,
                train_time_s: float | None, inference_latency_us: float | None,
                memory_bytes_serialized: int | None,
                memory_bytes_theoretical: int | None = None,
                machine: str = "?", wisardpkg_version: str = "?") -> dict:
    """Monta um dict no schema canônico PLANO §4."""
    m = {
        "accuracy": 0.0, "precision_macro": 0.0, "precision_weighted": 0.0,
        "recall_macro": 0.0, "recall_weighted": 0.0,
        "f1_macro": 0.0, "f1_weighted": 0.0, "auc_roc": None,
        "memory_bytes_serialized": 0, "memory_bytes_theoretical": 0,
        "train_time_s": 0.0, "inference_latency_us": 0.0,
    }
    if metrics is not None:
        for k, v in metrics.items():
            if k in m:
                m[k] = v
    if train_time_s is not None:
        m["train_time_s"] = train_time_s
    if inference_latency_us is not None:
        m["inference_latency_us"] = inference_latency_us
    if memory_bytes_serialized is not None:
        m["memory_bytes_serialized"] = memory_bytes_serialized
    if memory_bytes_theoretical is not None:
        m["memory_bytes_theoretical"] = memory_bytes_theoretical
    return {
        "model": model,
        "base": base,
        "task": task,
        "encoder": {"type": encoder_type, "size": encoder_size},
        "addressSize": address_size,
        "model_hyperparams": model_hyperparams,
        "split": {"random_state": 0, "test_size": 0.3, "stratified": True},
        "input": input_info,
        "skipped": skipped,
        "skipped_reason": skipped_reason,
        "metrics": m,
        "confusion_matrix": (metrics or {}).get("confusion_matrix", []),
        "labels": (metrics or {}).get("labels", []),
        "machine": machine,
        "wisardpkg_version": wisardpkg_version,
        "timestamp": pd.Timestamp.utcnow().strftime("%Y-%m-%dT%H:%M:%SZ"),
    }


def save_results(results: list[dict], path: Path) -> None:
    """Grava no schema do PLANO (array de configs por arquivo)."""
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(results, indent=1))

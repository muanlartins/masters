"""Utilitários para o notebook 06_consolidado_grupos.ipynb.

Pipeline final unificado:
    1. clean_df(df)          — strip + lower + map textual (neutraliza leaks categóricos)
    2. drop_temporal_leak(df) — descarta date/time (leak determinístico)
    3. encode_features(df)    — LabelEncoder em categóricas residuais + MinMaxScaler

Combined dataset:
    build_combined_dataset() — concatena os 7 CSVs em um único frame (alinhado
    à definição do paper Alsaedi 2020).
"""
from __future__ import annotations

from pathlib import Path
from typing import List, Optional, Tuple

import numpy as np
import pandas as pd
import wisardpkg as wp

DATA_DIR = Path("/Users/muanlartins/repos/masters/data/toniot")

CSVS = {
    "Weather":      "Train_Test_IoT_Weather.csv",
    "Modbus":       "Train_Test_IoT_Modbus.csv",
    "GPS_Tracker":  "Train_Test_IoT_GPS_Tracker.csv",
    "Fridge":       "Train_Test_IoT_Fridge.csv",
    "Thermostat":   "Train_Test_IoT_Thermostat.csv",
    "Motion_Light": "Train_Test_IoT_Motion_Light.csv",
    "Garage_Door":  "Train_Test_IoT_Garage_Door.csv",
}


# ---- cleaning unificado ----------------------------------------------------

# Mapeamento textual exaustivo cobrindo as variantes encontradas no TON_IoT cru:
#   - Fridge.temp_condition: 'high', 'high ', 'high  ', 'low', 'low ', 'low  '
#   - Garage_Door.sphone_signal: '0', '1', 'false  ', 'true  '
#   - Garage_Door.door_state: 'closed', 'open'
#   - Motion_Light.light_status: ' off', ' on', 'off', 'on'
# Strip + lower antes do dict resolve todas as variantes whitespace.
_BOOLEAN_MAP = {
    "off": 0, "on": 1,
    "closed": 0, "open": 1,
    "low": 0, "high": 1,
    "false": 0, "true": 1,
    "0": 0, "1": 1,
    "no": 0, "yes": 1,
    "disabled": 0, "enabled": 1,
    "inactive": 0, "active": 1,
}


def _is_string_col(s: pd.Series) -> bool:
    """True for any string-like column (pandas object, str dtype, StringArray)."""
    return pd.api.types.is_string_dtype(s) or s.dtype == "object"


def clean_df(df: pd.DataFrame) -> pd.DataFrame:
    """Limpeza unificada das CSVs cru do TON_IoT.

    Para cada coluna string:
      1. strip + lower
      2. Mapeia para int via dict booleano (cobre 'high'/'low', 'true'/'false',
         '0'/'1', 'open'/'closed', etc — variantes whitespace já neutralizadas
         pelo strip).
      3. Se algum valor não cai no dict, tenta `pd.to_numeric`; falhando,
         deixa como string (que vai virar LabelEncoder no `encode_features`).

    Tudo isso vivia em 3 funções (clean_df_g1, _g2, _g3) — unificamos na
    versão mais robusta (a estratégia G2 do Grupo 2/Morestem).
    """
    out = df.copy()
    out.columns = out.columns.str.strip()
    for col in out.columns:
        if _is_string_col(out[col]):
            s = out[col].astype(str).str.strip().str.lower()
            mapped = s.map(_BOOLEAN_MAP)
            if mapped.notna().all():
                out[col] = mapped.astype(int)
                continue
            # fallback: try numeric, else keep stripped string
            try:
                out[col] = pd.to_numeric(s)
            except (ValueError, TypeError):
                out[col] = s
    return out


# ---- temporal leak control -------------------------------------------------

TEMPORAL_COLS = {"date", "time", "ts", "timestamp",
                 "hour", "minute", "second",
                 "dayofweek", "day", "month", "year"}


def drop_temporal_leak(df: pd.DataFrame) -> pd.DataFrame:
    """Remove `date`, `time`, `ts` e derivados temporais.

    O paper Alsaedi 2020 (Section VI-A1) descarta explicitamente
    'date, time and timestamp ... they may cause some ML methods to overfit'.
    Adicionamos também a evidência empírica deste trabalho: `date` é leak
    determinístico em 100% das datas nas 7 bases (testbed montado em
    janelas temporais separadas por classe).
    """
    drop_cols = [c for c in df.columns if c.strip().lower() in TEMPORAL_COLS]
    return df.drop(columns=drop_cols)


# ---- presence-bit (helper opcional, para futuro uso com NaN) --------------

def presence_bit_encode(df: pd.DataFrame, fill: float = 0.0) -> pd.DataFrame:
    """Para cada coluna numérica com NaN, adiciona `<col>_present` (binária)
    indicando se o valor estava presente. Preserva o sinal de missingness."""
    out = df.copy()
    for col in df.columns:
        if df[col].isna().any() and pd.api.types.is_numeric_dtype(df[col]):
            out[f"{col}_present"] = (~df[col].isna()).astype(int)
            out[col] = df[col].fillna(fill)
    return out


# ---- combined dataset (alinhado à Tabela 12-13 do paper) -------------------

def build_combined_dataset(apply_cleaning: bool = True,
                            drop_temporal: bool = True) -> pd.DataFrame:
    """Concatena as 7 CSVs num único frame `combined_IoT_dataset`.

    Estratégia (alinhada ao paper Section VI-D1):
      - Concatena as 7 bases.
      - Features ausentes em uma base ficam NaN; o paper imputa com mediana.

    Args:
      apply_cleaning: aplica clean_df antes de concatenar.
      drop_temporal: descarta date/time/ts antes de concatenar.
    """
    parts = []
    for base, fname in CSVS.items():
        df = pd.read_csv(DATA_DIR / fname)
        if apply_cleaning:
            df = clean_df(df)
        if drop_temporal:
            df = drop_temporal_leak(df)
        df["_source_base"] = base
        parts.append(df)
    combined = pd.concat(parts, ignore_index=True, sort=False)
    # impute median (per Alsaedi)
    for col in combined.columns:
        if col in ("label", "type", "_source_base"):
            continue
        if pd.api.types.is_numeric_dtype(combined[col]):
            combined[col] = combined[col].fillna(combined[col].median())
    combined = combined.drop(columns=["_source_base"])
    return combined


# ---- thermometer dispatch (mantém helpers úteis pro sweep) -----------------

def select_thermometer_type(series: pd.Series, feature_name: str = "") -> str:
    """Dispatch automático: 'circular' / 'logarithmic' / 'distributive'."""
    name = feature_name.lower()
    if any(k in name for k in ("longitude", "latitude", "lon", "lat",
                                "hour", "dayofweek")):
        return "circular"
    s = pd.to_numeric(series, errors="coerce").dropna()
    if len(s) < 2:
        return "distributive"
    mx, mn = s.max(), s.min()
    if mx > 1000 or (mn > 0 and mx / mn > 500):
        return "logarithmic"
    return "distributive"


def build_per_feature_thermometer(
    df: pd.DataFrame,
    base_bits: int = 16,
    weights: Optional[dict] = None,
    fit_on: Optional[pd.DataFrame] = None,
) -> Tuple[List, List[str]]:
    """Para cada feature numérica: dispatch automático de termômetro."""
    if fit_on is None:
        fit_on = df
    therms: List = []
    feats: List[str] = []
    for col in df.columns:
        w = (weights or {}).get(col, 1)
        n_bits = base_bits * w
        kind = select_thermometer_type(fit_on[col], col)
        if kind == "logarithmic":
            t = wp.LogarithmicThermometer(n_bits)
            t.fit([[v] for v in fit_on[col].values])
        elif kind == "circular":
            lo = float(fit_on[col].min()); hi = float(fit_on[col].max())
            t = wp.CircularThermometer(n_bits, lo, hi)
        else:
            t = wp.DistributiveThermometer(n_bits)
            t.fit([[v] for v in fit_on[col].values])
        therms.append(t)
        feats.append(col)
    return therms, feats


# ---- G2's contributions: adaptive bleaching + device-specific dispatch -----

def adaptive_bleaching_ternary(model, X_val_binarized, y_val,
                                  max_bleach: int = 256,
                                  classify_fn=None):
    """Ternary search do bleach ótimo no validation set (G2/Morestem).

    Para cada candidato (best - step, best, best + step), avalia accuracy
    no validation set e move para o melhor. Reduz step pela metade quando
    não há mudança até step==1. Retorna (best_bleach, best_acc).

    Args:
      model: WiSARD-like model que aceita `bleach` em classify_fn(model, X, bleach).
      X_val_binarized: features já binarizadas pelo termômetro.
      y_val: labels verdadeiros.
      max_bleach: bleach inicial (padrão 256, busca em [0, 256]).
      classify_fn: função (model, X, bleach) -> y_pred. Default: model.predict(X, bleach).

    Reproduz `evaluate_config` de G2 (train_cluswisard.py:225-262).
    """
    from sklearn.metrics import accuracy_score
    if classify_fn is None:
        classify_fn = lambda m, X, b: [m.predict(x, b) for x in X]

    best = max_bleach // 2
    step = max(max_bleach // 4, 1)
    scores: dict = {}
    while True:
        candidates = [best - step, best, best + step]
        candidates = [c for c in candidates if 0 <= c <= max_bleach]
        accs = []
        for b in candidates:
            if b not in scores:
                y_pred = classify_fn(model, X_val_binarized, b)
                scores[b] = accuracy_score(y_val, y_pred)
            accs.append(scores[b])
        new_best = candidates[accs.index(max(accs))]
        if new_best == best and step == 1:
            break
        best = new_best
        if step > 1:
            step //= 2
    return best, scores[best]


# G2's per-device ULEEN BITS_RESOLUTION dispatch (Ton_IoT_Uleen(4).ipynb)
G2_ULEEN_DEVICE_BITS = {
    "Fridge": 8,
    "Thermostat": 8,
    "Weather": 16,
    "Modbus": 16,
    "GPS_Tracker": 24,
    "Motion_Light": 24,
    "Garage_Door": 24,
}


__all__ = [
    "DATA_DIR", "CSVS",
    "clean_df", "drop_temporal_leak",
    "presence_bit_encode",
    "build_combined_dataset",
    "select_thermometer_type", "build_per_feature_thermometer",
    "adaptive_bleaching_ternary", "G2_ULEEN_DEVICE_BITS",
]

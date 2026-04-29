"""F4RM notebook helpers — Section 4 baseline wrappers + Pareto utilities.

Imported by F4RM.ipynb. Houses code that would otherwise make Section 4 cells
unwieldy:
- Per-system fit_predict_<X>() wrappers returning a uniform result dict.
- Memory accounting per spec §0.5 protocols.
- Pareto frontier extraction + iso-acc/iso-mem comparison.

All wrappers share the signature:

    fit_predict_<X>(X_tr, y_tr, X_te, y_te, hp, seed) -> dict

Returning:
    {test_acc, mem_bytes, mem_method, train_s, infer_us_per_sample,
     hp_id, infeasible, infeasible_reason}
"""
from __future__ import annotations

import io
import json
import math
import os
import pickle
import sys
import tempfile
import time
import warnings
from pathlib import Path
from typing import Any, Iterable

import numpy as np
import pandas as pd

# ============================================================================
# Helpers
# ============================================================================

def _hp_id(hp: dict) -> str:
    """JSON-serialise hyperparams as a stable cache key."""
    return json.dumps(hp, sort_keys=True, default=str)


def _wrap_result(test_acc, mem_bytes, mem_method, train_s, infer_us, hp,
                 infeasible=False, infeasible_reason=""):
    return dict(
        test_acc=float(test_acc) if test_acc is not None else float("nan"),
        mem_bytes=int(mem_bytes) if mem_bytes is not None else 0,
        mem_method=mem_method,
        train_s=float(train_s) if train_s is not None else float("nan"),
        infer_us_per_sample=float(infer_us) if infer_us is not None else float("nan"),
        hp_id=_hp_id(hp),
        infeasible=infeasible,
        infeasible_reason=infeasible_reason,
    )


def _pickle_size_bytes(obj) -> int:
    """Memory accounting for sklearn-style models: pickle.dumps size."""
    return len(pickle.dumps(obj))


def _save_model_size_bytes(model, save_method: str, ext: str = ".bin") -> int:
    """Generic save-model-to-temp-file size measurement (CatBoost/XGBoost/LightGBM)."""
    with tempfile.NamedTemporaryFile(suffix=ext, delete=False) as f:
        path = f.name
    try:
        getattr(model, save_method)(path)
        return os.path.getsize(path)
    finally:
        if os.path.exists(path):
            os.unlink(path)


def _torch_param_bytes(model) -> int:
    """sum(p.numel() for p in model.parameters()) × 4 bytes (float32)."""
    return int(sum(p.numel() for p in model.parameters()) * 4)


# ============================================================================
# Decision Tree
# ============================================================================

def fit_predict_dt(X_tr, y_tr, X_te, y_te, hp, seed):
    from sklearn.tree import DecisionTreeClassifier
    model = DecisionTreeClassifier(
        criterion=hp.get("criterion", "gini"),
        max_depth=hp.get("max_depth", None),
        min_samples_split=hp.get("min_samples_split", 2),
        min_samples_leaf=hp.get("min_samples_leaf", 1),
        ccp_alpha=hp.get("ccp_alpha", 0.0),
        random_state=seed,
    )
    t0 = time.perf_counter(); model.fit(X_tr, y_tr); train_s = time.perf_counter() - t0
    t1 = time.perf_counter(); preds = model.predict(X_te); infer_us = (time.perf_counter() - t1) * 1e6 / max(len(y_te), 1)
    acc = float((preds == y_te).mean())
    mem = _pickle_size_bytes(model)
    return _wrap_result(acc, mem, "pickle", train_s, infer_us, hp)


# ============================================================================
# Random Forest
# ============================================================================

def fit_predict_rf(X_tr, y_tr, X_te, y_te, hp, seed):
    from sklearn.ensemble import RandomForestClassifier
    model = RandomForestClassifier(
        n_estimators=hp.get("n_estimators", 100),
        max_depth=hp.get("max_depth", None),
        min_samples_leaf=hp.get("min_samples_leaf", 1),
        max_features=hp.get("max_features", "sqrt"),
        n_jobs=1,
        random_state=seed,
    )
    t0 = time.perf_counter(); model.fit(X_tr, y_tr); train_s = time.perf_counter() - t0
    t1 = time.perf_counter(); preds = model.predict(X_te); infer_us = (time.perf_counter() - t1) * 1e6 / max(len(y_te), 1)
    acc = float((preds == y_te).mean())
    mem = _pickle_size_bytes(model)
    return _wrap_result(acc, mem, "pickle", train_s, infer_us, hp)


# ============================================================================
# CatBoost
# ============================================================================

def fit_predict_catboost(X_tr, y_tr, X_te, y_te, hp, seed):
    try:
        from catboost import CatBoostClassifier
    except ImportError as e:
        return _wrap_result(None, None, "catboost_unavailable", None, None, hp,
                            infeasible=True, infeasible_reason=f"catboost import failed: {e}")
    # Encode labels to ints (CatBoost requires consistent types)
    classes = sorted(set(y_tr.tolist()) | set(y_te.tolist()))
    cls_to_i = {c: i for i, c in enumerate(classes)}
    y_tr_i = np.array([cls_to_i[c] for c in y_tr])
    y_te_i = np.array([cls_to_i[c] for c in y_te])
    model = CatBoostClassifier(
        iterations=hp.get("iterations", 500),
        depth=hp.get("depth", 6),
        learning_rate=hp.get("learning_rate", 0.1),
        l2_leaf_reg=hp.get("l2_leaf_reg", 3),
        random_seed=seed,
        verbose=False,
        thread_count=1,
    )
    t0 = time.perf_counter(); model.fit(X_tr, y_tr_i); train_s = time.perf_counter() - t0
    t1 = time.perf_counter(); preds = model.predict(X_te).flatten(); infer_us = (time.perf_counter() - t1) * 1e6 / max(len(y_te_i), 1)
    acc = float((preds.astype(int) == y_te_i).mean())
    mem = _save_model_size_bytes(model, "save_model", ".cbm")
    return _wrap_result(acc, mem, "save_model_file", train_s, infer_us, hp)


# ============================================================================
# XGBoost
# ============================================================================

def fit_predict_xgboost(X_tr, y_tr, X_te, y_te, hp, seed):
    try:
        from xgboost import XGBClassifier
    except ImportError as e:
        return _wrap_result(None, None, "xgboost_unavailable", None, None, hp,
                            infeasible=True, infeasible_reason=f"xgboost import failed: {e}")
    classes = sorted(set(y_tr.tolist()) | set(y_te.tolist()))
    cls_to_i = {c: i for i, c in enumerate(classes)}
    y_tr_i = np.array([cls_to_i[c] for c in y_tr])
    y_te_i = np.array([cls_to_i[c] for c in y_te])
    model = XGBClassifier(
        n_estimators=hp.get("n_estimators", 500),
        max_depth=hp.get("max_depth", 6),
        learning_rate=hp.get("learning_rate", 0.1),
        reg_lambda=hp.get("reg_lambda", 1.0),
        random_state=seed,
        tree_method="hist",
        verbosity=0,
        n_jobs=1,
    )
    t0 = time.perf_counter(); model.fit(X_tr, y_tr_i); train_s = time.perf_counter() - t0
    t1 = time.perf_counter(); preds = model.predict(X_te); infer_us = (time.perf_counter() - t1) * 1e6 / max(len(y_te_i), 1)
    acc = float((preds == y_te_i).mean())
    mem = _save_model_size_bytes(model, "save_model", ".json")
    return _wrap_result(acc, mem, "save_model_file", train_s, infer_us, hp)


# ============================================================================
# LightGBM
# ============================================================================

def fit_predict_lightgbm(X_tr, y_tr, X_te, y_te, hp, seed):
    try:
        from lightgbm import LGBMClassifier
    except ImportError as e:
        return _wrap_result(None, None, "lightgbm_unavailable", None, None, hp,
                            infeasible=True, infeasible_reason=f"lightgbm import failed: {e}")
    classes = sorted(set(y_tr.tolist()) | set(y_te.tolist()))
    cls_to_i = {c: i for i, c in enumerate(classes)}
    y_tr_i = np.array([cls_to_i[c] for c in y_tr])
    y_te_i = np.array([cls_to_i[c] for c in y_te])
    model = LGBMClassifier(
        n_estimators=hp.get("n_estimators", 500),
        num_leaves=hp.get("num_leaves", 31),
        learning_rate=hp.get("learning_rate", 0.1),
        reg_lambda=hp.get("reg_lambda", 1.0),
        random_state=seed,
        verbose=-1,
        n_jobs=1,
    )
    t0 = time.perf_counter(); model.fit(X_tr, y_tr_i); train_s = time.perf_counter() - t0
    t1 = time.perf_counter(); preds = model.predict(X_te); infer_us = (time.perf_counter() - t1) * 1e6 / max(len(y_te_i), 1)
    acc = float((preds == y_te_i).mean())
    # LightGBM uses booster_.save_model
    with tempfile.NamedTemporaryFile(suffix=".txt", delete=False) as f:
        path = f.name
    try:
        model.booster_.save_model(path)
        mem = os.path.getsize(path)
    finally:
        if os.path.exists(path):
            os.unlink(path)
    return _wrap_result(acc, mem, "save_model_file", train_s, infer_us, hp)


# ============================================================================
# MLP (sklearn)
# ============================================================================

def fit_predict_mlp(X_tr, y_tr, X_te, y_te, hp, seed):
    from sklearn.neural_network import MLPClassifier
    classes = sorted(set(y_tr.tolist()) | set(y_te.tolist()))
    cls_to_i = {c: i for i, c in enumerate(classes)}
    y_tr_i = np.array([cls_to_i[c] for c in y_tr])
    y_te_i = np.array([cls_to_i[c] for c in y_te])
    with warnings.catch_warnings():
        warnings.simplefilter("ignore")
        model = MLPClassifier(
            hidden_layer_sizes=tuple(hp.get("hidden_layer_sizes", (64,))),
            learning_rate_init=hp.get("learning_rate_init", 1e-3),
            max_iter=hp.get("max_iter", 200),
            alpha=hp.get("alpha", 1e-4),
            early_stopping=True,
            validation_fraction=0.1,
            random_state=seed,
        )
        t0 = time.perf_counter(); model.fit(X_tr, y_tr_i); train_s = time.perf_counter() - t0
        t1 = time.perf_counter(); preds = model.predict(X_te); infer_us = (time.perf_counter() - t1) * 1e6 / max(len(y_te_i), 1)
    acc = float((preds == y_te_i).mean())
    n_params = sum(c.size for c in model.coefs_) + sum(b.size for b in model.intercepts_)
    mem = int(n_params * 4)
    return _wrap_result(acc, mem, "param_count_f32", train_s, infer_us, hp)


# ============================================================================
# FT-Transformer (rtdl_revisiting_models)
# ============================================================================

def fit_predict_fttransformer(X_tr, y_tr, X_te, y_te, hp, seed):
    try:
        import torch
        import torch.nn as nn
        from torch.utils.data import DataLoader, TensorDataset
        import rtdl_revisiting_models as rtdl
    except ImportError as e:
        return _wrap_result(None, None, "fttransformer_unavailable", None, None, hp,
                            infeasible=True, infeasible_reason=f"deps missing: {e}")

    classes = sorted(set(y_tr.tolist()) | set(y_te.tolist()))
    nc = len(classes)
    cls_to_i = {c: i for i, c in enumerate(classes)}
    y_tr_i = torch.tensor([cls_to_i[c] for c in y_tr], dtype=torch.long)
    y_te_i = torch.tensor([cls_to_i[c] for c in y_te], dtype=torch.long)
    X_tr_t = torch.tensor(X_tr, dtype=torch.float32)
    X_te_t = torch.tensor(X_te, dtype=torch.float32)

    torch.manual_seed(seed)
    n_features = X_tr.shape[1]
    d_block = hp.get("d_token", 64)  # rtdl_revisiting_models calls it d_block
    n_blocks = hp.get("n_blocks", 3)
    n_heads = hp.get("n_heads", 8)
    attention_dropout = hp.get("attention_dropout", 0.2)
    lr = hp.get("learning_rate", 1e-4)
    n_epochs = hp.get("n_epochs", 30)
    batch_size = hp.get("batch_size", min(256, len(X_tr)))

    # FTTransformer signature: (*, n_cont_features, cat_cardinalities, _is_default=False, **backbone_kwargs)
    try:
        model = rtdl.FTTransformer(
            n_cont_features=n_features,
            cat_cardinalities=[],
            d_out=nc,
            n_blocks=n_blocks,
            d_block=d_block,
            attention_n_heads=n_heads,
            attention_dropout=attention_dropout,
            ffn_d_hidden=int(d_block * 4 / 3),
            ffn_d_hidden_multiplier=None,
            ffn_dropout=0.1,
            residual_dropout=0.0,
        )
    except Exception as e:
        return _wrap_result(None, None, "fttransformer_init_failed", None, None, hp,
                            infeasible=True, infeasible_reason=str(e))

    optimizer = torch.optim.AdamW(model.parameters(), lr=lr)
    loss_fn = nn.CrossEntropyLoss()
    loader = DataLoader(TensorDataset(X_tr_t, y_tr_i), batch_size=batch_size, shuffle=True)

    t0 = time.perf_counter()
    model.train()
    for _ in range(n_epochs):
        for xb, yb in loader:
            optimizer.zero_grad()
            out = model(xb, None)
            loss = loss_fn(out, yb)
            loss.backward()
            optimizer.step()
    train_s = time.perf_counter() - t0

    model.eval()
    t1 = time.perf_counter()
    with torch.no_grad():
        out = model(X_te_t, None)
        preds = out.argmax(dim=1).numpy()
    infer_us = (time.perf_counter() - t1) * 1e6 / max(len(y_te_i), 1)
    acc = float((preds == y_te_i.numpy()).mean())
    mem = _torch_param_bytes(model)
    return _wrap_result(acc, mem, "param_count_f32", train_s, infer_us, hp)


# ============================================================================
# TabPFN-v2
# ============================================================================

def fit_predict_tabpfn(X_tr, y_tr, X_te, y_te, hp, seed):
    try:
        from tabpfn import TabPFNClassifier
    except ImportError as e:
        return _wrap_result(None, None, "tabpfn_unavailable", None, None, hp,
                            infeasible=True, infeasible_reason=f"tabpfn import failed: {e}")
    if len(X_tr) > 10000:
        return _wrap_result(None, None, "tabpfn_size_limit", None, None, hp,
                            infeasible=True,
                            infeasible_reason=f"n_train={len(X_tr)} > TabPFN-v2 limit (10000)")
    try:
        model = TabPFNClassifier(device="cpu", random_state=seed,
                                  ignore_pretraining_limits=False)
        t0 = time.perf_counter(); model.fit(X_tr, y_tr); train_s = time.perf_counter() - t0
        t1 = time.perf_counter(); preds = model.predict(X_te); infer_us = (time.perf_counter() - t1) * 1e6 / max(len(y_te), 1)
    except Exception as e:
        return _wrap_result(None, None, "tabpfn_runtime_error", None, None, hp,
                            infeasible=True, infeasible_reason=str(e))
    acc = float((preds == y_te).mean())
    # TabPFN-v2 model footprint: pretrained weights ~ 100MB. Document this.
    # Use placeholder constant for now; the spec asks for "pretrained weights size + reference set".
    PRETRAINED_BYTES = 100 * 1024 * 1024
    reference_set_bytes = X_tr.nbytes + y_tr.nbytes
    mem = PRETRAINED_BYTES + reference_set_bytes
    return _wrap_result(acc, mem, "tabpfn_pretrained_plus_refset", train_s, infer_us, hp)


# ============================================================================
# Hyperparameter grid generators
# ============================================================================

def grid_dt():
    """~360 cells before filtering."""
    grid = []
    for criterion in ("gini", "entropy"):
        for max_depth in (None, 4, 8, 16, 32):
            for mss in (2, 10, 50):
                for msl in (1, 5, 20):
                    for ccp in (0.0, 0.001, 0.01, 0.1):
                        grid.append(dict(criterion=criterion, max_depth=max_depth,
                                          min_samples_split=mss, min_samples_leaf=msl,
                                          ccp_alpha=ccp))
    return grid

def grid_rf():
    grid = []
    for n_est in (10, 50, 100, 200):
        for md in (None, 8, 16):
            for msl in (1, 5):
                for mf in ("sqrt", "log2", 1.0):
                    grid.append(dict(n_estimators=n_est, max_depth=md,
                                      min_samples_leaf=msl, max_features=mf))
    return grid

def grid_catboost():
    grid = []
    for it in (100, 500, 1000):
        for d in (4, 6, 8, 10):
            for lr in (0.03, 0.1, 0.3):
                for l2 in (1, 3, 10):
                    grid.append(dict(iterations=it, depth=d, learning_rate=lr, l2_leaf_reg=l2))
    return grid

def grid_xgboost():
    grid = []
    for n_est in (100, 500, 1000):
        for md in (4, 6, 8, 10):
            for lr in (0.03, 0.1, 0.3):
                for rl in (0.1, 1.0, 10.0):
                    grid.append(dict(n_estimators=n_est, max_depth=md, learning_rate=lr, reg_lambda=rl))
    return grid

def grid_lightgbm():
    grid = []
    for n_est in (100, 500, 1000):
        for nl in (15, 31, 63, 127):
            for lr in (0.03, 0.1, 0.3):
                for rl in (0.1, 1.0, 10.0):
                    grid.append(dict(n_estimators=n_est, num_leaves=nl, learning_rate=lr, reg_lambda=rl))
    return grid

def grid_mlp():
    grid = []
    for hls in ((32,), (64,), (128,), (64, 32), (128, 64), (256, 128, 64), (512, 256, 128, 64)):
        for lr in (1e-3, 1e-4):
            for max_iter in (200, 500):
                for alpha in (1e-4, 1e-2):
                    grid.append(dict(hidden_layer_sizes=hls, learning_rate_init=lr,
                                      max_iter=max_iter, alpha=alpha))
    return grid

def grid_fttransformer():
    grid = []
    for d_token in (32, 64):
        for n_blocks in (2, 3, 4):
            for ad in (0.0, 0.2):
                for nh in (4, 8):
                    for lr in (1e-4, 1e-3):
                        grid.append(dict(d_token=d_token, n_blocks=n_blocks,
                                          attention_dropout=ad, n_heads=nh,
                                          learning_rate=lr))
    return grid

def grid_tabpfn():
    return [dict(default=True)]


# ============================================================================
# BTHOWeN (Susskind et al., PACT 2022 / arXiv 2203.01479)
#
# Clean reference port at wisardpkg.models.bthowen. Built on our
# wisardpkg's BloomWisard with the H3 hash mode (added for this port) and the
# native GaussianThermometer. Memory accounting matches the paper's
# calc_model_size.py — bits_in_model / 8.
# ============================================================================

def fit_predict_bthowen(X_tr, y_tr, X_te, y_te, hp, seed):
    try:
        from wisardpkg.models import BTHOWeN
    except ImportError as e:
        return _wrap_result(None, None, "bthowen_unavailable", None, None, hp,
                            infeasible=True, infeasible_reason=f"BTHOWeN import failed: {e}")
    try:
        model = BTHOWeN(
            addressSize=hp["addressSize"],
            numBits=hp["numBits"],
            numHashes=hp["numHashes"],
            bitsPerInput=hp["bitsPerInput"],
        )
        t0 = time.perf_counter(); model.fit(X_tr, y_tr, seed=seed); train_s = time.perf_counter() - t0
        t1 = time.perf_counter(); preds = model.predict(X_te); infer_us = (time.perf_counter() - t1) * 1e6 / max(len(y_te), 1)
        # Compare as strings — BTHOWeN.predict returns str class labels
        y_te_str = np.array([str(v) for v in y_te])
        acc = float((preds.astype(str) == y_te_str).mean())
        mem = model.model_size_bytes()
    except Exception as e:
        return _wrap_result(None, None, "bthowen_runtime_error", None, None, hp,
                            infeasible=True, infeasible_reason=str(e))
    return _wrap_result(acc, mem, "bthowen_analytical_bloom_post_binarize",
                        train_s, infer_us, hp)


def grid_bthowen():
    """48-cell hyperparameter grid covering memory and accuracy axes.

    Spans the regimes used in the BTHOWeN paper Table 3:
    - small/cheap: (addressSize=6, numBits=128, numHashes=2, bitsPerInput=3)
    - mid: (12, 512, 2, 3)
    - large/accurate: (28, 2048, 4, 9)
    """
    grid = []
    for addr in (6, 12, 20, 28):
        for nbits in (128, 512, 2048):
            for nhash in (2, 4):
                for bpi in (3, 9):
                    grid.append(dict(
                        addressSize=addr, numBits=nbits,
                        numHashes=nhash, bitsPerInput=bpi,
                    ))
    return grid


# ============================================================================
# DWN — Differentiable Weightless Neural Networks
# (Bacellar et al., ICML 2024 / arXiv 2410.11112)
#
# Clean PyTorch port at wisardpkg.models.dwn. Replaces the reference's
# CUDA-only EFDFunction with a vectorised CPU implementation that matches
# the kernel formula bit-for-bit (verified by direct comparison and by
# torch.autograd.gradcheck on the LUT gradient — the input gradient is an
# intentional approximation, same situation as STE).
# ============================================================================

def fit_predict_dwn(X_tr, y_tr, X_te, y_te, hp, seed):
    try:
        from wisardpkg.models import DWNClassifier
    except ImportError as e:
        return _wrap_result(None, None, "dwn_unavailable", None, None, hp,
                            infeasible=True, infeasible_reason=f"DWN import failed: {e}")
    try:
        model = DWNClassifier(
            bits_per_input=hp.get("bits_per_input", 3),
            n=hp.get("n", 6),
            num_luts_l1=hp.get("num_luts_l1", 1000),
            num_luts_l2=hp.get("num_luts_l2", 500),
            tau=hp.get("tau", 1 / 0.3),
            epochs=hp.get("epochs", 15),
            lr=hp.get("lr", 1e-2),
            batch_size=hp.get("batch_size", 32),
            scheduler_step=hp.get("scheduler_step", 8),
            scheduler_gamma=hp.get("scheduler_gamma", 0.1),
        )
        t0 = time.perf_counter(); model.fit(X_tr, y_tr, seed=seed); train_s = time.perf_counter() - t0
        t1 = time.perf_counter(); preds = model.predict(X_te); infer_us = (time.perf_counter() - t1) * 1e6 / max(len(y_te), 1)
        y_te_str = np.array([str(v) for v in y_te])
        acc = float((preds.astype(str) == y_te_str).mean())
        mem = model.deployed_size_bytes()
    except Exception as e:
        return _wrap_result(None, None, "dwn_runtime_error", None, None, hp,
                            infeasible=True, infeasible_reason=str(e))
    return _wrap_result(acc, mem, "dwn_binarized_lut",
                        train_s, infer_us, hp)


def grid_dwn():
    """Compact 12-cell hyperparameter grid spanning the small/mid/large regimes.

    DWN training is gradient-based and dominates per-cell wall clock; we trade
    point density for breadth across datasets. Grid is structured so each
    (n, bits_per_input) pair has 3 capacity points.
    """
    grid = []
    base = dict(tau=1/0.3, lr=1e-2, batch_size=32, scheduler_step=8, scheduler_gamma=0.1)
    # (bits_per_input, n, l1, l2, epochs)
    cells = [
        (2, 4, 200, 100, 10),    # tiny
        (2, 6, 500, 250, 10),    # small
        (3, 6, 500, 250, 15),    # small-mid
        (3, 6, 1000, 500, 15),   # mid
        (6, 6, 1000, 500, 15),   # mid-large
        (6, 6, 2000, 1000, 20),  # large
    ]
    for bpi, n, l1, l2, ep in cells:
        grid.append(dict(bits_per_input=bpi, n=n, num_luts_l1=l1, num_luts_l2=l2,
                          epochs=ep, **base))
    return grid


# ============================================================================
# ULEEN — Ultra Low-Energy Edge Networks
# (Susskind et al., ACM TACO 2023, doi:10.1145/3629522)
#
# Clean PyTorch port at wisardpkg.models.uleen. The reference's libtorch
# C++ extension for H3 hashing is replaced by a vectorised einsum+XOR
# implementation; everything else is standard PyTorch autograd through STE.
# ============================================================================

def fit_predict_uleen(X_tr, y_tr, X_te, y_te, hp, seed):
    try:
        from wisardpkg.models import ULEENClassifier
    except ImportError as e:
        return _wrap_result(None, None, "uleen_unavailable", None, None, hp,
                            infeasible=True, infeasible_reason=f"ULEEN import failed: {e}")
    try:
        model = ULEENClassifier(
            bits_per_input=hp.get("bits_per_input", 3),
            filter_inputs=hp.get("filter_inputs", 12),
            filter_entries=hp.get("filter_entries", 64),
            filter_hash_functions=hp.get("filter_hash_functions", 2),
            n_submodels=hp.get("n_submodels", 3),
            dropout_p=hp.get("dropout_p", 0.0),
            epochs=hp.get("epochs", 30),
            lr=hp.get("lr", 1e-2),
            batch_size=hp.get("batch_size", 32),
            decay_lr=hp.get("decay_lr", True),
        )
        t0 = time.perf_counter(); model.fit(X_tr, y_tr, seed=seed); train_s = time.perf_counter() - t0
        t1 = time.perf_counter(); preds = model.predict(X_te); infer_us = (time.perf_counter() - t1) * 1e6 / max(len(y_te), 1)
        y_te_str = np.array([str(v) for v in y_te])
        acc = float((preds.astype(str) == y_te_str).mean())
        mem = model.deployed_size_bytes()
    except Exception as e:
        return _wrap_result(None, None, "uleen_runtime_error", None, None, hp,
                            infeasible=True, infeasible_reason=str(e))
    return _wrap_result(acc, mem, "uleen_binarized_table",
                        train_s, infer_us, hp)


def grid_uleen():
    """6-cell hyperparameter grid spanning the small/mid/large regimes.

    Mirrors the structure of the DWN grid: 6 cells covering memory and
    accuracy regimes. ULEEN's per-cell wall clock is similar to DWN's;
    multiple submodels multiply training cost linearly.

    Cells loosely follow the structure of ULEEN paper Table 2 but use
    smaller `filter_inputs` to remain useful on tiny tabular datasets
    (Iris has only 12 input bits at bits_per_input=3 — large `filter_inputs`
    collapses the model to 1 filter per discriminator).

    Cells:
    - tiny single submodel
    - small ensemble
    - mid bpi/ensemble
    - mid filter
    - large filter
    - XL (mostly useful for higher-feature datasets)
    """
    grid = []
    base = dict(lr=1e-2, batch_size=32, decay_lr=True, dropout_p=0.0)
    # (bits_per_input, filter_inputs, filter_entries, filter_hash_functions, n_submodels, epochs, batch_size)
    cells = [
        (3,  4,  64, 1, 1, 30, 16),   # tiny single
        (3,  4,  64, 2, 3, 30, 16),   # small ensemble
        (6,  4, 128, 2, 3, 40, 32),   # mid-bpi
        (6,  6, 128, 2, 3, 40, 32),   # mid filter
        (6,  8, 256, 2, 5, 50, 32),   # large
        (6, 12, 256, 2, 5, 50, 32),   # XL (degenerate on smallest datasets)
    ]
    for bpi, fi, fe, fh, ns, ep, bs in cells:
        cfg = {**base, "batch_size": bs}
        grid.append(dict(bits_per_input=bpi, filter_inputs=fi, filter_entries=fe,
                          filter_hash_functions=fh, n_submodels=ns,
                          epochs=ep, **cfg))
    return grid


# ============================================================================
# Pareto frontier extraction
# ============================================================================

def per_dataset_frontier(df: pd.DataFrame, dataset: str, system: str,
                         maximize="test_acc", minimize="mem_bytes") -> pd.DataFrame:
    """Returns the Pareto frontier on (maximize, minimize) for the system on the
    dataset, computed across all hyperparameter cells (mean over seeds).

    Filters out infeasible rows (seed != -1 and not infeasible)."""
    sub = df[(df["dataset"] == dataset) & (df["system"] == system) &
              (df["seed"] >= 0) & (~df.get("infeasible", False))]
    if len(sub) == 0:
        return pd.DataFrame()
    means = sub.groupby("hp_id").agg(
        test_acc=(maximize, "mean"),
        mem_bytes=(minimize, "mean"),
        train_s=("train_s", "mean"),
        infer_us_per_sample=("infer_us_per_sample", "mean"),
    ).reset_index()
    keep = []
    for i, row in means.iterrows():
        dominated = ((means["test_acc"] >= row["test_acc"]) &
                      (means["mem_bytes"] <= row["mem_bytes"]) &
                      ((means["test_acc"] > row["test_acc"]) |
                       (means["mem_bytes"] < row["mem_bytes"])))
        if not dominated.any():
            keep.append(i)
    return means.loc[keep].sort_values("mem_bytes").reset_index(drop=True)


def iso_acc_iso_mem_compare(frontier_a: pd.DataFrame, frontier_b: pd.DataFrame,
                            n_acc_levels=101, n_mem_levels=50,
                            mem_log_lo=1024, mem_log_hi=1e9) -> dict:
    """Aggregate iso-acc and iso-mem wins for system_a vs system_b on one dataset."""
    if len(frontier_a) == 0 or len(frontier_b) == 0:
        return dict(iso_acc_levels_compared=0, iso_acc_wins_a=0, iso_acc_wins_b=0,
                    iso_mem_levels_compared=0, iso_mem_wins_a=0, iso_mem_wins_b=0,
                    feasible_acc_overlap=(np.nan, np.nan),
                    feasible_mem_overlap=(np.nan, np.nan))
    a_acc = (frontier_a["test_acc"].min(), frontier_a["test_acc"].max())
    b_acc = (frontier_b["test_acc"].min(), frontier_b["test_acc"].max())
    a_mem = (frontier_a["mem_bytes"].min(), frontier_a["mem_bytes"].max())
    b_mem = (frontier_b["mem_bytes"].min(), frontier_b["mem_bytes"].max())
    overlap_acc = (max(a_acc[0], b_acc[0]), min(a_acc[1], b_acc[1]))
    overlap_mem = (max(a_mem[0], b_mem[0]), min(a_mem[1], b_mem[1]))

    iso_acc_compared = 0; iso_acc_a = 0; iso_acc_b = 0
    if overlap_acc[1] >= overlap_acc[0]:
        for A in np.linspace(overlap_acc[0], overlap_acc[1], n_acc_levels):
            ok_a = frontier_a[frontier_a["test_acc"] >= A]
            ok_b = frontier_b[frontier_b["test_acc"] >= A]
            if len(ok_a) and len(ok_b):
                iso_acc_compared += 1
                if ok_a["mem_bytes"].min() < ok_b["mem_bytes"].min(): iso_acc_a += 1
                elif ok_b["mem_bytes"].min() < ok_a["mem_bytes"].min(): iso_acc_b += 1

    iso_mem_compared = 0; iso_mem_a = 0; iso_mem_b = 0
    if overlap_mem[1] >= overlap_mem[0]:
        m_lo = max(mem_log_lo, overlap_mem[0])
        m_hi = min(mem_log_hi, overlap_mem[1])
        if m_hi > m_lo:
            for M in np.logspace(np.log10(m_lo), np.log10(m_hi), n_mem_levels):
                ok_a = frontier_a[frontier_a["mem_bytes"] <= M]
                ok_b = frontier_b[frontier_b["mem_bytes"] <= M]
                if len(ok_a) and len(ok_b):
                    iso_mem_compared += 1
                    if ok_a["test_acc"].max() > ok_b["test_acc"].max(): iso_mem_a += 1
                    elif ok_b["test_acc"].max() > ok_a["test_acc"].max(): iso_mem_b += 1

    return dict(
        iso_acc_levels_compared=iso_acc_compared,
        iso_acc_wins_a=iso_acc_a,
        iso_acc_wins_b=iso_acc_b,
        iso_mem_levels_compared=iso_mem_compared,
        iso_mem_wins_a=iso_mem_a,
        iso_mem_wins_b=iso_mem_b,
        feasible_acc_overlap=overlap_acc,
        feasible_mem_overlap=overlap_mem,
    )

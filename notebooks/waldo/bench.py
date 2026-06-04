"""Classification benchmark harness for the character-recognition task.

Encodes patches, trains any model, evaluates, and measures the four metrics we
care about (the energy axis is dropped as unmeasurable; memory is its proxy):
  - macro-F1 / accuracy
  - model memory (bytes)
  - train time (s)
  - inference time (s / sample)

WNN family gets a WNN-native binary encoding (per-channel thermometer); weighted
models get raw float pixels. The encoding is a first-class experimental knob.
"""
import time
import pickle
import numpy as np
from sklearn.metrics import f1_score, accuracy_score

import wisardpkg as wp
import characters as C
import detector as D


# ---------------------------------------------------------------------------
# Encodings — each maps a canon uint8 stack (N,s,s,3) -> (N, D) uint8 bits.
# The encoder is a first-class experimental knob: it sets how many bits feed
# the WNN, which drives memory (more bits -> more/bigger RAMs) and accuracy.
# ---------------------------------------------------------------------------
def to_canon(X, size):
    """Resize a stack of patches (N,H,W,3) uint8 to (N,size,size,3) uint8."""
    from PIL import Image
    out = np.empty((len(X), size, size, 3), dtype=np.uint8)
    for i, p in enumerate(X):
        out[i] = np.asarray(Image.fromarray(p).resize((size, size), Image.BILINEAR))
    return out


def thermometer_bits(canon_uint8, levels=8):
    """Per-channel thermometer encoding. (N,s,s,3) uint8 -> (N, s*s*3*levels) uint8.
    WNN-native: each channel value v∈[0,1] becomes `levels` bits [v>=k/levels].
    Captures full colour (needed to separate Odlaw's black/yellow from red/white).
    Bits/pixel = 3*levels (24 at levels=8) — the dense, high-memory encoding."""
    f = canon_uint8.astype(np.float32) / 255.0
    N = f.shape[0]
    thr = (np.arange(1, levels + 1) / (levels + 1)).reshape(1, 1, 1, 1, levels)
    bits = (f[..., None] >= thr).astype(np.uint8)          # (N,s,s,3,levels)
    return bits.reshape(N, -1)


# ---------------------------------------------------------------------------
# Fittable thermometers — the threshold set is the encoding's key design choice.
# A scalar v∈[0,1] becomes `size` bits [v>=θ_k]; the θ_k differ by KIND:
#   simple       : evenly spaced in [0,1] (ignores the data distribution)
#   distributive : at the data's empirical quantiles (equal mass per bin)
#   gaussian     : spaced per a fitted Normal (mean/std of the channel)
# Fit on TRAIN pixels, apply the same thresholds to test (no leakage).
# ---------------------------------------------------------------------------
THERM_KINDS = ('simple', 'distributive', 'gaussian')


def fit_thermometer(canon_uint8, kind='distributive', size=8):
    """Return per-channel thresholds (3, size) for the given thermometer kind."""
    from scipy.stats import norm
    f = canon_uint8.astype(np.float32) / 255.0
    qs = np.arange(1, size + 1) / (size + 1)
    th = np.zeros((3, size), dtype=np.float32)
    for ch in range(3):
        vals = f[..., ch].ravel()
        if kind == 'simple':
            th[ch] = qs
        elif kind == 'distributive':
            th[ch] = np.quantile(vals, qs)
        elif kind == 'gaussian':
            th[ch] = np.clip(vals.mean() + vals.std() * norm.ppf(qs), 0.0, 1.0)
        else:
            raise ValueError(kind)
    return th


def thermometer_encode(canon_uint8, th):
    """Encode with pre-fit thresholds `th` (3, size) -> (N, s*s*3*size) uint8."""
    f = canon_uint8.astype(np.float32) / 255.0
    bits = (f[..., None] >= th.reshape(1, 1, 1, 3, th.shape[1])).astype(np.uint8)
    return bits.reshape(len(canon_uint8), -1)


def colormask_bits(canon_uint8):
    """Compact 3-bit/pixel categorical (is_red/is_white/is_dark). 8x fewer bits
    than thermometer@8 — the lever that should make WiSARD memory-competitive."""
    N = len(canon_uint8)
    return np.stack([D.colormask_3bits(p) for p in canon_uint8]).reshape(N, -1).astype(np.uint8)


def colormask_stripe_bits(canon_uint8):
    """4-bit/pixel: colormask + the scale-invariant stripe-pattern bit. Adds the
    one structural feature that separates stripes from same-colour clutter."""
    N = len(canon_uint8)
    return np.stack([D.slim_encoder(p) for p in canon_uint8]).reshape(N, -1).astype(np.uint8)


# Named encoders for the sweep: name -> (fn, bits/pixel-at-canon-s description)
ENCODERS = {
    'therm8':         lambda Xc: thermometer_bits(Xc, 8),    # 24 bpp (dense)
    'therm4':         lambda Xc: thermometer_bits(Xc, 4),    # 12 bpp
    'colormask':      colormask_bits,                        #  3 bpp (compact)
    'colormask+stripe': colormask_stripe_bits,               #  4 bpp
}


def raw_float(canon_uint8):
    return (canon_uint8.astype(np.float32) / 255.0).reshape(len(canon_uint8), -1)


# ---------------------------------------------------------------------------
# Model wrappers — uniform .fit(Xc,y)/.predict(Xc) + .mem_bytes(), where Xc is
# the canon uint8 stack; each wrapper applies its own encoding.
# ---------------------------------------------------------------------------
# ---------------------------------------------------------------------------
# CONSISTENT MEMORY METRIC
# Definition: bytes to store all learned parameters / table entries for inference,
# at the implementation's native precision. Computed analytically per family so
# it does not depend on (often broken/verbose) serialization:
#   - WiSARD/ClusWiSARD : getsizeof() — the lib's real allocated bytes of the
#       sparse address->counter maps (only seen addresses are stored).
#   - BloomWiSARD       : n_classes * nRAMS * numBits * COUNTER_BYTES. Its dense
#       counting-Bloom arrays are NOT in json() and getsizeof() returns config-only
#       (~88 B) — a bug; we compute the true footprint structurally.
#   - RandomForest      : total tree nodes * (node fields + per-class value).
#   - Linear/SVM/CNN    : learned parameters * native dtype bytes.
BLOOM_COUNTER_BYTES = 4   # bloomfilter.cc stores std::vector<int> counters


def _wnn_mem_bytes(m, n_classes):
    if hasattr(m, 'getNumBits') and hasattr(m, 'getNumberOfRAMS'):   # BloomWiSARD
        return int(n_classes) * int(m.getNumberOfRAMS()) * int(m.getNumBits()) * BLOOM_COUNTER_BYTES
    if hasattr(m, 'getsizeof'):                                      # WiSARD / ClusWiSARD
        return int(m.getsizeof())
    return np.nan


class WNNModel:
    """WiSARD-family classifier (wisardpkg) with a pluggable binary encoder.

    `encoder` is a callable (canon uint8 stack -> N x D uint8 bits); `factory`
    is (bits_len -> wisardpkg model). The encoder is the key memory/accuracy
    knob being swept."""
    def __init__(self, name, factory, encoder=None):
        self.name = name
        self.factory = factory
        self.encoder = encoder if encoder is not None else (lambda Xc: thermometer_bits(Xc, 8))

    def fit(self, Xc, y):
        self.n_classes = len(np.unique(y))
        B = self.encoder(Xc)
        self.bits_len = B.shape[1]
        ds = wp.DataSet()
        for b, lab in zip(B, y):
            ds.add(b.tolist(), str(int(lab)))
        self.m = self.factory(self.bits_len)
        self.m.train(ds)
        return self

    def predict(self, Xc):
        B = self.encoder(Xc)
        ds = wp.DataSet()
        for b in B:
            ds.add(b.tolist(), '0')
        return np.array([int(o) for o in self.m.classify(ds)])

    def mem_bytes(self):
        return _wnn_mem_bytes(self.m, self.n_classes)


class SklearnModel:
    def __init__(self, name, clf):
        self.name, self.clf = name, clf

    def fit(self, Xc, y):
        self.clf.fit(raw_float(Xc), y); return self

    def predict(self, Xc):
        return self.clf.predict(raw_float(Xc))

    def mem_bytes(self):
        clf = self.clf
        if hasattr(clf, 'estimators_'):          # RandomForest / forest ensembles
            nodes = sum(e.tree_.node_count for e in clf.estimators_)
            nc = getattr(clf, 'n_classes_', 1)
            return int(nodes) * (7 * 8 + int(nc) * 8)   # 7 int64/float64 node fields + value[]
        if hasattr(clf, 'coef_'):                # Linear models / linear SVM
            b = clf.coef_.nbytes
            if getattr(clf, 'intercept_', None) is not None:
                b += np.asarray(clf.intercept_).nbytes
            if hasattr(clf, 'support_vectors_'):
                b += clf.support_vectors_.nbytes + clf.dual_coef_.nbytes
            return int(b)
        return len(pickle.dumps(clf))            # fallback


# ---------------------------------------------------------------------------
# Benchmark runner
# ---------------------------------------------------------------------------
def evaluate(model, Xtr, ytr, Xte, yte, canon=24):
    Xc_tr, Xc_te = to_canon(Xtr, canon), to_canon(Xte, canon)
    t0 = time.time(); model.fit(Xc_tr, ytr); train_s = time.time() - t0
    t0 = time.time(); pred = model.predict(Xc_te); infer_s = (time.time() - t0) / max(len(yte), 1)
    return dict(model=model.name,
                f1=round(f1_score(yte, pred, average='macro'), 3),
                acc=round(accuracy_score(yte, pred), 3),
                train_s=round(train_s, 3),
                infer_ms=round(infer_s * 1000, 3),
                mem_kb=round(model.mem_bytes() / 1024, 1))

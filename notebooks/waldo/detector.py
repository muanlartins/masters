"""Shared detector code for the synthetic-Waldo notebooks (19+).

Contains the encoder-independent harness:
- multi-scale rectangle generation for training
- canonical resize, hierarchical recursion (greedy descent over 5-overlap quadrants)
- snap-to-stripe-blob bbox refinement
- training (Wisard + Local2DMapping over canonical)
- evaluation against ground truth (lenient hit, IoU, centre-to-centre distance)

The encoder is *injected* by passing an `encode_fn` callable that takes a
canonical-resized HxWx3 uint8 array and returns an HxWxN bool array of features.
The number of bits per pixel (`bpp`) is inferred from the encoder's output and
must match the Local2DMapping configuration.

This file is the project's stable foundation as of notebook 19. Subsequent
notebooks (20+) build different encoders against it.
"""
from __future__ import annotations
import time
from typing import Callable, Iterable, Sequence
import numpy as np
import pandas as pd
from PIL import Image
from scipy import ndimage as ndi
import wisardpkg as wp
import synthetic

# ----- canonical & WiSARD -----------------------------------------------------

CANON_W = 64
CANON_H = 128
TARGET_W = 24
TARGET_H = 48
ADDRESS_SIZE = 12

# Default Local2DMapping window/stride. With bpp=4 (SLIM) each window is
# 16*8*4=512 bits; each RAM samples 12 of them; ~4 RAMs per window over 435
# windows = ~1740 RAMs. Same shape as notebook 14.
WIN_H = 16
WIN_W = 8
STRIDE = 4
RAMS_PER_WINDOW = 4

# ----- standard encoder primitives ------------------------------------------

def colormask_3bits(im_uint8: np.ndarray) -> np.ndarray:
    """Per-pixel 3-bit categorical: is_red / is_white / is_dark."""
    f = im_uint8.astype(np.float32) / 255.0
    r, g, b = f[..., 0], f[..., 1], f[..., 2]
    is_red = (r > 0.5) & (r - g > 0.10) & (r - b > 0.10)
    is_white = (r > 0.75) & (g > 0.75) & (b > 0.75)
    is_dark = (r < 0.20) & (g < 0.20) & (b < 0.20)
    return np.stack([is_red, is_white, is_dark], axis=-1)


def stripe_pattern_bit(im_uint8: np.ndarray, min_run_len: int = 2,
                        min_alternations: int = 3) -> np.ndarray:
    """Per-pixel boolean: is this pixel part of a column with >= min_alternations
    alternating red/white runs (each run >= min_run_len pixels)? Naturally
    scale-invariant — works whether stripes are 3 px or 30 px tall."""
    f = im_uint8.astype(np.float32) / 255.0
    r, g, b = f[..., 0], f[..., 1], f[..., 2]
    is_red = (r > 0.5) & (r - g > 0.10) & (r - b > 0.10)
    is_white = (r > 0.75) & (g > 0.75) & (b > 0.75)
    H, W = im_uint8.shape[:2]
    out = np.zeros((H, W), dtype=bool)
    for w in range(W):
        col_r = is_red[:, w]
        col_w = is_white[:, w]
        runs = []  # list of (start, end, color)
        i = 0
        while i < H:
            if col_r[i]:
                j = i
                while j < H and col_r[j]: j += 1
                if j - i >= min_run_len: runs.append((i, j, 'R'))
                i = j
            elif col_w[i]:
                j = i
                while j < H and col_w[j]: j += 1
                if j - i >= min_run_len: runs.append((i, j, 'W'))
                i = j
            else:
                i += 1
        if not runs: continue
        # Longest alternating subsequence length.
        best = 1; cur = 1
        for k in range(1, len(runs)):
            if runs[k][2] != runs[k - 1][2]:
                cur += 1
                best = max(best, cur)
            else:
                cur = 1
        if best >= min_alternations:
            for s, e, _ in runs:
                out[s:e, w] = True
    return out[..., None]


def slim_encoder(im_uint8: np.ndarray) -> np.ndarray:
    """Default 4-bit-per-pixel encoder: ColorMask + column-RLE stripe-pattern bit.
    This is the state-of-the-art as of notebook 19 — paper notebook 18 sweep results."""
    return np.concatenate([colormask_3bits(im_uint8), stripe_pattern_bit(im_uint8)], axis=-1)


def _is_red_strict_pixel(im):
    # Calibrated to real Hey-Waldo muted red (185,84,78)→(0.725,0.33,0.31); the
    # green ceiling rejects Odlaw's yellow (high G). See project-waldo-calibration.
    f = im.astype(np.float32) / 255.0
    return ((f[..., 0] > 0.55) & (f[..., 0] - f[..., 1] > 0.20)
            & (f[..., 0] - f[..., 2] > 0.20) & (f[..., 1] < 0.6))


def _is_white_strict_pixel(im):
    f = im.astype(np.float32) / 255.0
    return (f[..., 0] > 0.68) & (f[..., 1] > 0.68) & (f[..., 2] > 0.62)


def _alt_count_1d(strip_r, strip_w, min_run_len=2):
    """Longest alternating R/W run-length sequence along a 1D strip. Returns int."""
    runs = []
    n = len(strip_r); i = 0
    while i < n:
        if strip_r[i]:
            j = i
            while j < n and strip_r[j]: j += 1
            if j - i >= min_run_len: runs.append('R')
            i = j
        elif strip_w[i]:
            j = i
            while j < n and strip_w[j]: j += 1
            if j - i >= min_run_len: runs.append('W')
            i = j
        else:
            i += 1
    if not runs: return 0
    best = 1; cur = 1
    for k in range(1, len(runs)):
        if runs[k] != runs[k - 1]: cur += 1; best = max(best, cur)
        else: cur = 1
    return best


def stripe_count_bit_column(im_uint8, lo=4, hi=6, min_run_len=2):
    """Encoder B from nb33+: per-column alternation count in [lo, hi].
    Fires on near-horizontal Waldo stripes. Returns HxWx1 bool."""
    is_red = _is_red_strict_pixel(im_uint8); is_white = _is_white_strict_pixel(im_uint8)
    H, W = im_uint8.shape[:2]
    counts = np.zeros(W, dtype=np.int32)
    for w in range(W):
        counts[w] = _alt_count_1d(is_red[:, w], is_white[:, w], min_run_len)
    fire = (counts >= lo) & (counts <= hi)
    return np.broadcast_to(fire[None, :, None], (H, W, 1)).astype(bool).copy()


def stripe_count_bit_row(im_uint8, lo=4, hi=6, min_run_len=2):
    """Encoder C from nb48: per-row alternation count in [lo, hi].
    Fires on near-vertical Waldo stripes (i.e. 90deg-rotated Waldo). Returns HxWx1 bool.
    Orthogonal to stripe_count_bit_column; combining both closes most of the rotation x
    friends gap (see project_waldo memory)."""
    is_red = _is_red_strict_pixel(im_uint8); is_white = _is_white_strict_pixel(im_uint8)
    H, W = im_uint8.shape[:2]
    counts = np.zeros(H, dtype=np.int32)
    for h in range(H):
        counts[h] = _alt_count_1d(is_red[h, :], is_white[h, :], min_run_len)
    fire = (counts >= lo) & (counts <= hi)
    return np.broadcast_to(fire[:, None, None], (H, W, 1)).astype(bool).copy()


def stripe_count_principal_axis(im_uint8, min_pixels=20, min_elongation=1.3,
                                nbins=12, color_margin=1.5):
    """Encoder D (nb52): alternation count along the data-driven principal axis
    of the red+white mask. Rotation-invariant — same result regardless of how
    the image is rotated.

    Returns the alternation count (int >= 0), or -1 if no clear striped pattern
    can be detected (insufficient pixels, isotropic blob, or degenerate projection).

    Use as a global predicate (e.g. lo<=k<=hi) added directly to the beam-search
    score, not via a WiSARD: the bit is global, so it would degenerate the RAM
    addresses. See nb52 for justification.

    IMPORTANT: call this on the ORIGINAL CROP, not on the canonical resize. The
    canon (64x128 portrait) distorts the blob aspect ratio, which can flip PCA's
    long/short axis identification at landscape-AABB rotations (e.g. 90deg, where
    AABB is 48x24). The crop preserves true aspect so PCA tracks the stripe
    direction faithfully."""
    is_red = _is_red_strict_pixel(im_uint8)
    is_white = _is_white_strict_pixel(im_uint8)
    mask = is_red | is_white
    n_mask = int(mask.sum())
    if n_mask < min_pixels:
        return -1
    ys, xs = np.where(mask)
    pts = np.column_stack([ys.astype(np.float64), xs.astype(np.float64)])
    pts -= pts.mean(axis=0)
    cov = (pts.T @ pts) / max(n_mask, 1)
    eigvals, eigvecs = np.linalg.eigh(cov)  # ascending
    if eigvals[-1] < 1.0 or eigvals[0] < 1e-6:
        return -1
    if eigvals[-1] / eigvals[0] < min_elongation:
        return -1
    long_axis = eigvecs[:, -1]
    proj = pts @ long_axis
    proj_min, proj_max = float(proj.min()), float(proj.max())
    if proj_max - proj_min < 4:
        return -1
    bin_edges = np.linspace(proj_min, proj_max, nbins + 1)
    bin_idx = np.clip(np.digitize(proj, bin_edges) - 1, 0, nbins - 1)
    is_red_pt = is_red[ys, xs]
    is_white_pt = is_white[ys, xs]
    bin_red = np.bincount(bin_idx[is_red_pt], minlength=nbins)
    bin_white = np.bincount(bin_idx[is_white_pt], minlength=nbins)
    runs = []
    for b in range(nbins):
        r, w = int(bin_red[b]), int(bin_white[b])
        if r + w < 3:
            continue
        if r > w * color_margin:
            tag = 'R'
        elif w > r * color_margin:
            tag = 'W'
        else:
            continue
        if not runs or runs[-1] != tag:
            runs.append(tag)
    return len(runs)


def stripe_count_principal_fires(im_uint8, lo: int = 4, hi: int = 6) -> bool:
    """Boolean predicate: principal-axis alternation count is in [lo, hi]."""
    return lo <= stripe_count_principal_axis(im_uint8) <= hi


# ----- canonical resize / cropping ------------------------------------------

def to_canon(arr_uint8: np.ndarray) -> np.ndarray:
    return np.asarray(Image.fromarray(arr_uint8).resize((CANON_W, CANON_H), Image.LANCZOS), dtype=np.uint8)


def crop_arr(scene_arr: np.ndarray, rect: tuple[int, int, int, int]) -> np.ndarray:
    H, W = scene_arr.shape[:2]
    x, y, w, h = rect
    return scene_arr[max(0, y):min(H, y + h), max(0, x):min(W, x + w)]


def overlap(a: tuple[int, int, int, int], b: tuple[int, int, int, int]) -> bool:
    return not (a[0] + a[2] <= b[0] or a[0] >= b[0] + b[2]
                or a[1] + a[3] <= b[1] or a[1] >= b[1] + b[3])


# ----- multi-scale rectangles for training ----------------------------------

DEFAULT_POS_SCALES = [(256, 256), (128, 128), (96, 192), (48, 96), (36, 72)]


def positive_rects(scene_arr, gt, rng, scales=None):
    """Rectangles that fully contain the Waldo bbox at multiple scales."""
    H, W = scene_arr.shape[:2]
    gx, gy, gw, gh = gt
    gcx, gcy = gx + gw // 2, gy + gh // 2
    out = []
    for sw, sh in (scales or DEFAULT_POS_SCALES) + [(gw, gh)]:
        if sw > W or sh > H: continue
        max_dx = max(0, (sw - gw) // 2 - 1)
        max_dy = max(0, (sh - gh) // 2 - 1)
        dx = int(rng.integers(-max_dx, max_dx + 1)) if max_dx > 0 else 0
        dy = int(rng.integers(-max_dy, max_dy + 1)) if max_dy > 0 else 0
        x = max(0, min(W - sw, gcx - sw // 2 + dx))
        y = max(0, min(H - sh, gcy - sh // 2 + dy))
        if x <= gx and y <= gy and x + sw >= gx + gw and y + sh >= gy + gh:
            out.append((x, y, sw, sh))
    return out


def negative_rects(scene_arr, gt, n_per_scale, rng, scales=None):
    """Rectangles that do not overlap the Waldo bbox at multiple scales."""
    H, W = scene_arr.shape[:2]
    out = []
    for sw, sh in (scales or DEFAULT_POS_SCALES) + [(gt[2], gt[3])]:
        if sw > W or sh > H: continue
        placed, attempts = 0, 0
        while placed < n_per_scale and attempts < n_per_scale * 8:
            attempts += 1
            x = int(rng.integers(0, W - sw + 1))
            y = int(rng.integers(0, H - sh + 1))
            if not overlap((x, y, sw, sh), gt):
                out.append((x, y, sw, sh)); placed += 1
    return out


# ----- training ----------------------------------------------------------------

def train_classifier(scene_params: dict,
                     n_train: int,
                     seed: int,
                     encode_fn: Callable[[np.ndarray], np.ndarray] = slim_encoder,
                     n_neg_per_scale: int = 5):
    """Generate `n_train` synthetic scenes, build multi-scale training rectangles,
    encode them, train a Wisard with Local2DMapping over the encoded canonical."""
    rng = np.random.default_rng(seed)
    ds = wp.DataSet()
    bpp = None
    for _ in range(n_train):
        im, bbox = synthetic.make_scene(rng=rng, **scene_params)
        arr = np.asarray(im)
        for r in positive_rects(arr, bbox, rng):
            enc = encode_fn(to_canon(crop_arr(arr, r)))
            if bpp is None: bpp = enc.shape[-1]
            ds.add(enc.flatten().astype(np.uint8).tolist(), 'waldo')
        for r in negative_rects(arr, bbox, n_neg_per_scale, rng):
            ds.add(encode_fn(to_canon(crop_arr(arr, r))).flatten().astype(np.uint8).tolist(), 'notwaldo')
    if bpp is None:
        raise RuntimeError('No positives generated — check scene_params and n_train')
    mapping = wp.Local2DMapping(
        imageHeight=CANON_H, imageWidth=CANON_W, bitsPerPixel=bpp,
        windowHeight=WIN_H, windowWidth=WIN_W, tupleSize=ADDRESS_SIZE,
        stride=STRIDE, ramsPerWindow=RAMS_PER_WINDOW,
    )
    m = wp.Wisard(ADDRESS_SIZE, mappingGenerator=mapping, bleaching=True, verbose=False)
    m.train(ds)
    return m, bpp


# ----- inference --------------------------------------------------------------

def split_5(rect):
    x, y, w, h = rect
    sw, sh = w // 2, h // 2
    return [(x, y, sw, sh), (x + w - sw, y, sw, sh), (x, y + h - sh, sw, sh),
            (x + w - sw, y + h - sh, sw, sh),
            (x + (w - sw) // 2, y + (h - sh) // 2, sw, sh)]


def is_leaf(rect, leaf_factor: float = 1.5):
    return rect[2] <= int(TARGET_W * leaf_factor) and rect[3] <= int(TARGET_H * leaf_factor)


def is_leaf_rot(rect, leaf_factor: float = 1.5):
    """Rotation-aware leaf criterion. Compares max(W, H) of the rect to
    max(TARGET_W, TARGET_H) so a landscape AABB (e.g. 48x24 at 90deg rotation)
    can also reach a valid leaf. Use this instead of `is_leaf` when targets
    may rotate. Old `is_leaf` (portrait-only) is preserved for non-rotation
    notebooks that depended on its exact behaviour."""
    long_dim = max(rect[2], rect[3])
    return long_dim <= int(max(TARGET_W, TARGET_H) * leaf_factor)


def score_rect(scene_arr, rect, model, encode_fn=slim_encoder):
    crop = crop_arr(scene_arr, rect)
    if crop.shape[0] < 4 or crop.shape[1] < 4: return -1e9
    bits = encode_fn(to_canon(crop)).flatten().astype(np.uint8).tolist()
    r = model.rank(wp.BinInput(bits))
    return float(r.get('waldo', 0) - r.get('notwaldo', 0))


def descend(scene_arr, model, encode_fn=slim_encoder, max_depth: int = 8):
    H, W = scene_arr.shape[:2]
    rect = (0, 0, W, H)
    trace = [(rect, score_rect(scene_arr, rect, model, encode_fn), 0)]
    for d in range(1, max_depth + 1):
        if is_leaf(rect): break
        children = [c for c in split_5(rect) if c[2] >= 4 and c[3] >= 4]
        if not children: break
        scored = [(c, score_rect(scene_arr, c, model, encode_fn)) for c in children]
        for c, s in scored:
            trace.append((c, s, d))
        rect = max(scored, key=lambda cs: cs[1])[0]
    return rect, trace


def snap_bbox(scene_arr, leaf_rect, expand_px: int = 8):
    """Refine leaf rectangle to the tight stripe-pattern bbox in the surrounding region."""
    H, W = scene_arr.shape[:2]
    x, y, w, h = leaf_rect
    rx = max(0, x - expand_px)
    ry = max(0, y - expand_px)
    rw = min(W - rx, w + 2 * expand_px)
    rh = min(H - ry, h + 2 * expand_px)
    s = stripe_pattern_bit(scene_arr[ry:ry + rh, rx:rx + rw])[..., 0]
    if not s.any():
        return leaf_rect
    rows = np.any(s, axis=1)
    cols = np.any(s, axis=0)
    rmin = int(np.where(rows)[0][0]); rmax = int(np.where(rows)[0][-1])
    cmin = int(np.where(cols)[0][0]); cmax = int(np.where(cols)[0][-1])
    return (rx + cmin, ry + rmin, cmax - cmin + 1, rmax - rmin + 1)


def _is_red_strict(im):
    # Calibrated to real Hey-Waldo muted red; green ceiling rejects Odlaw yellow.
    f = im.astype(np.float32) / 255.0
    return ((f[..., 0] > 0.55) & (f[..., 0] - f[..., 1] > 0.20)
            & (f[..., 0] - f[..., 2] > 0.20) & (f[..., 1] < 0.6))


def _is_white_default(im):
    f = im.astype(np.float32) / 255.0
    return (f[..., 0] > 0.68) & (f[..., 1] > 0.68) & (f[..., 2] > 0.62)


def snap_bbox_rot(scene_arr, leaf_rect, expand_px: int = 12):
    """Rotation-aware snap: AABB of the largest red/white connected component
    overlapping the leaf rect. Direction-agnostic — works for axis-aligned and
    rotated Waldo equally well. Use this instead of snap_bbox when rotation may
    be present. (nb42 confirmed IoU dominates snap_bbox at every angle.)"""
    H, W = scene_arr.shape[:2]
    x, y, w, h = leaf_rect
    rx = max(0, x - expand_px); ry = max(0, y - expand_px)
    rw = min(W - rx, w + 2 * expand_px); rh = min(H - ry, h + 2 * expand_px)
    region = scene_arr[ry:ry+rh, rx:rx+rw]
    mask = _is_red_strict(region) | _is_white_default(region)
    if not mask.any():
        return leaf_rect
    labels, n = ndi.label(mask, structure=np.ones((3, 3), dtype=bool))
    if n == 0:
        return leaf_rect
    lx0 = max(0, x - rx); ly0 = max(0, y - ry)
    lx1 = min(rw, x + w - rx); ly1 = min(rh, y + h - ry)
    leaf_mask = np.zeros_like(mask)
    leaf_mask[ly0:ly1, lx0:lx1] = True
    overlap = ndi.sum(leaf_mask, labels, index=np.arange(1, n + 1))
    total = ndi.sum(mask, labels, index=np.arange(1, n + 1))
    score = overlap + 1e-3 * total
    best = int(np.argmax(score)) + 1
    if overlap[best - 1] == 0:
        return leaf_rect
    slc = ndi.find_objects(labels)[best - 1]
    if slc is None:
        return leaf_rect
    sy, sx = slc
    return (rx + sx.start, ry + sy.start, sx.stop - sx.start, sy.stop - sy.start)


def _is_red_loose_pixel(im):
    """The loose is_red predicate from colormask_3bits, applied directly.
    Used by snap_bbox_loose to include pink-stripe friends in the CC."""
    f = im.astype(np.float32) / 255.0
    return (f[..., 0] > 0.5) & (f[..., 0] - f[..., 1] > 0.10) & (f[..., 0] - f[..., 2] > 0.10)


def _is_white_loose_pixel(im):
    f = im.astype(np.float32) / 255.0
    return (f[..., 0] > 0.75) & (f[..., 1] > 0.75) & (f[..., 2] > 0.75)


def snap_bbox_loose(scene_arr, leaf_rect, expand_px: int = 12):
    """Snap variant using LOOSE colour predicates so it also catches
    pink+grey (shifted_palette) friend stripes. snap_bbox_rot uses strict
    predicates and fails on pink — under multi-instance evaluation that
    causes shifted_palette friends to snap to only their grey-strict
    connected component (half the instance). nb57 introduces this for the
    detect-then-classify pipeline."""
    H, W = scene_arr.shape[:2]
    x, y, w, h = leaf_rect
    rx = max(0, x - expand_px); ry = max(0, y - expand_px)
    rw = min(W - rx, w + 2 * expand_px); rh = min(H - ry, h + 2 * expand_px)
    region = scene_arr[ry:ry+rh, rx:rx+rw]
    mask = _is_red_loose_pixel(region) | _is_white_loose_pixel(region)
    if not mask.any():
        return leaf_rect
    labels, n = ndi.label(mask, structure=np.ones((3, 3), dtype=bool))
    if n == 0:
        return leaf_rect
    lx0 = max(0, x - rx); ly0 = max(0, y - ry)
    lx1 = min(rw, x + w - rx); ly1 = min(rh, y + h - ry)
    leaf_mask = np.zeros_like(mask)
    leaf_mask[ly0:ly1, lx0:lx1] = True
    overlap = ndi.sum(leaf_mask, labels, index=np.arange(1, n + 1))
    total = ndi.sum(mask, labels, index=np.arange(1, n + 1))
    score = overlap + 1e-3 * total
    best = int(np.argmax(score)) + 1
    if overlap[best - 1] == 0:
        return leaf_rect
    slc = ndi.find_objects(labels)[best - 1]
    if slc is None:
        return leaf_rect
    sy, sx = slc
    return (rx + sx.start, ry + sy.start, sx.stop - sx.start, sy.stop - sy.start)


def find_waldo(scene_arr, model, encode_fn=slim_encoder):
    leaf, trace = descend(scene_arr, model, encode_fn)
    return leaf, snap_bbox(scene_arr, leaf), trace


# ----- metrics ---------------------------------------------------------------

def hit_lenient(gt, pred):
    return (pred[0] <= gt[0] + gt[2] / 2 <= pred[0] + pred[2]
            and pred[1] <= gt[1] + gt[3] / 2 <= pred[1] + pred[3])


def iou(a, b):
    ix = max(0, min(a[0] + a[2], b[0] + b[2]) - max(a[0], b[0]))
    iy = max(0, min(a[1] + a[3], b[1] + b[3]) - max(a[1], b[1]))
    inter = ix * iy
    union = a[2] * a[3] + b[2] * b[3] - inter
    return inter / union if union > 0 else 0.0


def dist(gt, pred):
    return float(np.hypot((pred[0] + pred[2] / 2) - (gt[0] + gt[2] / 2),
                           (pred[1] + pred[3] / 2) - (gt[1] + gt[3] / 2)))


def evaluate(model,
             scene_params: dict,
             n_test: int,
             seed: int,
             encode_fn: Callable[[np.ndarray], np.ndarray] = slim_encoder) -> pd.DataFrame:
    rng = np.random.default_rng(seed)
    rows = []
    for _ in range(n_test):
        im, gt = synthetic.make_scene(rng=rng, **scene_params)
        arr = np.asarray(im)
        leaf, snapped, _ = find_waldo(arr, model, encode_fn)
        rows.append({'gt': gt, 'leaf': leaf, 'snapped': snapped,
                     'hit_leaf': hit_lenient(gt, leaf),
                     'hit_snap': hit_lenient(gt, snapped),
                     'iou': iou(gt, snapped),
                     'dist_px': dist(gt, snapped)})
    return pd.DataFrame(rows)


# ----- regime presets --------------------------------------------------------

EASY = dict(scene_size=512, target_size=24, target_aspect=0.5,
            n_distractors=50, palette_overlap=0.0, n_near_waldo=0,
            background='gradient')

HARD = dict(scene_size=512, target_size=24, target_aspect=0.5,
            n_distractors=100, palette_overlap=0.4, n_near_waldo=3,
            background='gradient')


def sweep_one(param_name: str, values: Sequence,
              base_params: dict = None,
              n_train: int = 500, n_test: int = 50,
              encode_fn: Callable[[np.ndarray], np.ndarray] = slim_encoder,
              seed_base: int = 0,
              verbose: bool = True) -> pd.DataFrame:
    """Train+evaluate a fresh classifier at each value of `param_name`. Returns
    a DataFrame with one row per value."""
    base_params = base_params or EASY
    rows = []
    for i, v in enumerate(values):
        p = dict(base_params); p[param_name] = v
        t0 = time.time()
        model, _ = train_classifier(p, n_train, seed=seed_base + 100 * i, encode_fn=encode_fn)
        df = evaluate(model, p, n_test, seed=seed_base + 100 * i + 1, encode_fn=encode_fn)
        rows.append({param_name: v,
                     'hit': df.hit_snap.mean(),
                     'med_dist': df.dist_px.median(),
                     'med_iou': df.iou.median(),
                     't_s': round(time.time() - t0, 1)})
        if verbose:
            print(f'  {param_name}={v}: hit={df.hit_snap.mean()*100:.0f}% '
                  f'med_dist={df.dist_px.median():.0f}px med_IoU={df.iou.median():.2f} ({rows[-1]["t_s"]}s)')
    return pd.DataFrame(rows)

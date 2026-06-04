"""Character-patch dataset for the Where's-Wally weightless-NN study.

Reframes the project from localisation to **multi-class character recognition** —
the task weightless networks are designed for. A patch is a `size x size` RGB
tile containing one centred character (or none → 'background'), so the task is
pure 6-class classification.

Classes: waldo, odlaw, wenda, wizard, woof, background.
  - waldo  : red+white horizontal stripes, 5 stripes              (the target)
  - odlaw  : black+yellow stripes                                 (wrong palette)
  - wenda  : red+white, wrong stripe count (2/3/8/10)             (wrong count)
  - wizard : red+white vertical stripes                          (wrong orientation)
  - woof   : red+white, only lower band striped, rest solid red  (partial pattern)
  - background : distractors / striped clutter, no character     (hard negative)

Reuses synthetic.py renderers + the calibrated palette + the adversary knobs
(rotation / scale / palette-jitter / occlusion / photometric). See
[[project-waldo-calibration]].
"""
import numpy as np
from PIL import Image

import synthetic as S

CHAR_CLASSES = ['waldo', 'odlaw', 'wenda', 'wizard', 'woof']
CLASSES = CHAR_CLASSES + ['background']
CLASS_TO_IDX = {c: i for i, c in enumerate(CLASSES)}


def _render_char(cls, w, h, rng, rotation_deg, palette_jitter):
    """RGBA of a single character (pre-placement)."""
    if cls == 'waldo':
        return S.render_target(w, h, n_stripes=5, rotation_deg=rotation_deg,
                               rng=rng, palette_jitter=palette_jitter)
    im, _ = S.render_near_waldo(w, h, rng, rotation_deg=rotation_deg,
                                variants=(cls,), palette_jitter=palette_jitter)
    return im


def render_patch(cls, size, rng,
                 rotation=0.0, palette_jitter=0, occlusion=0.0,
                 photometric=None, scale_range=(0.55, 0.9),
                 aspect=0.5, n_clutter=4, palette_overlap=0.4,
                 background='gradient'):
    """One labelled `size x size` RGB patch. `cls` in CLASSES.

    A character (if any) is sized to `scale_range` of the tile's larger side,
    placed near-centre with small jitter, optionally rotated/occluded; the whole
    tile then gets optional photometric degradation. Background tiles carry a few
    distractors (and sometimes striped clutter) so 'background' is a hard negative
    rather than empty canvas."""
    tile = S.render_background(size, background, rng).convert('RGBA')

    # A little clutter on every tile (context + makes background non-trivial).
    for _ in range(n_clutter):
        dw = int(rng.integers(max(4, size // 16), max(6, size // 4)))
        dh = int(rng.integers(max(4, size // 16), max(6, size // 4)))
        d = S.render_distractor(dw, dh, rng, palette_overlap, palette_jitter)
        dx = int(rng.integers(0, size - dw)); dy = int(rng.integers(0, size - dh))
        tile.paste(d, (dx, dy), d)

    if cls == 'background':
        # ~40% of background tiles get a striped-clutter fragment (the texture trap).
        if rng.random() < 0.4:
            clut, (cw, ch) = S.render_striped_clutter(rng, size, palette_jitter)
            if cw < size and ch < size:
                tile.paste(clut, (int(rng.integers(0, size - cw)),
                                  int(rng.integers(0, size - ch))), clut)
        out = tile.convert('RGB')
        return np.asarray(S._apply_photometric(out, rng, photometric)), CLASS_TO_IDX[cls]

    # Character sized to scale_range of the tile (the scale axis).
    frac = float(rng.uniform(*scale_range))
    h = max(8, int(size * frac))
    w = max(6, int(h * aspect))
    rot = S._sample_rotation(rng, rotation)
    char = _render_char(cls, w, h, rng, rot, palette_jitter)
    cw, ch = char.size
    # Near-centre placement with mild jitter; keep fully inside the tile.
    cx = int(np.clip((size - cw) // 2 + rng.integers(-size // 8, size // 8 + 1), 0, size - cw))
    cy = int(np.clip((size - ch) // 2 + rng.integers(-size // 8, size // 8 + 1), 0, size - ch))
    tile.paste(char, (cx, cy), char)
    box = (cx, cy, cx + cw, cy + ch)
    S._occlude(tile, box, rng, occlusion)
    out = tile.convert('RGB')
    out = S._apply_photometric(out, rng, photometric)
    return np.asarray(out), CLASS_TO_IDX[cls]


def make_dataset(n_per_class, size=48, seed=0, classes=CLASSES, **knobs):
    """Balanced multi-class patch dataset.

    Returns (X: (N, size, size, 3) uint8, y: (N,) int) shuffled. `knobs` are
    passed to render_patch (rotation, palette_jitter, occlusion, photometric,
    scale_range, n_clutter, palette_overlap, background)."""
    rng = np.random.default_rng(seed)
    X, y = [], []
    for cls in classes:
        for _ in range(n_per_class):
            patch, label = render_patch(cls, size, rng, **knobs)
            X.append(patch); y.append(label)
    X = np.stack(X); y = np.array(y, dtype=np.int64)
    perm = rng.permutation(len(y))
    return X[perm], y[perm]


# Difficulty presets (mirror fair.PROTOCOL philosophy: one axis at a time + 'full').
PRESETS = {
    'clean':       dict(rotation=0.0, palette_jitter=10, occlusion=0.0, photometric=None),
    'rotation':    dict(rotation=(0, 360), palette_jitter=10),
    'palette':     dict(palette_jitter=40),
    'occlusion':   dict(occlusion=0.45, palette_jitter=10),
    'photometric': dict(photometric=0.6, palette_jitter=10),
    'full':        dict(rotation=(0, 360), palette_jitter=30, occlusion=0.3,
                        photometric=0.4),
}

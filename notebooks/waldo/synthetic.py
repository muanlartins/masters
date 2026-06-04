"""Synthetic 'Where's Wally'-style scene generator.

A scene is a `scene_size × scene_size` RGB image containing:
- A **target** (Wally): red+white horizontally striped rectangle of configurable
  size and aspect.
- **`n_distractors`** random shapes (rectangle/circle/triangle) with configurable
  `palette_overlap` between their colour distribution and Wally's red+white palette.
- **`n_near_waldo`** "friends": canonical look-alikes (Odlaw, Wenda, Wizard, Woof)
  that each mimic Wally on all-but-one feature. Deliberate hard negatives.
- **`n_striped_clutter`** striped non-targets (barber poles / awnings / flags):
  right *colour and stripes* but wrong *scale/shape*. These attack the "detect any
  red-white stripe texture" shortcut head-on — the key fairness adversary.
- Optional **occlusion** of the target (truncated stripes) and **photometric**
  degradation (brightness/contrast/noise/blur/JPEG) of the whole scene.

Palette and scale defaults are CALIBRATED to the 14 annotated real Hey-Waldo
scenes (see notebooks/waldo/_calibration; measured 2026-05-29):
  - Wally red   ≈ (185, 84, 78)  [muted/warm, not saturated]
  - Wally white ≈ (247, 225, 217) [cream]
  - Wally width / page width: median 1.4% (range 0.4–2.4%)
  - aspect (W/H): median 0.52 (range 0.33–1.0)
  - page-wide red ≈ 17%, white ≈ 22%  → colour alone is near-useless; the task
    demands stripe structure + counting, which is why palette_overlap is high.

Returns `(PIL.Image, (x, y, w, h))` where the bbox is the target's pixel-coords box.
"""
import io
import numpy as np
from PIL import Image, ImageDraw, ImageFilter

# Calibrated to real Hey-Waldo in-bbox median pixel colours.
WALDO_RED   = (185, 84, 78)
WALDO_WHITE = (247, 225, 217)

# Odlaw (Wally's nemesis): black + yellow.
ODLAW_BLACK  = (35, 35, 40)
ODLAW_YELLOW = (235, 205, 60)

# Distractor colours that don't overlap Wally's palette.
COLD_PALETTE = [
    (30, 100, 220),   # blue
    (40, 180, 60),    # green
    (240, 220, 30),   # yellow
    (140, 50, 200),   # purple
    (220, 120, 30),   # orange
    (50, 200, 200),   # cyan
    (160, 80, 30),    # brown
    (10, 70, 30),     # dark green
]


def _rotate_rgba(im, deg):
    if not deg:
        return im
    return im.rotate(float(deg), resample=Image.BICUBIC, expand=True)


def _jitter_color(rng, base, amt):
    """Perturb an RGB tuple by uniform ±amt per channel (clamped to [0,255]).
    `amt` is in absolute 0..255 units; 0 disables."""
    if not amt:
        return tuple(int(c) for c in base)
    return tuple(int(np.clip(c + rng.uniform(-amt, amt), 0, 255)) for c in base)


def render_target(w, h, n_stripes=5, rotation_deg=0.0, rng=None, palette_jitter=0):
    """Red+white horizontally striped rectangle, optionally rotated. Returns RGBA."""
    red = _jitter_color(rng, WALDO_RED, palette_jitter) if rng is not None else WALDO_RED
    white = _jitter_color(rng, WALDO_WHITE, palette_jitter) if rng is not None else WALDO_WHITE
    im = Image.new('RGBA', (w, h), (0, 0, 0, 0))
    draw = ImageDraw.Draw(im)
    for i in range(n_stripes):
        y0, y1 = int(i * h / n_stripes), int((i + 1) * h / n_stripes)
        color = red if i % 2 == 0 else white
        draw.rectangle((0, y0, w, y1), fill=color + (255,))
    return _rotate_rgba(im, rotation_deg)


# Canonical friend characters, each differing from Wally on exactly one feature.
# Mechanism names kept as aliases so older notebooks keep working.
NEAR_WALDO_VARIANTS = ('odlaw', 'wenda', 'wizard', 'woof')
_VARIANT_ALIASES = {
    'shifted_palette': 'odlaw',       # wrong palette (the nemesis)
    'wrong_stripe_count': 'wenda',    # right palette, wrong stripe count
    'vertical_stripes': 'wizard',     # right palette, stripes rotated 90°
}


def render_near_waldo(w, h, rng, rotation_deg=0.0, variants=NEAR_WALDO_VARIANTS,
                      palette_jitter=0):
    """A canonical 'friend' — Wally-shaped but with one feature off.
    Returns (RGBA, variant_name). Differs from Wally on exactly one axis:
      - odlaw  : black+yellow palette  (wrong colour)
      - wenda  : red+white, wrong stripe count (2/3/8/10)
      - wizard : red+white, vertical stripes (orientation)
      - woof   : red+white, right count, but only the lower band is striped (rest solid)
    """
    variant = str(rng.choice(list(variants)))
    variant = _VARIANT_ALIASES.get(variant, variant)
    red = _jitter_color(rng, WALDO_RED, palette_jitter)
    white = _jitter_color(rng, WALDO_WHITE, palette_jitter)
    im = Image.new('RGBA', (w, h), (0, 0, 0, 0))
    draw = ImageDraw.Draw(im)
    if variant == 'odlaw':
        c1 = _jitter_color(rng, ODLAW_BLACK, palette_jitter)
        c2 = _jitter_color(rng, ODLAW_YELLOW, palette_jitter)
        n = 5
        for i in range(n):
            y0, y1 = int(i * h / n), int((i + 1) * h / n)
            draw.rectangle((0, y0, w, y1), fill=(c1 if i % 2 == 0 else c2) + (255,))
    elif variant == 'wizard':
        n = 5
        for i in range(n):
            x0, x1 = int(i * w / n), int((i + 1) * w / n)
            draw.rectangle((x0, 0, x1, h), fill=(red if i % 2 == 0 else white) + (255,))
    elif variant == 'woof':
        # Lower third striped, upper two-thirds solid red (a 'tail' poking out).
        split = int(h * 2 / 3)
        draw.rectangle((0, 0, w, split), fill=red + (255,))
        n = 4
        for i in range(n):
            y0 = split + int(i * (h - split) / n)
            y1 = split + int((i + 1) * (h - split) / n)
            draw.rectangle((0, y0, w, y1), fill=(red if i % 2 == 0 else white) + (255,))
    else:  # wenda — wrong stripe count
        n = int(rng.choice([2, 3, 8, 10]))
        for i in range(n):
            y0, y1 = int(i * h / n), int((i + 1) * h / n)
            draw.rectangle((0, y0, w, y1), fill=(red if i % 2 == 0 else white) + (255,))
    return _rotate_rgba(im, rotation_deg), variant


def render_striped_clutter(rng, scene_size, palette_jitter=0):
    """A red+white striped NON-target: right colour and stripe texture, but wrong
    scale/shape (barber pole, awning, flag). Attacks the texture shortcut.
    Returns (RGBA, (w, h)) — sized and oriented at random, generally much larger
    or more extreme-aspect than Wally."""
    red = _jitter_color(rng, WALDO_RED, palette_jitter)
    white = _jitter_color(rng, WALDO_WHITE, palette_jitter)
    kind = str(rng.choice(['awning', 'pole', 'flag']))
    if kind == 'awning':       # wide, short, horizontal stripes, many of them
        w = int(rng.integers(scene_size // 6, scene_size // 3))
        h = int(rng.integers(scene_size // 12, scene_size // 6))
        n = int(rng.integers(6, 14)); axis = 'h'
    elif kind == 'pole':       # tall, thin, diagonal feel (rotate later)
        w = int(rng.integers(8, 22))
        h = int(rng.integers(scene_size // 6, scene_size // 3))
        n = int(rng.integers(8, 20)); axis = 'h'
    else:                      # flag — squarish, vertical stripes
        w = int(rng.integers(scene_size // 10, scene_size // 5))
        h = int(rng.integers(scene_size // 12, scene_size // 6))
        n = int(rng.integers(3, 7)); axis = 'v'
    im = Image.new('RGBA', (max(w, 2), max(h, 2)), (0, 0, 0, 0))
    draw = ImageDraw.Draw(im)
    if axis == 'h':
        for i in range(n):
            y0, y1 = int(i * h / n), int((i + 1) * h / n)
            draw.rectangle((0, y0, w, y1), fill=(red if i % 2 == 0 else white) + (255,))
    else:
        for i in range(n):
            x0, x1 = int(i * w / n), int((i + 1) * w / n)
            draw.rectangle((x0, 0, x1, h), fill=(red if i % 2 == 0 else white) + (255,))
    rot = float(rng.uniform(-25, 25)) if kind == 'pole' else float(rng.uniform(-8, 8))
    out = _rotate_rgba(im, rot)
    return out, out.size


def render_distractor(w, h, rng, palette_overlap, palette_jitter=0):
    """A random shape (rectangle/circle/triangle) with cold or Wally-palette colour."""
    if rng.random() < palette_overlap:
        base = WALDO_RED if rng.random() < 0.5 else WALDO_WHITE
        color = _jitter_color(rng, base, palette_jitter)
    else:
        color = tuple(int(c) for c in COLD_PALETTE[int(rng.integers(0, len(COLD_PALETTE)))])
    shape = rng.choice(['rectangle', 'circle', 'triangle'])
    im = Image.new('RGBA', (w, h), (0, 0, 0, 0))
    draw = ImageDraw.Draw(im)
    rgba = color + (255,)
    if shape == 'rectangle':
        draw.rectangle((0, 0, w - 1, h - 1), fill=rgba)
    elif shape == 'circle':
        draw.ellipse((0, 0, w - 1, h - 1), fill=rgba)
    else:
        draw.polygon([(w // 2, 0), (0, h - 1), (w - 1, h - 1)], fill=rgba)
    return im


def render_background(scene_size, kind, rng):
    if kind == 'solid':
        c = tuple(int(rng.integers(80, 200)) for _ in range(3))
        return Image.new('RGB', (scene_size, scene_size), c)
    if kind == 'gradient':
        c1 = tuple(int(rng.integers(50, 150)) for _ in range(3))
        c2 = tuple(int(rng.integers(150, 230)) for _ in range(3))
        arr = np.zeros((scene_size, scene_size, 3), dtype=np.uint8)
        for i in range(scene_size):
            t = i / max(1, scene_size - 1)
            for k in range(3):
                arr[i, :, k] = int(c1[k] * (1 - t) + c2[k] * t)
        return Image.fromarray(arr)
    if kind == 'noise':
        arr = rng.integers(0, 256, size=(scene_size, scene_size, 3), dtype=np.uint8)
        return Image.fromarray(arr)
    raise ValueError(f'unknown background kind: {kind!r}')


def _occlude(scene, box, rng, amount):
    """Paint 1–2 opaque background-coloured patches over part of `box` to truncate
    its stripes. `amount` in [0,1] is the max fraction of the box's area covered."""
    if not amount:
        return
    x0, y0, x1, y1 = box
    bw, bh = x1 - x0, y1 - y0
    if bw < 4 or bh < 4:
        return
    draw = ImageDraw.Draw(scene)
    for _ in range(int(rng.integers(1, 3))):
        frac = float(rng.uniform(0.2, amount))
        # Occlude from a random edge so part of the target stays visible.
        side = str(rng.choice(['top', 'bottom', 'left', 'right']))
        col = tuple(int(rng.integers(60, 180)) for _ in range(3)) + (255,)
        if side == 'top':
            draw.rectangle((x0, y0, x1, y0 + int(bh * frac)), fill=col)
        elif side == 'bottom':
            draw.rectangle((x0, y1 - int(bh * frac), x1, y1), fill=col)
        elif side == 'left':
            draw.rectangle((x0, y0, x0 + int(bw * frac), y1), fill=col)
        else:
            draw.rectangle((x1 - int(bw * frac), y0, x1, y1), fill=col)


def _apply_photometric(im, rng, spec):
    """Degrade the final RGB scene to mimic a photographed printed page.
    `spec` is None/0 (off) or a level in (0,1]; or a dict of explicit knobs."""
    if not spec:
        return im
    if isinstance(spec, dict):
        p = spec
    else:
        lv = float(spec)
        p = dict(brightness=0.15 * lv, contrast=0.15 * lv, noise=12 * lv,
                 blur=0.8 * lv, jpeg_q=int(90 - 40 * lv))
    arr = np.asarray(im).astype(np.float32)
    b = 1.0 + rng.uniform(-p.get('brightness', 0), p.get('brightness', 0))
    c = 1.0 + rng.uniform(-p.get('contrast', 0), p.get('contrast', 0))
    arr = (arr - 128.0) * c + 128.0 * b
    if p.get('noise', 0):
        arr = arr + rng.normal(0, p['noise'], size=arr.shape)
    im = Image.fromarray(np.clip(arr, 0, 255).astype(np.uint8))
    if p.get('blur', 0):
        im = im.filter(ImageFilter.GaussianBlur(radius=float(p['blur'])))
    if p.get('jpeg_q'):
        buf = io.BytesIO()
        im.save(buf, format='JPEG', quality=int(p['jpeg_q']))
        buf.seek(0)
        im = Image.open(buf).convert('RGB')
    return im


def _overlap(a, b):
    return not (a[2] <= b[0] or a[0] >= b[2] or a[3] <= b[1] or a[1] >= b[3])


def _sample_rotation(rng, spec):
    """`spec` can be None/0 (no rotation), a number (fixed), or a (lo,hi) tuple."""
    if spec is None:
        return 0.0
    if isinstance(spec, (int, float)):
        return float(spec)
    lo, hi = spec
    return float(rng.uniform(lo, hi))


def _sample_size_scale(rng, jitter):
    """`jitter` in [0,1] → multiplicative factor uniform in [1-j, 1+j]. 0 disables."""
    if not jitter:
        return 1.0
    return float(rng.uniform(1.0 - jitter, 1.0 + jitter))


def _sample_target_size(rng, spec):
    """`spec` is a number (fixed) or a (lo,hi) tuple sampled log-uniformly so the
    scale axis covers small and large Wallys evenly in log-space."""
    if isinstance(spec, (int, float)):
        return float(spec)
    lo, hi = spec
    return float(np.exp(rng.uniform(np.log(lo), np.log(hi))))


def make_scene(rng=None,
               scene_size=768,
               target_size=(8, 20),
               target_aspect=0.5,
               aspect_jitter=0.0,
               target_rotation=0.0,
               target_size_jitter=0.0,
               palette_jitter=0,
               n_distractors=100,
               palette_overlap=0.5,
               n_near_waldo=3,
               near_waldo_variants=NEAR_WALDO_VARIANTS,
               n_striped_clutter=0,
               occlusion=0.0,
               photometric=None,
               distractor_size_range=(8, 40),
               background='gradient',
               return_instances=False):
    """Generate one synthetic scene.

    Args:
      rng: numpy Generator; one is created if None.
      scene_size: scene side length in pixels. Default 768 keeps a calibrated-small
        Wally resolvable (real Wally is ~1.4% of page width → ~11px here, ~21px tall,
        ~4px/stripe). Push lower to enter the sub-resolvable regime.
      target_size: Wally width in px. Scalar (fixed) or (lo,hi) tuple sampled
        log-uniformly. Default (8,20) ≈ real rel-width 1.0–2.6% (median 1.6%) at
        scene_size=768, matching the real median of 1.4%.
      target_aspect: Wally W/H ratio (0.5 → twice as tall as wide). Real median 0.52.
      aspect_jitter: per-scene multiplicative jitter on aspect in [0,1] (real range
        0.33–1.0). 0 disables.
      target_rotation: rotation degrees; number (fixed) or (lo,hi) sampled per shape.
        Friends sample independently from the same spec so rotation isn't a tell.
      target_size_jitter: per-scene multiplicative size jitter in [0,1].
      palette_jitter: per-shape ±RGB jitter (0..255 units) on Wally/friend/clutter
        palettes, to span the measured real palette spread. 0 = exact calibrated colours.
      n_distractors: number of random shape distractors.
      palette_overlap: P(each distractor uses Wally-palette). Default 0.5 reflects
        the ~17–22% real page red/white density — colour alone can't localise.
      n_near_waldo: number of canonical 'friend' hard distractors.
      near_waldo_variants: which friends to sample (odlaw/wenda/wizard/woof, or the
        legacy mechanism aliases).
      n_striped_clutter: number of striped NON-targets (awning/pole/flag) — right
        colour+texture, wrong scale/shape. The texture-shortcut adversary.
      occlusion: in [0,1]; max fraction of Wally (and friends) covered by opaque
        patches that truncate stripes. 0 disables.
      photometric: None/0 (off), a level in (0,1], or a dict of explicit knobs
        (brightness/contrast/noise/blur/jpeg_q) applied to the final scene.
      distractor_size_range: (min, max) pixel width/height for distractors.
      background: 'solid', 'gradient', or 'noise'.
      return_instances: if True, also return friend instances as
        `[((x,y,w,h), variant_name), ...]` for multi-instance evaluation.

    Returns:
      `(PIL.Image RGB, target_bbox=(x,y,w,h))` by default; `(im, target_bbox,
      friend_instances)` if return_instances. Target painted last (on top).
    """
    if rng is None:
        rng = np.random.default_rng()

    # Render target first so we know its (post-rotation) AABB and can reserve space.
    base_size = _sample_target_size(rng, target_size)
    aspect = target_aspect * _sample_size_scale(rng, aspect_jitter)
    t_scale = _sample_size_scale(rng, target_size_jitter)
    tw_raw = max(6, int(round(base_size * t_scale)))
    th_raw = max(6, int(round(base_size / max(aspect, 1e-3) * t_scale)))
    if tw_raw >= scene_size - 20 or th_raw >= scene_size - 20:
        raise ValueError(f'target {tw_raw}x{th_raw} too large for scene {scene_size}')
    t_rot = _sample_rotation(rng, target_rotation)
    target_im = render_target(tw_raw, th_raw, n_stripes=5, rotation_deg=t_rot,
                              rng=rng, palette_jitter=palette_jitter)
    tw, th = target_im.size  # post-rotation AABB

    scene = render_background(scene_size, background, rng).convert('RGBA')

    tx = int(rng.integers(5, scene_size - tw - 5))
    ty = int(rng.integers(5, scene_size - th - 5))
    target_box = (tx, ty, tx + tw, ty + th)

    # Striped non-target clutter (placed before distractors so smaller shapes layer on top).
    for _ in range(n_striped_clutter):
        a = 0
        while a < 40:
            a += 1
            d, (cw, ch) = render_striped_clutter(rng, scene_size, palette_jitter)
            if cw >= scene_size - 5 or ch >= scene_size - 5:
                continue
            cx = int(rng.integers(0, scene_size - cw))
            cy = int(rng.integers(0, scene_size - ch))
            if _overlap((cx, cy, cx + cw, cy + ch), target_box):
                continue
            scene.paste(d, (cx, cy), d)
            break

    # Random shape distractors.
    attempts = 0
    placed = 0
    max_attempts = max(n_distractors * 5, 100)
    while placed < n_distractors and attempts < max_attempts:
        attempts += 1
        dw = int(rng.integers(distractor_size_range[0], distractor_size_range[1] + 1))
        dh = int(rng.integers(distractor_size_range[0], distractor_size_range[1] + 1))
        if dw >= scene_size - 5 or dh >= scene_size - 5:
            continue
        dx = int(rng.integers(0, scene_size - dw))
        dy = int(rng.integers(0, scene_size - dh))
        bb = (dx, dy, dx + dw, dy + dh)
        if _overlap(bb, target_box):
            continue
        d = render_distractor(dw, dh, rng, palette_overlap, palette_jitter)
        scene.paste(d, (dx, dy), d)
        placed += 1

    # Near-Wally hard distractors — same rotation/size-jitter distribution as target.
    friend_instances = []
    placed_friend_boxes = []
    for _ in range(n_near_waldo):
        a = 0
        while a < 60:
            a += 1
            f_scale = _sample_size_scale(rng, target_size_jitter)
            nw_w_raw = int(tw_raw * float(rng.uniform(0.8, 1.2)) * (f_scale / max(t_scale, 1e-6)))
            nw_h_raw = int(th_raw * float(rng.uniform(0.8, 1.2)) * (f_scale / max(t_scale, 1e-6)))
            if nw_w_raw < 4 or nw_h_raw < 4:
                continue
            f_rot = _sample_rotation(rng, target_rotation)
            d, variant = render_near_waldo(nw_w_raw, nw_h_raw, rng, rotation_deg=f_rot,
                                           variants=near_waldo_variants,
                                           palette_jitter=palette_jitter)
            nw_w, nw_h = d.size
            if nw_w >= scene_size - 10 or nw_h >= scene_size - 10:
                continue
            nx = int(rng.integers(5, scene_size - nw_w - 5))
            ny = int(rng.integers(5, scene_size - nw_h - 5))
            bb = (nx, ny, nx + nw_w, ny + nw_h)
            if _overlap(bb, target_box):
                continue
            if any(_overlap(bb, pf) for pf in placed_friend_boxes):
                continue
            scene.paste(d, (nx, ny), d)
            # Friends can be occluded too (so occlusion isn't a Wally-only tell).
            _occlude(scene, bb, rng, occlusion)
            placed_friend_boxes.append(bb)
            friend_instances.append(((nx, ny, nw_w, nw_h), variant))
            break

    # Target painted last so it's on top of any overlapping shapes that snuck through.
    scene.paste(target_im, (tx, ty), target_im)
    _occlude(scene, target_box, rng, occlusion)

    scene = scene.convert('RGB')
    scene = _apply_photometric(scene, rng, photometric)
    if return_instances:
        return scene, (tx, ty, tw, th), friend_instances
    return scene, (tx, ty, tw, th)

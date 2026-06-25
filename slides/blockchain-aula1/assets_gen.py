"""Figuras da Aula 1 (introdução a blockchain).

Matplotlib, paleta fixa por PLAN.md (objeto -> cor), fontes >=13 pt, fundo
branco, 300 dpi. Diagramas conceituais com _box/_arrow; gráficos de dados
(energia, TPS) usam estimativas públicas de ORDEM DE GRANDEZA, rotuladas com a
fonte na própria figura — nunca apresentadas como precisas.

Run: venv/bin/python slides/blockchain/assets_gen.py
"""
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
from matplotlib.patches import FancyBboxPatch, FancyArrowPatch, Circle, Rectangle
import numpy as np
from pathlib import Path

OUT = Path(__file__).parent / "assets"
OUT.mkdir(exist_ok=True)

COL = {
    "chain":  "#1f77b4",   # cadeia / bitcoin / a resposta
    "risk":   "#d62728",   # autoridade central / traidor / gasto-duplo
    "honest": "#2ca02c",   # rede honesta / distribuida
    "energy": "#ff7f0e",   # custo / energia
    "gray":   "#6b7280",   # estrutura neutra
}
INK = "#1f2937"
plt.rcParams.update({
    "font.family": "sans-serif",
    "font.sans-serif": ["Helvetica", "Arial", "DejaVu Sans"],
    "text.color": INK, "axes.labelcolor": INK,
    "xtick.color": INK, "ytick.color": INK, "axes.edgecolor": INK,
    "savefig.dpi": 300, "savefig.bbox": "tight", "figure.facecolor": "white",
})


def _ax(w=9.5, h=5.2, xlim=10, ylim=6):
    fig, ax = plt.subplots(figsize=(w, h))
    ax.set_xlim(0, xlim); ax.set_ylim(0, ylim); ax.axis("off")
    return fig, ax


def _tint(hex_, f=0.85):
    h = hex_.lstrip("#"); r, g, b = (int(h[i:i + 2], 16) for i in (0, 2, 4))
    return "#%02x%02x%02x" % (int(r + (255 - r) * f),
                              int(g + (255 - g) * f), int(b + (255 - b) * f))


def _box(ax, xy, w, h, text, fc, ec, fs=15, tc=INK, bold=True):
    x, y = xy
    ax.add_patch(FancyBboxPatch(
        (x, y), w, h, boxstyle="round,pad=0.02,rounding_size=0.08",
        linewidth=2, edgecolor=ec, facecolor=fc, zorder=2))
    if text:
        ax.text(x + w / 2, y + h / 2, text, ha="center", va="center",
                fontsize=fs, color=tc,
                fontweight="bold" if bold else "normal", zorder=3)


def _arrow(ax, p0, p1, color=INK, text=None, fs=13, lw=2.4, style="-|>"):
    ax.add_patch(FancyArrowPatch(
        p0, p1, arrowstyle=style, mutation_scale=20,
        linewidth=lw, color=color, zorder=1))
    if text:
        mx, my = (p0[0] + p1[0]) / 2, (p0[1] + p1[1]) / 2
        ax.text(mx, my + 0.18, text, ha="center", va="bottom",
                fontsize=fs, color=color, style="italic", zorder=3)


def _note(ax, x, y, text, color, fs=12.5, bold=False, italic=True):
    ax.text(x, y, text, ha="center", va="center", fontsize=fs, color=color,
            fontweight="bold" if bold else "normal",
            style="italic" if italic else "normal")


def _key(ax, x, y, color, s=1.0, flip=False):
    """Glifo de chave (anel + lâmina + dentes); lâmina p/ direita, flip=esquerda."""
    d = -1 if flip else 1
    r = 0.17 * s
    ax.add_patch(Circle((x, y), r, facecolor="white", edgecolor=color, lw=3.2, zorder=4))
    ax.add_patch(Circle((x, y), r * 0.42, facecolor=color, edgecolor=color, lw=0, zorder=5))
    x2 = x + d * (r + 0.62 * s)
    ax.plot([x + d * r, x2], [y, y], color=color, lw=4.5, solid_capstyle="round", zorder=4)
    ax.plot([x2, x2], [y, y - 0.18 * s], color=color, lw=4.5, solid_capstyle="round", zorder=4)
    ax.plot([x2 - d * 0.2 * s, x2 - d * 0.2 * s], [y, y - 0.13 * s], color=color,
            lw=4.5, solid_capstyle="round", zorder=4)


# ============================================================ double spend
def diagram_double_spend():
    fig, ax = _ax()
    _box(ax, (0.6, 2.5), 2.4, 1.3, "Alice", _tint(COL["gray"]), COL["gray"], fs=18)
    ax.add_patch(Circle((3.7, 3.15), 0.45, facecolor=_tint(COL["energy"], 0.55),
                        edgecolor=COL["energy"], lw=2.2, zorder=4))
    ax.text(3.7, 3.15, "moeda", ha="center", va="center", fontsize=11,
            color=INK, zorder=5)
    _box(ax, (6.9, 4.0), 2.4, 1.2, "Bob", _tint(COL["honest"]), COL["honest"], fs=18)
    _box(ax, (6.9, 0.9), 2.4, 1.2, "Carol", _tint(COL["honest"]), COL["honest"], fs=18)
    _arrow(ax, (4.15, 3.4), (6.9, 4.55), color=COL["risk"], lw=2.6)
    _arrow(ax, (4.15, 2.9), (6.9, 1.55), color=COL["risk"], lw=2.6)
    fig.savefig(OUT / "diagram_double_spend.png"); plt.close(fig)


# =========================================================== central ledger
def diagram_central_ledger():
    fig, ax = _ax(w=9.5, h=4.6, ylim=5)
    _box(ax, (3.6, 1.7), 2.8, 1.6, "BANCO\n(livro-razão único)",
         _tint(COL["risk"]), COL["risk"], fs=15)
    users = [(0.8, 3.3), (0.8, 0.7), (8.3, 3.3), (8.3, 0.7)]
    names = ["A", "B", "C", "D"]
    for (ux, uy), nm in zip(users, names):
        _box(ax, (ux, uy), 0.9, 0.9, nm, _tint(COL["gray"]), COL["gray"], fs=15)
    _arrow(ax, (1.7, 3.75), (3.6, 2.9), color=COL["gray"], lw=1.6)
    _arrow(ax, (1.7, 1.15), (3.6, 2.1), color=COL["gray"], lw=1.6)
    _arrow(ax, (8.3, 3.75), (6.4, 2.9), color=COL["gray"], lw=1.6)
    _arrow(ax, (8.3, 1.15), (6.4, 2.1), color=COL["gray"], lw=1.6)
    fig.savefig(OUT / "diagram_central_ledger.png"); plt.close(fig)


# ======================================================= distributed ledger
def diagram_distributed_ledger():
    fig, ax = _ax()
    cx, cy, R, n = 5.0, 3.0, 2.0, 6
    pts = []
    for i in range(n):
        ang = np.pi / 2 - i * 2 * np.pi / n
        pts.append((cx + R * np.cos(ang), cy + R * np.sin(ang)))
    for i in range(n):
        x0, y0 = pts[i]; x1, y1 = pts[(i + 1) % n]
        ax.plot([x0, x1], [y0, y1], color=_tint(COL["honest"], 0.45),
                lw=1.6, zorder=1)
    for (px, py) in pts:
        _box(ax, (px - 0.6, py - 0.36), 1.2, 0.72, "livro",
             _tint(COL["honest"]), COL["honest"], fs=12)
    ax.add_patch(Circle((cx, cy), 0.62, facecolor="white",
                        edgecolor=COL["risk"], lw=2.2, zorder=4))
    ax.text(cx, cy, "?", ha="center", va="center", fontsize=42,
            fontweight="bold", color=COL["risk"], zorder=5)
    fig.savefig(OUT / "diagram_distributed_ledger.png"); plt.close(fig)


# ============================================================== signature
def diagram_signature():
    fig, ax = _ax(w=12, h=5.0, xlim=13, ylim=5)
    g, r, b, gr = COL["gray"], COL["risk"], COL["chain"], COL["honest"]
    # pipeline principal (assinar -> assinatura -> verificar), y ~ 3.15
    _box(ax, (0.2, 2.7), 1.8, 0.9, "mensagem", _tint(g), g, fs=14)
    _box(ax, (2.6, 2.55), 1.7, 1.2, "ASSINAR", _tint(b), b, fs=15)
    _box(ax, (4.9, 2.6), 1.9, 1.1, "", _tint(b, 0.78), b)
    ax.text(5.85, 3.4, "assinatura", ha="center", va="center", fontsize=13,
            color=b, fontweight="bold")
    ax.add_patch(Circle((5.85, 2.97), 0.2, facecolor=_tint(b, 0.4), edgecolor=b, lw=1.8, zorder=4))
    _box(ax, (7.4, 2.55), 1.8, 1.2, "VERIFICAR", _tint(gr), gr, fs=15)
    _box(ax, (9.8, 2.65), 1.95, 1.0, "", _tint(gr), gr)
    ax.plot([10.0, 10.18, 10.5], [3.13, 2.92, 3.45], color=gr, lw=4.5,
            solid_capstyle="round", solid_joinstyle="round", zorder=5)
    ax.text(11.05, 3.13, "válida", ha="center", va="center", fontsize=16,
            color=gr, fontweight="bold")
    _arrow(ax, (2.0, 3.15), (2.6, 3.15), color=g, lw=2.0)
    _arrow(ax, (4.3, 3.15), (4.9, 3.15), color=b, lw=2.2)
    _arrow(ax, (6.8, 3.15), (7.4, 3.15), color=b, lw=2.2)
    _arrow(ax, (9.2, 3.15), (9.8, 3.15), color=gr, lw=2.2)
    # chaves: privada alimenta ASSINAR, pública alimenta VERIFICAR (y ~ 1.55)
    _key(ax, 3.0, 1.55, r, s=1.1)
    _key(ax, 7.7, 1.55, gr, s=1.1, flip=True)
    _arrow(ax, (3.2, 1.95), (3.4, 2.55), color=r, lw=2.0)
    _arrow(ax, (7.95, 1.95), (8.2, 2.55), color=gr, lw=2.0)
    ax.text(3.0, 0.78, "chave privada", ha="center", fontsize=13.5, color=r, fontweight="bold")
    ax.text(3.0, 0.38, "só Alice tem", ha="center", fontsize=11, color=g, style="italic")
    ax.text(7.85, 0.78, "chave pública", ha="center", fontsize=13.5, color=gr, fontweight="bold")
    ax.text(7.85, 0.38, "todos têm", ha="center", fontsize=11, color=g, style="italic")
    # as duas chaves são um par casado
    ax.plot([3.6, 7.1], [1.55, 1.55], color=g, lw=1.4, ls=(0, (5, 4)), zorder=1)
    ax.text(5.35, 1.32, "mesmo par de chaves", ha="center", fontsize=11.5,
            color=g, style="italic")
    fig.savefig(OUT / "diagram_signature.png"); plt.close(fig)


# ================================================================== hash
def diagram_hash():
    fig, ax = _ax(w=11, h=4.2, xlim=12, ylim=4)
    _box(ax, (0.5, 2.5), 3.0, 1.0, '"blockchain"', _tint(COL["gray"]), COL["gray"], fs=16, bold=False)
    _box(ax, (4.2, 2.5), 1.8, 1.0, "HASH", _tint(COL["chain"]), COL["chain"], fs=15)
    _arrow(ax, (3.5, 3.0), (4.2, 3.0), color=COL["gray"], lw=1.8)
    _arrow(ax, (6.0, 3.0), (6.7, 3.0), color=COL["chain"], lw=1.8)
    ax.text(6.9, 3.0, "ef7a 91c4 ...", ha="left", va="center", fontsize=17,
            family="monospace", color=COL["chain"])
    _box(ax, (0.5, 0.5), 3.0, 1.0, '"Blockchain"', _tint(COL["gray"]), COL["gray"], fs=16, bold=False)
    _box(ax, (4.2, 0.5), 1.8, 1.0, "HASH", _tint(COL["chain"]), COL["chain"], fs=15)
    _arrow(ax, (3.5, 1.0), (4.2, 1.0), color=COL["gray"], lw=1.8)
    _arrow(ax, (6.0, 1.0), (6.7, 1.0), color=COL["chain"], lw=1.8)
    ax.text(6.9, 1.0, "02b9 7de1 ...", ha="left", va="center", fontsize=17,
            family="monospace", color=COL["risk"])
    fig.savefig(OUT / "diagram_hash.png"); plt.close(fig)


# ============================================================== hash chain
def diagram_hashchain():
    fig, ax = _ax(w=12, h=5.0, xlim=13.4, ylim=5.2)
    g, r, gr = COL["gray"], COL["risk"], COL["honest"]
    n, bw, gap, by, bh, x0 = 3, 3.0, 1.5, 1.1, 3.1, 0.6
    # (cor_bloco, prev, cor_prev, dados, cor_dados, hash, cor_hash)
    blocks = [
        (gr, "(gênese)", g, "dados",           g, "a1b2", gr),
        (r,  "a1b2",     g, "dados ALTERADOS", r, "9f0e", r),
        (r,  "c3d4",     r, "dados",           g, "b7e5", r),
    ]
    cx = []
    for i, (bc, prev, pc, dlbl, dc, hsh, hc) in enumerate(blocks):
        x = x0 + i * (bw + gap); c = x + bw / 2; cx.append(c)
        _box(ax, (x, by), bw, bh, "", _tint(bc, 0.9), bc)
        ax.text(c, by + bh - 0.5, f"Bloco {i + 1}", ha="center", fontsize=15,
                fontweight="bold", color=bc)
        ax.text(c, by + bh - 1.2, f"prev: {prev}", ha="center", fontsize=13,
                family="monospace", color=pc, fontweight="bold" if pc == r else "normal")
        ax.text(c, by + 1.35, dlbl, ha="center", fontsize=12.5, color=dc,
                fontweight="bold" if dc == r else "normal")
        ax.add_patch(FancyBboxPatch((x + 0.35, by + 0.32), bw - 0.7, 0.62,
                     boxstyle="round,pad=0.02,rounding_size=0.06",
                     linewidth=0, facecolor=_tint(hc, 0.8), zorder=2))
        ax.text(c, by + 0.63, f"hash: {hsh}", ha="center", fontsize=13.5,
                family="monospace", fontweight="bold", color=hc, zorder=3)
    # elos: hash do bloco i vira o prev do bloco i+1 (diagonal)
    for i in range(n - 1):
        broken = (i == 1)
        ec = r if broken else g
        _arrow(ax, (cx[i] + bw / 2, by + 0.63),
               (cx[i + 1] - bw / 2, by + bh - 1.2), color=ec, lw=2.4)
        if broken:
            gap_c = x0 + i * (bw + gap) + bw + gap / 2
            ax.text(gap_c, by + bh - 0.75, "não bate", ha="center", fontsize=12.5,
                    color=r, fontweight="bold", style="italic")
    fig.savefig(OUT / "diagram_hashchain.png"); plt.close(fig)


# ================================================================ mining
def diagram_mining():
    fig, ax = _ax(w=11, h=5.0, xlim=12, ylim=5.4)
    g, r, gr = COL["gray"], COL["risk"], COL["honest"]
    # alvo (a regra do jogo): o hash precisa começar com 0000
    ax.text(0.8, 5.0, "alvo:", ha="left", va="center", fontsize=15,
            color=INK, fontweight="bold")
    _box(ax, (2.0, 4.68), 1.5, 0.62, "0000…", _tint(gr, 0.78), gr, fs=15, tc=gr)
    # tentativas de nonce -> hash; só o último começa com 0000
    rows = [("nonce 1",     "9c2f", "a1 d3 …", False),
            ("nonce 2",     "41ab", "77 0e …", False),
            ("nonce 3",     "d7e0", "3c b9 …", False),
            ("…",           "",     "",        None),
            ("nonce 30418", "0000", "a3 5f …", True)]
    y = 3.75
    for lbl, head, tail, ok in rows:
        ax.text(0.8, y, lbl, ha="left", va="center", fontsize=14.5,
                family="monospace", color=INK)
        if ok is None:
            y -= 0.78; continue
        ec = gr if ok else r
        _arrow(ax, (3.5, y), (4.2, y), color=g, lw=1.5)
        _box(ax, (4.4, y - 0.3), 1.25, 0.6, head, _tint(ec, 0.78), ec, fs=14.5, tc=ec)
        ax.text(5.85, y, tail, ha="left", va="center", fontsize=14.5,
                family="monospace", color=g)
        ax.text(8.1, y, "vale!" if ok else "não bate", ha="left", va="center",
                fontsize=14 if ok else 13, color=ec,
                fontweight="bold" if ok else "normal")
        y -= 0.78
    fig.savefig(OUT / "diagram_mining.png"); plt.close(fig)


# =============================================================== generals
def diagram_generals():
    fig, ax = _ax(w=11, h=5.0, xlim=12, ylim=5.4)
    g, r, gr = COL["gray"], COL["risk"], COL["honest"]
    # um general traidor manda ordens conflitantes
    _box(ax, (0.5, 2.1), 2.9, 1.3, "General\n(traidor)", _tint(r), r, fs=15)
    # dois generais leais recebem coisas diferentes
    _box(ax, (8.0, 3.5), 3.5, 1.35, "", _tint(gr), gr)
    ax.text(9.75, 4.42, "General leal", ha="center", va="center", fontsize=14,
            color=gr, fontweight="bold")
    ax.text(9.75, 3.85, "ouviu: ATACAR", ha="center", va="center",
            fontsize=12.5, color=g, family="monospace")
    _box(ax, (8.0, 0.4), 3.5, 1.35, "", _tint(gr), gr)
    ax.text(9.75, 1.32, "General leal", ha="center", va="center", fontsize=14,
            color=gr, fontweight="bold")
    ax.text(9.75, 0.75, "ouviu: RECUAR", ha="center", va="center",
            fontsize=12.5, color=g, family="monospace")
    _arrow(ax, (3.4, 3.0), (8.0, 4.2), color=r, lw=2.4, text="ATACAR")
    _arrow(ax, (3.4, 2.4), (8.0, 1.05), color=r, lw=2.4, text="RECUAR")
    # os leais ouviram ordens opostas — não dá pra concordar
    ax.plot([9.75, 9.75], [3.5, 1.75], color=g, lw=1.4, ls=(0, (5, 4)), zorder=1)
    ax.add_patch(Circle((9.75, 2.62), 0.42, facecolor="white", edgecolor=r,
                        lw=2.2, zorder=4))
    ax.text(9.75, 2.62, "?", ha="center", va="center", fontsize=26, color=r,
            fontweight="bold", zorder=5)
    fig.savefig(OUT / "diagram_generals.png"); plt.close(fig)


# ============================================================ byzantine 3f+1
def diagram_byzantine_3f1():
    fig, ax = _ax(w=11, xlim=12, ylim=6)
    _box(ax, (4.5, 2.7), 3.0, 1.4, "Tenente 1\n(leal)", _tint(COL["honest"]), COL["honest"], fs=15)
    _box(ax, (0.4, 4.4), 3.6, 1.0, 'Comandante: "ATACAR"', _tint(COL["gray"]), COL["gray"], fs=13, bold=False)
    _box(ax, (0.4, 2.9), 3.6, 1.0, 'Tenente 2: "ele disse RECUAR"', _tint(COL["gray"]), COL["gray"], fs=12, bold=False)
    _arrow(ax, (4.0, 4.9), (4.5, 3.7), color=COL["gray"], lw=1.6)
    _arrow(ax, (4.0, 3.4), (4.5, 3.2), color=COL["gray"], lw=1.6)
    _box(ax, (8.0, 4.3), 3.6, 1.0, "culpado: o Comandante?", _tint(COL["risk"], 0.9), COL["risk"], fs=13, bold=False)
    _box(ax, (8.0, 2.7), 3.6, 1.0, "culpado: o Tenente 2?", _tint(COL["risk"], 0.9), COL["risk"], fs=13, bold=False)
    _arrow(ax, (7.5, 3.6), (8.0, 4.8), color=COL["risk"], lw=1.6)
    _arrow(ax, (7.5, 3.2), (8.0, 3.2), color=COL["risk"], lw=1.6)
    _note(ax, 6.0, 1.7,
          "as duas situações são IDÊNTICAS para ele — impossível decidir",
          COL["risk"], fs=14, bold=True, italic=False)
    _note(ax, 6.0, 0.8,
          "com 3 generais, 1 traidor já é insolúvel  ->  precisa de 3f+1 (mais de 2/3 leais)",
          INK, fs=13)
    fig.savefig(OUT / "diagram_byzantine_3f1.png"); plt.close(fig)


# =============================================================== sybil / pow
def diagram_sybil_pow():
    fig, ax = _ax(w=11, xlim=12, ylim=6)
    ax.plot([6, 6], [0.5, 5.2], color=COL["gray"], lw=1, ls="--", zorder=0)
    _note(ax, 3.0, 5.5, "voto por IDENTIDADE", COL["risk"], fs=15, bold=True, italic=False)
    _box(ax, (0.4, 3.3), 1.9, 1.0, "1 pessoa", _tint(COL["risk"]), COL["risk"], fs=14)
    for i, yy in enumerate([4.6, 3.8, 3.0, 2.2]):
        _box(ax, (3.2, yy - 0.28), 2.0, 0.56, f"identidade {i + 1}",
             _tint(COL["gray"]), COL["gray"], fs=10.5, bold=False)
        _arrow(ax, (2.3, 3.8), (3.2, yy), color=COL["risk"], lw=1.3)
    _note(ax, 3.0, 1.1, "identidades são de graça -> dá pra forjar mil votos",
          COL["risk"], fs=12)
    _note(ax, 9.0, 5.5, "voto por TRABALHO (PoW)", COL["chain"], fs=15, bold=True, italic=False)
    _box(ax, (6.7, 3.3), 1.9, 1.0, "1 voto", _tint(COL["chain"]), COL["chain"], fs=14)
    _box(ax, (9.7, 3.3), 1.7, 1.0, "energia", _tint(COL["energy"]), COL["energy"], fs=13)
    _arrow(ax, (8.6, 3.8), (9.7, 3.8), color=COL["energy"], lw=2.2, text="custa")
    _note(ax, 9.0, 1.1, "cada voto custa trabalho real -> não dá pra forjar de graça",
          COL["chain"], fs=12)
    fig.savefig(OUT / "diagram_sybil_pow.png"); plt.close(fig)


# ============================================================= longest chain
def diagram_longest_chain():
    fig, ax = _ax(w=11, xlim=12, ylim=6)

    def blk(x, y, c):
        _box(ax, (x, y), 1.2, 0.9, "", _tint(c), c)

    for i in range(3):
        x = 0.4 + i * 1.6; blk(x, 2.6, COL["gray"])
        if i:
            _arrow(ax, (x - 0.4, 3.05), (x, 3.05), color=COL["gray"], lw=1.4)
    fx = 0.4 + 3 * 1.6
    for j in range(3):
        x = fx + j * 1.6; blk(x, 4.0, COL["chain"])
        if j:
            _arrow(ax, (x - 0.4, 4.45), (x, 4.45), color=COL["chain"], lw=1.4)
    for j in range(2):
        x = fx + j * 1.6; blk(x, 1.2, COL["gray"])
        if j:
            _arrow(ax, (x - 0.4, 1.65), (x, 1.65), color=COL["gray"], lw=1.4)
    last = 0.4 + 2 * 1.6 + 1.2
    _arrow(ax, (last, 3.2), (fx, 4.3), color=COL["chain"], lw=1.6)
    _arrow(ax, (last, 2.9), (fx, 1.75), color=COL["gray"], lw=1.6)
    _note(ax, fx + 3 * 1.6 + 0.7, 4.45, "mais longa\n-> vence",
          COL["chain"], fs=13, bold=True, italic=False)
    _note(ax, fx + 2 * 1.6 + 0.6, 1.65, "descartada", COL["gray"], fs=12.5)
    _note(ax, 5.6, 0.35,
          "sem autoridade, vale a cadeia com mais trabalho acumulado",
          COL["gray"], fs=12.5)
    fig.savefig(OUT / "diagram_longest_chain.png"); plt.close(fig)


# ================================================================== bridge
def diagram_bridge():
    fig, ax = _ax(w=11, xlim=12, ylim=6)
    for i in range(3):
        x = 0.5 + i * 1.5
        _box(ax, (x, 3.4), 1.3, 1.2, "moeda", _tint(COL["chain"]), COL["chain"], fs=12)
        if i:
            _arrow(ax, (x - 0.2, 4.0), (x, 4.0), color=COL["chain"], lw=1.4)
    _note(ax, 2.65, 5.1, "livro-razão de moedas", COL["chain"], fs=14, bold=True, italic=False)
    _arrow(ax, (5.3, 4.0), (6.6, 4.0), color=INK, lw=2.4, text="e se...")
    for i in range(3):
        x = 6.9 + i * 1.5
        _box(ax, (x, 3.4), 1.3, 1.2, "{ código }", _tint(COL["honest"]), COL["honest"], fs=11)
        if i:
            _arrow(ax, (x - 0.2, 4.0), (x, 4.0), color=COL["honest"], lw=1.4)
    _note(ax, 9.05, 5.1, "livro-razão que roda código", COL["honest"], fs=14, bold=True, italic=False)
    _note(ax, 6.0, 2.0, "Aula 2: smart contracts", INK, fs=18, bold=True, italic=False)
    _note(ax, 6.0, 1.1,
          "...mas você precisa mesmo de uma blockchain para tudo?",
          COL["gray"], fs=13)
    fig.savefig(OUT / "diagram_bridge.png"); plt.close(fig)


# ================================================================ timeline
def fig_timeline():
    # Inventário: peças reaproveitadas (esquerda) + a única peça nova (direita).
    fig, ax = plt.subplots(figsize=(12.5, 6.0))
    ax.set_xlim(0, 14); ax.set_ylim(0, 6.5); ax.axis("off")
    g, b = COL["gray"], COL["chain"]
    # --- esquerda: peças que já existiam (cada uma com origem e ano) ---
    ax.text(2.95, 6.28, "peças que já existiam", ha="center", fontsize=14,
            fontweight="bold", color=g)
    pieces = [
        ("hash de mão única", "cripto clássica · ~1976"),
        ("assinatura digital (dono da moeda)", "Diffie-Hellman, RSA · 1976"),
        ("árvore de Merkle (resumo do bloco)", "Merkle · 1980"),
        ("cadeia de hashes (à prova de fraude)", "Haber-Stornetta · 1991"),
        ("prova de trabalho (o custo)", "Hashcash · 1997"),
        ("moeda PoW descentralizada (a visão)", "b-money, bit gold · 1998"),
    ]
    pwd, ph, x0, y = 5.5, 0.66, 0.25, 5.65
    for name, src in pieces:
        _box(ax, (x0, y - ph), pwd, ph, "", _tint(g, 0.87), g)
        ax.text(x0 + 0.22, y - ph / 2 + 0.1, name, ha="left", va="center",
                fontsize=11.5, color=INK, fontweight="bold")
        ax.text(x0 + 0.22, y - ph / 2 - 0.17, src, ha="left", va="center",
                fontsize=9.5, color=g, style="italic")
        y -= (ph + 0.19)
    # --- "+" entre as zonas ---
    ax.text(6.2, 3.1, "+", ha="center", va="center", fontsize=38, color=g)
    # --- direita: a única peça nova ---
    bx, bwd, byy, bhd = 6.75, 7.0, 1.75, 3.6
    _box(ax, (bx, byy), bwd, bhd, "", _tint(b, 0.82), b)
    cx = bx + bwd / 2
    ax.text(cx, byy + bhd - 0.42, "a única peça NOVA  (Nakamoto, 2008)",
            ha="center", fontsize=11.5, color=b, fontweight="bold", style="italic")
    ax.text(cx, byy + bhd - 0.98, "Consenso de membro aberto", ha="center",
            fontsize=17, color=b, fontweight="bold")
    chips = ["PoW = voto  (resiste a Sybil)",
             "cadeia mais longa  (desempate objetivo)",
             "incentivo  (recompensa o honesto)"]
    cyy = byy + bhd - 1.7
    for ch in chips:
        _box(ax, (bx + 0.55, cyy - 0.27), bwd - 1.1, 0.5, ch, "white", b,
             fs=11.5, tc=INK, bold=False)
        cyy -= 0.64
    # --- resultado ---
    ax.text(cx, byy - 0.42, "concordar entre desconhecidos anônimos,",
            ha="center", fontsize=10.5, color=g, style="italic")
    ax.text(cx, byy - 0.8, "sem cadastro e sem autoridade   =   Bitcoin",
            ha="center", fontsize=13, color=INK, fontweight="bold")
    fig.savefig(OUT / "fig_timeline.png"); plt.close(fig)


# ============================================== BLOCO TECNICO (pos-intervalo)
# Espinha tecnica: cada marco da timeline = um mecanismo real do Bitcoin.
# Formula = o proprio artefato visual (mathtext); a prosa explicativa fica na
# legenda editavel do slide (build_pptx). Matematica entre medio e completo.

# ----------------------------------------------------------- arvore de Merkle
def fig_merkle():
    fig, ax = _ax(w=12.5, h=5.6, xlim=14, ylim=6)
    g, b, e, gr = COL["gray"], COL["chain"], COL["energy"], COL["honest"]
    faint = "#cdd0d6"  # nós que o verificador NUNCA vê
    # ---- a árvore (esquerda) ----
    leafc = [1.0, 2.6, 5.0, 6.6]
    h01x, h23x, rootx = 1.8, 5.8, 3.8
    ly, lh, my, mh, ry, rh = 1.6, 0.7, 3.0, 0.7, 4.5, 0.85

    def edge(x0, y0, x1, y1, c, lw=1.6):
        ax.plot([x0, x1], [y0, y1], color=c, lw=lw, zorder=1)

    # azul = recomputado · laranja = recebido (a prova) · apagado = nunca visto
    edge(leafc[0], ly + lh, h01x, my, faint); edge(leafc[1], ly + lh, h01x, my, faint)
    edge(leafc[2], ly + lh, h23x, my, b, lw=2.8)
    edge(leafc[3], ly + lh, h23x, my, e, lw=2.2)
    edge(h01x, my + mh, rootx, ry, e, lw=2.2); edge(h23x, my + mh, rootx, ry, b, lw=2.8)
    leafcol = [faint, faint, b, e]
    for i, xc in enumerate(leafc):
        c = leafcol[i]; on = c is not faint
        _box(ax, (xc - 0.7, ly), 1.4, lh, f"$h_{i}$",
             _tint(c, 0.62 if on else 0.5), c, fs=15, tc=c)
        ax.text(xc, ly - 0.18, f"tx$_{i}$", ha="center", va="top", fontsize=10.5,
                color=b if i == 2 else faint, fontweight="bold" if i == 2 else "normal")
    _box(ax, (h01x - 0.7, my), 1.4, mh, "$h_{01}$", _tint(e, 0.62), e, fs=15, tc=e)
    _box(ax, (h23x - 0.7, my), 1.4, mh, "$h_{23}$", _tint(b, 0.7), b, fs=15, tc=b)
    _box(ax, (rootx - 0.8, ry), 1.6, rh, "raiz", _tint(b), b, fs=14, tc=b)
    ax.text(rootx, ry + rh + 0.3, "(no cabeçalho — lacrada pela mineração)",
            ha="center", fontsize=10, color=g, style="italic")
    # ---- painel: o que a carteira leve faz (direita) ----
    px, pw = 8.9, 4.9
    _box(ax, (px, 0.95), pw, 4.3, "", "white", g)
    cx = px + pw / 2
    ax.text(cx, 4.9, "a carteira leve verifica", ha="center", fontsize=13,
            fontweight="bold", color=INK)
    ax.text(px + 0.3, 4.42, "tem: a raiz (do cabeçalho) + sua tx$_2$",
            ha="left", fontsize=11, color=g)
    ax.text(px + 0.3, 4.04, "recebe: $h_3$, $h_{01}$  (a prova)", ha="left",
            fontsize=11, color=e, fontweight="bold")
    ax.plot([px + 0.3, px + pw - 0.3], [3.75, 3.75], color=faint, lw=1)
    ax.text(px + 0.3, 3.45, "recomputa de baixo p/ cima:", ha="left", fontsize=11, color=INK)
    ax.text(cx, 3.0, r"$h_2 = H(\mathrm{tx}_2)$", ha="center", fontsize=14, color=b)
    ax.text(cx, 2.5, r"$h_{23} = H(h_2 \Vert h_3)$", ha="center", fontsize=14, color=b)
    ax.text(cx, 2.0, r"$\mathrm{raiz}' = H(h_{01} \Vert h_{23})$", ha="center", fontsize=14, color=b)
    ax.plot([px + 0.3, px + pw - 0.3], [1.68, 1.68], color=faint, lw=1)
    ax.text(cx, 1.36, r"$\mathrm{raiz}'$ bate com a raiz?", ha="center", fontsize=12.5, color=INK)
    ax.text(cx, 1.04, "-> então tx$_2$ está no bloco", ha="center", fontsize=12.5,
            color=gr, fontweight="bold")
    # ---- faixa inferior: n e log(n) ----
    ax.text(3.8, 0.5, r"$n$ = nº de transações  ·  prova = 1 irmão por nível = $\log_2 n$ hashes",
            ha="center", fontsize=11.5, color=INK)
    ax.text(3.8, 0.13, "4 txs -> 2 hashes    ·    ~4000 txs -> ~12 hashes (~400 B, não a MB inteira)",
            ha="center", fontsize=10.5, color=g, style="italic")
    fig.savefig(OUT / "fig_merkle.png"); plt.close(fig)


# ------------------------------------------------ cabecalho de 80 bytes + elo
def fig_header():
    fig, ax = _ax(w=12, h=5.4, xlim=12, ylim=6)
    g, b, e = COL["gray"], COL["chain"], COL["energy"]
    hx, hw = 0.5, 4.7
    _box(ax, (hx, 0.5), hw, 5.0, "", "white", g)
    ax.text(hx + hw / 2, 5.15, "Cabeçalho do bloco · 80 bytes", ha="center",
            va="center", fontsize=14, fontweight="bold", color=INK)
    rows = [("versão", "4 B", g),
            ("hash do bloco anterior", "32 B", b),
            ("raiz de Merkle", "32 B", b),
            ("tempo", "4 B", g),
            ("alvo (bits)", "4 B", e),
            ("nonce", "4 B", e)]
    ry = 4.35; rowy = {}
    for label, size, c in rows:
        hl = c is not g
        _box(ax, (hx + 0.25, ry - 0.28), hw - 0.5, 0.56, "",
             _tint(c, 0.8 if hl else 0.93), c if hl else g)
        ax.text(hx + 0.45, ry, label, ha="left", va="center", fontsize=12.5,
                color=INK, fontweight="bold" if hl else "normal")
        ax.text(hx + hw - 0.35, ry, size, ha="right", va="center", fontsize=10.5,
                color=g, family="monospace")
        rowy[label] = ry; ry -= 0.68
    # cabecalho -> SHA256^2 -> hash do bloco
    _arrow(ax, (hx + hw, 3.0), (6.3, 3.0), color=g, lw=2.0)
    _box(ax, (6.3, 2.5), 1.9, 1.0, r"$\mathrm{SHA256}^2$", _tint(b), b, fs=14)
    _arrow(ax, (8.2, 3.0), (8.9, 3.0), color=b, lw=2.2)
    _box(ax, (8.9, 2.5), 2.4, 1.0, "hash\ndo bloco", _tint(b, 0.8), b, fs=13)
    # encadeamento: o hash deste bloco vira o "prev" do proximo
    _arrow(ax, (10.1, 3.5), (10.1, 4.55), color=b, lw=2.0)
    ax.text(10.1, 4.95, "= prev do\npróximo bloco", ha="center", va="center",
            fontsize=11.5, color=b, fontweight="bold")
    # alvo + nonce alimentam a prova de trabalho (proximo slide)
    _arrow(ax, (hx + hw, 1.3), (6.7, 1.3), color=e, lw=1.8)
    ax.text(8.9, 1.3, "alvo + nonce:\nentram na prova\nde trabalho", ha="center",
            va="center", fontsize=11.5, color=e, fontweight="bold")
    fig.savefig(OUT / "fig_header.png"); plt.close(fig)


# ------------------------------------------------- prova de trabalho: H < alvo
def fig_pow_target():
    fig, ax = _ax(w=11, h=5.2, xlim=12, ylim=5.6)
    g, b, gr, e = COL["gray"], COL["chain"], COL["honest"], COL["energy"]
    ax.text(6, 4.95, r"$\mathrm{SHA256}^2(\mathrm{header}) < T$", ha="center",
            va="center", fontsize=24, color=INK, fontweight="bold")
    x0, x1, yb, hb = 1.0, 11.0, 2.7, 0.5
    ax.add_patch(Rectangle((x0, yb), x1 - x0, hb, facecolor=_tint(g, 0.85),
                           edgecolor=g, lw=1.5, zorder=2))
    tw = 0.42
    ax.add_patch(Rectangle((x0, yb), tw, hb, facecolor=_tint(gr, 0.35),
                           edgecolor=gr, lw=1.5, zorder=3))
    ax.plot([x0 + tw, x0 + tw], [yb - 0.2, yb + hb + 0.25], color=gr, lw=1.6, zorder=4)
    ax.text(x0 + tw, yb + hb + 0.45, "$T$", ha="center", fontsize=16,
            color=gr, fontweight="bold")
    ax.text(x0, yb - 0.22, "0", ha="center", va="top", fontsize=12, color=g)
    ax.text(x1, yb - 0.22, r"$2^{256}-1$", ha="right", va="top", fontsize=12, color=g)
    ax.text(6, yb - 0.62, "todos os valores de hash possíveis", ha="center",
            fontsize=12.5, color=g, style="italic")
    _note(ax, 2.5, 4.0, "hash $< T$\n-> bloco vale", gr, fs=13, bold=True, italic=False)
    _arrow(ax, (1.7, 3.7), (x0 + tw / 2, yb + hb + 0.05), color=gr, lw=1.8)
    ax.text(6, 1.35, r"em média $\approx 2^{256}/T$ tentativas até cair na janela",
            ha="center", fontsize=14, color=INK)
    _note(ax, 6, 0.6, "alvo $T$ menor  ->  janela menor  ->  mais zeros à esquerda  ->  mais trabalho",
          e, fs=12.5, bold=True, italic=False)
    fig.savefig(OUT / "fig_pow_target.png"); plt.close(fig)


# ------------------------------------------------ dificuldade: retarget ~10min
def fig_difficulty():
    fig, ax = _ax(w=11, h=5.2, xlim=12, ylim=5.6)
    g, b, gr, e = COL["gray"], COL["chain"], COL["honest"], COL["energy"]
    ax.text(6, 5.05, r"$T_{\mathrm{novo}} = T_{\mathrm{velho}}\times "
            r"\frac{\Delta t_{\mathrm{real}}}{2\ \mathrm{semanas}}$",
            ha="center", va="center", fontsize=20, color=INK)
    ax.text(6, 4.35, r"(limitado a $\times\frac{1}{4}\ \dots\ \times 4$)",
            ha="center", fontsize=13, color=g, style="italic")
    bw, bh = 3.0, 1.05
    B1, B2 = (0.7, 2.55), (8.3, 2.55)
    B3, B4 = (8.3, 0.5), (0.7, 0.5)
    _box(ax, B1, bw, bh, "mais mineradores\n(hashrate sobe)", _tint(e), e, fs=12.5)
    _box(ax, B2, bw, bh, "blocos saem\nrápido demais", _tint(g), g, fs=12.5)
    _box(ax, B3, bw, bh, "alvo $T$ desce\n(fica mais difícil)", _tint(b), b, fs=12.5)
    _box(ax, B4, bw, bh, "volta a\n~10 min por bloco", _tint(gr), gr, fs=12.5)
    _arrow(ax, (B1[0] + bw, B1[1] + bh / 2), (B2[0], B2[1] + bh / 2), color=g)
    _arrow(ax, (B2[0] + bw / 2, B2[1]), (B3[0] + bw / 2, B3[1] + bh), color=g)
    _arrow(ax, (B3[0], B3[1] + bh / 2), (B4[0] + bw, B4[1] + bh / 2), color=g)
    _arrow(ax, (B4[0] + bw / 2, B4[1] + bh), (B1[0] + bw / 2, B1[1]), color=g)
    _note(ax, 6, 1.55, "reajuste a cada 2016 blocos\n(~2 semanas)", INK,
          fs=12.5, bold=True, italic=False)
    fig.savefig(OUT / "fig_difficulty.png"); plt.close(fig)


# --------------------------------------------- seguranca: ruina do apostador
def fig_security():
    fig, ax = plt.subplots(figsize=(9.5, 5.2))
    z = np.arange(0, 11)
    series = [(0.10, COL["chain"], "atacante 10%"),
              (0.30, COL["energy"], "atacante 30%"),
              (0.45, COL["risk"], "atacante 45%")]
    for q, c, lbl in series:
        ax.plot(z, (q / (1 - q)) ** z, "o-", color=c, lw=2.2, ms=5, label=lbl)
    ax.set_yscale("log"); ax.set_ylim(1e-6, 2); ax.set_xlim(0, 10)
    ax.set_xlabel("z = blocos de profundidade (confirmações)", fontsize=14)
    ax.set_ylabel("P(atacante reverter)  ·  escala log", fontsize=13)
    ax.axvline(6, color=COL["gray"], ls="--", lw=1.4)
    ax.text(5.85, 1.0, "6 confirmações", fontsize=11.5, color=COL["gray"],
            rotation=90, va="top", ha="right")
    ax.legend(fontsize=12, loc="upper right", frameon=False)
    ax.tick_params(labelsize=11)
    for s in ("top", "right"):
        ax.spines[s].set_visible(False)
    ax.text(0.0, 1.06, r"$P(\mathrm{reverter}) \approx (q/p)^{z}$",
            transform=ax.transAxes, fontsize=16, color=INK, va="bottom")
    ax.text(0.03, 0.06,
            "ruína do apostador · q = atacante, p = honesto, q < p\n"
            "(o whitepaper refina com a vantagem de Poisson)",
            transform=ax.transAxes, fontsize=9.5, color=COL["gray"], va="bottom")
    fig.savefig(OUT / "fig_security.png"); plt.close(fig)


# ================================================================== energy
def fig_energy():
    labels = ["Bitcoin", "Argentina", "Suécia", "Países\nBaixos"]
    vals = [150, 125, 130, 110]
    cols = [COL["energy"], COL["gray"], COL["gray"], COL["gray"]]
    x = np.arange(len(labels))
    fig, ax = plt.subplots(figsize=(8.6, 5.2))
    bars = ax.bar(x, vals, 0.62, color=cols, edgecolor=INK, linewidth=1)
    ax.set_ylabel("consumo elétrico anual (TWh)", fontsize=15)
    ax.set_xticks(x); ax.set_xticklabels(labels, fontsize=14)
    ax.set_ylim(0, 180); ax.tick_params(axis="y", labelsize=12)
    for b, v in zip(bars, vals):
        ax.text(b.get_x() + b.get_width() / 2, v + 2.5, f"~{v}",
                ha="center", fontsize=14, fontweight="bold")
    for s in ("top", "right"):
        ax.spines[s].set_visible(False)
    ax.text(0.0, 1.02,
            "ordem de grandeza — fontes: Cambridge CBECI + consumo nacional (~2024)",
            transform=ax.transAxes, fontsize=10.5, color=COL["gray"], va="bottom")
    fig.savefig(OUT / "fig_energy.png"); plt.close(fig)


# ===================================================================== tps
def fig_tps():
    labels = ["Bitcoin", "Ethereum", "Visa\n(média)", "Visa\n(pico)"]
    vals = [7, 20, 1700, 65000]
    cols = [COL["chain"], COL["chain"], COL["gray"], COL["gray"]]
    x = np.arange(len(labels))
    fig, ax = plt.subplots(figsize=(8.6, 5.2))
    bars = ax.bar(x, vals, 0.62, color=cols, edgecolor=INK, linewidth=1)
    ax.set_yscale("log"); ax.set_ylim(1, 2e5)
    ax.set_ylabel("transações por segundo (escala log)", fontsize=15)
    ax.set_xticks(x); ax.set_xticklabels(labels, fontsize=14)
    ax.tick_params(axis="y", labelsize=12)
    for b, v in zip(bars, vals):
        ax.text(b.get_x() + b.get_width() / 2, v * 1.25, f"{v:,}".replace(",", "."),
                ha="center", fontsize=14, fontweight="bold")
    for s in ("top", "right"):
        ax.spines[s].set_visible(False)
    ax.text(0.0, 1.02,
            "estimativas — Visa (pico) = capacidade anunciada; L2/rollups mudam o quadro",
            transform=ax.transAxes, fontsize=10.5, color=COL["gray"], va="bottom")
    fig.savefig(OUT / "fig_tps.png"); plt.close(fig)


if __name__ == "__main__":
    for fn in (diagram_double_spend, diagram_central_ledger,
               diagram_distributed_ledger, diagram_signature, diagram_hash,
               diagram_hashchain, diagram_mining, diagram_generals,
               diagram_byzantine_3f1, diagram_sybil_pow, diagram_longest_chain,
               diagram_bridge, fig_timeline, fig_merkle, fig_header,
               fig_pow_target, fig_difficulty, fig_security,
               fig_energy, fig_tps):
        fn()
    print("wrote:", *sorted(p.name for p in OUT.glob("*.png")))

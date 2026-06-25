"""Figuras da Aula 2 (da moeda ao computador-mundo: smart contracts).

Matplotlib, paleta fixa por PLAN.md (objeto -> cor, herdada da Aula 1),
fontes >=13 pt, fundo branco, 300 dpi. Diagramas conceituais com _box/_arrow;
a prosa explicativa vai na legenda editavel do slide (build_pptx). Setas em
ASCII (`->`): Helvetica nao tem o glifo de seta unicode.

Run: venv/bin/python slides/blockchain-aula2/assets_gen.py
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
    "chain":  "#1f77b4",   # ethereum / estado / computador-mundo / cadeia
    "code":   "#2ca02c",   # contrato / codigo / "se cumpre sozinho"
    "risk":   "#d62728",   # atacante / bug / reentrancia / risco
    "energy": "#ff7f0e",   # gas / custo
    "gray":   "#6b7280",   # estrutura neutra / banco de dados comum
}
INK = "#1f2937"
MONO = {"family": "monospace"}
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


def _box(ax, xy, w, h, text, fc, ec, fs=15, tc=INK, bold=True, mono=False):
    x, y = xy
    ax.add_patch(FancyBboxPatch(
        (x, y), w, h, boxstyle="round,pad=0.02,rounding_size=0.08",
        linewidth=2, edgecolor=ec, facecolor=fc, zorder=2))
    if text:
        ax.text(x + w / 2, y + h / 2, text, ha="center", va="center",
                fontsize=fs, color=tc, fontweight="bold" if bold else "normal",
                zorder=3, **(MONO if mono else {}))


def _arrow(ax, p0, p1, color=INK, text=None, fs=13, lw=2.4, style="-|>",
           dashed=False):
    ax.add_patch(FancyArrowPatch(
        p0, p1, arrowstyle=style, mutation_scale=20, linewidth=lw, color=color,
        zorder=1, linestyle="--" if dashed else "-"))
    if text:
        mx, my = (p0[0] + p1[0]) / 2, (p0[1] + p1[1]) / 2
        ax.text(mx, my + 0.18, text, ha="center", va="bottom",
                fontsize=fs, color=color, style="italic", zorder=3)


def _note(ax, x, y, text, color, fs=12.5, bold=False, italic=True):
    ax.text(x, y, text, ha="center", va="center", fontsize=fs, color=color,
            fontweight="bold" if bold else "normal",
            style="italic" if italic else "normal")


# ============================================================ recap (a virada)
def diagram_recap():
    fig, ax = _ax(w=12, h=5.2, xlim=13, ylim=6)
    g, b, code = COL["gray"], COL["chain"], COL["code"]
    # esquerda: as pecas da Aula 1 colapsam num livro replicado
    pieces = ["hash + assinatura", "cadeia de blocos",
              "prova de trabalho", "cadeia mais longa"]
    y = 5.0
    for p in pieces:
        _box(ax, (0.4, y - 0.5), 3.2, 0.62, p, _tint(g, 0.9), g, fs=12, bold=False)
        y -= 0.82
    _arrow(ax, (2.0, 1.65), (2.0, 1.2), color=g, lw=2.0)
    _box(ax, (0.2, 0.25), 3.6, 0.9, "um livro replicado,\nsem dono, a prova de fraude",
         _tint(b, 0.8), b, fs=12)
    # seta central
    _arrow(ax, (4.1, 3.0), (6.2, 3.0), color=INK, lw=2.8, text="e se...")
    # direita: e se cada entrada rodasse codigo?
    _box(ax, (6.6, 1.8), 6.0, 2.4, "", _tint(code, 0.88), code)
    ax.text(9.6, 3.65, "e se cada entrada", ha="center", fontsize=16,
            color=INK, fontweight="bold")
    ax.text(9.6, 3.1, "pudesse RODAR", ha="center", fontsize=18,
            color=code, fontweight="bold")
    ax.text(9.6, 2.55, "{ codigo }", ha="center", fontsize=20, color=code,
            fontweight="bold", **MONO)
    _note(ax, 9.6, 0.95, "Aula 2: contratos inteligentes", INK, fs=15,
          bold=True, italic=False)
    fig.savefig(OUT / "diagram_recap.png"); plt.close(fig)


# ====================================================== conta = estado / tx
def diagram_state_machine():
    fig, ax = _ax(w=12, h=5.0, xlim=12, ylim=5.4)
    b, e = COL["chain"], COL["energy"]

    def ledger(x0, w, head, sub, rows):
        _box(ax, (x0, 1.45), w, 2.7, "", _tint(b, 0.92), b)
        ax.text(x0 + w / 2, 3.78, head, ha="center", fontsize=15, color=b, fontweight="bold")
        ax.text(x0 + w / 2, 3.38, sub, ha="center", fontsize=10, color=COL["gray"], style="italic")
        y = 2.78
        for nome, val, hi in rows:
            ax.text(x0 + 0.28, y, nome, ha="left", va="center", fontsize=12.5,
                    color=INK, **MONO)
            ax.text(x0 + w - 0.28, y, val, ha="right", va="center", fontsize=12.5,
                    color=b if hi else INK, fontweight="bold" if hi else "normal", **MONO)
            y -= 0.62

    # estado S (antes) -> a transacao -> estado S' (depois)
    ledger(0.4, 3.2, "estado S", "saldos de todo mundo",
           [("Alice", "10 ETH", False), ("Bob", "2 ETH", False)])
    ledger(8.4, 3.2, "estado S'", "so Alice e Bob mudaram",
           [("Alice", "7 ETH - gas", True), ("Bob", "5 ETH", True)])

    # a transacao: um objeto concreto (de / para / valor / taxa) - o que voce ve no Etherscan
    _box(ax, (4.4, 1.25), 3.2, 3.0, "", "white", INK)
    ax.text(6.0, 3.9, "transacao", ha="center", fontsize=14, color=INK, fontweight="bold")
    fields = [("de:", "Alice", INK), ("para:", "Bob", INK),
              ("valor:", "3 ETH", INK), ("taxa:", "gas", e)]
    y = 3.25
    for k, v, c in fields:
        ax.text(4.75, y, k, ha="left", va="center", fontsize=12.5, color=COL["gray"], **MONO)
        ax.text(7.25, y, v, ha="right", va="center", fontsize=12.5, color=c,
                fontweight="bold", **MONO)
        y -= 0.55

    _arrow(ax, (3.6, 2.75), (4.4, 2.75), color=b, lw=2.4)
    _arrow(ax, (7.6, 2.75), (8.4, 2.75), color=b, lw=2.4)
    fig.savefig(OUT / "diagram_state_machine.png"); plt.close(fig)


# ===================================================== computador-mundo
def diagram_world_computer():
    fig, ax = _ax(w=11.5, h=5.2, xlim=12, ylim=6)
    b, code, gr = COL["chain"], COL["code"], COL["gray"]

    # 1) a MESMA transacao chega a todos os nos
    _box(ax, (0.3, 2.25), 2.35, 1.5, "", "white", INK)
    ax.text(1.47, 3.42, "transacao", ha="center", fontsize=12.5, color=INK, fontweight="bold")
    ax.text(1.47, 2.92, "increment()", ha="center", fontsize=12.5, color=code, fontweight="bold", **MONO)
    ax.text(1.47, 2.5, "a mesma p/ todos", ha="center", fontsize=9.5, color=gr, style="italic")

    # 2) cada no roda o MESMO codigo e chega ao MESMO resultado (execucao deterministica)
    nx, nw, nh = 3.6, 2.9, 1.0
    ys = [4.55, 3.0, 1.45]
    for i, y in enumerate(ys, 1):
        _box(ax, (nx, y - nh / 2), nw, nh, "", _tint(gr, 0.93), gr)
        ax.text(nx + 0.3, y + 0.22, f"no {i}", ha="left", va="center",
                fontsize=11.5, color=gr, fontweight="bold")
        ax.text(nx + 0.3, y - 0.23, "-> count: 42", ha="left", va="center",
                fontsize=12.5, color=code, fontweight="bold", **MONO)
        _arrow(ax, (2.65, 3.0), (nx, y), color=_tint(gr, 0.25), lw=1.4)

    # 3) como todos concordam, a rede age como UMA maquina: o computador-mundo
    rx = 8.0
    _box(ax, (rx, 1.9), 3.7, 2.2, "", _tint(b, 0.85), b)
    ax.text(rx + 1.85, 3.6, "computador-mundo", ha="center", fontsize=14.5,
            color=b, fontweight="bold")
    ax.text(rx + 1.85, 2.92, "count: 42", ha="center", fontsize=16, color=INK,
            fontweight="bold", **MONO)
    ax.text(rx + 1.85, 2.32, "um resultado, no mundo todo", ha="center",
            fontsize=11, color=gr, style="italic")
    for y in ys:
        _arrow(ax, (nx + nw, y), (rx, 3.0), color=_tint(b, 0.4), lw=1.5)

    fig.savefig(OUT / "diagram_world_computer.png"); plt.close(fig)


# ================================================= contrato = vending (Szabo)
def diagram_vending():
    fig, ax = _ax(w=12, h=5.6, xlim=12, ylim=5.6)
    g, code, e, b = COL["gray"], COL["code"], COL["energy"], COL["chain"]

    # quem chama: manda uma tx chamando comprar() e paga junto
    _box(ax, (0.25, 2.25), 2.3, 1.3, "", _tint(g, 0.93), g)
    ax.text(1.4, 3.22, "comprador", ha="center", fontsize=12, color=g, fontweight="bold")
    ax.text(1.4, 2.8, "comprar()", ha="center", fontsize=11.5, color=INK, **MONO)
    ax.text(1.4, 2.42, "+ 2 ETH", ha="center", fontsize=12, color=e, fontweight="bold", **MONO)

    # o contrato: codigo Solidity de verdade, alinhado a esquerda como num editor
    cx0, cw = 3.0, 6.0
    _box(ax, (cx0, 0.8), cw, 4.3, "", "white", code)
    tx = cx0 + 0.25
    lines = [  # (texto, cor, bold)
        ("contract MaquinaDeVenda {",             code, True),
        ("  uint public preco = 2 ether;",        INK,  False),
        ("  function comprar() public payable {", INK,  False),
        ("    require(msg.value >= preco);",       b,    True),
        ("    entregar(msg.sender);",              INK,  False),
        ("  }",                                    INK,  False),
        ("}",                                      INK,  False),
    ]
    y = 4.55
    for txt, c, bold in lines:
        ax.text(tx, y, txt, ha="left", va="center", fontsize=11.5, color=c,
                fontweight="bold" if bold else "normal", **MONO)
        y -= 0.55

    # o contrato entrega sozinho
    _box(ax, (9.35, 2.25), 2.4, 1.3, "", _tint(code, 0.78), code)
    ax.text(10.55, 3.18, "produto", ha="center", fontsize=14, color=code, fontweight="bold")
    ax.text(10.55, 2.68, "entregue", ha="center", fontsize=12, color=INK)

    _arrow(ax, (2.55, 2.9), (3.0, 2.9), color=e, lw=2.4)
    _arrow(ax, (9.0, 2.9), (9.35, 2.9), color=code, lw=2.4)
    fig.savefig(OUT / "diagram_vending.png"); plt.close(fig)


# ========================================================== o problema do oraculo
def diagram_oracle():
    fig, ax = _ax(w=12, h=5.8, xlim=12, ylim=5.8)
    g, code, r, e = COL["gray"], COL["code"], COL["risk"], COL["energy"]

    # o contrato tenta sair da rede e nao consegue (determinismo) - codigo de verdade
    cx0, cw = 0.4, 6.4
    _box(ax, (cx0, 2.7), cw, 2.9, "", "white", code)
    tx = cx0 + 0.25
    lines = [  # (texto, cor, bold, italic)
        ("contract Aposta {",                     code, True,  False),
        ("  function preco() public view {",      INK,  False, False),
        ('    return api.get("usd/brl");',        r,    True,  False),
        ("    // cada no veria um valor diferente", g,   False, True),
        ("  }",                                    INK,  False, False),
        ("}",                                      INK,  False, False),
    ]
    y = 5.15
    for txt, c, bold, ital in lines:
        ax.text(tx, y, txt, ha="left", va="center", fontsize=11, color=c,
                fontweight="bold" if bold else "normal",
                style="italic" if ital else "normal", **MONO)
        y -= 0.48

    # o mundo la fora: dados que o contrato nao alcanca
    ax.text(9.5, 5.35, "o mundo la fora", ha="center", fontsize=12.5,
            color=g, fontweight="bold")
    for o, yc in zip(["preco do dolar", "placar do jogo", "clima de hoje"],
                     [4.5, 3.7, 2.9]):
        _box(ax, (8.0, yc - 0.31), 3.4, 0.62, o, _tint(g, 0.92), g, fs=12, bold=False)

    # a chamada direta e bloqueada
    _arrow(ax, (6.85, 4.15), (7.95, 4.15), color=r, lw=1.8, dashed=True)
    ax.text(7.4, 4.15, "X", ha="center", va="center", fontsize=22, color=r, fontweight="bold")
    ax.text(7.4, 3.62, "nao pode chamar", ha="center", fontsize=10, color=r)

    # o unico jeito: um oraculo grava o dado on-chain -> mas voce passa a confiar nele
    _box(ax, (2.6, 0.55), 5.2, 1.35, "", _tint(e, 0.85), e)
    ax.text(5.2, 1.55, "ORACULO", ha="center", fontsize=14, color=e, fontweight="bold")
    ax.text(5.2, 1.12, "le a API la fora e grava o valor on-chain", ha="center",
            fontsize=11, color=INK)
    ax.text(5.2, 0.76, "(voce passa a confiar nele)", ha="center", fontsize=11,
            color=r, style="italic")
    _arrow(ax, (4.0, 1.9), (3.6, 2.7), color=e, lw=2.4)
    ax.text(4.35, 2.32, "empurra pra dentro", ha="left", fontsize=10, color=g, style="italic")
    fig.savefig(OUT / "diagram_oracle.png"); plt.close(fig)


# ================================================================== gas
def fig_gas():
    fig, ax = _ax(w=12, h=5.6, xlim=12, ylim=5.6)
    g, code, r, e = COL["gray"], COL["code"], COL["risk"], COL["energy"]

    # enquadramento (o slide pede mais explicacao, entao a moldura fica)
    ax.text(6.0, 5.28,
            "voce poe um teto de gas; cada operacao gasta um pouco - ate terminar ou bater no teto",
            ha="center", fontsize=11.5, color=g)

    x0, x1 = 2.3, 8.5                 # trilho: do inicio ate o teto
    bw, h = x1 - x0, 0.72
    yb1, yb2 = 3.45, 1.7             # base das duas barras
    cy1, cy2 = yb1 + h / 2, yb2 + h / 2

    def track(yb):
        ax.add_patch(Rectangle((x0, yb), bw, h, facecolor=_tint(g, 0.93),
                               edgecolor=g, lw=1.3, zorder=1))

    def fill(yb, frac):
        ax.add_patch(Rectangle((x0, yb), bw * frac, h, facecolor=_tint(e, 0.45),
                               edgecolor=e, lw=1.3, zorder=2))

    # selos de status a esquerda
    _box(ax, (0.3, cy1 - 0.42), 1.75, 0.84, "TUDO BEM", _tint(code, 0.85), code, fs=12, tc=code)
    _box(ax, (0.3, cy2 - 0.42), 1.75, 0.84, "TRAVA", _tint(r, 0.9), r, fs=12.5, tc=r)

    # barra 1: termina antes do teto -> paga so o usado, devolve o resto
    track(yb1); fill(yb1, 0.37)
    xfim = x0 + bw * 0.37
    ax.plot([xfim, xfim], [yb1 - 0.07, yb1 + h + 0.07], color=code, lw=2.6, zorder=4)
    ax.text(xfim, yb1 + h + 0.2, "fim", ha="center", fontsize=11, color=code, fontweight="bold")
    ax.text(x0 + bw * 0.185, cy1, "gas usado", ha="center", va="center", fontsize=10.5, color=INK, zorder=5)
    ax.text((xfim + x1) / 2, cy1, "nao usado -> devolvido", ha="center", va="center",
            fontsize=10.5, color=g, style="italic", zorder=5)
    ax.text(x1 + 0.25, cy1, "termina e paga so\no que usou", ha="left", va="center",
            fontsize=11, color=code, fontweight="bold")

    # barra 2: nunca termina -> bate no teto, REVERTE, mas paga o que queimou
    track(yb2); fill(yb2, 1.0)
    ax.text(x0 + bw / 2, cy2, "gasta ate o teto e nao termina", ha="center", va="center",
            fontsize=10.5, color=INK, zorder=5)
    ax.text(x1, cy2, "X", ha="center", va="center", fontsize=22, color=r, fontweight="bold", zorder=6)
    ax.text(x1 + 0.25, cy2, "REVERTE (estado nao muda)\nmas paga o gas queimado",
            ha="left", va="center", fontsize=11, color=r, fontweight="bold")

    # o teto compartilhado
    ax.plot([x1, x1], [yb2 - 0.12, yb1 + h + 0.12], color=INK, lw=2.2, ls="--", zorder=3)
    ax.text(x1, yb1 + h + 0.58, "LIMITE", ha="center", fontsize=12.5, color=INK, fontweight="bold")

    # quanto se paga, nos dois casos
    ax.text(6.0, 0.92, "taxa paga  =  gas usado  x  preco do gas",
            ha="center", fontsize=14, color=e, fontweight="bold")
    ax.text(6.0, 0.42, "voce escolhe o preco: pagar mais confirma mais rapido (e um leilao)",
            ha="center", fontsize=10.5, color=g)
    fig.savefig(OUT / "fig_gas.png"); plt.close(fig)


# ============================================================ counter (backup)
def diagram_counter():
    fig, ax = _ax(w=11, h=5.0, xlim=12, ylim=5.4)
    g, code, r, e, b = COL["gray"], COL["code"], COL["risk"], COL["energy"], COL["chain"]
    # contador no centro
    _box(ax, (4.7, 3.4), 2.6, 1.2, "count = 3", _tint(code, 0.8), code, fs=18)
    # increment: transacao (laranja), gasta gas
    _box(ax, (0.5, 3.55), 2.6, 0.9, "increment()", _tint(e, 0.8), e, fs=14, mono=True)
    _arrow(ax, (3.1, 4.0), (4.7, 4.0), color=e, lw=2.4, text="tx · gas")
    # count: leitura (azul), gratis
    _box(ax, (8.9, 3.55), 2.6, 0.9, "count()", _tint(b, 0.85), b, fs=14, mono=True)
    _arrow(ax, (7.3, 4.0), (8.9, 4.0), color=b, lw=2.2, text="call · gratis")
    # decrement em 0 -> revert
    _box(ax, (2.0, 1.4), 3.2, 0.95, "decrement() em 0", _tint(r, 0.9), r, fs=13, mono=True)
    _box(ax, (6.8, 1.4), 3.2, 0.95, 'revert "ja em zero"', _tint(r, 0.7), r, fs=13)
    _arrow(ax, (5.2, 1.87), (6.8, 1.87), color=r, lw=2.2)
    _note(ax, 6.0, 0.55,
          "escrita = transacao (laranja, vira bloco, gasta gas)  ·  leitura = call (azul, gratis)  ·  require = trava",
          g, fs=11.5)
    fig.savefig(OUT / "diagram_counter.png"); plt.close(fig)


# ============================================================= escrow (backup)
def diagram_escrow():
    fig, ax = _ax(w=12, h=5.2, xlim=12, ylim=5.6)
    g, code, b = COL["gray"], COL["code"], COL["chain"]
    # contrato no centro guardando 1 ETH
    _box(ax, (4.5, 2.0), 3.0, 1.6, "", _tint(code, 0.88), code)
    ax.text(6.0, 3.15, "CONTRATO", ha="center", fontsize=13, color=code, fontweight="bold")
    ax.text(6.0, 2.55, "guarda 1 ETH", ha="center", fontsize=14, color=INK, fontweight="bold")
    # atores
    _box(ax, (0.5, 2.3), 2.4, 1.0, "comprador", _tint(g, 0.9), g, fs=13)
    _box(ax, (9.1, 2.3), 2.4, 1.0, "vendedor", _tint(g, 0.9), g, fs=13)
    _box(ax, (4.7, 4.4), 2.6, 0.9, "arbitro", _tint(b, 0.8), b, fs=13)
    # deposit comprador -> contrato
    _arrow(ax, (2.9, 2.95), (4.5, 2.9), color=g, lw=2.2, text="deposit 1 ETH")
    # release contrato -> vendedor (so o arbitro autoriza)
    _arrow(ax, (7.5, 2.9), (9.1, 2.95), color=code, lw=2.4, text="release")
    _arrow(ax, (6.0, 4.4), (6.0, 3.6), color=b, lw=2.0)
    ax.text(7.15, 3.95, "so o arbitro", ha="left", fontsize=11.5, color=b, fontweight="bold")
    # refund (opcional) de volta ao comprador
    _arrow(ax, (4.5, 2.3), (2.9, 2.45), color=g, lw=1.6, dashed=True, text="refund")
    _note(ax, 6.0, 0.7,
          "nem comprador nem vendedor mexem no dinheiro - so o arbitro decide (controle de acesso = require)",
          g, fs=12)
    fig.savefig(OUT / "diagram_escrow.png"); plt.close(fig)


# =========================================================== reentrancia
def diagram_reentrancy():
    fig, ax = _ax(w=12, h=5.2, xlim=12, ylim=5.6)
    g, r, code = COL["gray"], COL["risk"], COL["code"]
    # VulnerableBank.withdraw com a ordem perigosa
    _box(ax, (0.5, 1.2), 4.6, 3.6, "", "white", g)
    ax.text(2.8, 4.45, "VulnerableBank.withdraw()", ha="center", fontsize=13,
            color=INK, fontweight="bold", **MONO)
    ax.text(0.8, 3.7, "1.  envia o ETH ao chamador", ha="left", fontsize=13, color=r, fontweight="bold")
    ax.text(0.8, 2.95, "    <-- aqui o atacante reentra", ha="left", fontsize=11.5, color=r, style="italic")
    ax.text(0.8, 2.1, "2.  zera o saldo", ha="left", fontsize=13, color=g)
    ax.text(0.8, 1.6, "    (tarde demais)", ha="left", fontsize=11.5, color=g, style="italic")
    # Attacker.receive() que rechama withdraw
    _box(ax, (7.0, 2.4), 4.4, 2.2, "", _tint(r, 0.92), r)
    ax.text(9.2, 4.25, "Attacker.receive()", ha="center", fontsize=13,
            color=r, fontweight="bold", **MONO)
    ax.text(9.2, 3.55, "ao receber o ETH,", ha="center", fontsize=12, color=INK)
    ax.text(9.2, 3.1, "chama withdraw() de NOVO", ha="center", fontsize=12.5,
            color=r, fontweight="bold", **MONO)
    ax.text(9.2, 2.65, "...e de novo, e de novo", ha="center", fontsize=11.5,
            color=r, style="italic")
    # laco de reentrada
    _arrow(ax, (5.1, 3.7), (7.0, 3.7), color=r, lw=2.4, text="envia")
    _arrow(ax, (7.0, 2.9), (5.1, 2.9), color=r, lw=2.6, text="reentra antes do passo 2")
    _note(ax, 6.0, 0.6,
          "o saldo so zera no passo 2 - mas o saque do passo 1 ja rodou de novo: 1 ETH vira 6",
          g, fs=12.5)
    fig.savefig(OUT / "diagram_reentrancy.png"); plt.close(fig)


# ===================================================== correcao (checks-effects)
def diagram_checks_effects():
    fig, ax = _ax(w=12, h=5.0, xlim=12, ylim=5.4)
    g, r, code = COL["gray"], COL["risk"], COL["code"]
    # ERRADO (vermelho)
    _box(ax, (0.5, 1.0), 5.0, 3.6, "", _tint(r, 0.96), r)
    ax.text(3.0, 4.25, "VULNERAVEL", ha="center", fontsize=14, color=r, fontweight="bold")
    ax.text(0.85, 3.45, "function withdraw() {", ha="left", fontsize=12.5, color=INK, **MONO)
    ax.text(1.15, 2.85, "enviar(saldo);", ha="left", fontsize=12.5, color=r, fontweight="bold", **MONO)
    ax.text(1.15, 2.3, "saldo = 0;", ha="left", fontsize=12.5, color=g, **MONO)
    ax.text(0.85, 1.7, "}", ha="left", fontsize=12.5, color=INK, **MONO)
    ax.text(3.0, 1.25, "envia ANTES de zerar", ha="center", fontsize=11.5, color=r, style="italic")
    # CERTO (verde)
    _box(ax, (6.5, 1.0), 5.0, 3.6, "", _tint(code, 0.94), code)
    ax.text(9.0, 4.25, "SEGURO", ha="center", fontsize=14, color=code, fontweight="bold")
    ax.text(6.85, 3.45, "function withdraw() {", ha="left", fontsize=12.5, color=INK, **MONO)
    ax.text(7.15, 2.85, "saldo = 0;", ha="left", fontsize=12.5, color=code, fontweight="bold", **MONO)
    ax.text(7.15, 2.3, "enviar(valor);", ha="left", fontsize=12.5, color=g, **MONO)
    ax.text(6.85, 1.7, "}", ha="left", fontsize=12.5, color=INK, **MONO)
    ax.text(9.0, 1.25, "zera ANTES de enviar", ha="center", fontsize=11.5, color=code, style="italic")
    _note(ax, 6.0, 0.5,
          "checks-effects-interactions: mude o estado antes de chamar pra fora - a unica diferenca e a ordem",
          g, fs=12.5)
    fig.savefig(OUT / "diagram_checks_effects.png"); plt.close(fig)


# ================================================================ fork ETH/ETC
def diagram_fork():
    fig, ax = _ax(w=12, h=5.0, xlim=12, ylim=5.4)
    g, b, r, code = COL["gray"], COL["chain"], COL["risk"], COL["code"]

    def blk(x, y, c, w=1.05, h=0.85):
        _box(ax, (x, y), w, h, "", _tint(c, 0.85), c)

    # tronco comum (3 blocos azuis)
    for i in range(3):
        x = 0.5 + i * 1.4; blk(x, 2.55, b)
        if i:
            _arrow(ax, (x - 0.35, 2.97), (x, 2.97), color=b, lw=1.7)
    # bloco do hack
    hx = 0.5 + 3 * 1.4
    blk(hx, 2.55, r)
    _arrow(ax, (hx - 0.35, 2.97), (hx, 2.97), color=b, lw=1.7)
    ax.text(hx + 0.52, 2.3, "The DAO", ha="center", fontsize=11, color=r,
            fontweight="bold", va="top")
    ax.text(hx + 0.52, 2.0, "hack", ha="center", fontsize=10.5, color=r, va="top")
    # ramo de cima: ETH (desfez) — um bloco, rotulo claro a direita
    bx = hx + 1.55
    blk(bx, 3.85, code)
    _arrow(ax, (hx + 1.05, 3.1), (bx, 4.1), color=code, lw=2.0)
    ax.text(bx + 1.3, 4.28, "Ethereum (ETH)", ha="left", va="center",
            fontsize=13, color=code, fontweight="bold")
    ax.text(bx + 1.3, 3.88, "desfez o roubo", ha="left", va="center",
            fontsize=12, color=INK)
    # ramo de baixo: ETC (manteve) — um bloco, rotulo claro a direita
    blk(bx, 1.2, g)
    _arrow(ax, (hx + 1.05, 2.85), (bx, 1.85), color=g, lw=2.0)
    ax.text(bx + 1.3, 1.63, "Ethereum Classic (ETC)", ha="left", va="center",
            fontsize=13, color=g, fontweight="bold")
    ax.text(bx + 1.3, 1.23, "manteve: 'codigo e lei'", ha="left", va="center",
            fontsize=12, color=g)
    _note(ax, 6.0, 0.45,
          "$60M / 3,6M ETH · a cadeia e imutavel: o roubo ficou gravado, so um fork o desfez",
          INK, fs=12.5)
    fig.savefig(OUT / "diagram_fork.png"); plt.close(fig)


# ========================================================== etherscan (backup)
def diagram_etherscan():
    fig, ax = _ax(w=11, h=5.0, xlim=12, ylim=5.4)
    g, b, code, e = COL["gray"], COL["chain"], COL["code"], COL["energy"]
    _box(ax, (1.0, 0.7), 10.0, 4.2, "", "white", g)
    ax.text(6.0, 4.45, "Contrato USDC  ·  etherscan.io", ha="center",
            fontsize=14, color=INK, fontweight="bold")
    rows = [
        ("codigo verificado (cadeado 'Exact Match')", code),
        ("Read Contract: le o estado sem carteira", b),
        ("evento Transfer(from, to, amount) gravado no bloco", b),
        ("gas pago, taxa, bloco, timestamp - tudo publico", e),
    ]
    y = 3.7
    for txt, c in rows:
        ax.add_patch(Circle((1.7, y), 0.13, facecolor=c, edgecolor=c, zorder=4))
        ax.text(2.1, y, txt, ha="left", va="center", fontsize=13, color=INK)
        y -= 0.78
    _note(ax, 6.0, 0.3, "o escrow da aula, mas movendo bilhoes - e permanente",
          g, fs=12)
    fig.savefig(OUT / "diagram_etherscan.png"); plt.close(fig)


# =============================================================== erc-20 pegadinha
def diagram_erc20():
    fig, ax = _ax(w=11, h=5.0, xlim=12, ylim=5.4)
    g, b, code = COL["gray"], COL["chain"], COL["code"]
    # transacao externa: Value 0 ETH
    _box(ax, (0.6, 1.0), 4.4, 3.6, "", "white", g)
    ax.text(2.8, 4.3, "a transacao", ha="center", fontsize=13, color=INK, fontweight="bold")
    ax.text(0.95, 3.6, "To:  contrato USDC", ha="left", fontsize=12.5, color=g, **MONO)
    ax.text(0.95, 3.0, "Value:  0 ETH", ha="left", fontsize=13.5, color="#b00", fontweight="bold", **MONO)
    ax.text(0.95, 2.5, "nada nativo se moveu", ha="left", fontsize=11, color=g, style="italic")
    ax.text(0.95, 1.7, "...mas DENTRO da chamada:", ha="left", fontsize=11.5, color=INK)
    # dentro: transfer move tokens
    _arrow(ax, (5.0, 2.8), (6.4, 2.8), color=b, lw=2.6, text="transfer()")
    _box(ax, (6.6, 1.6), 4.8, 2.4, "", _tint(b, 0.9), b)
    ax.text(9.0, 3.55, "transfer(Bob, 7.151 USDC)", ha="center", fontsize=13,
            color=b, fontweight="bold", **MONO)
    ax.text(9.0, 2.9, "Alice  ->  Bob", ha="center", fontsize=15, color=INK, fontweight="bold")
    ax.text(9.0, 2.25, "evento Transfer no Log", ha="center", fontsize=12, color=code, fontweight="bold")
    _note(ax, 6.0, 0.55,
          "o dinheiro andou DENTRO de uma chamada de funcao; o evento Transfer no Log e a fonte de tudo",
          g, fs=12)
    fig.savefig(OUT / "diagram_erc20.png"); plt.close(fig)


# ====================================================== arvore de decisao (W-G)
def fig_decision_tree():
    fig, ax = _ax(w=12.5, h=6.6, xlim=13, ylim=11)
    g, b, code, r = COL["gray"], COL["chain"], COL["code"], COL["risk"]
    qx, qw, qh = 3.4, 4.2, 0.78          # coluna das perguntas (esquerda/centro)
    lx, lw_ = 8.6, 4.0                    # coluna das folhas (direita)

    def q(y, text):
        _box(ax, (qx, y - qh / 2), qw, qh, text, _tint(g, 0.9), g, fs=11.5, bold=False)

    def leaf(y, text, c):
        _box(ax, (lx, y - 0.42), lw_, 0.84, text, _tint(c, 0.82), c, fs=12)

    def down(y0, y1):
        _arrow(ax, (qx + qw / 2, y0), (qx + qw / 2, y1), color=g, lw=1.8, text=None)
        ax.text(qx + qw / 2 + 0.18, (y0 + y1) / 2, "sim", ha="left",
                va="center", fontsize=10.5, color=g, style="italic")

    def side(y, c, label="nao"):
        _arrow(ax, (qx + qw, y), (lx, y), color=c, lw=1.8)
        ax.text((qx + qw + lx) / 2, y + 0.16, label, ha="center", va="bottom",
                fontsize=10.5, color=c, style="italic")

    ys = [10.2, 8.7, 7.2, 5.7, 4.2, 2.7]
    qs = ["Precisa guardar estado?",
          "Ha multiplos escritores?",
          "Da pra usar um terceiro\nconfiavel sempre online (TTP)?",
          "Todos os escritores\nsao conhecidos?",
          "Voce confia em\ntodos os escritores?",
          "Precisa de\nverificabilidade publica?"]
    for y, t in zip(ys, qs):
        q(y, t)
    for i in range(len(ys) - 1):
        down(ys[i] - qh / 2, ys[i + 1] + qh / 2)
    # folhas "nao use blockchain" (cinza)
    side(ys[0], g, "nao"); leaf(ys[0], "nao use blockchain", g)
    side(ys[1], g, "nao"); leaf(ys[1], "nao use blockchain", g)
    side(ys[2], g, "sim"); leaf(ys[2], "use o TTP / banco central", g)
    # escritores conhecidos? nao -> publica sem permissao
    side(ys[3], b, "nao"); leaf(ys[3], "blockchain PUBLICA\n(sem permissao)", b)
    # confia em todos? sim -> nao precisa
    side(ys[4], g, "sim"); leaf(ys[4], "nao use blockchain", g)
    # verificabilidade publica? sim/nao -> permissionada publica/privada
    side(ys[5], code, "sim"); leaf(ys[5], "permissionada PUBLICA", code)
    _arrow(ax, (qx + qw / 2, ys[5] - qh / 2), (qx + qw / 2, ys[5] - 1.05), color=g, lw=1.8)
    ax.text(qx + qw / 2 + 0.18, ys[5] - 0.85, "nao", ha="left", fontsize=10.5,
            color=g, style="italic")
    _box(ax, (qx, ys[5] - 1.9), qw, 0.84, "permissionada PRIVADA",
         _tint(code, 0.7), code, fs=12)
    ax.text(6.5, 0.35, "arvore de decisao · Wust & Gervais, 2018 (redesenhada)",
            ha="center", fontsize=10.5, color=g, style="italic")
    fig.savefig(OUT / "fig_decision_tree.png"); plt.close(fig)


# ================================================================= 3 casos
def diagram_cases():
    fig, ax = _ax(w=12, h=5.2, xlim=12, ylim=5.6)
    g, b, code = COL["gray"], COL["chain"], COL["code"]
    cases = [
        ("Registro interno de uma\nempresa (um dono so)", "banco de dados comum", g),
        ("Pagar um desconhecido\nsem intermediario", "blockchain publica", b),
        ("Consorcio de partes conhecidas\nque nao confiam 100%", "permissionada (ou nem isso)", code),
    ]
    y = 4.7
    for caso, vered, c in cases:
        _box(ax, (0.5, y - 0.55), 5.0, 1.1, caso, _tint(g, 0.92), g, fs=12.5, bold=False)
        _arrow(ax, (5.7, y), (7.2, y), color=c, lw=2.4)
        _box(ax, (7.3, y - 0.5), 4.2, 1.0, vered, _tint(c, 0.78), c, fs=13)
        y -= 1.5
    _note(ax, 6.0, 0.35,
          "a mesma arvore: so o caso do meio (sem dono, sem confianca) precisa de blockchain",
          INK, fs=13, bold=True, italic=False)
    fig.savefig(OUT / "diagram_cases.png"); plt.close(fig)


# =============================================================== sintese (final)
def fig_synthesis():
    fig, ax = _ax(w=12, h=5.6, xlim=12, ylim=6)
    g, b, code = COL["gray"], COL["chain"], COL["code"]
    # a pergunta no centro, dois caminhos
    _box(ax, (3.6, 4.4), 4.8, 1.1, "as partes confiam entre si\nou num terceiro?",
         _tint(g, 0.9), g, fs=14, bold=True)
    # NAO -> blockchain
    _box(ax, (0.5, 1.9), 4.6, 1.7, "", _tint(b, 0.85), b)
    ax.text(2.8, 3.1, "NAO", ha="center", fontsize=16, color=b, fontweight="bold")
    ax.text(2.8, 2.55, "blockchain", ha="center", fontsize=15, color=INK, fontweight="bold")
    ax.text(2.8, 2.1, "o consenso caro vale a pena", ha="center", fontsize=11.5, color=g, style="italic")
    _arrow(ax, (4.6, 4.4), (2.8, 3.6), color=b, lw=2.4)
    # SIM -> banco de dados
    _box(ax, (6.9, 1.9), 4.6, 1.7, "", _tint(code, 0.85), code)
    ax.text(9.2, 3.1, "SIM", ha="center", fontsize=16, color=code, fontweight="bold")
    ax.text(9.2, 2.55, "banco de dados comum", ha="center", fontsize=14, color=INK, fontweight="bold")
    ax.text(9.2, 2.1, "mais simples, rapido e barato", ha="center", fontsize=11.5, color=g, style="italic")
    _arrow(ax, (7.4, 4.4), (9.2, 3.6), color=code, lw=2.4)
    # a tese
    _note(ax, 6.0, 1.05,
          "Blockchain resolve UM problema: concordar sem confiar, sem dono.",
          INK, fs=15, bold=True, italic=False)
    _note(ax, 6.0, 0.5,
          "toda a maquinaria (hash, mineracao, gas) existe a servico disso.",
          g, fs=12.5)
    fig.savefig(OUT / "fig_synthesis.png"); plt.close(fig)


if __name__ == "__main__":
    for fn in (diagram_recap, diagram_state_machine, diagram_world_computer,
               diagram_vending, diagram_oracle, fig_gas, diagram_counter,
               diagram_escrow, diagram_reentrancy, diagram_checks_effects,
               diagram_fork, diagram_etherscan, diagram_erc20,
               fig_decision_tree, diagram_cases, fig_synthesis):
        fn()
    print("wrote:", *sorted(p.name for p in OUT.glob("*.png")))

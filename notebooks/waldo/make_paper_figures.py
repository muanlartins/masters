"""Generate the ENIAC-Waldo paper figures as vector PDFs.

Reproduces the relevant setup from 03_machine_unlearning.ipynb and writes:
  figures/trade_surface.pdf     -- Fig 1: deletion cost vs retained accuracy (S1)
  figures/forgetting_inside.pdf -- Fig 2: Odlaw memory before/after untrain vs gradient-ascent ghost

Run from notebooks/waldo:  python make_paper_figures.py
S1 metrics are the recorded single-threaded run from the notebook (cell 6).
"""
import os, json, sys
import numpy as np
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import characters as C, bench
import wisardpkg as wp

OUT = os.path.join(os.path.dirname(__file__), '..', '..', 'articles', 'eniac-waldo', 'figures')
os.makedirs(OUT, exist_ok=True)

ORDER = ['background', 'waldo', 'odlaw', 'wenda', 'wizard', 'woof']
IDX = {c: C.CLASS_TO_IDX[c] for c in ORDER}
CLASSES = [IDX[c] for c in ORDER]
NTR, NTE, CANON = 120, 60, 24
plt.rcParams.update({'font.size': 9, 'axes.titlesize': 9, 'figure.dpi': 150})

# ---------------------------------------------------------------- Fig 1
# S1 (right-to-be-forgotten class erasure), single-threaded; from notebook 03 cell 6.
# (cost_s, retained_util, memory_MB, exact, mia)
S1 = {
    'WiSARD':      (0.0403,  0.890, 9.30,   True,  0.50),
    'RF-gold':     (1.283,   0.950, 3.80,   True,  0.50),
    'SISA':        (1.310,   0.873, 6.30,   True,  0.50),
    'DaRE-greedy': (13.872,  0.953, 1585.7, True,  0.50),
    'DaRE-random': (0.177,   0.853, 89.1,   True,  0.50),
    'GradAscent':  (0.0917,  0.773, 0.083,  False, 0.48),  # S1 MIA ~chance; the leak (0.63) is S2
}
# DaRE topd frontier sweep (cost_s, util) from cell 22.
FRONTIER = [(0.165, 0.853), (2.186, 0.923), (4.793, 0.950), (7.970, 0.960), (12.956, 0.953)]
COL = {'WiSARD': '#E45756', 'RF-gold': '#4C78A8', 'SISA': '#72B7B2',
       'DaRE-greedy': '#54A24B', 'DaRE-random': '#2C7A2C', 'GradAscent': '#B279A2'}


def memsize(mb):
    return 40 + 65 * (np.log10(mb) + 1.5)


def fig_trade_surface():
    fig, ax = plt.subplots(figsize=(5.6, 3.5))
    fx, fy = zip(*FRONTIER)
    ax.plot(fx, fy, '-', color=COL['DaRE-greedy'], alpha=0.35, lw=1.2, zorder=1,
            label='DaRE frontier (topd sweep)')
    for name, (cost, util, mem, exact, mia) in S1.items():
        marker = '*' if name == 'WiSARD' else ('^' if not exact else 'o')
        size = (520 if name == 'WiSARD' else memsize(mem))
        ax.scatter(cost, util, s=size, marker=marker, c=COL[name],
                   edgecolors='black', linewidths=0.6, zorder=3,
                   alpha=0.9, label=None)
        dy = 0.012 if name not in ('SISA',) else -0.022
        ha = 'left'
        lbl = f'{name}\n{mem:.0f} MB' if mem >= 1 else f'{name}\n{mem*1000:.0f} KB'
        ax.annotate(lbl, (cost, util), textcoords='offset points',
                    xytext=(8, 6 if dy > 0 else -16), fontsize=7.5, ha=ha)
    ax.scatter([], [], marker='o', c='gray', edgecolors='black', linewidths=0.6, label='exact')
    ax.scatter([], [], marker='^', c=COL['GradAscent'], edgecolors='black', linewidths=0.6,
               label='approximate')
    ax.scatter([], [], marker='*', c=COL['WiSARD'], edgecolors='black', linewidths=0.6, s=120,
               label='WiSARD (ours)')
    ax.set_xscale('log')
    ax.set_xlabel('deletion cost (s, single-threaded, log scale)')
    ax.set_ylabel('retained accuracy')
    ax.set_ylim(0.74, 0.98)
    ax.set_xlim(0.025, 30)
    ax.grid(alpha=0.25, which='both')
    ax.legend(fontsize=7, loc='lower right', framealpha=0.9)
    fig.tight_layout()
    fig.savefig(os.path.join(OUT, 'trade_surface.pdf'), bbox_inches='tight')
    plt.close(fig)
    print('wrote trade_surface.pdf')


# ---------------------------------------------------------------- Fig 2
def build_pools():
    Xcal, _ = C.make_dataset(40, size=48, seed=999, classes=ORDER, **C.PRESETS['clean'])
    WIS = json.load(open(os.path.join(os.path.dirname(__file__), 'cache', 'best_wisard.json')))
    THERM = bench.fit_thermometer(bench.to_canon(Xcal, CANON), WIS['kind'], WIS['size'])

    def bits(Xc):
        return bench.thermometer_encode(bench.to_canon(Xc, CANON), THERM)

    def feats(Xc):
        return bench.raw_float(bench.to_canon(Xc, CANON))

    Xtr, ytr = {}, {}
    for c in ORDER:
        X, y = C.make_dataset(NTR, size=48, seed=100 + C.CLASS_TO_IDX[c],
                              classes=[c], **C.PRESETS['clean'])
        Xtr[c], ytr[c] = X, y
    return WIS, bits, feats, Xtr, ytr


def mk_ds(bits, Xc, y):
    ds = wp.DataSet()
    for b, l in zip(bits(Xc), y):
        ds.add(b.tolist(), str(int(l)))
    return ds


def fig_forgetting_inside():
    WIS, bits, feats, Xtr, ytr = build_pools()

    def mental(m, label):
        mi = np.array(m.getMentalImages()[str(int(IDX[label]))]).reshape(CANON, CANON, 3, WIS['size'])
        return mi.sum(axis=(2, 3))

    m = wp.Wisard(WIS['addr'])
    for c in ORDER:
        m.train(mk_ds(bits, Xtr[c], ytr[c]))
    od_b = mental(m, 'odlaw')
    m.untrain(mk_ds(bits, Xtr['odlaw'], ytr['odlaw']))
    od_a = mental(m, 'odlaw')

    # gradient ascent on a numpy multinomial logistic model (mirrors notebook LR)
    Xtr_all = np.concatenate([Xtr[c] for c in ORDER])
    ytr_all = np.concatenate([ytr[c] for c in ORDER])
    Ftr = feats(Xtr_all)
    mu, sd = Ftr.mean(0), Ftr.std(0) + 1e-6
    keep = ytr_all != IDX['odlaw']

    def softmax(Z):
        Z = Z - Z.max(1, keepdims=True); e = np.exp(Z); return e / e.sum(1, keepdims=True)

    def onehot(y):
        Y = np.zeros((len(y), len(CLASSES)))
        for i, t in enumerate(y):
            Y[i, CLASSES.index(int(t))] = 1
        return Y

    Xn = (Ftr - mu) / sd
    W = np.zeros((Xn.shape[1], len(CLASSES))); b = np.zeros(len(CLASSES))
    Y = onehot(ytr_all)
    for _ in range(400):
        P = softmax(Xn @ W + b)
        W -= 0.5 * (Xn.T @ (P - Y) / len(Y) + 1e-3 * W); b -= 0.5 * (P - Y).mean(0)
    oc = CLASSES.index(IDX['odlaw'])

    def classmap(W):
        return np.abs(W[:, oc]).reshape(CANON, CANON, 3).sum(2)

    lr_b = classmap(W)
    # gradient ASCENT on the forgotten (odlaw) rows, descent on retained
    Xf = (feats(Xtr['odlaw']) - mu) / sd; Yf = onehot(ytr['odlaw'])
    Xr = Xn[keep]; Yr = onehot(ytr_all[keep])
    for _ in range(30):
        Pf = softmax(Xf @ W + b); Pr = softmax(Xr @ W + b)
        W += 0.1 * (Xf.T @ (Pf - Yf) / len(Yf))            # ascend on forget set
        W -= 0.1 * (Xr.T @ (Pr - Yr) / len(Yr) + 1e-3 * W)  # keep retain set
    lr_a = classmap(W)

    fig, ax = plt.subplots(2, 2, figsize=(4.7, 4.9))
    rows = [('WiSARD vote-memory\n(exact untrain)', od_b, od_a, COL['WiSARD']),
            ('gradient ascent |weights|\n(approximate)', lr_b, lr_a, COL['GradAscent'])]
    for r, (name, before, after, c) in enumerate(rows):
        vmax = before.max()
        ax[r, 0].imshow(before, cmap='magma', vmin=0, vmax=vmax)
        ax[r, 1].imshow(after, cmap='magma', vmin=0, vmax=vmax)
        ax[r, 0].set_ylabel(name, fontsize=8.5, color=c)
        for k in (0, 1):
            ax[r, k].set_xticks([]); ax[r, k].set_yticks([])
    ax[0, 0].set_title('before request', fontsize=9)
    ax[0, 1].set_title('after request', fontsize=9)
    keep_frac = lr_a.sum() / lr_b.sum()
    ax[0, 1].text(0.5, -0.10, 'Odlaw evidence: 100% to 0%', transform=ax[0, 1].transAxes,
                  ha='center', fontsize=8, color=COL['WiSARD'])
    ax[1, 1].text(0.5, -0.10, 'ghost remains: %.0f%%' % (100 * keep_frac),
                  transform=ax[1, 1].transAxes, ha='center', fontsize=8, color=COL['GradAscent'])
    fig.tight_layout(rect=[0, 0.02, 1, 1])
    fig.savefig(os.path.join(OUT, 'forgetting_inside.pdf'), bbox_inches='tight')
    plt.close(fig)
    print('wrote forgetting_inside.pdf  (WiSARD Odlaw %d->%d votes, gradient-ascent ghost %.0f%%)'
          % (od_b.sum(), od_a.sum(), 100 * keep_frac))


def fig_classes_difficulty():
    classes = C.CLASSES  # waldo, odlaw, wenda, wizard, woof, background
    presets = ['clean', 'rotation', 'palette', 'occlusion', 'photometric', 'full']
    rng = np.random.default_rng(7)
    fig, ax = plt.subplots(2, 6, figsize=(7.4, 2.9))
    for j, cls in enumerate(classes):
        patch, _ = C.render_patch(cls, 64, rng, **C.PRESETS['clean'])
        ax[0, j].imshow(patch); ax[0, j].set_title(cls, fontsize=8.5); ax[0, j].axis('off')
    for j, p in enumerate(presets):
        patch, _ = C.render_patch('waldo', 64, rng, **C.PRESETS[p])
        ax[1, j].imshow(patch); ax[1, j].set_title(p, fontsize=8.5); ax[1, j].axis('off')
    fig.text(0.5, 1.0, 'The six classes (clean)', ha='center', va='top', fontsize=9.5)
    fig.text(0.5, 0.50, 'Waldo across the difficulty axes', ha='center', va='top', fontsize=9.5)
    fig.tight_layout(rect=[0, 0, 1, 0.96])
    fig.subplots_adjust(hspace=0.55)
    fig.savefig(os.path.join(OUT, 'classes_difficulty.pdf'), bbox_inches='tight')
    plt.close(fig)
    print('wrote classes_difficulty.pdf')


if __name__ == '__main__':
    fig_classes_difficulty()
    fig_trade_surface()
    fig_forgetting_inside()

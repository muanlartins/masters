"""Bridge to the AUTHORS' DaRE-RF package (Brophy & Lowd, ICML 2021) for nb03.

The published `dare-rf` is a *binary* exact-unlearning random forest and does not build on
Python 3.13 (its PyPI sdist omits the .pyx; its C also predates 3.13). We therefore run it in
a dedicated Python-3.12 environment and call it from the 3.13 notebook through this script:

    <py3.12> dare_real.py <tag> <io_dir> <cfg_json>

`tag` in {s1, s2, stream, selftest}. Arrays are passed in `<io_dir>/in_<tag>.npz`; results are
written to `cache/dare_real_<tag>.json`. The notebook owns all WiSARD/RF/SISA scoring; this
script only produces DaRE's numbers, so the comparison uses the SAME data, splits and metrics.

Multiclass is handled by **one-vs-rest** (one binary DaRE forest per class) — the faithful
binary→multiclass reduction, and a structural mirror of WiSARD's one-discriminator-per-class
layout. Deletion removes the requested rows from *every* forest (the rows are positives in one
and negatives in the rest), which is what "as if never trained" requires.

Setup once:  pyenv virtualenv 3.12.12 dare-rf
             ~/.pyenv/versions/dare-rf/bin/pip install numpy Cython
             ~/.pyenv/versions/dare-rf/bin/pip install --no-build-isolation \
                 git+https://github.com/jjbrophy47/dare_rf.git
"""
import sys, os, json, time
import numpy as np
import dare


def _auc(yv, sv):  # rank-based ROC-AUC (ties averaged); no sklearn in this env
    yv = np.asarray(yv); sv = np.asarray(sv)
    _, inv, cnt = np.unique(sv, return_inverse=True, return_counts=True)
    csum = np.cumsum(cnt); avg = (csum - cnt + csum + 1) / 2.0
    r = avg[inv]
    npos = int((yv == 1).sum()); nneg = int((yv == 0).sum())
    if npos == 0 or nneg == 0:
        return 0.5
    return float((r[yv == 1].sum() - npos * (npos + 1) / 2) / (npos * nneg))


def ovr_fit(X, y, classes, cfg):
    F = {}
    for c in classes:
        yb = (y == c).astype(np.int32)
        F[c] = dare.Forest(**cfg).fit(X.copy(), yb.copy())
    return F


def ovr_pos(F, classes, Xq):                       # (n, C) positive-class proba per class
    return np.column_stack([F[c].predict_proba(Xq.astype(np.float32))[:, 1] for c in classes])


def ovr_pred(F, classes, Xq):
    return np.array(classes)[ovr_pos(F, classes, Xq).argmax(1)]


def claimed_conf(F, Xq, ylab):                     # membership score = forest[claimed label] proba
    out = np.zeros(len(ylab))
    for t in np.unique(ylab):
        m = ylab == t
        out[m] = F[int(t)].predict_proba(Xq[m].astype(np.float32))[:, 1]
    return out


def retrain_frac(F):                               # mean fraction of per-tree deletes that retrained
    fr = []
    for f in F.values():
        try:
            types, _, _ = f.get_delete_metrics()
            if len(types):
                fr.append(float(np.mean(types)))
        except Exception:
            pass
    return float(np.mean(fr)) if fr else float('nan')


def mem_mb(F):
    return sum(sum(f.get_memory_usage()) for f in F.values()) / 1e6


def run_s(tag, d, cfg_all):
    X, y = d['Xtr'].astype(np.float32), d['ytr'].astype(np.int32)
    Xte, yte = d['Xte'].astype(np.float32), d['yte'].astype(np.int32)
    del_idx = d['del_idx'].astype(np.int32); retain_te = d['retain_te'].astype(bool)
    Fmem, ymem = d['Fmem'].astype(np.float32), d['ymem'].astype(np.int32)
    Fnon, ynon = d['Fnon'].astype(np.float32), d['ynon'].astype(np.int32)
    classes = [int(c) for c in d['classes']]
    out = {}
    for nm, cfg in cfg_all.items():
        F = ovr_fit(X, y, classes, cfg)
        t0 = time.time()
        for c in classes:
            F[c].delete(del_idx)
        cost = time.time() - t0
        pred = ovr_pred(F, classes, Xte)
        out[nm] = dict(cost=cost,
                       util=float((pred[retain_te] == yte[retain_te]).mean()),
                       forget=float((pred[~retain_te] == yte[~retain_te]).mean()),
                       mem=claimed_conf(F, Fmem, ymem).tolist(),
                       non=claimed_conf(F, Fnon, ynon).tolist(),
                       mem_mb=mem_mb(F), retrain_frac=retrain_frac(F))
    return out


def run_stream(d, cfg_all):
    X, y = d['Xtr'].astype(np.float32), d['ytr'].astype(np.int32)
    classes = [int(c) for c in d['classes']]
    contribs = [d[k].astype(np.int32) for k in sorted((k for k in d.files if k.startswith('contrib_')),
                                                       key=lambda s: int(s.split('_')[1]))]
    out = {}
    # live cumulative curve for the cheap (random) regime; greedy per-deletion cost is reported from S1/S2
    for nm, cfg in cfg_all.items():
        if cfg['topd'] == 0:           # greedy: measure ONE contributor delete for annotation, skip full stream
            F = ovr_fit(X, y, classes, cfg)
            t0 = time.time()
            for c in classes:
                F[c].delete(contribs[0])
            out[nm] = dict(per_del=time.time() - t0, n0=int(len(contribs[0])))
            continue
        F = ovr_fit(X, y, classes, cfg); cum = []; t = 0.0
        for cb in contribs:
            t0 = time.time()
            for c in classes:
                F[c].delete(cb)
            t += time.time() - t0; cum.append(t)
        out[nm] = dict(cum=cum, n=len(contribs))
    return out


def run_frontier(d, cfg_all):
    """DaRE's OWN accuracy/cost frontier: sweep topd 0..max at fixed k/n_estimators (answers the
    'you only showed the two extremes' objection). Reuses the S1 arrays."""
    X, y = d['Xtr'].astype(np.float32), d['ytr'].astype(np.int32)
    Xte, yte = d['Xte'].astype(np.float32), d['yte'].astype(np.int32)
    retain_te = d['retain_te'].astype(bool); del_idx = d['del_idx'].astype(np.int32)
    classes = [int(c) for c in d['classes']]
    base = cfg_all['DaRE-greedy']                       # take k/n_estimators/depth from the greedy cfg
    out = []
    for topd in [0, 4, 8, 12, 16, 99]:
        F = ovr_fit(X, y, classes, {**base, 'topd': topd})
        t0 = time.time()
        for c in classes:
            F[c].delete(del_idx)
        cost = time.time() - t0
        pred = ovr_pred(F, classes, Xte)
        out.append(dict(topd=int(topd), cost=cost,
                        util=float((pred[retain_te] == yte[retain_te]).mean())))
    return out


def run_selftest(d, cfg_all):
    """Exactness + index-stability with the real package: sequential deletes == retrain-from-scratch."""
    X, y = d['Xtr'].astype(np.float32), d['ytr'].astype(np.int32)
    Xte = d['Xte'].astype(np.float32); classes = [int(c) for c in d['classes']]
    del_idx = d['del_idx'].astype(np.int32)
    half = len(del_idx) // 2
    res = {}
    for nm, cfg in cfg_all.items():
        # (a) one-shot delete of the whole set
        Fa = ovr_fit(X, y, classes, cfg)
        for c in classes:
            Fa[c].delete(del_idx)
        # (b) sequential delete in two disjoint batches (tests index stability across calls)
        Fb = ovr_fit(X, y, classes, cfg)
        for c in classes:
            Fb[c].delete(del_idx[:half]); Fb[c].delete(del_idx[half:])
        # (c) retrain from scratch on the surviving rows (the gold reference)
        keep = np.setdiff1d(np.arange(len(y)), del_idx)
        Fc = ovr_fit(X[keep], y[keep], classes, cfg)
        Pa, Pb, Pc = (ovr_pos(F, classes, Xte) for F in (Fa, Fb, Fc))
        res[nm] = dict(max_dev_oneshot=float(np.abs(Pa - Pc).max()),
                       max_dev_sequential=float(np.abs(Pb - Pc).max()))
    return res


if __name__ == '__main__':
    tag, io_dir, cfg_json = sys.argv[1], sys.argv[2], sys.argv[3]
    cfg_all = json.loads(cfg_json)
    d = np.load(os.path.join(io_dir, f'in_{tag}.npz'))
    if tag in ('s1', 's2'):
        out = run_s(tag, d, cfg_all)
    elif tag == 'stream':
        out = run_stream(d, cfg_all)
    elif tag == 'frontier':
        out = run_frontier(d, cfg_all)
    elif tag == 'selftest':
        out = run_selftest(d, cfg_all)
    else:
        raise SystemExit('unknown tag ' + tag)
    os.makedirs('cache', exist_ok=True)
    json.dump(out, open(f'cache/dare_real_{tag}.json', 'w'))
    print(f'dare_real {tag}: wrote cache/dare_real_{tag}.json')

"""Research8 phase 1: walk-forward stock return distribution forecasts and scores.

python -m research8.phase1 dev   --panel ../wrds_studies/research8_phase1/panel.npz --out ../wrds_studies/research8_phase1/scores
python -m research8.phase1 final --panel ... --out ...   (refuses unless research8/phase1_frozen.json is committed)

dev scores only the original names with targets <= 2022-12-30. final scores the untouched test (expanded names,
origins from 2023) and the two secondary holdouts. Per-forecast scores are private; summaries go to docs/.
"""
import argparse
import datetime as dt
import json
import os
import subprocess
import time

import numpy as np
from sklearn.ensemble import HistGradientBoostingRegressor

from . import dist
from . import features as F
from . import panel as P

HERE = os.path.dirname(os.path.abspath(__file__))
METHODS = ('EWMA', 'GARCH', 'HAR')
SHAPES = ('Gauss', 'T', 'FHS')
JUMPS = ('none', 'name', 'shrunk')
GRID_MODELS = [f'{m}_{s}_{j}' for m in METHODS for s in SHAPES for j in JUMPS]
MODELS = ['B0_EWMA_raw_Gauss', 'B1_HS_name'] + GRID_MODELS + ['GBQ']
GBQ_LEVELS = np.array([0.01, 0.05, 0.10, 0.25, 0.50, 0.75, 0.90, 0.95, 0.99])
NAME_DRAWS = 2000
DEV_END = dt.date(2022, 12, 30).toordinal()
TEST_START = dt.date(2023, 1, 3).toordinal()
FIRST_ORIGIN = dt.date(2016, 1, 4).toordinal()
FLOOR = 1e-10
HKEYS = [str(h) for h in F.HORIZONS] + ['rel']


def lg(x):
    return np.log(np.maximum(x, FLOOR))


class Prepared:
    """Panel-wide matrices and the origin table."""

    def __init__(self, panel):
        self.p = panel
        r, rel = panel['r'], panel['rel']
        self.dates = panel['dates']
        T, N = r.shape
        self.rd = np.where(rel, np.nan, r)
        self.v_ewma = F.ewma(self.rd)
        self.v_raw = F.ewma(r)
        self.lr = F.trailing_mean(self.rd ** 2, F.LR_WINDOW, F.LR_MIN)
        self.lr252 = F.trailing_mean(self.rd ** 2, 252, 126)
        on2 = np.where(rel, np.nan, panel['on'] ** 2)
        gkd = np.where(rel, np.nan, panel['gk'])
        self.har_x = [lg(F.trailing_mean(on2, w, max(1, w // 2))) for w in (5, 22, 66)] + \
                     [lg(F.trailing_mean(gkd, w, max(1, w // 2))) for w in (1, 5, 22, 66)]
        prox = on2 + gkd
        self.har_y = {}
        for h in F.HORIZONS:
            s = F.forward_sum(np.where(np.isnan(prox), 0.0, prox), h)
            c = F.forward_count(prox, h)
            with np.errstate(invalid='ignore', divide='ignore'):
                self.har_y[h] = np.where(c >= 1, lg(s / np.maximum(c, 1)), np.nan)
        self.R = {h: F.forward_sum(r, h) for h in F.HORIZONS}
        relr = np.where(rel, r, 0.0)
        self.nrel = {h: F.forward_sum(rel.astype(float), h) for h in F.HORIZONS}
        self.D = {h: self.R[h] - F.forward_sum(relr, h) for h in F.HORIZONS}
        self.ret22 = F.trailing_mean(r, 22, 15) * 22
        self.ret66 = F.trailing_mean(r, 66, 44) * 66
        count = np.cumsum(~np.isnan(r), 0)
        self.eligible = (panel['close'] >= 5) & (count >= 252) & ~np.isnan(self.v_ewma) & ~np.isnan(self.v_raw)
        # origins: weekly grid and release P closes
        grid_t = np.arange(0, T, 5)
        gt, gj = np.meshgrid(grid_t, np.arange(N), indexing='ij')
        gt, gj = gt.ravel(), gj.ravel()
        q, ej = panel['ev_q'], panel['ev_j']
        keep = q >= 1
        rt, rj = q[keep] - 1, ej[keep]
        t = np.concatenate([gt, rt])
        j = np.concatenate([gj, rj])
        kind = np.concatenate([np.zeros(len(gt), int), np.ones(len(rt), int)])
        ok = self.eligible[t, j] & (self.dates[t] >= dt.date(2015, 1, 1).toordinal())
        self.t, self.j, self.kind = t[ok], j[ok], kind[ok]
        self.offs, self.hist = F.release_inputs(panel, self.t, self.j)
        self.nhist = (~np.isnan(self.hist)).sum(1)
        self.mhist = np.nansum(self.hist ** 2, 1) / np.maximum(self.nhist, 1)
        self.week = (self.dates[self.t] - 1) // 7
        self.group = panel['group'][self.j]

    def k_fcst(self, idx, h):
        return (self.offs[idx] <= h).sum(1)


def sample_tag(prep, idx, h):
    """'dev', 'test', 'time_holdout', 'name_holdout' or '' for each origin at horizon h."""
    t = prep.t[idx]
    end = np.minimum(t + h, len(prep.dates) - 1)
    target_day = np.where(t + h < len(prep.dates), prep.dates[end], 10 ** 9)
    orig = prep.group[idx] == 'original'
    start = prep.dates[t]
    dev_like = (target_day <= DEV_END) & (start >= FIRST_ORIGIN)
    late = (start >= TEST_START) & (t + h < len(prep.dates))
    tag = np.full(len(idx), '', dtype='<U12')
    tag[orig & dev_like] = 'dev'
    tag[~orig & late] = 'test'
    tag[orig & late] = 'time_holdout'
    tag[~orig & dev_like] = 'name_holdout'
    return tag


class YearModel:
    """Everything fitted at one refit date (1 January of `year`) from training names' earlier data."""

    def __init__(self, prep, year, train_names, log):
        self.prep, self.year = prep, year
        d = prep.dates
        self.refit = int(np.searchsorted(d, dt.date(year, 1, 1).toordinal()))
        self.end = int(np.searchsorted(d, dt.date(year + 1, 1, 1).toordinal()))
        tn = np.isin(prep.j, train_names)
        self.train_names = train_names
        t0 = time.time()
        cols = np.array(sorted(train_names))
        self.theta, ll = F.fit_garch(prep.rd[:, cols], prep.lr[:, cols], self.refit)
        self.gstate, _ = F.garch_filter(prep.rd[:self.end], prep.lr[:self.end], self.theta)
        log(f'{year}: GARCH {np.round(self.theta, 4).tolist()} ll {ll:.4f} ({time.time() - t0:.0f}s)')
        # jump pool from training release origins (P closes) with release before the refit date
        rel_o = np.where((prep.kind == 1) & tn & (prep.t + 1 < self.refit))[0]
        J = prep.p['r'][prep.t[rel_o] + 1, prep.j[rel_o]]
        v = prep.v_ewma[prep.t[rel_o], prep.j[rel_o]]
        ok = np.isfinite(J) & np.isfinite(v) & (v > 0)
        rel_o, J, v = rel_o[ok], J[ok], v[ok]
        self.c = float(np.mean(J * J / v))
        sj = np.sqrt(self.sj2(rel_o))
        self.upool = J / sj
        log(f'{year}: c={self.c:.2f} jumps={len(J)} sd(u)={np.std(self.upool):.3f}')
        # training grid origins per horizon
        self.har, self.shapes, self.tables = {}, {}, {}
        for h in F.HORIZONS:
            tr = np.where((prep.kind == 0) & tn & (prep.t + h < self.refit))[0]
            tr = tr[np.isfinite(prep.R[h][prep.t[tr], prep.j[tr]])]
            X = self.har_X(tr)
            y = prep.har_y[h][prep.t[tr], prep.j[tr]]
            okh = np.isfinite(X).all(1) & np.isfinite(y)
            A = np.c_[np.ones(okh.sum()), X[okh]]
            beta, *_ = np.linalg.lstsq(A, y[okh], rcond=None)
            smear = float(np.mean(np.exp(y[okh] - A @ beta)))
            self.har[h] = (beta, smear)
            recent = prep.dates[prep.t[tr]] >= dt.date(year - 5, 1, 1).toordinal()
            R = prep.R[h][prep.t[tr], prep.j[tr]]
            D = prep.D[h][prep.t[tr], prep.j[tr]]
            nd = h - prep.nrel[h][prep.t[tr], prep.j[tr]]
            for m in METHODS:
                z_none = R / np.sqrt(self.hvar(m, tr, h, np.full(len(tr), h)))
                with np.errstate(invalid='ignore', divide='ignore'):
                    z_jump = np.where(nd >= 1, D / np.sqrt(self.hvar(m, tr, h, np.maximum(nd, 1))), np.nan)
                for s in SHAPES:
                    for jf, z in (('none', z_none), ('jump', z_jump)):
                        zz = z[recent] if s == 'FHS' else z
                        self.shapes[m, s, jf, h] = dist.Shape(s, zz[np.isfinite(zz)])
                    self.tables[m, s, h] = dist.jump_table(self.shapes[m, s, 'jump', h], self.upool, seed=year * 100 + h)
        self.gbq = self.fit_gbq(tn, log)
        log(f'{year}: fitted ({time.time() - t0:.0f}s)')

    def sj2(self, idx):
        p = self.prep
        v = p.v_ewma[p.t[idx], p.j[idx]]
        n = p.nhist[idx]
        return (n * p.mhist[idx] + F.K0 * self.c * v) / (n + F.K0)

    def har_X(self, idx):
        p = self.prep
        return np.column_stack([x[p.t[idx], p.j[idx]] for x in p.har_x])

    def hvar(self, m, idx, h, n):
        """Horizon diffusion variance for n diffusion sessions out of h."""
        p = self.prep
        t, j = p.t[idx], p.j[idx]
        ew = p.v_ewma[t, j]
        if m == 'EWMA':
            return n * ew
        if m == 'GARCH':
            st = self.gstate[np.minimum(t, self.end - 1), j]
            lr = p.lr[t, j]
            out = F.garch_horizon(st, lr, self.theta, h, n / h)
            return np.where(np.isfinite(out) & (out > 0), out, n * ew)
        beta, smear = self.har[h]
        X = self.har_X(idx)
        daily = np.exp(np.c_[np.ones(len(idx)), X] @ beta) * smear
        return np.where(np.isfinite(daily), n * daily, n * ew)

    def gbq_X(self, idx, h):
        p = self.prep
        t, j = p.t[idx], p.j[idx]
        v = p.v_ewma[t, j]
        k = p.k_fcst(idx, h)
        first = np.where(k >= 1, p.offs[idx, 0] / h, -1.0)
        return np.column_stack([lg(v)] + [p.har_x[i][t, j] for i in (0, 1, 2, 4, 5, 6)] +
                               [lg(p.lr252[t, j]), p.ret22[t, j] / np.sqrt(v), p.ret66[t, j] / np.sqrt(v),
                                (k >= 1).astype(float), first, lg(self.sj2(idx) / v), p.nhist[idx],
                                lg(p.p['close'][t, j])])

    def fit_gbq(self, tn, log):
        p = self.prep
        out = {}
        for h in F.HORIZONS:
            tr = np.where((p.kind == 0) & tn & (p.t + h < self.refit))[0]
            y = p.R[h][p.t[tr], p.j[tr]] / np.sqrt(h * p.v_ewma[p.t[tr], p.j[tr]])
            ok = np.isfinite(y)
            X = self.gbq_X(tr[ok], h)
            out[h] = []
            for a in GBQ_LEVELS:
                m = HistGradientBoostingRegressor(loss='quantile', quantile=float(a), max_iter=300, learning_rate=0.05,
                                                  max_leaf_nodes=31, min_samples_leaf=200, random_state=0)
                out[h].append(m.fit(X, y[ok]))
        return out

    # ------------------------------------------------------------------ forecasts
    def quantiles(self, model, idx, h, rng):
        p = self.prep
        t, j = p.t[idx], p.j[idx]
        n = len(idx)
        if model == 'B0_EWMA_raw_Gauss':
            return np.sqrt(h * p.v_raw[t, j])[:, None] * dist.stats.norm.ppf(dist.LEVELS)[None, :]
        if model == 'B1_HS_name':
            Rh = p.R[h]
            w = np.arange(-504, -h + 1)
            rows = t[:, None] + w[None, :]
            vals = np.where(rows >= 0, Rh[np.maximum(rows, 0), j[:, None]], np.nan)
            enough = (~np.isnan(vals)).sum(1) >= 100
            Q = np.full((n, len(dist.LEVELS)), np.nan)
            if enough.any():
                Q[enough] = np.nanquantile(vals[enough], dist.LEVELS, axis=1).T
            if (~enough).any():
                Q[~enough] = self.quantiles('B0_EWMA_raw_Gauss', idx[~enough], h, rng)
            return Q
        if model == 'GBQ':
            X = self.gbq_X(idx, h)
            q = np.column_stack([m.predict(X) for m in self.gbq[h]])
            return dist.normal_score_interp(GBQ_LEVELS, q) * np.sqrt(h * p.v_ewma[t, j])[:, None]
        m, s, jm = model.split('_')
        if jm == 'none':
            sd = np.sqrt(self.hvar(m, idx, h, np.full(n, h)))
            return sd[:, None] * self.shapes[m, s, 'none', h].ppf(dist.LEVELS)[None, :]
        k = p.k_fcst(idx, h)
        nd = h - k
        shape = self.shapes[m, s, 'jump', h]
        sd = np.sqrt(self.hvar(m, idx, h, np.maximum(nd, 1))) * (nd >= 1)
        Q = np.empty((n, len(dist.LEVELS)))
        z0 = shape.ppf(dist.LEVELS)
        Q[k == 0] = sd[k == 0, None] * z0[None, :]
        sj = np.sqrt(self.sj2(idx))
        use_name = (jm == 'name') & (p.nhist[idx] >= F.MIN_NAME_EVENTS)
        a = (k >= 1) & ~use_name & (nd == 0) & (k == 1)
        Q[a] = sj[a, None] * np.quantile(self.upool, dist.LEVELS)[None, :]
        b = (k == 1) & ~use_name & (nd >= 1)
        if b.any():
            Q[b] = sd[b, None] * dist.table_lookup(self.tables[m, s, h], sj[b] / sd[b])
        c = (k >= 2) & ~use_name
        zs = shape.ppf(dist.stratified(NAME_DRAWS))
        for rows in np.array_split(np.where(c)[0], max(1, int(c.sum()) // 4000 + 1)):
            if len(rows) == 0:
                continue
            draws = sd[rows, None] * zs[None, :]
            for kk in range(int(k[rows].max())):
                u = rng.choice(self.upool, size=(len(rows), NAME_DRAWS))
                draws = draws + (kk < k[rows])[:, None] * sj[rows, None] * u
            Q[rows] = dist.sample_quantiles(draws)
        d = (k >= 1) & use_name
        v = p.v_ewma[t, j]
        for rows in np.array_split(np.where(d)[0], max(1, int(d.sum()) // 4000 + 1)):
            if len(rows) == 0:
                continue
            draws = sd[rows, None] * rng.permuted(np.tile(zs, (len(rows), 1)), axis=1)
            hist = p.hist[idx[rows]]
            nh = p.nhist[idx[rows]]
            for kk in range(int(k[rows].max())):
                pick = np.floor(rng.random((len(rows), NAME_DRAWS)) * nh[:, None]).astype(int)
                jump = np.take_along_axis(hist, pick, 1) + np.sqrt(v[rows])[:, None] * rng.standard_normal((len(rows), NAME_DRAWS))
                draws = draws + (kk < k[rows])[:, None] * jump
            Q[rows] = dist.sample_quantiles(draws)
        return Q


def run_year(prep, year, train_names, eval_names, allowed, out_dir, log):
    ym = YearModel(prep, year, train_names, log)
    rng = np.random.default_rng(20261003 + year)
    in_year = (prep.t >= ym.refit) & (prep.t < ym.end) & np.isin(prep.j, eval_names)
    saved = {}
    for hk in HKEYS:
        h = 1 if hk == 'rel' else int(hk)
        kind = 1 if hk == 'rel' else 0
        idx = np.where(in_year & (prep.kind == kind))[0]
        tag = sample_tag(prep, idx, h)
        keep = np.isin(tag, allowed)
        idx, tag = idx[keep], tag[keep]
        y = prep.R[h][prep.t[idx], prep.j[idx]]
        ok = np.isfinite(y)
        idx, tag, y = idx[ok], tag[ok], y[ok]
        if len(idx) == 0:
            continue
        sc = np.empty((len(MODELS), len(idx), 5), np.float32)
        for mi, model in enumerate(MODELS):
            Q = ym.quantiles(model, idx, h, rng)
            s = dist.score(Q, y)
            sc[mi] = np.column_stack([s[k] for k in ('crps', 'tw', 'log', 'pit', 'eabs')])
        saved[hk] = {'scores': sc, 'y': y.astype(np.float32), 'week': prep.week[idx], 'tag': tag,
                     'secid': prep.p['names'][prep.j[idx]], 'k': prep.k_fcst(idx, h), 'nrel': prep.nrel[h][prep.t[idx], prep.j[idx]]}
        log(f'{year} h={hk}: {len(idx)} forecasts')
    path = os.path.join(out_dir, f'scores_{year}.npz')
    flat = {f'{hk}__{k}': v for hk, d in saved.items() for k, v in d.items()}
    np.savez_compressed(path, models=np.array(MODELS), **flat)
    return {'year': year, 'theta': ym.theta, 'c': ym.c, 'har': {h: ym.har[h][0].round(4).tolist() for h in F.HORIZONS},
            'shapes': {f'{k[0]}_{k[1]}_{k[2]}_{k[3]}': (round(v.df, 2) if v.kind == 'T' else None)
                       for k, v in ym.shapes.items() if k[1] == 'T'}}


def committed(path):
    rel = os.path.relpath(path, os.path.dirname(HERE))
    r = subprocess.run(['git', '-C', os.path.dirname(HERE), 'status', '--porcelain', '--', rel], capture_output=True, text=True)
    t = subprocess.run(['git', '-C', os.path.dirname(HERE), 'ls-files', '--error-unmatch', rel], capture_output=True)
    return t.returncode == 0 and r.stdout.strip() == ''


def main():
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument('mode', choices=['dev', 'final'])
    ap.add_argument('--panel', default='../wrds_studies/research8_phase1/panel.npz')
    ap.add_argument('--out', default='../wrds_studies/research8_phase1/scores')
    ap.add_argument('--years', default='')
    a = ap.parse_args()
    out = os.path.join(a.out, a.mode)
    os.makedirs(out, exist_ok=True)
    logf = open(os.path.join(out, 'log.txt'), 'a')

    def log(msg):
        print(msg, flush=True)
        logf.write(msg + '\n')
        logf.flush()

    panel = P.load(a.panel)
    prep = Prepared(panel)
    log(f'prepared {len(prep.t)} origins')
    names = np.arange(len(panel['names']))
    orig = names[panel['group'] == 'original']
    meta = []
    if a.mode == 'dev':
        years = [int(y) for y in a.years.split(',')] if a.years else list(range(2016, 2023))
        for y in years:
            meta.append(run_year(prep, y, orig, orig, ['dev'], out, log))
    else:
        frozen = os.path.join(HERE, 'phase1_frozen.json')
        if not os.path.exists(frozen) or not committed(frozen):
            raise SystemExit('final mode needs a committed research8/phase1_frozen.json')
        exp = names[panel['group'] != 'original']
        for y in range(2016, 2023):
            meta.append(run_year(prep, y, orig, exp, ['name_holdout'], out, log))
        for y in range(2023, 2026):
            meta.append(run_year(prep, y, names, names, ['test', 'time_holdout'], out, log))
    with open(os.path.join(out, f'fit_meta_{a.years or "all"}.json'), 'w') as s:
        json.dump(meta, s, indent=1, default=float)


if __name__ == '__main__':
    main()

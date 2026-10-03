"""Stock trades around earnings releases (no options). Pre-registered in protocol_stockev.json.

python -m research8.stockev dev
python -m research8.stockev final   (needs committed research8/stockev_frozen.json)

Abnormal return = stock log total return - equal-weight mean log return of all panel names that day.
Aggregates only.
"""
import argparse
import datetime as dt
import json
import os

import numpy as np

from research7 import data
from . import panel as P
from . import rules2 as R2

HERE = os.path.dirname(os.path.abspath(__file__))
HOLDS = (5, 10, 20, 40, 60)
COSTS_BP = (0, 5, 10, 20)
ZS = (1.0, 2.0)
BLOCK = 8
DEV_START, DEV_END = dt.date(2015, 1, 1), dt.date(2022, 12, 30)
TEST_START = dt.date(2023, 1, 3)


def rules():
    out = []
    for e in ('Q', 'Q+1'):
        out += [('sue', e, h, None) for h in HOLDS]
        out += [('drift', e, h, z) for h in HOLDS for z in ZS]
        out += [('fade', e, h, z) for h in HOLDS for z in ZS]
        out += [('agree', e, h, None) for h in HOLDS]
    out += [('premium', f'P-{k}', None, None) for k in (1, 5, 10)]
    return out


def rname(r):
    return '|'.join('' if x is None else str(x) for x in r)


def load_events(caches, col, sessions_ord):
    evs = []
    for c in caches:
        for e in data.load_base(c)['events']:
            if e['secid'] not in col:
                continue
            cons = e.get('consensus')
            evs.append({'j': col[e['secid']], 'P': e['P_index'], 'Q': e['Q_index'], 'group': e.get('group', 'original'),
                        'eps': e.get('eps'), 'cons': cons['mean'] if cons else None})
    return evs


def build(pan, caches):
    r = pan['r']
    mkt = np.nanmean(r, 1)
    ar = r - mkt[:, None]
    car = np.vstack([np.zeros((1, r.shape[1])), np.nancumsum(np.nan_to_num(ar), 0)])
    bad = np.vstack([np.zeros((1, r.shape[1])), np.cumsum(np.isnan(ar), 0)])
    col = {int(s): j for j, s in enumerate(pan['names'])}
    evs = load_events(caches, col, pan['dates'])
    T = r.shape[0]
    rows = []
    hist = {}
    for e in sorted(evs, key=lambda x: x['Q']):
        j, p, q = e['j'], e['P'], e['Q']
        if q >= T or p < 0:
            continue
        cl = pan['close'][p, j]
        J = car[q + 1, j] - car[p + 1, j] if bad[q + 1, j] - bad[p + 1, j] == 0 else np.nan
        prev = hist.setdefault(j, [])
        sj = np.sqrt(np.mean(np.square(prev[-8:]))) if len([x for x in prev[-8:]]) >= 4 else np.nan
        sue = (e['eps'] - e['cons']) / cl if e['eps'] is not None and e['cons'] is not None and cl and cl > 0 else np.nan
        rows.append({'j': j, 'P': p, 'Q': q, 'group': e['group'], 'J': J, 'JZ': J / sj if sj and sj > 0 else np.nan,
                     'sue': sue, 'close_P': cl})
        if np.isfinite(J):
            prev.append(J)
    return rows, car, bad


def window_ret(car, bad, j, a, b):
    """Sum of abnormal returns over sessions a+1..b (entry close a, exit close b)."""
    if a < 0 or b >= car.shape[0] - 1 or b <= a or bad[b + 1, j] - bad[a + 1, j] > 0:
        return np.nan
    return car[b + 1, j] - car[a + 1, j]


def trades(rule, rows, car, bad, sue_cut, dates):
    fam, entry, h, z = rule
    out = []
    for i, x in enumerate(rows):
        if x['close_P'] is None or not np.isfinite(x['close_P']) or x['close_P'] < 5:
            continue
        if fam == 'premium':
            k = int(entry[2:])
            a, b, d = x['P'] - k, x['P'], 1
        else:
            a = x['Q'] + (1 if entry == 'Q+1' else 0)
            b = a + h
            if fam == 'sue':
                lo, hi = sue_cut[i]
                if not np.isfinite(x['sue']) or not np.isfinite(lo):
                    continue
                d = 1 if x['sue'] >= hi else -1 if x['sue'] <= lo else 0
            elif fam in ('drift', 'fade'):
                if not np.isfinite(x['JZ']) or abs(x['JZ']) < z:
                    continue
                d = int(np.sign(x['J'])) * (1 if fam == 'drift' else -1)
            else:  # agree
                lo, hi = sue_cut[i]
                if not np.isfinite(x['sue']) or not np.isfinite(lo) or not np.isfinite(x['J']):
                    continue
                s = 1 if x['sue'] >= hi else -1 if x['sue'] <= lo else 0
                d = s if s == int(np.sign(x['J'])) else 0
            if d == 0:
                continue
        w = window_ret(car, bad, x['j'], a, b)
        if np.isfinite(w):
            out.append((i, a, b, d * w))
    return out


def sue_cutoffs(rows, dates, allowed):
    """Point-in-time 20th/80th percentiles of SUE over allowed events with Q in the prior 365 days."""
    q = np.array([x['Q'] for x in rows])
    s = np.array([x['sue'] for x in rows])
    ok = allowed & np.isfinite(s)
    qd = dates[q]
    cuts = []
    for i in range(len(rows)):
        m = ok & (qd < qd[i]) & (qd >= qd[i] - 365)
        cuts.append(tuple(np.percentile(s[m], [20, 80])) if m.sum() >= 200 else (np.nan, np.nan))
    return cuts


def block_boot(weekly, rng, draws=2000):
    n = len(weekly)
    nb = int(np.ceil(n / BLOCK))
    starts = rng.integers(0, max(n - BLOCK, 1), (draws, nb))
    idx = (starts[:, :, None] + np.arange(BLOCK)[None, None, :]).reshape(draws, -1)[:, :n]
    return weekly[np.minimum(idx, n - 1)].mean(1)


def evaluate(rule, tr, rows, dates, sample, all_weeks, rng):
    sel = [t for t in tr if sample[t[0]]]
    out = {'rule': rname(rule), 'n': len(sel)}
    if len(sel) < 30:
        return out
    ret = np.array([t[3] for t in sel])
    wk = np.array([(dates[t[1]] - 1) // 7 for t in sel])
    yrs = np.array([dt.date.fromordinal(int(dates[t[1]])).year for t in sel])
    for c in COSTS_BP:
        rr = ret - 2 * c / 1e4
        w, s, cnt = R2.weekly(rr, wk, all_weeks)
        boot = block_boot(w, rng)
        sd = w.std(ddof=1)
        bsd = boot.std(ddof=1)
        out[f'c{c}'] = {'mean': float(rr.mean()), 'weekly_mean': float(w.mean()),
                        'ci_weekly': np.percentile(boot, [2.5, 97.5]).tolist(),
                        'sharpe': float(w.mean() / sd * np.sqrt(52)) if sd > 0 else 0.0,
                        't_block': float(w.mean() / bsd) if bsd > 0 else 0.0, 'win': float(np.mean(rr > 0))}
        if c == 10:
            out['by_year_c10'] = {str(y): float(rr[yrs == y].mean()) for y in sorted(set(yrs))}
    return out


def main():
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument('mode', choices=['dev', 'final'])
    ap.add_argument('--panel', default='../wrds_studies/research8_phase1/panel.npz')
    ap.add_argument('--caches', default='../wrds_studies/research7_cache,../wrds_studies/research7_cache_e')
    ap.add_argument('--docs', default='docs/research8/stockev')
    a = ap.parse_args()
    pan = P.load(a.panel)
    dates = pan['dates']
    rows, car, bad = build(pan, a.caches.split(','))
    grp = np.array([x['group'] for x in rows])
    orig = grp == 'original'
    qday = np.array([dt.date.fromordinal(int(dates[x['Q']])) for x in rows])
    if a.mode == 'dev':
        cuts = sue_cutoffs(rows, dates, orig)
        rl = rules()
    else:
        path = os.path.join(HERE, 'stockev_frozen.json')
        if not R2.committed(path):
            raise SystemExit('final needs a committed research8/stockev_frozen.json')
        cuts = sue_cutoffs(rows, dates, np.ones(len(rows), bool))
        rl = [tuple(x) for x in json.load(open(path))['rules']]
    os.makedirs(a.docs, exist_ok=True)
    rng = np.random.default_rng(R2.SEED)
    results = {}
    trade_sets = {r: trades(r, rows, car, bad, cuts, dates) for r in rl}
    for label in (['dev'] if a.mode == 'dev' else ['test', 'time_holdout']):
        res = []
        for r in rl:
            tr = trade_sets[r]
            ent = {t[0]: dt.date.fromordinal(int(dates[t[1]])) for t in tr}
            ext = {t[0]: dt.date.fromordinal(int(dates[t[2]])) for t in tr}
            if label == 'dev':
                sample = np.array([orig[i] and i in ent and ent[i] >= DEV_START and ext[i] <= DEV_END for i in range(len(rows))])
            elif label == 'test':
                sample = np.array([(not orig[i]) and i in ent and ent[i] >= TEST_START for i in range(len(rows))])
            else:
                sample = np.array([orig[i] and i in ent and ent[i] >= TEST_START for i in range(len(rows))])
            wks = np.unique([(dates[t[1]] - 1) // 7 for t in tr if sample[t[0]]]) if sample.any() else np.array([])
            if len(wks) == 0:
                res.append({'rule': rname(r), 'n': 0})
                continue
            all_weeks = np.arange(wks.min(), wks.max() + 1)
            res.append(evaluate(r, tr, rows, dates, sample, all_weeks, rng))
        extra = {}
        if label == 'dev':
            named = {rname(r): r for r in rl}
            elig = [x for x in res if 'c10' in x and x['n'] >= 300 and x['c10']['ci_weekly'][0] > 0 and x['c10']['t_block'] >= 3.0
                    and np.mean([v for k, v in x['by_year_c10'].items() if int(k) <= 2018] or [-1]) > 0
                    and np.mean([v for k, v in x['by_year_c10'].items() if int(k) >= 2019] or [-1]) > 0]
            picks, used = [], set()
            for x in sorted(elig, key=lambda x: -x['c10']['sharpe']):
                r = named[x['rule']]
                if r[0] in used:
                    continue
                used.add(r[0])
                picks.append(list(r))
                if len(picks) == 3:
                    break
            extra = {'eligible': len(elig), 'freeze_picks': picks}
            print('eligible', len(elig), 'picks', picks)
        else:
            extra['gates'] = {}
            for x in res:
                c, c2 = x.get('c10'), x.get('c20')
                g = {'g1': bool(c and c['ci_weekly'][0] > 0), 'g2': bool(c and c['sharpe'] >= 1.0),
                     'g3': bool(c and c['t_block'] >= 2.0), 'g4': bool(c2 and c2['mean'] > 0)}
                g['strong'] = all(g.values())
                g['weak'] = g['g1'] and not g['strong']
                extra['gates'][x['rule']] = g
                print('GATE', x['rule'], g)
        json.dump({'sample': label, 'rules': res, **extra}, open(os.path.join(a.docs, f'{label}.json'), 'w'), indent=1)
        ok = [x for x in res if 'c10' in x]
        print(f'[{label}] {len(ok)} rules')
        for x in sorted(ok, key=lambda x: -x['c10']['sharpe'])[:12]:
            c = x['c10']
            print(f"{x['rule']}: n={x['n']} gross {x['c0']['mean'] * 1e4:+.1f}bp c10 {c['mean'] * 1e4:+.1f}bp SR {c['sharpe']:.2f} "
                  f"t {c['t_block']:.2f} weekly CI [{c['ci_weekly'][0] * 1e4:+.1f},{c['ci_weekly'][1] * 1e4:+.1f}]bp "
                  f"c20 {x['c20']['mean'] * 1e4:+.1f}bp win {c['win']:.2f}")


if __name__ == '__main__':
    main()

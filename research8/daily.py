"""Daily-panel volatility-premium rules (pre-registered in protocol_daily.json before the data existed).

python -m research8.daily build   --src ../wrds_studies/research8_daily/daily --panel ../wrds_studies/research8_phase1/panel.npz \
                                  --work ../wrds_studies/research8_daily_work
python -m research8.daily records --work ...
python -m research8.daily value   --work ...
python -m research8.daily dev     --work ... --docs docs/research8/daily
python -m research8.daily final   --work ... --docs ...   (needs committed research8/daily_frozen.json)
"""
import argparse
import datetime as dt
import glob
import json
import os
import pickle
from collections import defaultdict

import numpy as np
import pandas as pd

from research7 import data
from . import options2 as O
from . import panel as P
from . import rules2 as R2

HERE = os.path.dirname(os.path.abspath(__file__))
SPY = 109820
EXITS = ('expiry', 5, 10)
DEV_START, DEV_END, TEST_START = dt.date(2016, 1, 1), dt.date(2021, 12, 31), dt.date(2022, 1, 3)
MODEL = 'HAR_FHS_shrunk'


# ---------------------------------------------------------------------------- build
def build(src, panel_path, work):
    os.makedirs(work, exist_ok=True)
    pan = P.load(panel_path)
    names = list(pan['names'])
    dates = pan['dates']
    sel = pd.read_csv(os.path.join(src, 'panel.csv'))
    st = pd.concat([pd.read_csv(f) for f in sorted(glob.glob(os.path.join(src, 'stocks_daily_*.csv.gz')))])
    st['secid'] = st['secid'].astype(int)
    add = [int(s) for s in sel['secid'] if int(s) not in names]
    T = len(dates)
    row = {dt.date.fromordinal(int(d)).isoformat(): i for i, d in enumerate(dates)}
    ext = {k: pan[k] for k in pan}
    for s in add:
        x = st[st['secid'] == s]
        x = x[x['date'].str[:10].isin(row)]
        ti = x['date'].str[:10].map(row).to_numpy()
        col = {k: np.full(T, np.nan) for k in ('r', 'id', 'gk', 'close', 'on')}
        close = np.abs(x['close'].to_numpy(float))
        o, h, l = (x[c].to_numpy(float) for c in ('open', 'high', 'low'))
        ok = (o > 0) & (h > 0) & (l > 0) & (close > 0)
        idr = np.where(ok, np.log(np.where(ok, close, 1) / np.where(ok, o, 1)), np.nan)
        gk = np.where(ok, 0.5 * np.log(np.where(ok, h, 1) / np.where(ok, l, 1)) ** 2 - (2 * np.log(2) - 1) * idr ** 2, np.nan)
        ret = x['return'].to_numpy(float)
        col['r'][ti] = np.where(ret > -1, np.log1p(np.where(ret > -1, ret, 0)), np.nan)
        col['id'][ti], col['gk'][ti], col['close'][ti] = idr, np.maximum(gk, 0), close
        col['on'] = col['r'] - col['id']
        for k in col:
            ext[k] = np.column_stack([ext[k], col[k]])
        ext['rel'] = np.column_stack([ext['rel'], np.zeros(T, bool)])
        ext['names'] = np.append(ext['names'], s)
        ext['group'] = np.append(ext['group'], 'spy' if s == SPY else 'daily_extra')
    np.savez_compressed(os.path.join(work, 'panel_ext.npz'), **ext)
    files = sorted(glob.glob(os.path.join(src, 'quotes_daily_*.csv.gz')))
    by_year = defaultdict(list)
    for f in files:
        by_year[os.path.basename(f).split('_')[2]].append(f)
    for y, fs in sorted(by_year.items()):
        snaps = {}
        for f in fs:
            _, _, part = data.parse_quotes(f)
            for k, chain in part.items():
                if k in snaps:
                    for ex, strikes in chain.items():
                        snaps[k].setdefault(ex, {}).update(strikes)
                else:
                    snaps[k] = chain
        with open(os.path.join(work, f'quotes_{y}.pkl'), 'wb') as s:
            pickle.dump(snaps, s, protocol=pickle.HIGHEST_PROTOCOL)
        print(y, len(snaps), 'snapshots', flush=True)
    div = defaultdict(list)
    dpath = os.path.join(src, 'distributions_daily.csv.gz')
    if os.path.exists(dpath):
        for r in data.rows(dpath):
            if r.get('cancel_flag') != '1' and r['ex_date']:
                div[int(float(r['secid']))].append(dt.date.fromisoformat(r['ex_date'][:10]))
    json.dump({'secids': [int(s) for s in sel['secid']], 'dividends': {str(k): [d.isoformat() for d in sorted(v)] for k, v in div.items()}},
              open(os.path.join(work, 'meta.json'), 'w'))


# ---------------------------------------------------------------------------- records
def choose_expiry(chain, day):
    best = None
    for ex in chain:
        d = (dt.date.fromisoformat(ex) - day).days
        if 21 <= d <= 45 and (best is None or abs(d - 30) < abs(best[1] - 30)):
            best = (ex, d)
    return best[0] if best else None


def records(work):
    pan = P.load(os.path.join(work, 'panel_ext.npz'))
    meta = json.load(open(os.path.join(work, 'meta.json')))
    dates = pan['dates']
    days = [dt.date.fromordinal(int(d)) for d in dates]
    col = {int(s): j for j, s in enumerate(pan['names'])}
    divs = {int(k): [dt.date.fromisoformat(x) for x in v] for k, v in meta['dividends'].items()}
    close, r = pan['close'], pan['r']
    grid = [t for t in range(0, len(dates), 5) if days[t] >= DEV_START]
    years = sorted({days[t].year for t in grid})
    out = []
    cache = {}

    def chain_at(secid, t):
        y = days[t].year
        if y not in cache:
            p = os.path.join(work, f'quotes_{y}.pkl')
            cache.clear()
            cache[y] = pickle.load(open(p, 'rb')) if os.path.exists(p) else {}
        return cache[y].get((secid, days[t].isoformat()))

    for y in years:
        ts = [t for t in grid if days[t].year == y]
        exits_needed = []
        for t in ts:
            for secid in meta['secids']:
                j = col.get(secid)
                if j is None:
                    continue
                chain = chain_at(secid, t)
                spot = close[t, j]
                if not chain or not np.isfinite(spot) or spot < 10:
                    continue
                ex = choose_expiry(chain, days[t])
                if ex is None:
                    continue
                exd = dt.date.fromisoformat(ex)
                if secid != SPY and any(days[t] < d <= exd for d in divs.get(secid, [])):
                    continue
                te = int(np.searchsorted(dates, exd.toordinal(), 'right')) - 1
                if te <= t or te >= len(dates):
                    continue
                path = close[t:te + 1, j]
                rets = r[t + 1:te + 1, j]
                if not np.isfinite(path).all() or not np.isfinite(rets).all():
                    continue
                if secid != SPY and abs(np.log(path[-1] / spot) - rets.sum()) > 0.02:
                    continue
                strikes = chain[ex]
                atm = None
                for k, leg in strikes.items():
                    if None in (leg[0], leg[1], leg[3], leg[4]):
                        continue
                    if atm is None or abs(k - spot) < abs(atm - spot):
                        atm = k
                if atm is None:
                    continue
                h = te - t
                tau = (te - np.arange(t, te + 1)) / 252.0
                legs = []
                for cp in ('C', 'P'):
                    q = O.leg_quote(chain, (ex, atm, cp, 1, 'core'))
                    if q is None:
                        break
                    bid, ask, oi = q
                    m = (bid + ask) / 2
                    if bid <= 0 or m < O.MIN_MID or oi < O.MIN_OI or (ask - bid) / m > O.SPREAD_LIMIT:
                        break
                    vol = O.implied_vol(m, spot, atm, h / 252.0, cp)
                    if vol is None:
                        break
                    dl = O.deltas(path[:-1], atm, tau[:-1], vol, cp)
                    legs.append({'cp': cp, 'bid': bid, 'ask': ask, 'iv': vol, 'dl': dl,
                                 'payoff': max(path[-1] - atm, 0.0) if cp == 'C' else max(atm - path[-1], 0.0)})
                if len(legs) != 2:
                    continue
                rec = {'secid': secid, 'j': j, 't': t, 'te': te, 'h': h, 'expiry': ex, 'strike': atm, 'spot': float(spot),
                       'week': (dates[t] - 1) // 7, 'mkt': sum((x['bid'] + x['ask']) / 2 for x in legs),
                       'half': sum((x['ask'] - x['bid']) / 2 for x in legs), 'payoff': sum(x['payoff'] for x in legs),
                       'iv': [x['iv'] for x in legs], 'exits': {}}
                for name in EXITS:
                    n = h if name == 'expiry' else name
                    if n > h:
                        continue
                    hedge = sum(float(-np.sum(x['dl'][:n] * np.diff(path[:n + 1]))) for x in legs)
                    tr = [np.abs(np.diff(np.concatenate([[0.0], x['dl'][:n], [0.0]]))) for x in legs]
                    hcost = sum(float(O.HEDGE_COST * np.sum(z * np.concatenate([path[:n], [path[n]]]))) for z in tr)
                    rec['exits'][str(name)] = {'n': n, 'hedge': hedge, 'hcost': hcost}
                out.append(rec)
                for name in (5, 10):
                    if str(name) in rec['exits']:
                        exits_needed.append((len(out) - 1, name))
        # exit quotes for 5/10-session exits (same legs; up to two sessions later if missing)
        for i, name in exits_needed:
            rec = out[i]
            got = None
            for extra in (0, 1, 2):
                te2 = rec['t'] + name + extra
                if te2 > rec['te'] or te2 >= len(dates):
                    break
                ch = chain_at(rec['secid'], te2)
                if not ch:
                    continue
                qs = [O.leg_quote(ch, (rec['expiry'], rec['strike'], cp, 1, 'core')) for cp in ('C', 'P')]
                if all(q is not None for q in qs):
                    got = (te2, sum((q[0] + q[1]) / 2 for q in qs), sum((q[1] - q[0]) / 2 for q in qs))
                    break
            if got is None:
                del rec['exits'][str(name)]
            else:
                rec['exits'][str(name)].update({'exit_t': got[0], 'exit_mid': got[1], 'exit_half': got[2]})
        print(y, 'records so far', len(out), flush=True)
    pickle.dump(out, open(os.path.join(work, 'records.pkl'), 'wb'), protocol=pickle.HIGHEST_PROTOCOL)


# ---------------------------------------------------------------------------- value
def value(work):
    from .phase1 import Prepared, YearModel
    from .value2 import nearest_h, leg_values
    pan = P.load(os.path.join(work, 'panel_ext.npz'))
    recs = pickle.load(open(os.path.join(work, 'records.pkl'), 'rb'))
    t = np.array([x['t'] for x in recs])
    j = np.array([x['j'] for x in recs])
    prep = Prepared(pan, extra=(t, j))
    pos = {(int(prep.t[i]), int(prep.j[i])): i for i in np.where(prep.kind == 2)[0]}
    names = np.arange(len(pan['names']))
    orig = names[pan['group'] == 'original']
    allnames = names[np.isin(pan['group'], ['original', 'expanded_2017', 'added_2020'])]
    years = np.array([dt.date.fromordinal(int(pan['dates'][x])).year for x in t])
    val = np.full(len(recs), np.nan)
    relwin = np.zeros(len(recs), bool)
    for y in sorted(set(years)):
        ym = YearModel(prep, int(y), orig if y <= 2021 else allnames, print, gbq=False)
        rng = np.random.default_rng(20261005 + int(y))
        ri = np.array([i for i in np.where(years == y)[0] if (t[i], j[i]) in pos])
        if len(ri) == 0:
            continue
        idx = np.array([pos[(t[i], j[i])] for i in ri])
        h = np.array([recs[i]['h'] for i in ri]).astype(float)
        hb = nearest_h(h)
        relwin[ri] = prep.k_fcst(idx, h) >= 1
        for b in np.unique(hb):
            s = hb == b
            Q = ym.quantiles(MODEL, idx[s], h[s], rng, hb=int(b))
            k = np.array([recs[i]['strike'] for i in ri[s]])
            vc, vp = leg_values(Q, np.array([recs[i]['spot'] for i in ri[s]]), [(k, 'C'), (k, 'P')])
            val[ri[s]] = vc + vp
        print(y, len(ri), 'valued', flush=True)
    pickle.dump({'value': val, 'release_in_window': relwin}, open(os.path.join(work, 'values.pkl'), 'wb'))


# ---------------------------------------------------------------------------- rules
def rules():
    out = []
    for uni in ('spy', 'names'):
        for ex in EXITS:
            for hedge in ('hedged', 'unhedged'):
                for win in ('all', 'no_release'):
                    out += [(uni, str(ex), hedge, win, 'sell', None), (uni, str(ex), hedge, win, 'sell', 1.1),
                            (uni, str(ex), hedge, win, 'sell', 1.25), (uni, str(ex), hedge, win, 'buy', 0.9)]
    return out


def rname(r):
    return '|'.join('' if x is None else str(x) for x in r)


def trade_returns(recs, val, relwin, rule, sample, cost):
    uni, ex, hedge, win, d, th = rule
    out = []
    for i, x in enumerate(recs):
        if not sample[i] or ex not in x['exits'] or not np.isfinite(val[i]) or val[i] <= 0:
            continue
        if (uni == 'spy') != (x['secid'] == SPY):
            continue
        if win == 'no_release' and relwin[i]:
            continue
        rho = x['mkt'] / val[i]
        if th is not None and ((d == 'sell' and rho < th) or (d == 'buy' and rho > th)):
            continue
        e = x['exits'][ex]
        if ex == 'expiry':
            gross, half = x['payoff'] - x['mkt'], x['half']
        else:
            gross, half = e['exit_mid'] - x['mkt'], x['half'] + e['exit_half']
        if hedge == 'hedged':
            gross += e['hedge']
        sgn = 1 if d == 'buy' else -1
        fees = 2 * R2.FEE_PER_SHARE * (1 if ex == 'expiry' else 2)
        pnl = sgn * gross - cost * half - fees - (e['hcost'] if hedge == 'hedged' else 0.0)
        out.append((i, pnl / x['mkt']))
    return out


def summarize(recs, dates, tr, all_weeks, rng):
    from .stockev import block_boot
    ret = np.array([v for _, v in tr])
    wk = np.array([recs[i]['week'] for i, _ in tr])
    w, s, cnt = R2.weekly(ret, wk, all_weeks)
    boot = block_boot(w, rng)
    sd, bsd = w.std(ddof=1), boot.std(ddof=1)
    wdates = [dt.date.fromordinal(int(x) * 7 + 1) for x in all_weeks]
    months = defaultdict(float)
    yearsum = defaultdict(float)
    for d0, v in zip(wdates, w):
        months[(d0.year, d0.month)] += v
        yearsum[d0.year] += v
    eq = np.cumsum(w)
    return {'mean': float(ret.mean()), 'ci_weekly': np.percentile(boot, [2.5, 97.5]).tolist(),
            'sharpe': float(w.mean() / sd * np.sqrt(52)) if sd > 0 else 0.0, 't_block': float(w.mean() / bsd) if bsd > 0 else 0.0,
            'worst_trade': float(ret.min()), 'worst_month': float(min(months.values())),
            'mean_annual': float(np.mean(list(yearsum.values()))), 'max_drawdown': float(np.max(np.maximum.accumulate(eq) - eq)),
            'win': float(np.mean(ret > 0))}


def evaluate_mode(work, mode, docs):
    pan = P.load(os.path.join(work, 'panel_ext.npz'))
    dates = pan['dates']
    recs = pickle.load(open(os.path.join(work, 'records.pkl'), 'rb'))
    v = pickle.load(open(os.path.join(work, 'values.pkl'), 'rb'))
    val, relwin = v['value'], v['release_in_window']
    tday = np.array([dt.date.fromordinal(int(dates[x['t']])) for x in recs])
    last_exit = np.array([dt.date.fromordinal(int(dates[max([x['te']] + [e.get('exit_t', 0) for e in x['exits'].values()])])) for x in recs])
    if mode == 'dev':
        sample = (tday >= DEV_START) & (last_exit <= DEV_END)
        rl = rules()
    else:
        path = os.path.join(HERE, 'daily_frozen.json')
        if not R2.committed(path):
            raise SystemExit('final needs a committed research8/daily_frozen.json')
        rl = [tuple(None if y is None else y for y in x) for x in json.load(open(path))['rules']]
        sample = tday >= TEST_START
    wk_all = np.unique([x['week'] for x, s in zip(recs, sample) if s])
    all_weeks = np.arange(wk_all.min(), wk_all.max() + 1)
    rng = np.random.default_rng(R2.SEED)
    res = []
    for r in rl:
        out = {'rule': rname(r)}
        for c in R2.COSTS:
            tr = trade_returns(recs, val, relwin, r, sample, c)
            if len(tr) < 30:
                break
            out['n'] = len(tr)
            out[f'c{int(c * 100)}'] = summarize(recs, dates, tr, all_weeks, rng)
            if c == 0.25:
                yrs = np.array([tday[i].year for i, _ in tr])
                rr = np.array([x for _, x in tr])
                out['by_year_c25'] = {str(y): float(rr[yrs == y].mean()) for y in sorted(set(yrs))}
        res.append(out)
    os.makedirs(docs, exist_ok=True)
    extra = {}
    if mode == 'dev':
        named = {rname(r): r for r in rl}
        elig = []
        for x in res:
            c = x.get('c25')
            if not c:
                continue
            spy = x['rule'].startswith('spy')
            if x['n'] < (100 if spy else 150) or c['ci_weekly'][0] <= 0 or c['t_block'] < (2.5 if spy else 3.0):
                continue
            yrs = x['by_year_c25']
            if np.mean([v for k, v in yrs.items() if int(k) <= 2018] or [-1]) <= 0 or np.mean([v for k, v in yrs.items() if int(k) >= 2019] or [-1]) <= 0:
                continue
            elig.append(x)
        picks, used = [], set()
        for x in sorted(elig, key=lambda x: -x['c25']['sharpe']):
            r = named[x['rule']]
            if (r[0], r[1], r[4]) in used:
                continue
            used.add((r[0], r[1], r[4]))
            picks.append(list(r))
            if len(picks) == 4:
                break
        extra = {'eligible': len(elig), 'freeze_picks': picks}
        print('eligible', len(elig), 'picks', picks)
    else:
        extra['gates'] = {}
        for x in res:
            c, c50 = x.get('c25'), x.get('c50')
            g = {'g1': bool(c and c['ci_weekly'][0] > 0), 'g2': bool(c and c['sharpe'] >= 1.0), 'g3': bool(c and c['t_block'] >= 2.0),
                 'g4': bool(c50 and c50['mean'] > 0), 'g5': bool(c and c['worst_month'] >= -3 * c['mean_annual'])}
            g['strong'] = all(g.values())
            g['weak'] = g['g1'] and not g['strong']
            extra['gates'][x['rule']] = g
            print('GATE', x['rule'], g)
    json.dump({'sample': mode, 'rules': res, **extra}, open(os.path.join(docs, f'{mode}.json'), 'w'), indent=1)
    ok = [x for x in res if 'c25' in x]
    for x in sorted(ok, key=lambda x: -x['c25']['sharpe'])[:12]:
        c = x['c25']
        print(f"{x['rule']}: n={x['n']} mid {x['c0']['mean']:+.3f} c25 {c['mean']:+.3f} SR {c['sharpe']:.2f} t {c['t_block']:.2f} "
              f"worst month {c['worst_month']:+.2f} maxDD {c['max_drawdown']:.2f} c50 {x['c50']['mean']:+.3f}")


def main():
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument('mode', choices=['build', 'records', 'value', 'dev', 'final'])
    ap.add_argument('--src', default='../wrds_studies/research8_daily/daily')
    ap.add_argument('--panel', default='../wrds_studies/research8_phase1/panel.npz')
    ap.add_argument('--work', default='../wrds_studies/research8_daily_work')
    ap.add_argument('--docs', default='docs/research8/daily')
    a = ap.parse_args()
    if a.mode == 'build':
        build(a.src, a.panel, a.work)
    elif a.mode == 'records':
        records(a.work)
    elif a.mode == 'value':
        value(a.work)
    else:
        evaluate_mode(a.work, a.mode, a.docs)


if __name__ == '__main__':
    main()

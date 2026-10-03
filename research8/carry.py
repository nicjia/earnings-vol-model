"""Volatility term-structure trades on the daily panel (pre-registered in protocol_carry.json).

python -m research8.carry build --work ../wrds_studies/research8_daily_work --top 10
python -m research8.carry dev   --work ...
python -m research8.carry final --work ...   (needs committed research8/carry_frozen.json)
"""
import argparse
import datetime as dt
import json
import os
import pickle

import numpy as np

from . import options2 as O
from . import panel as P
from . import rules2 as R2
from .converge import liquid, DEV_END, TEST_START
from .daily import SPY

HERE = os.path.dirname(os.path.abspath(__file__))
LOOK = 12
FEE4 = 4 * R2.FEE_PER_SHARE


def pick(chain, day, lo, hi, target):
    best = None
    for ex in chain:
        d = (dt.date.fromisoformat(ex) - day).days
        if lo <= d <= hi and (best is None or abs(d - target) < abs(best[1] - target)):
            best = (ex, d)
    return best[0] if best else None


def legs4(chain, fe, be, k):
    out = []
    for ex in (fe, be):
        for cp in ('C', 'P'):
            q = O.leg_quote(chain, (ex, k, cp, 1, 'core')) if chain else None
            if q is None:
                return None
            out.append(q)
    return out


def ivs(qs, spot, k, tf, tb):
    v = []
    for (b, a, _), cp, T in zip(qs, ('C', 'P', 'C', 'P'), (tf, tf, tb, tb)):
        iv = O.implied_vol((b + a) / 2, spot, k, T, cp)
        if iv is None:
            return None
        v.append(iv)
    return v


def build(work, top):
    pan = P.load(os.path.join(work, 'panel_ext.npz'))
    meta = json.load(open(os.path.join(work, 'meta.json')))
    order = json.load(open(os.path.join(os.path.dirname(work), 'research8_phase2', 'liquid50.json')))
    names = [SPY] + [s for s in order if s in set(meta['secids']) and s != SPY][:top]
    dates = pan['dates']
    days = [dt.date.fromordinal(int(d)) for d in dates]
    col = {int(s): j for j, s in enumerate(pan['names'])}
    divs = {int(k): [dt.date.fromisoformat(x) for x in v] for k, v in meta['dividends'].items()}
    cache = {}

    def chain_at(secid, t):
        y = days[t].year
        if y not in cache:
            if len(cache) > 1:
                cache.pop(min(cache))
            p = os.path.join(work, f'quotes_{y}.pkl')
            cache[y] = pickle.load(open(p, 'rb')) if os.path.exists(p) else {}
        return cache[y].get((secid, days[t].isoformat()))

    def term(secid, j, t, fe=None, be=None, k=None):
        chain = chain_at(secid, t)
        spot = pan['close'][t, j]
        if not chain or not np.isfinite(spot) or spot < 10:
            return None
        if fe is None:
            fe, be = pick(chain, days[t], 21, 45, 30), pick(chain, days[t], 50, 100, 75)
            if fe is None or be is None:
                return None
            k = None
            for kk, leg in chain[fe].items():
                if None in (leg[0], leg[1], leg[3], leg[4]) or kk not in chain[be]:
                    continue
                if k is None or abs(kk - spot) < abs(k - spot):
                    k = kk
            if k is None:
                return None
        qs = legs4(chain, fe, be, k)
        if qs is None:
            return None
        tf = max((dt.date.fromisoformat(fe) - days[t]).days, 1) / 365
        tb = max((dt.date.fromisoformat(be) - days[t]).days, 1) / 365
        v = ivs(qs, spot, k, tf, tb)
        if v is None:
            return None
        return {'fe': fe, 'be': be, 'k': k, 'qs': qs, 'iv': v, 'slope': (v[2] + v[3]) / (v[0] + v[1])}

    cands = []
    for t in range(len(days)):
        if days[t].year < 2016:
            continue
        for secid in names:
            j = col.get(secid)
            if j is None:
                continue
            x = term(secid, j, t)
            if x is None or not liquid(x['qs']):
                continue
            bed = dt.date.fromisoformat(x['be'])
            if secid != SPY and any(days[t] < d <= bed for d in divs.get(secid, [])):
                continue
            path = []
            for s in range(t + 1, min(len(days), t + LOOK + 1)):
                y = term(secid, j, s, x['fe'], x['be'], x['k'])
                path.append(None if y is None else {'mids': [(b + a) / 2 for b, a, _ in y['qs']],
                                                    'halfs': [(a - b) / 2 for b, a, _ in y['qs']], 'slope': y['slope']})
            cands.append({'t': t, 'j': j, 'secid': secid, 'k': x['k'], 'fe': x['fe'], 'be': x['be'], 'slope': x['slope'],
                          'iv': x['iv'], 'mids': [(b + a) / 2 for b, a, _ in x['qs']], 'halfs': [(a - b) / 2 for b, a, _ in x['qs']],
                          'path': path})
        if t % 250 == 0:
            print(days[t], len(cands), flush=True)
    pickle.dump(cands, open(os.path.join(work, 'carry_cands.pkl'), 'wb'), protocol=pickle.HIGHEST_PROTOCOL)
    print('candidates', len(cands))


def rules():
    return [(d, ex, h) for d in ('long_calendar', 'short_calendar') for ex in ('time5', 'time10', 'revert') for h in ('hedged', 'unhedged')]


def simulate(cands, rule, pan, ins):
    d, ex, hedge = rule
    rel, close, dates = pan['rel'], pan['close'], pan['dates']
    days = [dt.date.fromordinal(int(x)) for x in dates]
    by = {}
    for c in cands:
        by.setdefault(c['j'], []).append(c)
    trades = []
    for j, cs in by.items():
        cs.sort(key=lambda c: c['t'])
        hist, busy = [], -1
        for c in cs:
            past = [s for tt, s in hist if c['t'] - 252 <= tt < c['t']]
            pct = np.mean(np.array(past) <= c['slope']) if len(past) >= 60 else np.nan
            hist.append((c['t'], c['slope']))
            if c['t'] <= busy or not np.isfinite(pct) or not ins(c):
                continue
            if not ((d == 'long_calendar' and pct <= 0.2) or (d == 'short_calendar' and pct >= 0.8)):
                continue
            # sign per leg: long_calendar = sell front (legs 0,1), buy back (legs 2,3)
            w = np.array([-1, -1, 1, 1]) if d == 'long_calendar' else np.array([1, 1, -1, -1])
            maxk = 5 if ex == 'time5' else 10
            exit_k = None
            for k, p in enumerate(c['path'], start=1):
                s = c['t'] + k
                stop = k >= maxk or (s + 1 < rel.shape[0] and rel[s + 1, j])
                if ex == 'revert' and p is not None:
                    pnow = np.mean(np.array([x for tt, x in hist if c['t'] - 252 <= tt < c['t']]) <= p['slope'])
                    stop = stop or (d == 'long_calendar' and pnow >= 0.5) or (d == 'short_calendar' and pnow <= 0.5)
                if stop and p is not None:
                    exit_k = k
                    break
            if exit_k is None:
                continue
            p = c['path'][exit_k - 1]
            m0, m1 = np.array(c['mids']), np.array(p['mids'])
            h0, h1 = np.array(c['halfs']), np.array(p['halfs'])
            gross_legs = w * (m1 - m0)
            hp = hc = 0.0
            if hedge == 'hedged':
                s1 = c['t'] + exit_k
                path = close[c['t']:s1 + 1, j]
                net = np.zeros(len(path) - 1)
                for wi, iv, cp, exd in zip(w, c['iv'], ('C', 'P', 'C', 'P'), (c['fe'], c['fe'], c['be'], c['be'])):
                    T = np.array([max((dt.date.fromisoformat(exd) - days[s]).days, 0) / 365 for s in range(c['t'], s1 + 1)])
                    net += wi * O.deltas(path[:-1], c['k'], T[:-1], iv, cp)
                hp = float(-np.sum(net * np.diff(path)))
                tr = np.abs(np.diff(np.concatenate([[0.0], net, [0.0]])))  # stock traded = change in the NET delta
                hc = float(O.HEDGE_COST * np.sum(tr * np.concatenate([path[:-1], [path[-1]]])))
            base = m0.sum()
            trades.append({'tday': dates[c['t']], 'spy': c['secid'] == SPY, 'hold': exit_k,
                           'front': gross_legs[:2].sum() / base, 'back': gross_legs[2:].sum() / base, 'hedge': hp / base,
                           'gross_mid': (gross_legs.sum() + hp) / base, 'spread': (h0.sum() + h1.sum()) / base,
                           'fees': 2 * FEE4 / base, 'hcost': hc / base})
            busy = c['t'] + exit_k
    return trades


def summarize(tr):
    from .explore5 import stats
    if len(tr) < 10:
        return {'n': len(tr)}
    g, sp, fe, hc = (np.array([t[k] for t in tr]) for k in ('gross_mid', 'spread', 'fees', 'hcost'))
    days = [t['tday'] for t in tr]
    lv = {'mid': g - fe - hc, 'c25': g - 0.25 * sp - fe - hc, 'full': g - sp - fe - hc}
    out = {k: stats(v, days) for k, v in lv.items()}
    yrs = np.array([dt.date.fromordinal(int(d)).year for d in days])
    out['by_year_c25'] = {str(y): float(lv['c25'][yrs == y].mean()) for y in sorted(set(yrs))}
    out['attribution_mean'] = {k: float(np.mean([t[k] for t in tr])) for k in ('front', 'back', 'hedge', 'gross_mid', 'spread', 'fees', 'hcost')}
    out['mean_hold'] = float(np.mean([t['hold'] for t in tr]))
    out['spy_n'] = int(sum(t['spy'] for t in tr))
    return out


def main():
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument('mode', choices=['build', 'dev', 'final'])
    ap.add_argument('--work', default='../wrds_studies/research8_daily_work')
    ap.add_argument('--top', type=int, default=10)
    ap.add_argument('--docs', default='docs/research8/carry')
    a = ap.parse_args()
    if a.mode == 'build':
        build(a.work, a.top)
        return
    pan = P.load(os.path.join(a.work, 'panel_ext.npz'))
    cands = pickle.load(open(os.path.join(a.work, 'carry_cands.pkl'), 'rb'))
    D = lambda c: dt.date.fromordinal(int(pan['dates'][c['t']]))
    E = lambda c: dt.date.fromordinal(int(pan['dates'][min(c['t'] + LOOK, len(pan['dates']) - 1)]))
    if a.mode == 'dev':
        rl, ins = rules(), (lambda c: D(c) <= DEV_END and E(c) <= DEV_END)
    else:
        path = os.path.join(HERE, 'carry_frozen.json')
        if not R2.committed(path):
            raise SystemExit('final needs a committed research8/carry_frozen.json')
        rl, ins = [tuple(x) for x in json.load(open(path))['rules']], (lambda c: D(c) >= TEST_START)
    res = {'|'.join(r): summarize(simulate(cands, r, pan, ins)) for r in rl}
    ok = {k: v for k, v in res.items() if 'c25' in v and 'mean' in v['c25']}
    out = {'sample': a.mode, 'rules': res}
    if a.mode == 'dev':
        elig = [k for k, v in ok.items() if v['c25']['n'] >= 150 and v['c25']['t'] >= 3 and v['c25']['sharpe'] > 0.8
                and np.mean([x for y, x in v['by_year_c25'].items() if int(y) <= 2018] or [-1]) > 0
                and np.mean([x for y, x in v['by_year_c25'].items() if int(y) >= 2019] or [-1]) > 0]
        picks, used = [], set()
        for k in sorted(elig, key=lambda k: -ok[k]['c25']['sharpe']):
            r = k.split('|')
            if r[0] not in used:
                used.add(r[0])
                picks.append(r)
        out.update(eligible=len(elig), freeze_picks=picks)
        print('eligible', len(elig), 'picks', picks)
    else:
        out['gates'] = {}
        for k, v in ok.items():
            yrs = v['by_year_c25']
            g = {'t': v['c25']['t'] >= 2, 'sharpe': v['c25']['sharpe'] >= 1, 'full_positive': v['full']['mean'] > 0,
                 'years': sum(yrs.get(str(y), -1) > 0 for y in (2022, 2023, 2024, 2025)) >= 3}
            g['strong'] = all(g.values())
            out['gates'][k] = g
            print('GATE', k, g)
    os.makedirs(a.docs, exist_ok=True)
    json.dump(out, open(os.path.join(a.docs, f'{a.mode}.json'), 'w'), indent=1)
    from . import registry
    registry.add([{'name': f'carry|{a.mode}|{k}', 'family': f'carry_{a.mode}', 'n': v['c25']['n'], 'mean': v['c25']['mean'],
                   't': v['c25']['t'], 'sharpe': v['c25']['sharpe'], 'source': f'docs/research8/carry/{a.mode}.json',
                   'basis': '25% half-spread'} for k, v in ok.items()])
    for k, v in sorted(ok.items(), key=lambda kv: -kv[1]['c25']['sharpe']):
        at = v['attribution_mean']
        print(f"{k}: n={v['c25']['n']} mid {100 * v['mid']['mean']:+.2f}% c25 {100 * v['c25']['mean']:+.2f}% full {100 * v['full']['mean']:+.2f}% "
              f"t {v['c25']['t']:+.2f} SR {v['c25']['sharpe']:+.2f} hold {v['mean_hold']:.1f} | front {100 * at['front']:+.2f} "
              f"back {100 * at['back']:+.2f} hedge {100 * at['hedge']:+.2f} spread {100 * at['spread']:.2f} fees {100 * at['fees']:.2f}")


if __name__ == '__main__':
    main()

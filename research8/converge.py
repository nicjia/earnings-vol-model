"""Convergence engine on the daily panel (pre-registered in protocol_converge.json).

python -m research8.converge paths --work ../wrds_studies/research8_daily_work     # candidates, quote paths, fair values
python -m research8.converge dev   --work ...                                     # 32 rules on dev, attribution, freeze
python -m research8.converge final --work ...                                     # needs committed research8/converge_frozen.json

Frequency-agnostic by design: a 'snapshot' is any (time index, name); the daily panel uses sessions. A 30-minute
source plugs in by supplying the same arrays (quotes per snapshot, fair value per snapshot).
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
from .daily import choose_expiry, SPY

HERE = os.path.dirname(os.path.abspath(__file__))
MODEL = 'HAR_FHS_shrunk'
LOOKAHEAD = 15          # sessions of quote/fair path kept after each candidate entry (>= max_hold + slack)
DEV_END, TEST_START = dt.date(2021, 12, 31), dt.date(2022, 1, 3)
FEE = 2 * R2.FEE_PER_SHARE   # two legs, one side, per share


def quote_pair(chain, ex, k):
    out = []
    for cp in ('C', 'P'):
        q = O.leg_quote(chain, (ex, k, cp, 1, 'core')) if chain else None
        if q is None:
            return None
        out.append(q)
    return out


def liquid(qs):
    for b, a, oi in qs:
        m = (b + a) / 2
        if b <= 0 or m < O.MIN_MID or oi < O.MIN_OI or (a - b) / m > O.SPREAD_LIMIT:
            return False
    return True


def build_paths(work, top=None):
    """Per name and session: the candidate straddle, plus quote and spot paths for LOOKAHEAD sessions.
    top: keep SPY plus the `top` most liquid panel names (by research8_phase2/liquid50.json order)."""
    pan = P.load(os.path.join(work, 'panel_ext.npz'))
    meta = json.load(open(os.path.join(work, 'meta.json')))
    if top:
        order = json.load(open(os.path.join(os.path.dirname(work), 'research8_phase2', 'liquid50.json')))
        keep = [s for s in order if s in set(meta['secids'])][:top]
        meta['secids'] = [SPY] + [s for s in keep if s != SPY]
    dates = pan['dates']
    days = [dt.date.fromordinal(int(d)) for d in dates]
    col = {int(s): j for j, s in enumerate(pan['names'])}
    divs = {int(k): [dt.date.fromisoformat(x) for x in v] for k, v in meta['dividends'].items()}
    years = sorted({d.year for d in days if d.year >= 2016})
    cache = {}

    def chain_at(secid, t):
        y = days[t].year
        if y not in cache:
            if len(cache) > 1:
                cache.pop(min(cache))
            p = os.path.join(work, f'quotes_{y}.pkl')
            cache[y] = pickle.load(open(p, 'rb')) if os.path.exists(p) else {}
        return cache[y].get((secid, days[t].isoformat()))

    cands = []
    for t in range(len(days)):
        if days[t].year < 2016:
            continue
        for secid in meta['secids']:
            j = col.get(secid)
            if j is None:
                continue
            spot = pan['close'][t, j]
            chain = chain_at(secid, t)
            if not chain or not np.isfinite(spot) or spot < 10:
                continue
            ex = choose_expiry(chain, days[t])
            if ex is None:
                continue
            exd = dt.date.fromisoformat(ex)
            if secid != SPY and any(days[t] < d <= exd for d in divs.get(secid, [])):
                continue
            te = int(np.searchsorted(dates, exd.toordinal(), 'right')) - 1
            if te <= t + 5:
                continue
            atm = None
            for k, leg in chain[ex].items():
                if None in (leg[0], leg[1], leg[3], leg[4]):
                    continue
                if atm is None or abs(k - spot) < abs(atm - spot):
                    atm = k
            qs = quote_pair(chain, ex, atm) if atm is not None else None
            if qs is None or not liquid(qs):
                continue
            ivs = [O.implied_vol((b + a) / 2, spot, atm, (te - t) / 252.0, cp) for (b, a, _), cp in zip(qs, 'CP')]
            if None in ivs:
                continue
            cands.append({'t': t, 'j': j, 'secid': secid, 'ex': ex, 'te': te, 'K': atm, 'iv': ivs})
        if t % 250 == 0:
            print(days[t], 'candidates', len(cands), flush=True)
    # quote paths (same contract) for LOOKAHEAD sessions
    for c in cands:
        path = []
        for s in range(c['t'], min(c['te'], c['t'] + LOOKAHEAD) + 1):
            qs = quote_pair(chain_at(c['secid'], s), c['ex'], c['K'])
            path.append(None if qs is None else (sum((b + a) / 2 for b, a, _ in qs), sum((a - b) / 2 for b, a, _ in qs)))
        c['qpath'] = path
    return pan, cands


def fair_values(pan, cands):
    """Model straddle value for every (snapshot, contract) on every candidate path."""
    from .phase1 import Prepared, YearModel
    from .value2 import nearest_h, leg_values
    req = {}
    for c in cands:
        for k in range(len(c['qpath'])):
            s = c['t'] + k
            req.setdefault((s, c['j'], c['te'], c['K']), None)
    keys = list(req)
    ts = np.array([k[0] for k in keys])
    js = np.array([k[1] for k in keys])
    uniq = sorted(set(zip(ts.tolist(), js.tolist())))
    prep = Prepared(pan, extra=(np.array([u[0] for u in uniq]), np.array([u[1] for u in uniq])))
    pos = {(int(prep.t[i]), int(prep.j[i])): i for i in np.where(prep.kind == 2)[0]}
    names = np.arange(len(pan['names']))
    orig = names[pan['group'] == 'original']
    allnames = names[np.isin(pan['group'], ['original', 'expanded_2017', 'added_2020'])]
    years = np.array([dt.date.fromordinal(int(pan['dates'][t])).year for t in ts])
    out = np.full(len(keys), np.nan)
    for y in sorted(set(years.tolist())):
        ym = YearModel(prep, int(y), orig if y <= 2021 else allnames, print, gbq=False)
        rng = np.random.default_rng(20261011 + y)
        ri = np.array([i for i in np.where(years == y)[0] if (keys[i][0], keys[i][1]) in pos])
        if len(ri) == 0:
            continue
        idx = np.array([pos[(keys[i][0], keys[i][1])] for i in ri])
        h = np.array([keys[i][2] - keys[i][0] for i in ri], float)
        hb = nearest_h(h)
        spot = pan['close'][[keys[i][0] for i in ri], [keys[i][1] for i in ri]]
        K = np.array([keys[i][3] for i in ri])
        for b in np.unique(hb):
            s = hb == b
            Q = ym.quantiles(MODEL, idx[s], h[s], rng, hb=int(b))
            vc, vp = leg_values(Q, spot[s], [(K[s], 'C'), (K[s], 'P')])
            out[ri[s]] = vc + vp
        print(y, 'fair values', len(ri), flush=True)
    return {k: v for k, v in zip(keys, out)}


def paths(work, top=None):
    pan, cands = build_paths(work, top)
    fair = fair_values(pan, cands)
    for c in cands:
        c['fpath'] = [fair.get((c['t'] + k, c['j'], c['te'], c['K']), np.nan) for k in range(len(c['qpath']))]
    pickle.dump(cands, open(os.path.join(work, 'converge_paths.pkl'), 'wb'), protocol=pickle.HIGHEST_PROTOCOL)
    print('candidates', len(cands))


# ---------------------------------------------------------------------------- simulation
def rules():
    return [(d, e, tg, mh, hd) for d in ('buy_cheap', 'sell_rich') for e in ('pct', 'pct_edge') for tg in ('full', 'half')
            for mh in (5, 10) for hd in ('hedged', 'unhedged')]


def rname(r):
    return '|'.join(map(str, r))


def add_percentiles(cands):
    by = {}
    for i, c in enumerate(cands):
        by.setdefault(c['j'], []).append(i)
    for idx in by.values():
        idx.sort(key=lambda i: cands[i]['t'])
        hist = []
        for i in idx:
            c = cands[i]
            m0, f0 = c['qpath'][0][0], c['fpath'][0]
            c['rho'] = m0 / f0 if np.isfinite(f0) and f0 > 0 else np.nan
            past = [x for tt, x in hist if c['t'] - 252 <= tt < c['t']]
            c['pct'] = (np.mean(np.array(past) <= c['rho']) if len(past) >= 60 and np.isfinite(c['rho']) else np.nan)
            if np.isfinite(c['rho']):
                hist.append((c['t'], c['rho']))


def simulate(cands, rule, pan, rel, in_sample):
    d, entry, target, max_hold, hedge = rule
    sgn = 1 if d == 'buy_cheap' else -1
    close = pan['close']
    trades, busy_until = [], {}
    for c in sorted((c for c in cands if in_sample(c)), key=lambda c: (c['j'], c['t'])):
        if c['t'] <= busy_until.get(c['j'], -1) or not np.isfinite(c.get('pct', np.nan)):
            continue
        m0, h0 = c['qpath'][0]
        f0 = c['fpath'][0]
        if d == 'buy_cheap':
            ok = c['pct'] <= 0.25 and (entry == 'pct' or f0 >= m0 + h0 + FEE)
        else:
            ok = c['pct'] >= 0.75 and (entry == 'pct' or m0 - h0 >= f0 + FEE)
        if not ok:
            continue
        gap0 = f0 - m0
        exit_k, reason = None, None
        for k in range(1, len(c['qpath'])):
            s = c['t'] + k
            q, f = c['qpath'][k], c['fpath'][k]
            if c['te'] - s <= 5:
                reason = 'expiry_guard'
            elif s + 1 < rel.shape[0] and rel[s + 1, c['j']]:
                reason = 'event_guard'
            elif k >= max_hold:
                reason = 'time_stop'
            if q is not None and np.isfinite(f):
                mid, half = q
                execp = mid - half if sgn > 0 else mid + half
                goal = f if target == 'full' else m0 + 0.5 * gap0
                if (sgn > 0 and execp >= goal) or (sgn < 0 and execp <= goal):
                    reason = reason or 'converged'
            if reason and q is not None and np.isfinite(f):
                exit_k = k
                break
            if reason and q is None:
                reason = None if k < len(c['qpath']) - 1 else reason
        if exit_k is None:
            continue
        s1 = c['t'] + exit_k
        m1, h1 = c['qpath'][exit_k]
        f1 = c['fpath'][exit_k]
        hp = 0.0
        hc = 0.0
        if hedge == 'hedged':
            path = close[c['t']:s1 + 1, c['j']]
            tau = (c['te'] - np.arange(c['t'], s1 + 1)) / 252.0
            net = sum(O.deltas(path[:-1], c['K'], tau[:-1], iv, cp) for iv, cp in zip(c['iv'], 'CP'))
            hp = float(-np.sum(net * np.diff(path)))
            tr = np.abs(np.diff(np.concatenate([[0.0], net, [0.0]])))  # stock traded = change in the NET delta
            hc = float(O.HEDGE_COST * np.sum(tr * np.concatenate([path[:-1], [path[-1]]])))
        gross = sgn * (m1 - m0 + hp)
        trades.append({'j': c['j'], 'spy': c['secid'] == SPY, 'tday': pan['dates'][c['t']], 'hold': exit_k, 'reason': reason,
                       'm0': m0, 'gap0': sgn * gap0 / m0, 'conv': sgn * ((m1 - f1) - (m0 - f0)) / m0,
                       'drift': sgn * (f1 - f0) / m0, 'hedge': sgn * hp / m0, 'spread': (h0 + h1) / m0,
                       'fees': 2 * FEE / m0, 'hcost': hc / m0, 'gross_mid': gross / m0})
        busy_until[c['j']] = s1
    return trades


def summarize(tr):
    from .explore5 import stats
    if len(tr) < 10:
        return {'n': len(tr)}
    g = np.array([t['gross_mid'] for t in tr])
    sp, fe, hc = (np.array([t[k] for t in tr]) for k in ('spread', 'fees', 'hcost'))
    days = [t['tday'] for t in tr]
    levels = {'mid': g - fe - hc, 'c25': g - 0.25 * sp - fe - hc, 'full': g - sp - fe - hc}
    out = {lv: stats(v, days) for lv, v in levels.items()}
    yrs = np.array([dt.date.fromordinal(int(d)).year for d in days])
    out['by_year_c25'] = {str(y): float(levels['c25'][yrs == y].mean()) for y in sorted(set(yrs))}
    out['attribution_mean'] = {k: float(np.mean([t[k] for t in tr])) for k in
                               ('gap0', 'conv', 'drift', 'hedge', 'gross_mid', 'spread', 'fees', 'hcost')}
    out['exit_reasons'] = {r: float(np.mean([t['reason'] == r for t in tr])) for r in
                           ('converged', 'time_stop', 'event_guard', 'expiry_guard')}
    out['mean_hold'] = float(np.mean([t['hold'] for t in tr]))
    out['spy_n'] = int(sum(t['spy'] for t in tr))
    return out


def main():
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument('mode', choices=['paths', 'dev', 'final'])
    ap.add_argument('--work', default='../wrds_studies/research8_daily_work')
    ap.add_argument('--docs', default='docs/research8/converge')
    ap.add_argument('--top', type=int, default=10, help='SPY plus this many most liquid names')
    a = ap.parse_args()
    if a.mode == 'paths':
        paths(a.work, a.top)
        return
    pan = P.load(os.path.join(a.work, 'panel_ext.npz'))
    cands = pickle.load(open(os.path.join(a.work, 'converge_paths.pkl'), 'rb'))
    add_percentiles(cands)
    rel = pan['rel']
    D = lambda c: dt.date.fromordinal(int(pan['dates'][c['t']]))
    E = lambda c: dt.date.fromordinal(int(pan['dates'][min(c['t'] + LOOKAHEAD, len(pan['dates']) - 1)]))
    if a.mode == 'dev':
        rl, ins = rules(), (lambda c: D(c) <= DEV_END and E(c) <= DEV_END)
    else:
        path = os.path.join(HERE, 'converge_frozen.json')
        if not R2.committed(path):
            raise SystemExit('final needs a committed research8/converge_frozen.json')
        rl, ins = [tuple(x) for x in json.load(open(path))['rules']], (lambda c: D(c) >= TEST_START)
    res = {}
    for r in rl:
        res[rname(r)] = summarize(simulate(cands, r, pan, rel, ins))
    out = {'sample': a.mode, 'rules': res}
    ok = {k: v for k, v in res.items() if 'c25' in v and 'mean' in v['c25']}
    if a.mode == 'dev':
        elig = [k for k, v in ok.items() if v['c25']['n'] >= 150 and v['c25']['t'] >= 3.0 and v['c25']['sharpe'] > 0.8
                and np.mean([x for y, x in v['by_year_c25'].items() if int(y) <= 2018] or [-1]) > 0
                and np.mean([x for y, x in v['by_year_c25'].items() if int(y) >= 2019] or [-1]) > 0]
        picks, used = [], set()
        for k in sorted(elig, key=lambda k: -ok[k]['c25']['sharpe']):
            r = k.split('|')
            if (r[0], r[4]) in used:
                continue
            used.add((r[0], r[4]))
            picks.append([r[0], r[1], r[2], int(r[3]), r[4]])
            if len(picks) == 3:
                break
        out.update(eligible=len(elig), freeze_picks=picks)
        print('eligible', len(elig), 'picks', picks)
    else:
        gates = {}
        for k, v in ok.items():
            yrs = v['by_year_c25']
            g = {'t': v['c25']['t'] >= 2.0, 'sharpe': v['c25']['sharpe'] >= 1.0, 'full_positive': v['full']['mean'] > 0,
                 'years': sum(yrs.get(str(y), -1) > 0 for y in (2022, 2023, 2024, 2025)) >= 3}
            g['strong'] = all(g.values())
            gates[k] = g
            print('GATE', k, g)
        out['gates'] = gates
    os.makedirs(a.docs, exist_ok=True)
    json.dump(out, open(os.path.join(a.docs, f'{a.mode}.json'), 'w'), indent=1)
    from . import registry
    registry.add([{'name': f'converge|{a.mode}|{k}', 'family': f'converge_{a.mode}', 'n': v['c25']['n'], 'mean': v['c25']['mean'],
                   't': v['c25']['t'], 'sharpe': v['c25']['sharpe'], 'source': f'docs/research8/converge/{a.mode}.json',
                   'basis': '25% half-spread'} for k, v in ok.items()])
    for k, v in sorted(ok.items(), key=lambda kv: -kv[1]['c25']['sharpe']):
        at = v['attribution_mean']
        er = v['exit_reasons']
        print(f"{k}: n={v['c25']['n']} mid {100 * v['mid']['mean']:+.1f}% c25 {100 * v['c25']['mean']:+.1f}% full {100 * v['full']['mean']:+.1f}% "
              f"t {v['c25']['t']:+.2f} SR {v['c25']['sharpe']:+.2f} hold {v['mean_hold']:.1f} | gap0 {100 * at['gap0']:+.1f} "
              f"conv {100 * at['conv']:+.1f} drift {100 * at['drift']:+.1f} hedge {100 * at['hedge']:+.1f} spread {100 * at['spread']:.1f} "
              f"fees {100 * at['fees']:.1f} | conv'd {er['converged']:.2f} time {er['time_stop']:.2f} event {er['event_guard']:.2f}")


if __name__ == '__main__':
    main()

"""Exploratory pilot of five earnings ideas on the 50 most liquid names (aggregates only).

python -m research8.explore5

EXPLORATORY: these observations were inspected in earlier rounds, so nothing here is a test. Midpoint fills are the
primary assumption; fees and spread costs are reported separately. Signal exits execute at the next close observed.
  1 continuation vs reversal after large release moves (stock; option debit verticals)
  2 post-release volatility persistence vs normalization (straddles at Q / Q+1 vs the stock-only model)
  3 delta-hedged pre-release straddles/strangles (P-4 / P-1 -> P, hedged vs unhedged)
  4 separate upside / downside tails (buy the wing the name's history favours, through the release)
  5 surprise-confirmed drift (SUE extreme agrees with the reaction; stock and option verticals)
"""
import datetime as dt
import glob
import json
import os
import pickle

import numpy as np

from . import panel as P
from . import rules2 as R2
from . import stockev as SE

W = '../wrds_studies'
STOCK_FEE_BP = 5  # per side


def stats(ret, days):
    """n, mean, weekly-clustered t, annual Sharpe of the weekly series (inactive weeks 0), hit rate."""
    ret = np.asarray(ret, float)
    if len(ret) < 10:
        return {'n': int(len(ret))}
    wk = np.asarray([(int(d) - 1) // 7 for d in days], dtype=int)
    u, inv = np.unique(wk, return_inverse=True)
    wmean = np.bincount(inv, ret) / np.bincount(inv)
    full = np.zeros(u.max() - u.min() + 1)
    full[u - u.min()] = wmean
    t = wmean.mean() / (wmean.std(ddof=1) / np.sqrt(len(wmean))) if len(wmean) > 2 and wmean.std() > 0 else 0.0
    sr = full.mean() / full.std(ddof=1) * np.sqrt(52) if full.std() > 0 else 0.0
    return {'n': int(len(ret)), 'mean': float(ret.mean()), 't': float(t), 'sharpe': float(sr), 'hit': float(np.mean(ret > 0))}


def line(label, s, unit):
    if 'mean' not in s:
        return f'  {label}: n={s["n"]} (too few)'
    m = s['mean'] * (1e4 if unit == 'bp' else 100)
    return f"  {label}: n={s['n']} mean {m:+.1f}{unit} t {s['t']:+.2f} SR {s['sharpe']:+.2f} hit {s['hit']:.2f}"


def split_report(out, key, label, ret, days, unit):
    days = np.asarray(days)
    yrs = np.array([dt.date.fromordinal(int(d)).year for d in days]) if len(days) else np.array([])
    res = {'all': stats(ret, days)}
    for name, (a, b) in (('2018-21', (2018, 2021)), ('2022-25', (2022, 2025))):
        m = (yrs >= a) & (yrs <= b)
        res[name] = stats(np.asarray(ret)[m], days[m])
    out[key] = res
    print(line(label + ' [all]', res['all'], unit) + ' |' + line('18-21', res['2018-21'], unit)[1:] + ' |' + line('22-25', res['2022-25'], unit)[1:])


def load_r7(liquid):
    recs = []
    for f in sorted(glob.glob(os.path.join(W, 'research8_sport_bcd', 'records_[ABCD].pkl'))) + [os.path.join(W, 'research8_sport', 'records_E.pkl')]:
        d = pickle.load(open(f, 'rb'))
        recs += [r for r in (d['records'] if isinstance(d, dict) else d) if r.get('status') == 'closed' and r['secid'] in liquid]
    return recs


def main():
    liquid = set(json.load(open(os.path.join(W, 'research8_phase2', 'liquid50.json'))))
    out = {'status': 'exploratory pilot on the 50 most liquid names; observations previously inspected'}
    pan = P.load(os.path.join(W, 'research8_phase1', 'panel.npz'))
    dates = pan['dates']
    names = pan['names']
    rows, car, bad = SE.build(pan, [os.path.join(W, 'research7_cache'), os.path.join(W, 'research7_cache_e')])
    # SUE percentile cutoffs use every panel name's events (cross-sectional distribution only, no outcomes)
    all_cuts = SE.sue_cutoffs(rows, dates, np.ones(len(rows), bool))
    keep = [i for i, x in enumerate(rows) if int(names[x['j']]) in liquid and dt.date.fromordinal(int(dates[x['Q']])).year >= 2015]
    cuts = [all_cuts[i] for i in keep]
    rows = [rows[i] for i in keep]
    fee = 2 * STOCK_FEE_BP / 1e4
    r7 = load_r7(liquid)
    print(f'liquid names: {len(liquid)}; release events (2015+): {len(rows)}; research7 option records: {len(r7)}')

    # ---------------- 1. continuation vs reversal
    print('\n1. CONTINUATION vs REVERSAL after large release moves (|J| >= 1.5 x name RMS of last 8 release moves)')
    print(' stock, abnormal return from the Q close, mid; fees 5 bp/side shown separately:')
    for h in (2, 5, 10):
        rr, dd = [], []
        for x in rows:
            if np.isfinite(x['JZ']) and abs(x['JZ']) >= 1.5 and np.isfinite(x['J']):
                w = SE.window_ret(car, bad, x['j'], x['Q'], x['Q'] + h)
                if np.isfinite(w):
                    rr.append(np.sign(x['J']) * w)
                    dd.append(dates[x['Q']])
        rr = np.array(rr)
        split_report(out, f'1_stock_cont_h{h}', f'continue h={h}', rr, dd, 'bp')
        split_report(out, f'1_stock_rev_h{h}', f'reverse  h={h}', -rr, dd, 'bp')
        print(f'    fees cost {fee * 1e4:.0f} bp per trade either way')
    print(' options, debit verticals from Q (research7 builders), per risk; ret_mid includes $0.65/contract fees:')
    for fam, lab in (('post:post_momentum_vertical', 'continue'), ('post:post_reversal_vertical', 'reverse ')):
        for ex in ('Q+2', 'Q+4'):
            for cond, f in (('all moves', lambda r: True), ('|J|>=M', lambda r: (r.get('f_JM') or 0) >= 1.0)):
                sel = [r for r in r7 if r['family'] == fam and r['exit'] == ex and f(r)]
                gross = [(r['pnl_mid'] + r['fees']) / r['risk'] for r in sel]
                dd = [r['entry_day'].toordinal() for r in sel]
                split_report(out, f'1_opt_{lab.strip()}_{ex}_{cond}', f'{lab} {ex} {cond} gross-mid', gross, dd, '%')
                s25 = stats([r['ret_c25'] for r in sel], dd)
                print('     ' + line('same, after fees + 25% half-spread', s25, '%')[2:])

    # ---------------- 2. post-release vol persistence vs normalization
    print('\n2. POST-RELEASE VOLATILITY: straddles bought/sold at Q or Q+1, held to expiry, vs the stock-only model')
    recs = pickle.load(open(os.path.join(W, 'research8_phase2', 'records.pkl'), 'rb'))
    vals = pickle.load(open(os.path.join(W, 'research8_phase2', 'values.pkl'), 'rb'))
    f = R2.frame(recs, vals, 'HAR_FHS_shrunk', dates)
    liq = np.array([r['secid'] in liquid for r in recs])
    jz = {}
    for x in rows:
        jz[(int(names[x['j']]), dates[x['Q']])] = x['JZ']
    bigmove = np.array([abs(jz.get((r['secid'], dates[r['t']] if r['label'] == 'Q' else dates[r['t'] - 1]), np.nan)) >= 1.5
                        for r in recs])
    for lab in ('Q', 'Q+1'):
        for hedge in (True, False):
            base = liq & (f['label'] == lab) & (f['structure'] == 'straddle') & np.isfinite(f['rho'])
            for name, m, d in (('persist: buy, rho<=0.9', base & (f['rho'] <= 0.9), 1),
                               ('persist: buy after big move', base & bigmove, 1),
                               ('normalize: sell, rho>=1.1', base & (f['rho'] >= 1.1), -1),
                               ('normalize: sell, no big move, rho>=1.1', base & ~bigmove & (f['rho'] >= 1.1), -1)):
                gross = d * (f['payoff'] - f['mkt'] + (f['hedge'] if hedge else 0.0)) / f['mkt']
                net = (d * (f['payoff'] - f['mkt'] + (f['hedge'] if hedge else 0.0)) - 2 * R2.FEE_PER_SHARE
                       - 0.25 * f['half'] - (f['hcost'] if hedge else 0.0)) / f['mkt']
                tag = f'{lab} {"hedged" if hedge else "unhedged"} {name}'
                split_report(out, '2_' + tag, tag + ' gross-mid', gross[m], f['tday'][m], '%')
                print('     ' + line('same, after fees + 25% half-spread (+hedge cost)', stats(net[m], f['tday'][m]), '%')[2:])

    # ---------------- 3. delta-hedged pre-release straddles
    print('\n3. PRE-RELEASE LONG PREMIUM, entry P-4 / P-1, exit at the P close, hedged vs unhedged')
    ex = pickle.load(open(os.path.join(W, 'research8_phase2', 'prerel.pkl'), 'rb'))
    for lab in ('P-4', 'P-1'):
        for st in ('straddle', 'strangle'):
            idx = [i for i, r in enumerate(recs) if r['label'] == lab and r['structure'] == st and r['secid'] in liquid and i in ex]
            for hedge in (False, True):
                g = np.array([(ex[i]['exit_mid'] - f['mkt'][i] + (ex[i]['hedge_to_P'] if hedge else 0)) / f['mkt'][i] for i in idx])
                n25 = np.array([(ex[i]['exit_mid'] - f['mkt'][i] + (ex[i]['hedge_to_P'] - ex[i]['hcost_to_P'] if hedge else 0)
                                 - 0.25 * (f['half'][i] + ex[i]['exit_half']) - 4 * R2.FEE_PER_SHARE) / f['mkt'][i] for i in idx])
                dd = f['tday'][idx]
                tag = f'{lab} {st} {"hedged" if hedge else "unhedged"}'
                split_report(out, '3_' + tag, tag + ' gross-mid', g, dd, '%')
                print('     ' + line('same, after fees + 25% half-spreads (+hedge cost)', stats(n25, dd), '%')[2:])

    # ---------------- 4. separate upside / downside tails
    print('\n4. UPSIDE vs DOWNSIDE TAILS: buy one strangle wing at P, held through the release to expiry')
    hist = {}
    for x in sorted(rows, key=lambda x: x['Q']):
        hist.setdefault(x['j'], []).append((x['Q'], x['J']))
    col = {int(s): j for j, s in enumerate(names)}
    picks = {'history favours up: buy call': [], 'history favours down: buy put': [],
             'control: buy call when history favours down': [], 'control: buy put when history favours up': [],
             'model: buy the wing with model/mid >= 1.1': []}
    pick_days = {k: [] for k in picks}
    pick_net = {k: [] for k in picks}
    for i, r in enumerate(recs):
        if r['label'] != 'P' or r['structure'] != 'strangle' or r['secid'] not in liquid:
            continue
        past = [J for q, J in hist.get(col[r['secid']], []) if q <= r['t'] and np.isfinite(J)][-8:]
        call, put = r['legs']
        legret = {}
        for leg, key in ((call, 'C'), (put, 'P')):
            m = (leg['bid'] + leg['ask']) / 2
            legret[key] = ((leg['payoff'] - m) / m, (leg['payoff'] - m - 0.25 * (leg['ask'] - leg['bid']) / 2 - 2 * R2.FEE_PER_SHARE) / m)
        if len(past) >= 6:
            up = np.mean([max(J, 0) for J in past])
            dn = np.mean([max(-J, 0) for J in past])
            if up >= 1.25 * dn:
                for k, leg in (('history favours up: buy call', 'C'), ('control: buy put when history favours up', 'P')):
                    picks[k].append(legret[leg][0]); pick_net[k].append(legret[leg][1]); pick_days[k].append(f['tday'][i])
            elif dn >= 1.25 * up:
                for k, leg in (('history favours down: buy put', 'P'), ('control: buy call when history favours down', 'C')):
                    picks[k].append(legret[leg][0]); pick_net[k].append(legret[leg][1]); pick_days[k].append(f['tday'][i])
        vc, vp = vals['values']['HAR_FHS_shrunk'][i]
        mc, mp = (call['bid'] + call['ask']) / 2, (put['bid'] + put['ask']) / 2
        for v, mm, leg in ((vc, mc, 'C'), (vp, mp, 'P')):
            if np.isfinite(v) and v / mm >= 1.1:
                k = 'model: buy the wing with model/mid >= 1.1'
                picks[k].append(legret[leg][0]); pick_net[k].append(legret[leg][1]); pick_days[k].append(f['tday'][i])
    for k in picks:
        split_report(out, '4_' + k, k + ' gross-mid', picks[k], pick_days[k], '%')
        print('     ' + line('same, after fees + 25% half-spread', stats(pick_net[k], pick_days[k]), '%')[2:])

    # ---------------- 5. surprise-confirmed drift
    print('\n5. SURPRISE-CONFIRMED DRIFT: SUE in the top/bottom 20% (trailing year) and the reaction agrees')
    for h in (2, 5, 10, 20):
        rr, dd, rd = [], [], []
        for i, x in enumerate(rows):
            lo, hi = cuts[i]
            if not (np.isfinite(x['sue']) and np.isfinite(lo) and np.isfinite(x['J'])):
                continue
            s = 1 if x['sue'] >= hi else -1 if x['sue'] <= lo else 0
            w = SE.window_ret(car, bad, x['j'], x['Q'], x['Q'] + h)
            if s == 0 or not np.isfinite(w):
                continue
            if s == np.sign(x['J']):
                rr.append(s * w); dd.append(dates[x['Q']])
            else:
                rd.append((s * w, dates[x['Q']]))
        split_report(out, f'5_stock_agree_h{h}', f'agree: follow h={h}', rr, dd, 'bp')
        split_report(out, f'5_stock_disagree_h{h}', f'good-news-bad-reaction: follow SUE h={h}', [a for a, _ in rd], [b for _, b in rd], 'bp')
    print(f'    fees cost {fee * 1e4:.0f} bp per trade')
    jsign = {(int(names[x['j']]), int(dates[x['Q']])): np.sign(x['J']) for x in rows if np.isfinite(x['J'])}
    for ex in ('Q+2', 'Q+4'):
        sel = [r for r in r7 if r['family'] == 'post:post_surprise_vertical' and r['exit'] == ex and r.get('f_SUE')
               and np.sign(r['f_SUE']) == jsign.get((r['secid'], r['Q'].toordinal()), 0)]
        dd = [r['entry_day'].toordinal() for r in sel]
        split_report(out, f'5_opt_agree_{ex}', f'option vertical, SUE and reaction agree, exit {ex}, gross-mid',
                     [(r['pnl_mid'] + r['fees']) / r['risk'] for r in sel], dd, '%')
        print('     ' + line('same, after fees + 25% half-spread', stats([r['ret_c25'] for r in sel], dd), '%')[2:])

    os.makedirs('docs/research8/explore5', exist_ok=True)
    json.dump(out, open('docs/research8/explore5/results.json', 'w'), indent=1)


if __name__ == '__main__':
    main()

"""Descriptive report of the S1-S5 (and S+P1) portfolio on research7 records (see protocol_sportfolio.json).

python -m research8.sportfolio --records ../wrds_studies/research8_sport
"""
import argparse
import glob
import json
import os
import pickle

import numpy as np

from research5.candidates import passes
from live.strategies import RULES
from .stockev import block_boot

PRIORITY = ('S2', 'S3', 'S1', 'S4', 'S5', 'P1')


def selected(records, rule_ids):
    out = []
    for r in records:
        if r.get('status') != 'closed':
            continue
        for rid in rule_ids:
            fam, en, ex, flt, tier, _ = RULES[rid]
            if r['family'] == fam and r['entry'] == en and r['exit'] == ex and tier in r['tiers'] and passes(flt, r):
                out.append((rid, r))
    return out


def dedupe(sel):
    best = {}
    for rid, r in sel:
        key = (r['secid'], r['Q'])
        if key not in best or PRIORITY.index(rid) < PRIORITY.index(best[key][0]):
            best[key] = (rid, r)
    return list(best.values())


def weekly_stats(sel, key, rng):
    wk = np.array([(r['entry_day'].toordinal() - 1) // 7 for _, r in sel])
    ret = np.array([r[key] for _, r in sel])
    weeks = np.arange(wk.min(), wk.max() + 1)
    s = np.bincount(wk - weeks[0], ret, minlength=len(weeks))
    c = np.bincount(wk - weeks[0], minlength=len(weeks))
    w = np.where(c > 0, s / np.maximum(c, 1), 0.0)
    boot = block_boot(w, rng)
    sd = w.std(ddof=1)
    eq = np.cumsum(w)
    return {'trades': int(len(ret)), 'mean_trade': float(ret.mean()), 'weekly_mean': float(w.mean()),
            'sharpe': float(w.mean() / sd * np.sqrt(52)) if sd > 0 else 0.0, 't_block': float(w.mean() / boot.std(ddof=1)),
            'active_weeks': float(np.mean(c > 0)), 'max_drawdown_weeks_sum': float(np.max(np.maximum.accumulate(eq) - eq)),
            'worst_week': float(w.min())}


def main():
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument('--records', default='../wrds_studies/research8_sport')
    ap.add_argument('--docs', default='docs/research8/sportfolio')
    a = ap.parse_args()
    rng = np.random.default_rng(20261006)
    out = {'status': 'descriptive, not a test (see research8/protocol_sportfolio.json)'}
    for path in sorted(glob.glob(os.path.join(a.records, 'records_*.pkl'))):
        name = os.path.basename(path)[8:-4]
        if name.endswith('lag'):
            continue
        d = pickle.load(open(path, 'rb'))
        recs = d['records'] if isinstance(d, dict) else d
        for label, ids in (('S', ['S1', 'S2', 'S3', 'S4', 'S5']), ('S+P1', ['S1', 'S2', 'S3', 'S4', 'S5', 'P1'])):
            sel = selected(recs, ids)
            for variant, s in (('all', sel), ('dedupe', dedupe(sel))):
                k = f'{name}|{label}|{variant}'
                out[k] = {c: weekly_stats(s, f'ret_{c}', rng) for c in ('mid', 'c25', 'c50')}
                m = out[k]
                print(f"{k}: trades {m['mid']['trades']} | SR mid {m['mid']['sharpe']:.2f} c25 {m['c25']['sharpe']:.2f} "
                      f"c50 {m['c50']['sharpe']:.2f} | mean trade c25 {m['c25']['mean_trade']:+.3f} | t c25 {m['c25']['t_block']:.2f} "
                      f"| active weeks {m['c25']['active_weeks']:.2f} | maxDD(c25, sum of weekly) {m['c25']['max_drawdown_weeks_sum']:.2f}")
    os.makedirs(a.docs, exist_ok=True)
    json.dump(out, open(os.path.join(a.docs, 'portfolio.json'), 'w'), indent=1)


if __name__ == '__main__':
    main()

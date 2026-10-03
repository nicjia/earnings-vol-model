"""Sharpe ratios, deflated Sharpe ratios (Bailey & Lopez de Prado 2014) and t-statistics for research7 rules.

Weekly series over every calendar week 2018-2025: a week's return is the mean equal-risk return of the
rule's issuer-events whose announcement session falls in that week; weeks without trades are zero.
The DSR benchmark uses the variance of weekly Sharpe ratios across all 1,944 research7 candidates on the
same weeks, with N trials = 1,944 (this round) or 4,062 (research5 + research6 + research7).
"""
import argparse
import datetime as dt
import json
import math
import os
import pickle
from statistics import NormalDist

from research5 import candidates as c5
from research5 import stats

from . import candidates as cand

GAMMA = 0.5772156649
ND = NormalDist()


def weekly_series(trades, weeks, key='ret_mid'):
    sums, counts = {}, {}
    for w, v, _ in stats.issuer_events(trades, key):
        sums[w] = sums.get(w, 0.0) + v
        counts[w] = counts.get(w, 0) + 1
    return [sums[w] / counts[w] if w in sums else 0.0 for w in weeks]


def moments(x):
    n = len(x)
    m = sum(x) / n
    var = sum((v - m) ** 2 for v in x) / (n - 1)
    sd = math.sqrt(var)
    if sd == 0:
        return m, 0.0, 0.0, 3.0
    skew = sum((v - m) ** 3 for v in x) / n / sd ** 3
    kurt = sum((v - m) ** 4 for v in x) / n / sd ** 4
    return m, sd, skew, kurt


def deflated(sr, n_obs, skew, kurt, sr_var, n_trials):
    sr0 = math.sqrt(sr_var) * ((1 - GAMMA) * ND.inv_cdf(1 - 1 / n_trials)
                               + GAMMA * ND.inv_cdf(1 - 1 / (n_trials * math.e)))
    denom = math.sqrt(max(1 - skew * sr + (kurt - 1) / 4 * sr * sr, 1e-12))
    return sr0, ND.cdf((sr - sr0) * math.sqrt(n_obs - 1) / denom), ND.cdf(sr * math.sqrt(n_obs - 1) / denom)


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--results', default='../wrds_studies/research7_results')
    args = parser.parse_args()
    records = []
    for s in 'ABCD':
        with open(os.path.join(args.results, f'records_{s}.pkl'), 'rb') as stream:
            records += pickle.load(stream)['records']
    first, last = dt.date(2018, 1, 1), dt.date(2025, 8, 31)
    weeks, d = [], first - dt.timedelta(days=first.weekday())
    while d <= last:
        weeks.append(stats.week_of(d))
        d += dt.timedelta(days=7)
    by_base = c5.index_records(records)
    grid = cand.grid()
    srs = {}
    for c in grid:
        closed, _ = c5.members_indexed(c, by_base)
        if len(closed) >= 50:
            m, sd, _, _ = moments(weekly_series(closed, weeks))
            if sd > 0:
                srs[c['id']] = m / sd
    sr_values = list(srs.values())
    mu = sum(sr_values) / len(sr_values)
    sr_var = sum((v - mu) ** 2 for v in sr_values) / (len(sr_values) - 1)
    frozen = json.load(open(os.path.join(args.results, 'frozen_policies.json')))
    hyp = json.load(open(os.path.join(os.path.dirname(os.path.abspath(__file__)), 'e_hypotheses.json')))
    rules = [('replication ' + k, v) for k, v in frozen['replications'].items()]
    rules += [('frozen', p['id']) for p in frozen['policies']]
    rules += [('post-hoc', h) for h in hyp['post_hoc_candidates'] if 'double_calendar' in h]
    ids = cand.by_id()
    out = {'weeks': len(weeks), 'candidates_with_50_trades': len(sr_values),
           'trial_weekly_sr_mean': mu, 'trial_weekly_sr_sd': math.sqrt(sr_var), 'rules': []}
    for label, cid in rules:
        closed, _ = c5.members_indexed(ids[cid], by_base)
        row = {'label': label, 'id': cid, 'events': len(stats.issuer_events(closed))}
        for key in ('ret_mid', 'ret_c25'):
            x = weekly_series(closed, weeks, key)
            m, sd, skew, kurt = moments(x)
            sr = m / sd
            sr0_a, dsr_a, psr = deflated(sr, len(x), skew, kurt, sr_var, 1944)
            sr0_b, dsr_b, _ = deflated(sr, len(x), skew, kurt, sr_var, 4062)
            mean, se = stats.cluster_mean_se(stats.issuer_events(closed, key))
            row[key] = {'sharpe_annual': sr * math.sqrt(52), 't_cluster': mean / se, 't_weekly': sr * math.sqrt(len(x)),
                        'psr_vs_0': psr, 'dsr_N1944': dsr_a, 'dsr_N4062': dsr_b,
                        'sr0_annual_N1944': sr0_a * math.sqrt(52), 'sr0_annual_N4062': sr0_b * math.sqrt(52),
                        'skew': skew, 'kurtosis': kurt}
        out['rules'].append(row)
    print(json.dumps({k: v for k, v in out.items() if k != 'rules'}, indent=1))
    print(f"{'rule':78s} {'cost':>4s} {'SR/yr':>6s} {'t_clu':>6s} {'PSR':>5s} {'DSR1944':>7s} {'DSR4062':>7s}")
    for r in out['rules']:
        for key, tag in (('ret_mid', 'mid'), ('ret_c25', '25%')):
            v = r[key]
            print(f"{(r['label'] + ': ' + r['id'])[:78]:78s} {tag:>4s} {v['sharpe_annual']:6.2f} {v['t_cluster']:6.2f} "
                  f"{v['psr_vs_0']:5.2f} {v['dsr_N1944']:7.3f} {v['dsr_N4062']:7.3f}")
    print(f"DSR benchmark (expected max annual SR of noise): N=1944 {out['rules'][0]['ret_mid']['sr0_annual_N1944']:.2f}, "
          f"N=4062 {out['rules'][0]['ret_mid']['sr0_annual_N4062']:.2f}")
    with open(os.path.join(args.results, 'sharpe_dsr.json'), 'w') as stream:
        json.dump(out, stream, indent=1)


if __name__ == '__main__':
    main()

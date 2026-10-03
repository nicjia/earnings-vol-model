"""Out-of-time replication of V1 on CNDR, 1990-2006 (protocol_v1_replication.json).

python -m research8.v1rep --data ../wrds_studies/public
"""
import argparse
import json
import os

import numpy as np
import pandas as pd

from . import putwrite as W


def main():
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument('--data', default='../wrds_studies/public')
    ap.add_argument('--docs', default='docs/research8/putwrite')
    a = ap.parse_args()
    spx, vix, _, tb = W.load(a.data)
    d = pd.read_csv(os.path.join(a.data, 'CNDR.csv'))
    d['DATE'] = pd.to_datetime(d['DATE'])
    cndr = d.set_index('DATE')['CNDR'].astype(float)
    cndr = cndr[cndr.index <= '2006-12-31']
    rolls = W.roll_dates(cndr)
    sig = {'HAR': W.har_sigma(spx), 'EWMA': W.ewma_sigma(spx)}
    rows = []
    for s, e in zip(rolls[:-1], rolls[1:]):
        if s < pd.Timestamp('1990-02-01') or s not in vix.index:
            continue
        rf = tb.asof(s) / 100 * (e - s).days / 360
        rows.append({'start': s, 'end': e, 'ex': cndr[e] / cndr[s] - 1 - rf,
                     'ratio_HAR': vix[s] / 100 / sig['HAR'].asof(s), 'ratio_EWMA': vix[s] / 100 / sig['EWMA'].asof(s)})
    df = pd.DataFrame(rows)
    rng = np.random.default_rng(20261008)
    frozen = ('ratio', 'HAR', 1.5)
    res = {'frozen': W.evaluate(df, frozen, rng), 'always': W.evaluate(df, ('always', None, None), rng)}
    c, b = res['frozen']['c15bp'], res['always']['c15bp']
    gates = {'g1': c['ci'][0] > 0, 'g2': c['sharpe'] >= 1.0, 'g3': c['t_block'] >= 2.0, 'g4': c['sharpe'] > b['sharpe'],
             'g5': c['max_drawdown'] <= b['max_drawdown']}
    gates['passed'] = all(gates.values())
    diag = {W.rname(r): W.evaluate(df, r, rng) for r in W.rules()}
    held = df[df['ratio_HAR'] >= 1.5]
    out = {'months': len(df), 'results': res, 'gates': gates, 'diagnostics_not_selection': diag,
           'held_months_by_year': held['start'].dt.year.value_counts().sort_index().to_dict()}
    os.makedirs(a.docs, exist_ok=True)
    json.dump(out, open(os.path.join(a.docs, 'v1_replication_cndr_1990_2006.json'), 'w'), indent=1, default=str)
    print('months', len(df), 'GATES', gates)
    for k, x in [('frozen HAR>=1.5', res['frozen']), ('always', res['always'])] + list(diag.items()):
        c = x['c15bp']
        print(f"{k}: held {x['months_held']} | 15bp mean {c['mean_month'] * 100:+.2f}%/mo SR {c['sharpe']:.2f} t {c['t_block']:.2f} "
              f"CI [{c['ci'][0] * 100:+.2f},{c['ci'][1] * 100:+.2f}] worst {c['worst_month'] * 100:+.1f}% maxDD {c['max_drawdown'] * 100:.1f}%")
    print('held months by year:', out['held_months_by_year'])


if __name__ == '__main__':
    main()

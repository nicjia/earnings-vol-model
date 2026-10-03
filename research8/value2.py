"""Phase 2 model values: price every record's legs from a phase 1 distribution model (stock data only).

python -m research8.value2 --records ../wrds_studies/research8_phase2/records.pkl --models EWMA_FHS_shrunk,...

For each record the model forecasts the log total return from the decision close to the expiry close (h sessions;
shapes, tables and HAR coefficients from the nearest fitted horizon), centres it so E[exp R] = 1 (forward = spot,
r = 0, no dividends in the window by construction), and values each leg as E[payoff]. Walk-forward exactly as
phase 1: parameters refitted each 1 January from earlier data (original names through 2022, all names after).
"""
import argparse
import datetime as dt
import os
import pickle

import numpy as np

from . import dist
from . import features as F
from . import panel as P
from .phase1 import Prepared, YearModel

HZ = np.array(F.HORIZONS)


def nearest_h(h):
    return HZ[np.argmin(np.abs(np.log(HZ)[None, :] - np.log(np.maximum(h, 1))[:, None]), 1)]


def leg_values(Q, spot, legs):
    q = Q - np.log(np.exp(Q) @ dist.WEIGHTS)[:, None]
    ST = spot[:, None] * np.exp(q)
    out = []
    for k, cp in legs:
        pay = np.maximum(ST - k[:, None], 0) if cp == 'C' else np.maximum(k[:, None] - ST, 0)
        out.append(pay @ dist.WEIGHTS)
    return out


def main():
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument('--records', default='../wrds_studies/research8_phase2/records.pkl')
    ap.add_argument('--panel', default='../wrds_studies/research8_phase1/panel.npz')
    ap.add_argument('--models', required=True)
    ap.add_argument('--out', default='../wrds_studies/research8_phase2/values.pkl')
    a = ap.parse_args()
    models = a.models.split(',')
    recs = pickle.load(open(a.records, 'rb'))
    pan = P.load(a.panel)
    t = np.array([r['t'] for r in recs])
    j = np.array([r['j'] for r in recs])
    prep = Prepared(pan, extra=(t, j))
    xi = np.where(prep.kind == 2)[0]
    # map records to their origin rows (ineligible origins, e.g. < 252 returns, are dropped by Prepared)
    pos = {(int(prep.t[i]), int(prep.j[i])): i for i in xi}
    names = np.arange(len(pan['names']))
    orig = names[pan['group'] == 'original']
    years = np.array([dt.date.fromordinal(int(pan['dates'][x])).year for x in t])
    values = {m: np.full((len(recs), 2), np.nan) for m in models}
    need_gbq = 'GBQ' in models
    for y in sorted(set(years)):
        train = orig if y <= 2022 else names
        ym = YearModel(prep, int(y), train, print, gbq=need_gbq)
        rng = np.random.default_rng(20261004 + int(y))
        ri = np.where(years == y)[0]
        ri = np.array([r for r in ri if (t[r], j[r]) in pos])
        if len(ri) == 0:
            continue
        idx = np.array([pos[(t[r], j[r])] for r in ri])
        h = np.array([recs[r]['h'] for r in ri])
        hb = nearest_h(h)
        spot = np.array([recs[r]['spot'] for r in ri])
        for b in np.unique(hb):
            sel = hb == b
            for m in models:
                Q = ym.quantiles(m, idx[sel], h[sel].astype(float), rng, hb=int(b))
                legs = [(np.array([recs[r]['legs'][li]['strike'] for r in ri[sel]]), recs[ri[sel][0]]['legs'][li]['cp'])
                        for li in range(2)]
                v = leg_values(Q, spot[sel], legs)
                values[m][ri[sel], 0] = v[0]
                values[m][ri[sel], 1] = v[1]
        print(y, len(ri), 'valued', flush=True)
    os.makedirs(os.path.dirname(a.out), exist_ok=True)
    with open(a.out, 'wb') as s:
        pickle.dump({'models': models, 'values': values}, s)


if __name__ == '__main__':
    main()

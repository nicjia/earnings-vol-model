"""Daily stock panel and release calendar for research8 phase 1 (stock data only, no option quotes).

python -m research8.panel --data ../wrds_studies --output ../wrds_studies/research8_phase1/panel.npz

Matrices are sessions x names (float64, NaN when missing):
  r   log total return       id  log(close/open)      on  r - id (overnight, incl. dividends)
  gk  Garman-Klass variance  close  |close|            rel  release-session flag
Events per name (sorted by release session): announcement date ordinal, release session index, P index.
"""
import argparse
import csv
import datetime as dt
import glob
import gzip
import os

import numpy as np
import pandas as pd

SOURCES = {'original': 'research7_data', 'expanded': 'research7_expanded'}
GROUP_SAMPLE = {'original': 'original', 'expanded_2017': 'expanded', 'added_2020': 'expanded'}


def release_session(anndate, anntims, dates):
    """Index of the session whose close-to-close return contains the release, or None."""
    i = int(np.searchsorted(dates, anndate))
    if i >= len(dates):
        return None
    if dates[i] != anndate:
        return i  # non-session announcement date: first session after it
    minutes = int(anntims[:2]) * 60 + int(anntims[3:5]) if anntims else None
    if minutes is not None and minutes >= 16 * 60:
        return i + 1 if i + 1 < len(dates) else None
    return i  # before the open or during the session (or missing time): the announcement-date session


def build(data_root):
    dates = np.array(sorted(dt.date.fromisoformat(r['date'][:10]) for r in
                            csv.DictReader(open(os.path.join(data_root, SOURCES['original'], 'sessions.csv')))))
    frames, universe = [], []
    for key, folder in SOURCES.items():
        for path in sorted(glob.glob(os.path.join(data_root, folder, 'stocks', 'stocks_*.csv.gz'))):
            frames.append(pd.read_csv(path, usecols=['secid', 'date', 'close', 'return', 'open', 'high', 'low']))
        u = pd.read_csv(os.path.join(data_root, folder, 'universe.csv'))
        universe.append(u[u['group'].isin(GROUP_SAMPLE)][['secid', 'ticker', 'group']])
    universe = pd.concat(universe).drop_duplicates('secid')
    universe['secid'] = universe['secid'].astype(int)
    st = pd.concat(frames)
    st['secid'] = st['secid'].astype(int)
    st = st[st['secid'].isin(universe['secid'])].drop_duplicates(['secid', 'date'])
    names = np.array(sorted(universe['secid']))
    col = {s: j for j, s in enumerate(names)}
    row = {d.isoformat(): i for i, d in enumerate(dates)}
    st = st[st['date'].str[:10].isin(row)]
    ti = st['date'].str[:10].map(row).to_numpy()
    tj = st['secid'].map(col).to_numpy()
    shape = (len(dates), len(names))

    def mat(values):
        m = np.full(shape, np.nan)
        m[ti, tj] = values
        return m

    close = np.abs(st['close'].to_numpy(float))
    o, h, l = (st[c].to_numpy(float) for c in ('open', 'high', 'low'))
    ok = (o > 0) & (h > 0) & (l > 0) & (close > 0)
    idr = np.where(ok, np.log(np.where(ok, close, 1) / np.where(ok, o, 1)), np.nan)
    gk = np.where(ok, 0.5 * np.log(np.where(ok, h, 1) / np.where(ok, l, 1)) ** 2 - (2 * np.log(2) - 1) * idr ** 2, np.nan)
    ret = st['return'].to_numpy(float)
    r = np.where(ret > -1, np.log1p(np.where(ret > -1, ret, 0)), np.nan)
    out = {'dates': np.array([d.toordinal() for d in dates]), 'names': names,
           'group': universe.set_index('secid').loc[names, 'group'].to_numpy().astype(str),
           'r': mat(r), 'id': mat(idr), 'gk': mat(np.maximum(gk, 0)), 'close': mat(close)}
    out['on'] = out['r'] - out['id']

    rel = np.zeros(shape, bool)
    ev_name, ev_ann, ev_rel = [], [], []
    for key, folder in SOURCES.items():
        path = glob.glob(os.path.join(data_root, folder, 'events_*.csv.gz'))[0]
        ev = pd.read_csv(path, dtype={'anntims': str})
        ev['secid'] = ev['secid'].astype(int)
        ev = ev[ev['secid'].isin(col)].sort_values(['anndats', 'anntims'])
        ev = ev.drop_duplicates(['secid', 'pends'])  # earliest announcement per fiscal period
        for sid, ann, tims in zip(ev['secid'], ev['anndats'], ev['anntims'].fillna('')):
            a = dt.date.fromisoformat(ann[:10])
            q = release_session(a, tims, dates)
            if q is None:
                continue
            ev_name.append(col[sid]); ev_ann.append(a.toordinal()); ev_rel.append(q)
    ev = pd.DataFrame({'j': ev_name, 'ann': ev_ann, 'q': ev_rel}).drop_duplicates(['j', 'q']).sort_values(['j', 'q'])
    rel[ev['q'].to_numpy(), ev['j'].to_numpy()] = True
    out['rel'] = rel
    out['ev_j'], out['ev_ann'], out['ev_q'] = (ev[c].to_numpy() for c in ('j', 'ann', 'q'))
    return out


def load(path):
    with np.load(path, allow_pickle=False) as z:
        return {k: z[k] for k in z.files}


if __name__ == '__main__':
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument('--data', default='../wrds_studies')
    p.add_argument('--output', default='../wrds_studies/research8_phase1/panel.npz')
    a = p.parse_args()
    os.makedirs(os.path.dirname(a.output), exist_ok=True)
    panel = build(a.data)
    np.savez_compressed(a.output, **panel)
    print({k: v.shape for k, v in panel.items()}, 'events', len(panel['ev_q']), 'release flags', int(panel['rel'].sum()))

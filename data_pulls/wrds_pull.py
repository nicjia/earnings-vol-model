#!/usr/bin/env python3
"""Pull the research7 earnings-options dataset from WRDS (run locally with your own WRDS account).

Requirements:  python -m pip install wrds pandas
Credentials:   the wrds package prompts for your password (or uses ~/.pgpass); nothing is stored by this script.

Phases (run in order; every phase is resumable and skips files that already exist):
  calendar  trading sessions from OptionMetrics security prices
  universe  original 300 names + expanded names (ranks after the original 300 at Dec-2017, new top names at Dec-2020)
  ibes      I/B/E/S quarterly EPS actuals WITH announcement times, plus consensus before each release
  stocks    daily open/high/low/close/volume/return/cfadj, distributions, zero curve
  options   closing option quotes for sessions E-PRE..E+POST around every event, expiries <= E+MAX_DTE days
  manifest  counts, parameters and file hashes

Examples:
  python data_pulls/wrds_pull.py --out ~/stock/wrds_studies/research7_data --original-universe ~/stock/wrds_studies/earnings_vol/universe.csv --wrds-user YOURNAME --smoke
  python data_pulls/wrds_pull.py --out ~/stock/wrds_studies/research7_data --original-universe ~/stock/wrds_studies/earnings_vol/universe.csv --wrds-user YOURNAME --names original all
  python data_pulls/wrds_pull.py ... --names expanded all
"""
import argparse
import bisect
import datetime as dt
import hashlib
import json
import os
import sys

PHASES = ('calendar', 'universe', 'ibes', 'stocks', 'options', 'manifest')
SPY_SECID = 109820
QUOTE_COLUMNS = ('o.secid, o.date, o.exdate, o.optionid, o.cp_flag, o.strike_price, o.best_bid, o.best_offer, '
                 'o.volume, o.open_interest, o.impl_volatility, o.delta, o.cfadj')


def sha256(path):
    h = hashlib.sha256()
    with open(path, 'rb') as stream:
        for chunk in iter(lambda: stream.read(1 << 20), b''):
            h.update(chunk)
    return h.hexdigest()


def write_frame(df, path):
    """Write atomically so an interrupted run never leaves a truncated file that looks complete."""
    tmp = path + '.partial'
    df.to_csv(tmp, index=False, compression='gzip' if path.endswith('.gz') else None)
    os.replace(tmp, path)


def window_values(windows):
    """SQL VALUES rows for (secid, first session, last session, last expiry) tuples."""
    rows = [f"({int(s)}, date '{a.isoformat()}', date '{b.isoformat()}', date '{x.isoformat()}')" for s, a, b, x in windows]
    return ',\n'.join(rows)


def options_sql(table_year, windows, mny_lo, mny_hi):
    return f"""
with w(secid, d0, d1, xmax) as (values
{window_values(windows)}
)
select {QUOTE_COLUMNS}
from optionm_all.opprcd{table_year} o
join w on o.secid = w.secid and o.date between w.d0 and w.d1 and o.exdate <= w.xmax
join optionm_all.secprd{table_year} s on s.secid = o.secid and s.date = o.date
where o.ss_flag = '0'
  and o.strike_price >= {mny_lo * 1000:.0f} * abs(s.close)
  and o.strike_price <= {mny_hi * 1000:.0f} * abs(s.close)
"""


def event_windows(events, sessions, pre, post, max_dte):
    """[(secid, first session, last session, last expiry)] for events with enough sessions on both sides."""
    out = []
    for secid, e in events:
        i = bisect.bisect_left(sessions, e)
        if i - pre < 0 or i >= len(sessions):
            continue
        last = sessions[min(i + post, len(sessions) - 1)]
        out.append((secid, sessions[i - pre], last, sessions[i] + dt.timedelta(days=max_dte)))
    return out


class Puller:
    def __init__(self, args):
        self.args = args
        self.out = os.path.abspath(os.path.expanduser(args.out))
        os.makedirs(os.path.join(self.out, 'options'), exist_ok=True)
        os.makedirs(os.path.join(self.out, 'stocks'), exist_ok=True)
        self._db = None

    @property
    def db(self):
        if self._db is None:
            import wrds
            self._db = wrds.Connection(wrds_username=self.args.wrds_user)
        return self._db

    def sql(self, query, date_cols=None):
        return self.db.raw_sql(query, date_cols=date_cols)

    def path(self, *parts):
        return os.path.join(self.out, *parts)

    def years_available(self):
        tables = set(self.db.list_tables(library='optionm_all'))
        return sorted(int(t[6:]) for t in tables if t.startswith('opprcd') and t[6:].isdigit())

    # ------------------------------------------------------------------ calendar
    def calendar(self):
        path = self.path('sessions.csv')
        if os.path.exists(path):
            return
        import pandas as pd
        frames = []
        for y in range(self.args.history_start, self.args.last_year + 2):
            if f'secprd{y}' not in set(self.db.list_tables(library='optionm_all')):
                continue
            frames.append(self.sql(f'select date from optionm_all.secprd{y} where secid = {SPY_SECID}', ['date']))
        write_frame(pd.concat(frames).drop_duplicates().sort_values('date'), path)

    def sessions(self):
        import pandas as pd
        return [d.date() for d in pd.read_csv(self.path('sessions.csv'), parse_dates=['date'])['date']]

    # ------------------------------------------------------------------ universe
    def _ibes_cusips(self, year):
        df = self.sql(f"""select distinct cusip from ibes.actu_epsus
                          where usfirm = 1 and pdicity = 'QTR' and measure = 'EPS'
                            and anndats between '{year}-01-01' and '{year}-12-31'""")
        return set(df['cusip'].dropna())

    def _ranked(self, year):
        dv = self.sql(f"""select p.secid, avg(p.close * p.volume) as dollar_volume, avg(p.close) as avg_close,
                                 count(*) as sessions
                          from optionm_all.secprd{year} p
                          join optionm_all.securd s on s.secid = p.secid
                          where p.date between '{year}-12-01' and '{year}-12-31' and s.issue_type = '0'
                          group by p.secid having count(*) >= 15""")
        dv = dv[dv['avg_close'] > 10]
        names = self.sql(f"""select secid, cusip, ticker, issuer, effect_date from optionm_all.secnmd
                             where secid in ({','.join(str(int(s)) for s in dv['secid'])})""", ['effect_date'])
        covered = self._ibes_cusips(year)
        ok = set(names[names['cusip'].isin(covered)]['secid'])
        dv = dv[dv['secid'].isin(ok)].sort_values('dollar_volume', ascending=False).reset_index(drop=True)
        dv['rank'] = dv.index + 1
        latest = names[names['effect_date'] <= f'{year}-12-31'].sort_values('effect_date').groupby('secid').tail(1)
        return dv.merge(latest[['secid', 'cusip', 'ticker', 'issuer']], on='secid', how='left')

    def universe(self):
        path = self.path('universe.csv')
        if os.path.exists(path):
            return
        import pandas as pd
        orig = pd.read_csv(os.path.expanduser(self.args.original_universe))
        orig = orig.assign(group='original', formation=2017, rank=None, trade_start='2018-01-01')
        taken = set(orig['secid'])
        parts = [orig[['secid', 'ticker', 'issuer', 'cusip', 'group', 'formation', 'rank', 'trade_start']]]
        for year, group, count, start in ((2017, 'expanded_2017', self.args.expand_2017, '2018-01-01'),
                                          (2020, 'added_2020', self.args.added_2020, '2021-01-01')):
            ranked = self._ranked(year)
            new = ranked[~ranked['secid'].isin(taken)].head(count).copy()
            new = new.assign(group=group, formation=year, trade_start=start)
            taken |= set(new['secid'])
            parts.append(new[['secid', 'ticker', 'issuer', 'cusip', 'group', 'formation', 'rank', 'trade_start',
                              'dollar_volume']])
        write_frame(pd.concat(parts, ignore_index=True), path)

    def universe_frame(self):
        import pandas as pd
        uni = pd.read_csv(self.path('universe.csv'))
        if self.args.names != 'all':
            uni = uni[uni['group'] == 'original'] if self.args.names == 'original' else uni[uni['group'] != 'original']
        if self.args.smoke:
            uni = uni.head(3)
        return uni

    # ------------------------------------------------------------------ ibes
    def ibes(self):
        import pandas as pd
        tag = self.args.names + ('_smoke' if self.args.smoke else '')
        events_path = self.path(f'events_{tag}.csv.gz')
        if os.path.exists(events_path):
            return
        uni = self.universe_frame()
        secids = ','.join(str(int(s)) for s in uni['secid'])
        names = self.sql(f'select secid, cusip, effect_date from optionm_all.secnmd where secid in ({secids})', ['effect_date'])
        cusips = sorted(set(names['cusip'].dropna()))
        quoted = ','.join(f"'{c}'" for c in cusips)
        link = self.sql(f'select distinct ticker, cusip, oftic, cname from ibes.idsum where cusip in ({quoted})')
        link = link.merge(names[['secid', 'cusip']].drop_duplicates(), on='cusip')
        write_frame(link, self.path(f'ibes_link_{tag}.csv.gz'))
        tickers = ','.join(f"'{t}'" for t in sorted(set(link['ticker'])))
        start, end = f'{self.args.history_start}-01-01', f'{self.args.last_year + 1}-12-31'
        act = self.sql(f"""select ticker, cusip, oftic, cname, pends, pdicity, anndats, anntims, actdats, acttims,
                                  value, usfirm, curr_act
                           from ibes.actu_epsus
                           where ticker in ({tickers}) and measure = 'EPS' and pdicity = 'QTR'
                             and anndats between '{start}' and '{end}'""", ['pends', 'anndats', 'actdats'])
        write_frame(act, self.path(f'ibes_actuals_{tag}.csv.gz'))
        cons = self.sql(f"""select ticker, statpers, fpedats, fpi, numest, meanest, medest, stdev, highest, lowest,
                                   actual, anndats_act, anntims_act, usfirm
                            from ibes.statsumu_epsus
                            where ticker in ({tickers}) and measure = 'EPS' and fpi = '6'
                              and statpers between '{start}' and '{end}'""", ['statpers', 'fpedats', 'anndats_act'])
        write_frame(cons, self.path(f'ibes_consensus_{tag}.csv.gz'))
        # One event per security and fiscal quarter: earliest announcement among linked I/B/E/S tickers.
        ev = act.merge(link[['ticker', 'secid']].drop_duplicates(), on='ticker')
        ev = ev.sort_values(['secid', 'pends', 'anndats']).drop_duplicates(['secid', 'pends'])
        write_frame(ev[['secid', 'ticker', 'oftic', 'pends', 'anndats', 'anntims', 'actdats', 'acttims', 'value']],
                    events_path)

    # ------------------------------------------------------------------ stocks
    def stocks(self):
        import pandas as pd
        uni = self.universe_frame()
        secids = ','.join(str(int(s)) for s in uni['secid'])
        tag = self.args.names + ('_smoke' if self.args.smoke else '')
        tables = set(self.db.list_tables(library='optionm_all'))
        for y in range(self.args.history_start, self.args.last_year + 1):
            path = self.path('stocks', f'stocks_{tag}_{y}.csv.gz')
            if os.path.exists(path) or f'secprd{y}' not in tables:
                continue
            df = self.sql(f"""select secid, date, open, high, low, close, volume, "return", cfadj, shrout
                              from optionm_all.secprd{y} where secid in ({secids})""", ['date'])
            write_frame(df, path)
        path = self.path(f'distributions_{tag}.csv.gz')
        if not os.path.exists(path):
            write_frame(self.sql(f"""select secid, ex_date, declare_date, record_date, payment_date, amount,
                                            distr_type, frequency, cancel_flag, adj_factor
                                     from optionm_all.distrd where secid in ({secids})
                                       and ex_date >= '{self.args.history_start}-01-01'""",
                                 ['ex_date', 'declare_date', 'record_date', 'payment_date']), path)
        path = self.path('zero_curve.csv.gz')
        if not os.path.exists(path):
            write_frame(self.sql(f"select date, days, rate from optionm_all.zerocd where date >= '{self.args.history_start}-01-01' "
                                 'and days <= 400', ['date']), path)

    # ------------------------------------------------------------------ options
    def options(self):
        import pandas as pd
        tag = self.args.names + ('_smoke' if self.args.smoke else '')
        ev = pd.read_csv(self.path(f'events_{tag}.csv.gz'), parse_dates=['anndats'])
        uni = self.universe_frame()
        start = dict(zip(uni['secid'], pd.to_datetime(uni['trade_start'])))
        ev = ev[ev['secid'].isin(start)]
        ev = ev[ev.apply(lambda r: r['anndats'] >= start[r['secid']], axis=1)]
        sessions = self.sessions()
        available = set(self.years_available())
        years = [y for y in range(self.args.first_year, self.args.last_year + 1) if y in available]
        if self.args.smoke:
            years = years[-1:]
        windows = event_windows(sorted((int(s), d.date()) for s, d in zip(ev['secid'], ev['anndats'])),
                                sessions, self.args.pre, self.args.post, self.args.max_dte)
        secids = sorted({w[0] for w in windows})
        for y in years:
            lo, hi = dt.date(y, 1, 1), dt.date(y, 12, 31)
            for b in range(0, len(secids), self.args.batch):
                group = set(secids[b:b + self.args.batch])
                part = [(s, max(a, lo), min(z, hi), x) for s, a, z, x in windows if s in group and a <= hi and z >= lo]
                path = self.path('options', f'quotes_{tag}_{y}_{b // self.args.batch:03d}.csv.gz')
                if not part or os.path.exists(path):
                    continue
                df = self.sql(options_sql(y, part, self.args.mny_lo, self.args.mny_hi), ['date', 'exdate'])
                write_frame(df, path)
                print(f'{os.path.basename(path)}: {len(df):,} rows', flush=True)

    # ------------------------------------------------------------------ manifest
    def manifest(self):
        files = []
        for root, _, names in os.walk(self.out):
            for n in sorted(names):
                if n.endswith('.partial') or n == 'manifest.json':
                    continue
                p = os.path.join(root, n)
                files.append({'path': os.path.relpath(p, self.out), 'bytes': os.path.getsize(p), 'sha256': sha256(p)})
        doc = {'created_at': dt.datetime.now(dt.timezone.utc).isoformat(), 'source': 'WRDS OptionMetrics + I/B/E/S',
               'script_sha256': sha256(os.path.abspath(__file__)),
               'parameters': {k: v for k, v in vars(self.args).items() if k not in ('wrds_user', 'phases')},
               'announcement_times': 'I/B/E/S anntims/acttims included; still retrospective, not a point-in-time calendar',
               'files': files}
        with open(self.path('manifest.json'), 'w') as stream:
            json.dump(doc, stream, indent=1, default=str)
        print(f"manifest: {len(files)} files, {sum(f['bytes'] for f in files) / 1e6:.1f} MB")


def main(argv=None):
    p = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    p.add_argument('phases', nargs='+', choices=PHASES + ('all',))
    p.add_argument('--out', required=True)
    p.add_argument('--original-universe', required=True, help='earnings_vol/universe.csv from the existing cache')
    p.add_argument('--wrds-user')
    p.add_argument('--names', choices=('original', 'expanded', 'all'), default='original')
    p.add_argument('--expand-2017', type=int, default=300, help='new names from the Dec-2017 ranking')
    p.add_argument('--added-2020', type=int, default=200, help='new names from the Dec-2020 ranking')
    p.add_argument('--history-start', type=int, default=2014)
    p.add_argument('--first-year', type=int, default=2018)
    p.add_argument('--last-year', type=int, default=dt.date.today().year)
    p.add_argument('--pre', type=int, default=10, help='sessions before E')
    p.add_argument('--post', type=int, default=5, help='sessions after E')
    p.add_argument('--max-dte', type=int, default=45, help='calendar days after E for the last expiry kept')
    p.add_argument('--mny-lo', type=float, default=0.7)
    p.add_argument('--mny-hi', type=float, default=1.4)
    p.add_argument('--batch', type=int, default=25)
    p.add_argument('--smoke', action='store_true', help='3 names, latest year only: check access and SQL quickly')
    args = p.parse_args(argv)
    phases = PHASES if 'all' in args.phases else [x for x in PHASES if x in args.phases]
    puller = Puller(args)
    for phase in phases:
        print(f'== {phase}', flush=True)
        getattr(puller, phase)()


if __name__ == '__main__':
    sys.exit(main())

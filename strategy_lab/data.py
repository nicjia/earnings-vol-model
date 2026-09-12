from pathlib import Path
import json
import numpy as np
import pandas as pd
import exchange_calendars as xc
from variance_clock import Session, ClockWeights, clock_exposure


class MarketData:
    def __init__(self, root, end):
        root=Path(root)
        self.manifest=json.loads((root/'manifest.json').read_text())
        self.names={int(v):k for k,v in self.manifest['names'].items()}
        self.stocks=pd.read_pickle(root/'stocks.pkl')
        self.stocks['date']=pd.to_datetime(self.stocks.date)
        self.stocks=self.stocks[self.stocks.date<=pd.Timestamp(end)].copy()
        self.stocks.secid=self.stocks.secid.astype(int)
        self.stock=self.stocks.set_index(['secid','date']).sort_index()
        self.rates=pd.read_pickle(root/'rates.pkl')
        self.rates['date']=pd.to_datetime(self.rates.date)
        e=pd.read_pickle(root/'announcements.pkl')
        self.events={sid:sorted(pd.to_datetime(e.loc[e.oftic==name,'anndats']).unique())
                     for sid,name in self.names.items()}
        calendar_start=(self.stocks.date.min()-pd.Timedelta(days=32)).strftime('%Y-%m-%d')
        calendar_end=(pd.Timestamp(end)+pd.Timedelta(days=202)).strftime('%Y-%m-%d')
        cal=xc.get_calendar('XNYS',start=calendar_start,end=calendar_end)
        self.schedule=cal.schedule
        self.dates=self.schedule.index
        self.sessions=[Session(r.open.to_pydatetime(),r.close.to_pydatetime())
                       for r in self.schedule.itertuples()]
        self.exposure_cache={}
        self.root=root

    def quotes(self, sid):
        cache=self.root/f'normalized_{sid}.pkl'
        if cache.exists():
            return pd.read_pickle(cache)
        parts=[]
        for p in sorted(self.root.glob('quotes_q*.csv.gz')):
            for q in pd.read_csv(p,chunksize=150000):
                q=q[q.secid.eq(sid)]
                if len(q): parts.append(q)
        q=pd.concat(parts,ignore_index=True)
        for col in ['date','exdate']: q[col]=pd.to_datetime(q[col])
        for col in ['secid','optionid','strike_price']: q[col]=q[col].astype('int64')
        q['strike']=q.strike_price/1000
        q['mid']=(q.best_bid+q.best_offer)/2
        q['halfspread']=(q.best_offer-q.best_bid)/2
        if q.duplicated(['date','optionid']).any():
            raise ValueError('Duplicate optionid/date; resolve without selecting a favorable quote')
        q=q.sort_values(['date','optionid']).reset_index(drop=True)
        q.to_pickle(cache)
        return q

    def close_time(self,date):
        return self.schedule.loc[pd.Timestamp(date),'close'].to_pydatetime()

    def expiry_time(self,date):
        # Historical Saturday expiration dates use preceding exchange close.
        i=self.dates.searchsorted(pd.Timestamp(date),side='right')-1
        return self.close_time(self.dates[i])

    def shift(self,date,n):
        i=self.dates.searchsorted(pd.Timestamp(date))
        return self.dates[i+n]

    def exposure(self,date,expiry):
        key=(pd.Timestamp(date),pd.Timestamp(expiry))
        if key not in self.exposure_cache:
            self.exposure_cache[key]=clock_exposure(self.close_time(date),self.expiry_time(expiry),self.sessions)
        return self.exposure_cache[key]

    def rate(self,date,T):
        rows=self.rates[self.rates.date<=pd.Timestamp(date)]
        if rows.empty: raise ValueError('No rate known by prediction date')
        rows=rows[rows.date.eq(rows.date.max())].sort_values('days')
        return float(np.interp(T*365,rows.days,rows.rate))/100

    def physical_clock(self,sid,date,minimum_history):
        """Past-only physical relative variance prior, not a Q-measure estimate.

        Excludes earnings windows and split-factor transitions. Relative closure
        rates are pooled across completed intervals for this name only.
        """
        p=self.stocks[(self.stocks.secid==sid)&(self.stocks.date<pd.Timestamp(date))].sort_values('date').tail(100)
        records=[]
        for prev,now in zip(list(p.itertuples())[:-1],list(p.itertuples())[1:]):
            if any(prev.date<=pd.Timestamp(e)<=now.date for e in self.events[sid]): continue
            if min(prev.close,now.open,now.close)<=0 or prev.cfadj!=now.cfadj: continue
            exp=clock_exposure(self.close_time(prev.date),self.schedule.loc[now.date,'open'].to_pydatetime(),self.sessions)
            kind=max(('overnight','weekend','holiday'),key=lambda k:getattr(exp,k))
            seconds=getattr(exp,kind)
            h=(self.schedule.loc[now.date,'close']-self.schedule.loc[now.date,'open']).total_seconds()
            records.append((kind,seconds,np.log(now.open/prev.close),h,np.log(now.close/now.open)))
        if len(records)<minimum_history: return None
        a=pd.DataFrame(records,columns=['kind','seconds','gap','session_seconds','session_return'])
        session_rate=float((a.session_return**2).sum()/a.session_seconds.sum())
        if session_rate<=0: return None
        weights={}
        for k in ['overnight','weekend','holiday']:
            g=a[a.kind.eq(k)]
            # Sparse weekday holidays borrow the pooled closure estimate, with
            # provenance exposed. No arbitrary zero-variance closure assumption.
            if len(g)<3: g=a
            weights[k]=float((g.gap**2).sum()/g.seconds.sum()/session_rate)
        return ClockWeights(**weights), session_rate, len(a)

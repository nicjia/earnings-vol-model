"""Fetch daily prices + historical earnings dates for the study universe via
yfinance (no Robinhood). Saves to /tmp/earn_data.pkl so analysis never refetches."""
import time, pickle, sys
import yfinance as yf

NAMES = ["AAPL","MSFT","NVDA","AMZN","GOOGL","META","TSLA","AMD","NFLX","JPM",
         "ORCL","CRM","ADBE","AVGO","COST","WMT","DIS","BA"]

def grab(sym, tries=4):
    for k in range(tries):
        try:
            t = yf.Ticker(sym)
            h = t.history(period="4y", interval="1d", auto_adjust=True)
            ed = t.get_earnings_dates(limit=16)
            if h is not None and len(h) > 200 and ed is not None and len(ed) > 4:
                return h, ed
        except Exception as e:
            print(f"  {sym} try {k+1}: {repr(e)[:90]}")
        time.sleep(2.5*(k+1))
    return None, None

out = {}
for i, s in enumerate(NAMES):
    h, ed = grab(s)
    if h is None:
        print(f"{s}: FAILED"); continue
    out[s] = {"hist": h, "earn": ed}
    print(f"{s}: {len(h)} bars, {len(ed)} earnings dates "
          f"({ed.index.min().date()}..{ed.index.max().date()})")
    time.sleep(1.2)

pickle.dump(out, open("/tmp/earn_data.pkl","wb"))
print(f"\nsaved {len(out)}/{len(NAMES)} names -> /tmp/earn_data.pkl")

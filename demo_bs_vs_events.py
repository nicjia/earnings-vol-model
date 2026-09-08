"""
Show that the event structure is ALREADY priced by the market, and that flat
Black-Scholes loses it.

Two model-free tests on the real META curve:

TEST 1 - FORWARD VOLATILITY.
  Black-Scholes assumes ONE constant sigma, so the *forward* vol between any two
  consecutive expiries must be identical (forward variance = sigma^2 * dt).
  We compute the market's realized-implied forward vol window by window. If BS
  held, every bar is the same height. Instead one bar - the window straddling
  10/28 earnings - spikes. That spike is the event the market is pricing; BS says
  it shouldn't exist.

TEST 2 - CAN ONE FLAT VOL FIT THE CURVE?
  Fit the single sigma that best reprices every expiry (least squares on the ATM
  straddle). Show the per-expiry error: flat BS is forced to overprice the short
  expiries and underprice the long ones. Our diffusion+event model nails both.
"""
import numpy as np
from scipy.optimize import minimize_scalar
from earnings_mixture import black76, implied_vol

d = np.load("/tmp/meta_ts.npy", allow_pickle=True).item()
rows = [x for x in d["rows"] if x["exp"] != "2026-10-23"]   # drop the illiquid point
a, b, V_earn = d["a"], d["b"], d["V_earn"]
S0, r = 616.75, 0.045
EARN_DAY = (np.datetime64("2026-10-28") - np.datetime64("2026-09-04")).astype(int)

# ---- TEST 1: forward vol window by window --------------------------------- #
print("="*70)
print("TEST 1 - FORWARD VOL   (Black-Scholes says every row is EQUAL)")
print("="*70)
print(f"{'window':>22} {'days':>6} {'fwd vol':>9} {'has earnings?':>14}")
fwd = []
for x0, x1 in zip(rows[:-1], rows[1:]):
    dW = x1["W"] - x0["W"]; dT = x1["t"] - x0["t"]
    fv = np.sqrt(max(dW, 1e-9) / dT)
    d0 = x0["t"]*365; d1 = x1["t"]*365
    has = "  (earnings window)" if d0 < EARN_DAY <= d1 else ""
    fwd.append((f"{x0['exp'][5:]}->{x1['exp'][5:]}", d1-d0, fv, has))
    print(f"{fwd[-1][0]:>22} {d1-d0:>6.0f} {fv:>8.1%} {has:>14}")

pre_fv = np.mean([f[2] for f in fwd if not f[3]])
earn_fv = [f[2] for f in fwd if f[3]][0]
print(f"\n  non-event forward vol (should be the flat BS line): {pre_fv:.1%}")
print(f"  earnings-window forward vol                        : {earn_fv:.1%}"
      f"   ({earn_fv/pre_fv:.1f}x higher)")
print(f"  --> BS assumes these are equal; the market prices a {earn_fv-pre_fv:+.0%}"
      f" forward-vol spike for one day.")

# ---- TEST 2: best single flat vol vs the event model ---------------------- #
print("\n" + "="*70)
print("TEST 2 - ONE FLAT VOL CANNOT FIT THE CURVE")
print("="*70)
# market ATM straddle per expiry (at the forward, from market ATM IV)
def straddle(iv, x):
    F, t = x["F"], x["t"]
    q = x["q"]
    return (black76(F, F, iv, t, r, True) + black76(F, F, iv, t, r, False))
mkt = np.array([straddle(x["iv"], x) for x in rows])
# best single sigma (least squares on straddle price)
def sse(sig): return np.sum([(straddle(sig, x) - m)**2 for x, m in zip(rows, mkt)])
sig_flat = minimize_scalar(sse, bounds=(0.1, 0.8), method="bounded").x
# event model IV per expiry: diffusion + (event if after earnings)
def event_iv(x):
    W = a + b*x["t"] + (V_earn if x["t"]*365 > EARN_DAY else 0.0)
    return np.sqrt(max(W, 1e-9)/x["t"])

print(f"best single flat vol (least squares) = {sig_flat:.1%}\n")
print(f"{'expiry':>12} {'mktIV':>7} | {'flatBS IV':>9} {'err(volpt)':>11} "
      f"| {'event IV':>9} {'err(volpt)':>11}")
flat_err, ev_err = [], []
for x in rows:
    fe = (sig_flat - x["iv"])*100
    ee = (event_iv(x) - x["iv"])*100
    flat_err.append(fe); ev_err.append(ee)
    tag = "EARN" if x["t"]*365 > EARN_DAY else ""
    print(f"{x['exp']:>12} {x['iv']:>6.1%} | {sig_flat:>8.1%} {fe:>+10.2f} "
          f"| {event_iv(x):>8.1%} {ee:>+10.2f}  {tag}")
print(f"\n  RMS error:   flat Black-Scholes = {np.sqrt(np.mean(np.square(flat_err))):.2f} vol pts"
      f"   |   diffusion+event = {np.sqrt(np.mean(np.square(ev_err))):.2f} vol pts")

np.save("/tmp/bs_vs_events.npy", dict(fwd=fwd, pre_fv=pre_fv, sig_flat=sig_flat,
        rows=rows, a=a, b=b, V_earn=V_earn, EARN_DAY=EARN_DAY,
        flat_err=flat_err, ev_err=ev_err), allow_pickle=True)

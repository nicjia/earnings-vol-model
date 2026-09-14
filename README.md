# earnings-vol-model

Prices options with a schedule earnings jump instead of using a single falt volatility metric. 

Earnings are the largest predictable event in a stock's option surface. They represent ~1.6% of trading days, but carry a median 18% of a stock's annual variance.
This project builds a pricing engine that treats the earnings event as a dated jump on top of ordinary diffusion. Using this, we can forecast the market in a way normal volatility metrics cannot.

![earnings jump study](figures/earnings_study.png)

## What it does

- Prices European options as diffusion with a scheduled jump that applies only to
  expiries taht contain the earnings date. The jump is a Gaussian mixture and the
  price is a closed form weighted sum of Black-76 prices. This does not require Monte-Carlo Simulations, which can get computationally expensive.
- Adds Heston stochastic volatility for skew and prices the combination by the
  Fourier-cosine method which is a Bates-style model with a scheduled jump.
- Decomposes the ATM implied-vol term structure into diffusion with an
  earnings step, and pulls the implied earnings move from the live data.
- Forecasts the post-earnings IV crush and the tail of the realized move.
- Prices with or without reference option quotes, if calibrated parameters are provided, this can act as a standalone model

More specifics on the math and derivations are in [`docs/methods.pdf`](docs/methods.pdf).

### Market Efficiency & Trading Frictions
A core finding of this project is the difference between frictionless theoretical returns and executable reality. When trading the model's fair-value discrepancies purely at the midpoint, the strategy yields a **+26% return**. 

This edge concentrates mostly in wide-quoted, illiquid options (where entry spreads averaged 81% of the midpoint). Break-even analysis shows that a taker strategy would need to consistently execute by crossing **less than 42.6% of the quoted bid-ask spread** to remain net-positive. However, securing fills inside the spread on illiquid chain data is structurally unlikely.

## What works

When the model is calibrated to a few reference strikes, the engine can prices held out strikes across all strikes and maturities within the quoted bid-ask 87-90% of the time.
This shows the model's accuracy for reflecting the true state of the market. 

The term structure splits cleanly into
diffusion, skew, and event components. Forward volatility is ~36% between every
pair of expiries except the one straddling earnings, where it jumps to 48%, which is a signature that a singlular flat volatility cannot show
(`figures/bs_vs_events.png`).

Forecasting that survives out-of-sample. On OOS tests:

- **Move magnitude** is genuinely forecastable and beats a naive prior.
- **Tail risk ranks cleanly** and when sorting by implied vol, P(|move| > 10%) rises
  monotonically from **9% to 37%** across quintiles.
- The **mechanical IV crush** after the announcement is predictable from the event
  decomposition.

**A concrete risk result.** Adding protective wings to short-vol earnings
positions roughly **halved the worst observed loss** and cut return variability by
**62%** across 38 events.


## Results

Prototype fits, mostly in-sample. Better fit with more parameters is not evidence
of an edge — these show the engine reproduces observed surfaces, not that it beats
the market.

| Experiment | RMSE (vol pts) | Scope |
|---|---|---|
| META ATM curve | flat 3.78 / event-strip 0.25 | one expiry excluded |
| META Dec options | 0.36 | 11 strikes, no per-strike fit |
| META joint (Bates) | 0.58 | 6 params, 20 targets, in-sample |
| ORCL Sep-11 smile | flat+jump 2.37 / full 1.08 | 2 vs 5 params, in-sample |
| 9-stock smiles | flat 0.58 / Heston 0.08 | mean per-stock, 5 strikes |
| Held-out strike repricing | inside bid–ask ~87–90% | temporal OOS |

One empirical detail worth calling out: across 144 events, **realized moves aren't
bimodal** — a single wide Gaussian beats a 2- or 3-component beat/miss mixture by
BIC. So the honest default jump is one fat single jump; the mixture is kept only as
a flexible fitter for the implied smile.

![META term structure](figures/meta_term_structure.png)

## Run

```bash
pip install -r requirements.txt
python demo_price.py            # closed form vs Monte Carlo
python fetch_earnings_data.py   # pull prices + earnings dates (yfinance)
python earnings_study.py        # the realized-move study
```

## Layout

- `earnings_mixture.py` — closed-form mixture-of-Black-76 pricer, MC check, IV inversion
- `cos_pricer.py` — COS Heston-plus-jump (Bates) pricer
- `real_orcl.py`, `orcl_heston.py` — single-expiry smile, mispricing scan, flat vs Bates refit
- `meta_term_structure.py`, `bates_term_structure.py` — event decomposition, surface fit
- `meta_smile.py`, `demo_bs_vs_events.py`, `multistock_confirm.py` — per-strike repricing, forward-vol tests, cross-name skew
- `fetch_earnings_data.py`, `earnings_study.py` — the empirical study
- `docs/methods.tex` — the write-up; `figures/` — result plots

## Scope

This is a **pricing, decomposition, and forecasting** project. Calibrating to
market prices makes the engine a fair-value / market-making surface — it reproduces
the market's view of an option consistently, which is exactly what makes it useful
for decomposition and event-vol forecasting. It is not marketed as a taker trading
strategy; the value is in the pricing surface, the diffusion/skew/event
decomposition, and the volatility and tail forecasts it produces that one flat vol
cannot.

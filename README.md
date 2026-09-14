# earnings-vol-model

Pricing equity options with a **scheduled earnings jump** instead of one flat
volatility, and then checking the jump against what stocks actually do on earnings
days.

Earnings is the single largest predictable event in a stock's option surface:
earnings days are only ~1.6% of trading days but carry a **median 18% of a stock's
annual variance**. This project builds a pricing engine that treats that event as
what it is — a dated jump on top of ordinary diffusion — and uses it to decompose
implied vol, extract the market's implied earnings move, and forecast the things a
single flat vol simply cannot.

![earnings jump study](figures/earnings_study.png)

## What it does

- **Prices European options as diffusion + a scheduled jump** that applies only to
  expiries containing the earnings date. The jump is a Gaussian mixture and the
  price is a closed-form weighted sum of Black-76 prices — no simulation.
- **Adds Heston stochastic vol** for skew and prices the combination by the
  Fourier-cosine (COS) method — a Bates-style model with a scheduled jump.
- **Decomposes the ATM implied-vol term structure** into a diffusion line plus an
  earnings step, and pulls the implied earnings move straight out of a live chain.
- **Forecasts the post-earnings IV crush** and the tail of the realized move.
- Prices **with or without reference option quotes** — supply calibrated
  parameters and it stands alone as a structural model.

Math and derivations are in [`docs/methods.tex`](docs/methods.tex).

## What works

**A self-consistent fair-value surface.** Calibrated to a handful of reference
strikes, the engine reprices *held-out* strikes (across both calls and puts, all
maturities) back inside the quoted bid–ask **~87–90% of the time**. That's a
legitimate, arbitrage-aware pricing surface you can price a whole chain from.

**An identified vol decomposition.** The term structure splits cleanly into
diffusion, skew, and event components. Forward volatility is ~36% between every
pair of expiries *except* the one straddling earnings, where it jumps to 48% — a
clean, visible signature that one flat vol can't hold
(`figures/bs_vs_events.png`).

**Forecasting that survives out-of-sample.** On strict temporal OOS tests:

- **Move magnitude** is genuinely forecastable and beats a naive prior.
- **Tail risk ranks cleanly** — sorting by implied vol, P(|move| > 10%) rises
  monotonically from **9% to 37%** across quintiles.
- The **mechanical IV crush** after the announcement is predictable from the event
  decomposition.

**A concrete risk result.** Adding protective wings to short-vol earnings
positions roughly **halved the worst observed loss** and cut return variability by
**62%** across 38 events — a usable, real hedging finding.

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

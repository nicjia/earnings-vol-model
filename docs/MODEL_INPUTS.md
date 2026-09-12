# Pricing inputs and manual control

## Two entry points

The market surface (`MarketSlice.fit` in `market_surface.py`) requires spot, time to expiry, rate, dividend yield/carry, and reference option quotes: strike, midpoint, call/put indicator and half-spread. At least four distinct reference strikes are required. The fitted curve then prices a requested call or put strike at that expiry. An optional structural-price callback provides the Heston/jump prior. It does not fetch earnings dates or stock history by itself. It is a within-expiry European market-price estimator.

The structural timestamp-aware pricer (`price_clocked_option` in `clocked_pricer.py`) takes spot, option strike/type, valuation and expiry timestamps, rates/dividends, a complete exchange schedule, diffusion volatility or Heston parameters, closure variance weights, and a list of dated jump distributions. It can price with manually supplied parameters and no option quotes. This returns a price conditional on the chosen risk-neutral assumptions, not an independently known true value.

Each jump can have any positive number of Gaussian-mixture components. Each component has a nonnegative weight, raw log-return mean, and nonnegative log-return standard deviation. Weights are normalized. A common shift of component means enforces E[exp(J)] = 1, preserving component spacing and widths. Consequently, manually entered raw means are not the final compensated means, and physical probabilities are not automatically pricing probabilities. The automatic research calibration was more restricted: it fixed a two-component core/downside shape and fitted its scale. The historical substitution changed that scale, not every component parameter.

To express a manual view, preserve the market calibration/correction before changing the jump. Refitting all reference residuals afterward can absorb the change and remove the intended valuation gap. `demo_clock.py` illustrates explicit reopening jumps with hypothetical inputs; its numbers are not calibrated results.

## Overnight, weekend and holiday handling

The current clock divides the horizon into regular sessions, ordinary overnight closures, weekend closures, and holiday closures, using timezone-aware exchange open/close times. It includes daylight-saving changes and early closes. The weekend bucket covers the entire Friday-close to Monday-open interval. Discounting and carry use actual calendar time.

Effective variance time is:

(session seconds + overnight weight × overnight seconds + weekend weight × weekend seconds + holiday weight × holiday seconds) / seconds per year.

For flat diffusion, background variance is sigma² times effective variance time. Heston uses the effective time as its model clock. This is not an automatic K-component jump every night.

The older physical-clock research estimator takes up to 100 past daily records, requires at least 30 usable intervals, excludes earnings-adjacent intervals and split-factor transitions, and compares squared open-to-close and close-to-next-open log returns per elapsed second. Each closure weight is its estimated variance-per-second divided by the session variance-per-second. Buckets with fewer than three observations borrow the pooled closure estimate. These are historical/physical relative variance estimates; they were not established as optimal risk-neutral weights. The overall structural parameters are fitted to reference option quotes.

The latest historical-jump trading runs use calendar weights (1,1,1). They do not separately estimate overnight/weekend weights, and they do not automatically schedule reopening mixture jumps. The market-only curve has no explicit overnight decomposition at all.

Optional explicit reopening jumps can be supplied as dated events, each with its own mixture. The engine multiplies independent event characteristic functions. Log jumps add and independent variances add, but the full mixture distribution is retained; it does not simply sum standard deviations or enumerate K^N branches. Independence is an assumption. If explicit closure jumps are added, background closure variance must be allocated consistently to avoid counting the same risk twice.

## What the trading screen covers

The original six 5%-threshold trades came from six/five names across 112 eligible earnings events, one signal snapshot three sessions before each release. Candidates were the nearest three held-out strikes per option type at the first eligible expiry, with 8–45 days to expiry, strike/spot 0.9–1.1, positive bid and midpoint at least $0.25. Calls and puts at calibration/reference strikes were excluded from the target test. This was not the entire daily option surface.

The broader follow-up screen includes all held-out strikes in 0.8–1.2 spot across the existing pipeline's selected reference-supported expiries (up to five), 8–90 days to expiry. It still is not every listed option or every daily snapshot. Wide-target relative spreads are recorded rather than screened away; underlying reference-quote quality filters remain.

The relevant event condition is valuation time < earnings time <= expiry. Original contract listing/creation time is irrelevant to remaining earnings risk. The backtest enters the session after the signal and exits the first close after the earnings date; it does not hold to option settlement. Long signals require model > midpoint × (1 + threshold), short signals model < midpoint × (1 - threshold). Only eligible selected candidates trade. Reported results are research books without a complete portfolio capital/margin model.

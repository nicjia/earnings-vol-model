# Phase 1 implementation clarifications

Written 2026-10-03, after `protocol_phase1.json` (commit `7d6be9d`) and before any dev score was computed.
They fix details the protocol left open; none was chosen by looking at a score.

1. **Name jump smoothing.** The `name` jump draws one of the name's last 8 release returns and adds one diffusion
   day of Normal noise with the EWMA daily variance, so the release-day density is continuous (8 point masses have
   no log score). This slightly double-counts one diffusion day.
2. **`none` jump.** Releases are ordinary days: horizon variance uses all h sessions and the shape is fitted to
   `R / sqrt(h var)` (the full target, release returns included). The diffusion variance itself still skips
   release returns.
3. **Jump scale inputs.** `v` in `s_J` (and in the name-jump noise) is the EWMA diffusion variance for every
   diffusion method, so the jump component is identical across EWMA, GARCH and HAR.
4. **E|R|.** Computed as the trapezoid integral of |quantile| over the full 105-level grid (the protocol's "uniform
   sub-grid" would drop the outer 2% of each forecast and bias E|R| down for every model).
5. **Fallbacks** (each forecast always gets a value, so all models are scored on identical forecast sets):
   GARCH uses EWMA when the 504-session long-run variance is missing (fewer than 252 diffusion returns);
   HAR uses EWMA when any input is missing; B1 uses B0 with fewer than 100 earlier h-session returns;
   `name` uses `shrunk` with fewer than 4 earlier releases.
6. **Two or more releases in one window** (`shrunk`): 2,000 draws with independent pooled jump draws. One release:
   a precomputed table of quantiles of `Z + rho U` over 161 log-spaced `rho` from 0.01 to 100 (20,000 stratified
   draws), interpolated linearly in log rho.
7. **Release-day forecasts** (1 session from P, so no diffusion session remains): `shrunk` = `s_J` times pooled
   jump quantiles; `name` = name draws plus the one-day noise; `none` = one-day diffusion shape.
8. **HAR target** is the log mean of the future daily proxy over the window's diffusion sessions (at least one);
   logs of features and targets are floored at 1e-10. HAR training rows with any missing input are dropped.
9. **Origins** start 2015 (inputs need 252 earlier returns); only origins from 2016-01-04 are scored. Weekly-grid
   origins are rows 0, 5, 10, ... of the session calendar from 2014-01-02.
10. **Student-t shape** is fitted by maximum likelihood on at most 50,000 training z (random subsample, seed 0),
    df floored at 2.05.
11. **Week** for the bootstrap is the Monday-start calendar week of the origin date.
12. **Forecasts of windows whose actual releases differ from the known/projected ones** are scored as they are
    (the forecast never sees actual future release dates beyond the 30-day rule).

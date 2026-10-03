# Paper trader (phase 6)

`strategies.py` turns the STRATEGIES.md rules (S1-S5 validated, P1 provisional) into orders at a decision close,
reusing `research7.engine.plan` and the research5 filters unchanged. Verified on 400 historical 2019 events: the live
selections equal the backtest engine's selections (252 vs 252, 0 mismatches).

Still needed (blocked on `rh_direct.py`, which is not in this repository):
- an adapter that fills a research7-style `Market` from `rh_direct` (sessions, stock closes and total returns for
  the 60-session background vol and earlier release moves, dividends, the current option chain as
  `{(secid, 'YYYY-MM-DD'): {expiry: {strike: [call bid, call ask, call OI, put bid, put ask, put OI]}}}`, and the
  upcoming release calendar with before-open/after-close timing);
- order placement at leg mids with every fill recorded against the quoted bid/ask (to measure real costs);
- a daily loop: at about 15:45 ET call `entries_for` and `exits_due`, size with `size(order, equity)`.
Per the user's rules, `rh_direct` output is filtered in code only and never printed raw.

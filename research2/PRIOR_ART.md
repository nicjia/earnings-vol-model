# Prior art and contribution boundaries

The components below are established. This project does not claim to have invented them.

- Scheduled earnings jumps: Dubinsky and Johannes, *Earnings Announcements and Equity Options*, working paper: https://business.columbia.edu/sites/default/files-efs/pubfiles/6051/DJ_2006.pdf . The paper also discusses hedging anticipated jumps with stock and another option.
- Scheduled jumps under alternative equity dynamics: Leung and Santoli, *Accounting for Earnings Announcements in the Pricing of Equity Options*: https://arxiv.org/abs/1412.8414 .
- Arbitrage-free SVI/SSVI: Gatheral and Jacquier, *Arbitrage-free SVI volatility surfaces*: https://arxiv.org/abs/1204.0646 .
- Empirical minimum-variance delta: Hull and White, *Optimal Delta Hedging for Options*, 2017: https://www-2.rotman.utoronto.ca/~hull/downloadablepublications/Optimal%20Delta%20Hedging.pdf . Our regression is a specified adaptation, not an exact replication of their empirical setup.
- Arbitrage-free local-volatility interpolation: Andreasen and Huge, discussed and implemented by QuantLib maintainers: https://hpcquantlib.wordpress.com/2018/01/05/andreasen-huge-volatility-interpolation/ . Our constrained cubic spline is not their method and should not be labeled as such.

- Smooth arbitrage-constrained option interpolation predates this implementation: Le Floc'h, *An arbitrage-free interpolation of class C2 for option prices*: https://arxiv.org/abs/2004.08650 . Its local-variance-gamma construction is not our natural-cubic projection.
- Weekend/holiday variance-time adjustments: Peter Jöckel, *Time-Weighted Volatility*, 2020: https://onlinelibrary.wiley.com/doi/abs/10.1002/wilm.10889 .

Research questions specific to this implementation:

1. Does a structural-event residual prior improve a constrained call-price smoother over the identical smoother using only market-reference IV?
2. Does the event decomposition add hedge information beyond empirical delta/vega features?
3. Does transporting an earlier identifiable event estimate through the final pre-announcement week improve actual option-plus-stock hedging over delta-vega matching?

A successful comparison could establish an empirical contribution in the specified data and task. It would not by itself establish worldwide novelty or a tradeable edge. Current prior-art search is targeted, not exhaustive.

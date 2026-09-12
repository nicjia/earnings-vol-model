from pathlib import Path
import json
import numpy as np
import pandas as pd
from .protocol import STRATEGIES


def write_report(root):
    root=Path(root)
    trades=pd.DataFrame(json.loads((root/'trades.json').read_text()))
    pred=pd.read_pickle(root/'predictions.pkl')
    future=pd.read_pickle(root/'future_repricing.pkl')
    coverage=json.loads((root/'coverage.json').read_text())
    lines=['# Seven-strategy calibration research', '',
        '**Exploratory 2020 calibration results. No prospectively untouched trading test was run.**', '',
        'Reference quotes and test quotes are separated by strike across both calls/puts and all expirations. '
        'Held-strike pricing is an interpolation/generalization test conditional on reference market prices. '
        'It is not a prediction made without any market inputs.', '',
        '## Pricing accuracy on withheld contracts', '',
        '| Model | Quotes | Mean absolute error (spot bp) | Within bid/ask |',
        '|---|---:|---:|---:|']
    if len(pred):
        common=pred.dropna(subset=['theory','calendar_theory','baseline','mid','spot'])
        for name,col in [('New clock + event/Heston','theory'),('Refitted calendar clock + event/Heston','calendar_theory'),
                         ('Reference-only IV interpolation','baseline')]:
            mae=(abs(common[col]-common.mid)/common.spot*10000).mean()
            inside=((common[col]>=common.best_bid)&(common[col]<=common.best_offer)).mean()
            lines.append(f'| {name} | {len(common)} | {mae:.3f} | {inside:.1%} |')
        lines += ['', f'Numerical convergence screening passed for {pred.numerical_ok.mean():.1%} of withheld quotes. '
                  'Only passing quotes were eligible for trades; all common valid quotes remain in the accuracy table.']
    if len(future):
        f=future.dropna(subset=['actual','predicted'])
        lines += ['', '## Later-date conditional repricing', '',
            'Parameters are fitted at the preceding close and held fixed. The next observed stock price is '
            'provided at scoring time. Thus this tests parameter transport through time, not stock-price forecasting.', '',
            f'{len(f)} scored contracts; {len(future)-len(f)} unresolved observations retained.',
            f'Frozen-model MAE: {(abs(f.predicted-f.actual)/f.spot*10000).mean():.3f} spot bp; '
            f'frozen reference-IV smile with the same updated spot input: {(abs(f.frozen_reference_iv-f.actual)/f.spot*10000).mean():.3f} spot bp; '
            f'previous-option-price baseline: {(abs(f.persistence-f.actual)/f.spot*10000).mean():.3f} spot bp.']
    lines += ['', '## Quoted-price strategy scenarios', '',
        'Signals are observed at a close; entry and convergence-exit fills use a later close. '
        'These are bid/ask scenarios, not verified fills. Includes $0.65 per contract per side, '
        '$0.01/share option slippage per side, and a 2 bp stock hedge cost per side. '
        'Initial stock hedges are fixed until exit. Financing, borrow, margin and American assignment are not modeled.', '',
        'Each strategy is a separate book. Do not add overlapping books into a portfolio result. '
        'Percentages use gross option contract spot notional, not premium paid or margin capital.', '',
        '| Strategy | Closed | Unfilled / unresolved / censored | Mean net % | Median net % | Win rate |',
        '|---|---:|---:|---:|---:|---:|']
    summaries=[]
    for key,title in STRATEGIES.items():
        if key=='session_rotation' and coverage['intraday_status'].startswith('blocked'):
            lines.append(f'| {title} | — | Opening quotes unavailable | — | — | — |'); continue
        g=trades[trades.strategy.eq(key)] if len(trades) else pd.DataFrame()
        closed=g[g.status.eq('closed')] if len(g) else pd.DataFrame()
        status=g.status.value_counts().to_dict() if len(g) else {}
        if closed.empty:
            lines.append(f'| {title} | 0 | {status or "No qualifying entries"} | — | — | — |'); continue
        x=closed.net_per_gross_option_notional
        lines.append(f'| {title} | {len(x)} | {len(g)-len(closed)} | {x.mean()*100:+.3f}% | {x.median()*100:+.3f}% | {(x>0).mean():.1%} |')
        for side,s in closed.groupby('direction'):
            summaries.append(dict(strategy=key,direction=side,n=len(s),mean_net_pct=100*s.net_per_gross_option_notional.mean(),
                option_mid_dollars=s.option_mid_pnl.mean(),hedge_dollars=s.stock_hedge_pnl.mean(),
                spread_dollars=s.spread_cost.mean(),other_cost_dollars=(s.commissions+s.option_slippage+s.stock_cost).mean(),
                net_dollars=s.net_pnl.mean()))
    lines += ['', 'Unresolved outcomes are not silently treated as zero or as completed trades. '
              'Means above describe resolved trades only; incomplete books do not support profitability conclusions.', '',
              '## Calibration P&L attribution by side', '',
              '| Strategy / side | N | Option mids $ | Stock hedge $ | Spread $ | Other costs $ | Net $ |',
              '|---|---:|---:|---:|---:|---:|---:|']
    for s in summaries:
        lines.append(f'| {s["strategy"]} / {s["direction"]} | {s["n"]} | {s["option_mid_dollars"]:+.2f} | '
          f'{s["hedge_dollars"]:+.2f} | {s["spread_dollars"]:.2f} | {s["other_cost_dollars"]:.2f} | {s["net_dollars"]:+.2f} |')
    pd.DataFrame(summaries).to_csv(root/'side_diagnostics.csv',index=False)
    lines += ['', '## Interpretation and remaining limitations', '',
        '- All seven rules are implemented. The session strategy requires genuine timestamped opening and closing option quotes.',
        '- No thresholds were optimized against these returns. Exploring seven strategies still creates selection risk; subsequent tuning requires fresh final evaluation.',
        '- 2021–2024 were already discussed in earlier work. Even if reused later, they cannot honestly be described as prospectively untouched.',
        '- Earnings dates are retrospective records, not a verified point-in-time announcement calendar. Earnings-day snapshots are excluded because release times are unavailable.',
        '- Data cover six selected stocks and a pandemic-year calibration window. This is not market-wide evidence.',
        '- Clock weights are historical physical variance ratios used as a prior. Their risk-neutral equivalence is unproven; the calendar-clock comparison tests their incremental pricing value.',
        '- The European engine is applied to equity options. OTM reference selection and non-dividend names reduce, but do not eliminate, early-exercise confounding.',
        '- Restricted Heston and fixed jump shape are deliberate model specifications. Low residuals on fitted quotes are not independent accuracy evidence.',
        '- Convergence is an executable-quote signal with a one-session delay. It can occur through model-value changes and does not guarantee profit.',
        '- Unfiltered exit data are used. Missing quotes and corporate-action handling failures remain explicitly unresolved.',
        '', '## Coverage exclusions', '', '```json',json.dumps(coverage,indent=2),'```','']
    (root/'REPORT.md').write_text('\n'.join(lines))

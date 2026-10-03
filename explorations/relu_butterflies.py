"""Quick exploration (not pre-registered): ReLU / butterfly views of option chains on 12 liquid names.

A call payoff is ReLU(S - K); a non-negative ReLU combination of strikes is a call portfolio, and the
second difference of call prices (a butterfly) is the option-implied probability mass near K. Tests:
  1. static arbitrage: equal-wing butterflies priced below zero at mids, and at executable prices;
  2. density shape: butterflies held to expiry, by centre strike in units of the ATM implied move,
     split by whether the expiry spans an earnings release and by period;
  3. roughness: a butterfly cheaper than the average of its two neighbours (a bumpy density) - does it pay?
Butterflies use OTM options (puts below spot, calls above), entered at closing mids on sessions E-10,
E-5, E-1 and E+1 of each research7 event, settled at intrinsic from the stock close on expiry.
"""
import bisect
import csv
import datetime as dt
import math
import os
from collections import defaultdict

from research5 import stats
from research7 import data

CACHE = '/home/user/wrds_studies/research7_cache'
UNIVERSE = '/home/user/wrds_studies/earnings_vol/universe.csv'
N_NAMES = 12
OFFSETS = (-10, -5, -1, 1)


def mid(b, a):
    return 0.5 * (b + a)


def leg(chain_ex, k, cp):
    row = chain_ex.get(k)
    if row is None:
        return None
    b, a = (row[0], row[1]) if cp == 'C' else (row[3], row[4])
    if b is None or a is None or a <= 0 or b <= 0 or a < b:
        return None
    return b, a


def butterflies(chain_ex, spot):
    """[(K, width, mid price, executable price, OTM side)] for equal-wing triplets of adjacent strikes."""
    ks = sorted(chain_ex)
    out = []
    for i in range(1, len(ks) - 1):
        lo, k, hi = ks[i - 1], ks[i], ks[i + 1]
        if abs((k - lo) - (hi - k)) > 1e-6:
            continue
        cp = 'P' if k < spot else 'C'
        q = [leg(chain_ex, x, cp) for x in (lo, k, hi)]
        if None in q:
            continue
        m = mid(*q[0]) - 2 * mid(*q[1]) + mid(*q[2])
        ex = q[0][1] - 2 * q[1][0] + q[2][1]  # buy wings at ask, sell body at bid
        out.append((k, k - lo, m, ex, cp))
    return out


def main():
    names = sorted(csv.DictReader(open(UNIVERSE)), key=lambda r: -float(r['dollar_volume']))[:N_NAMES]
    secids = {int(r['secid']): r['ticker'] for r in names}
    print('names:', ', '.join(secids.values()))
    base = data.load_base(CACHE)
    sessions = base['sessions']
    events = [e for e in base['events'] if e['secid'] in secids and 2018 <= e['E'].year <= 2025]
    arb = defaultdict(int)
    rows = []
    for year in range(2018, 2026):
        snaps = data.load_quotes(CACHE, year)
        snaps = {k: v for k, v in snaps.items() if k[0] in secids}
        for ev in events:
            ei = bisect.bisect_left(sessions, ev['E'])
            for off in OFFSETS:
                if not 0 <= ei + off < len(sessions):
                    continue
                day = sessions[ei + off]
                if day.year != year:
                    continue
                chain = snaps.get((ev['secid'], day.isoformat()))
                st = base['stocks'].get(ev['secid'], {}).get(day)
                if not chain or not st:
                    continue
                spot, cf = st[0], st[2]
                for ex, strikes in chain.items():
                    exd = dt.date.fromisoformat(ex)
                    j = bisect.bisect_right(sessions, exd) - 1
                    if exd <= day or j < 0 or sessions[j] > dt.date(2025, 8, 29) or exd > sessions[-1]:
                        continue
                    settle = base['stocks'][ev['secid']].get(sessions[j])
                    if not settle or settle[2] != cf:
                        continue
                    ks = [k for k in strikes if leg(strikes, k, 'C') and leg(strikes, k, 'P')]
                    if not ks:
                        continue
                    atm = min(ks, key=lambda k: abs(k - spot))
                    M = (mid(*leg(strikes, atm, 'C')) + mid(*leg(strikes, atm, 'P'))) / spot
                    flies = butterflies(strikes, spot)
                    spans = ev['Q'] <= exd and day < ev['Q']
                    for i, (k, w, m, ex_price, cp) in enumerate(flies):
                        arb['butterflies'] += 1
                        arb['mid < 0'] += m < 0
                        arb['executable < 0'] += ex_price < 0
                        s_t = settle[0]
                        payoff = max(0.0, w - abs(s_t - k))
                        rough = None
                        if 0 < i < len(flies) - 1 and flies[i - 1][1] == w == flies[i + 1][1] \
                                and abs(flies[i - 1][0] - (k - w)) < 1e-6 and abs(flies[i + 1][0] - (k + w)) < 1e-6:
                            rough = (m - 0.5 * (flies[i - 1][2] + flies[i + 1][2])) / w
                        rows.append({'issuer': secids[ev['secid']], 'E': exd, 'z': (k / spot - 1) / M if M > 0 else None,
                                     'spans': spans, 'period': '2018-21' if day.year <= 2021 else '2022-25',
                                     'ret_mid': (payoff - m) / w, 'ret_exec': (payoff - ex_price) / w,
                                     'price_mid': m / w, 'rough': rough})
        del snaps
    print(f"\n1. Static arbitrage: {arb['butterflies']:,} equal-wing butterflies; priced below zero at mids "
          f"{arb['mid < 0'] / arb['butterflies']:.2%}, at executable prices {arb['executable < 0'] / arb['butterflies']:.3%}")

    def line(label, group):
        pts = stats.issuer_events(group, 'ret_mid')  # clusters by expiry week
        if len(group) < 30:
            return f'{label:44s} n={len(group):6d}'
        m, se = stats.cluster_mean_se(pts)
        mx = sum(g['ret_exec'] for g in group) / len(group)
        avg_price = sum(g['price_mid'] for g in group) / len(group)
        return (f'{label:44s} n={len(group):6d} price={avg_price:6.3f} payoff-price at mid={m:+.4f} (t={m / se:+5.1f})'
                f'  at bid/ask={mx:+.4f}')

    print('\n2. Butterflies held to expiry, P&L as a fraction of wing width (cluster = expiry week x name)')
    buckets = [(-9, -2), (-2, -1), (-1, -0.5), (-0.5, 0.5), (0.5, 1), (1, 2), (2, 9)]
    for spans in (True, False):
        print(f"  expiry {'spans' if spans else 'does not span'} an earnings release")
        for lo, hi in buckets:
            for period in ('2018-21', '2022-25'):
                g = [r for r in rows if r['spans'] == spans and r['period'] == period and r['z'] is not None and lo < r['z'] <= hi]
                print('   ' + line(f'centre {lo:+}..{hi:+} implied moves, {period}', g))
    print('\n3. Roughness: butterfly minus mean of its two neighbours (per width); quintiles within each period')
    for period in ('2018-21', '2022-25'):
        g = sorted((r for r in rows if r['rough'] is not None and r['period'] == period), key=lambda r: r['rough'])
        n = len(g)
        for q in range(5):
            part = g[q * n // 5:(q + 1) * n // 5]
            print('   ' + line(f'{period} quintile {q + 1} ({"cheapest" if q == 0 else "richest" if q == 4 else "mid"})', part))


if __name__ == '__main__':
    main()

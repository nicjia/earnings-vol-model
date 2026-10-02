"""Event-level inference with calendar-week clusters (standard library only)."""
import math
import random
from collections import defaultdict


def week_of(day):
    y, w, _ = day.isocalendar()
    return f'{y}-W{w:02d}'


def issuer_events(trades, key='ret_mid'):
    """Average share-class duplicates within issuer-event; returns [(week, value, record)]."""
    groups = defaultdict(list)
    for t in trades:
        groups[(t['issuer'], t['E'])].append(t)
    out = []
    for (_, day), group in sorted(groups.items(), key=lambda x: (x[0][1], x[0][0])):
        out.append((week_of(day), sum(g[key] for g in group) / len(group), group[0]))
    return out


def clusters(points):
    sums, counts = defaultdict(float), defaultdict(int)
    for week, value, _ in points:
        sums[week] += value
        counts[week] += 1
    return sums, counts


def cluster_mean_se(points):
    n = len(points)
    if n == 0:
        return None, None
    mean = sum(v for _, v, _ in points) / n
    resid = defaultdict(float)
    for week, value, _ in points:
        resid[week] += value - mean
    g = len(resid)
    if g < 2:
        return mean, None
    var = g / (g - 1) * sum(r * r for r in resid.values()) / (n * n)
    return mean, math.sqrt(var)


def bootstrap_interval(points, draws=2000, seed=20261002, level=0.95):
    sums, counts = clusters(points)
    weeks = sorted(sums)
    if len(weeks) < 2:
        return None, None
    rng = random.Random(seed)
    means = []
    for _ in range(draws):
        s = c = 0
        for _ in weeks:
            w = weeks[rng.randrange(len(weeks))]
            s += sums[w]
            c += counts[w]
        means.append(s / c)
    means.sort()
    lo = means[int((1 - level) / 2 * draws)]
    hi = means[min(int((1 + level) / 2 * draws), draws - 1)]
    return lo, hi


def summarize(trades, unresolved=0, bootstrap=False):
    """Statistics for closed trades of one candidate (all cost levels)."""
    out = {'trades': len(trades), 'unresolved': unresolved}
    if not trades:
        return out
    points = issuer_events(trades, 'ret_mid')
    out['events'] = len(points)
    out['issuers'] = len({t['issuer'] for t in trades})
    out['weeks'] = len({w for w, _, _ in points})
    total = len(trades) + unresolved
    out['unresolved_share'] = unresolved / total if total else 0.0
    mean, se = cluster_mean_se(points)
    out['mean'] = mean
    out['se'] = se
    out['ci_low_normal'] = mean - 1.96 * se if se is not None else None
    values = sorted(v for _, v, _ in points)
    out['median'] = values[len(values) // 2]
    out['win_rate'] = sum(v > 0 for v in values) / len(values)
    out['worst'] = values[0]
    out['best'] = values[-1]
    out['without_best5'] = (sum(values[:-5]) / (len(values) - 5)) if len(values) > 5 else None
    for c in ('c25', 'c50'):
        cp = issuer_events(trades, 'ret_' + c)
        out['mean_' + c] = sum(v for _, v, _ in cp) / len(cp)
    out['pnl_mid_one_unit'] = sum(t['pnl_mid'] for t in trades)
    out['pnl_c25_one_unit'] = sum(t['pnl_c25'] for t in trades)
    out['fees_one_unit'] = sum(t['fees'] for t in trades)
    if bootstrap:
        out['ci_low_boot'], out['ci_high_boot'] = bootstrap_interval(points)
        for c in ('c25', 'c50'):
            out['ci_low_boot_' + c], out['ci_high_boot_' + c] = bootstrap_interval(issuer_events(trades, 'ret_' + c))
    return out


def max_t_pvalues(candidate_points, draws=500, seed=20261002):
    """Single-step max-t adjusted p-values (centered weekly-cluster bootstrap, fixed SEs).

    candidate_points: {name: points}.  All candidates share one week universe so
    that a resample applies the same calendar weeks to every candidate.
    """
    names = sorted(candidate_points)
    if not names:
        return {}
    stats = {}
    for name in names:
        mean, se = cluster_mean_se(candidate_points[name])
        stats[name] = (mean, se)
    weeks = sorted({w for pts in candidate_points.values() for w, _, _ in pts})
    week_pos = {w: i for i, w in enumerate(weeks)}
    per = {}
    for name in names:
        sums = [0.0] * len(weeks)
        counts = [0] * len(weeks)
        for w, v, _ in candidate_points[name]:
            sums[week_pos[w]] += v
            counts[week_pos[w]] += 1
        per[name] = (sums, counts)
    rng = random.Random(seed)
    maxima = []
    for _ in range(draws):
        idx = [rng.randrange(len(weeks)) for _ in weeks]
        best = -math.inf
        for name in names:
            mean, se = stats[name]
            if not se:
                continue
            sums, counts = per[name]
            s = sum(sums[i] for i in idx)
            c = sum(counts[i] for i in idx)
            if c == 0:
                continue
            t = (s / c - mean) / se
            if t > best:
                best = t
        maxima.append(best)
    out = {}
    for name in names:
        mean, se = stats[name]
        if not se:
            out[name] = None
            continue
        t = mean / se
        out[name] = sum(m >= t for m in maxima) / len(maxima)
    return out

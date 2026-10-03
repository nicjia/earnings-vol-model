"""Summarize phase 1 scores (aggregates only) and apply the pre-registered freeze rule.

python -m research8.report1 dev   --scores ../wrds_studies/research8_phase1/scores --docs docs/research8/phase1
python -m research8.report1 final --scores ... --docs ...
"""
import argparse
import glob
import hashlib
import json
import os

import numpy as np

from . import features as F

HKEYS = [str(h) for h in F.HORIZONS] + ['rel']
GROUPS = {'short': ['1', '2', '5'], 'medium': ['10', '21'], 'long': ['42', '63'], 'release_day': ['rel']}
COLS = {'crps': 0, 'tw': 1, 'log': 2, 'pit': 3, 'eabs': 4}
DRAWS, SEED = 2000, 20261003
COVER = (0.5, 0.8, 0.9, 0.98)


def load(scores_dir, mode, tags):
    data = {hk: [] for hk in HKEYS}
    models = None
    files = sorted(glob.glob(os.path.join(scores_dir, mode, 'scores_*.npz')))
    for path in files:
        with np.load(path) as z:
            models = list(z['models'])
            for hk in HKEYS:
                if f'{hk}__scores' not in z.files:
                    continue
                keep = np.isin(z[f'{hk}__tag'], tags)
                data[hk].append({k: z[f'{hk}__{k}'][..., keep] if k == 'scores' else z[f'{hk}__{k}'][keep]
                                 for k in ('y', 'week', 'nrel', 'k')} | {'scores': z[f'{hk}__scores'][:, keep]})
    out = {}
    for hk, parts in data.items():
        if parts:
            out[hk] = {k: np.concatenate([p[k] for p in parts], axis=1 if k == 'scores' else 0) for k in parts[0]}
    hashes = {os.path.basename(f): hashlib.sha256(open(f, 'rb').read()).hexdigest() for f in files}
    return models, out, hashes


def week_mult(weeks, rng):
    u, inv = np.unique(weeks, return_inverse=True)
    m = np.stack([np.bincount(rng.integers(0, len(u), len(u)), minlength=len(u)) for _ in range(DRAWS)])
    return u, inv, m


def summarize(models, data, tag_label):
    rng = np.random.default_rng(SEED)
    allweeks = np.unique(np.concatenate([d['week'] for d in data.values()]))
    mult = np.stack([np.bincount(rng.integers(0, len(allweeks), len(allweeks)), minlength=len(allweeks))
                     for _ in range(DRAWS)])  # shared across horizons so averages get joint intervals
    res = {'sample': tag_label, 'models': models, 'horizons': {}}
    boot = {}
    b0 = models.index('B0_EWMA_raw_Gauss')
    for hk, d in data.items():
        sc = d['scores'].astype(np.float64)
        n = sc.shape[1]
        wi = np.searchsorted(allweeks, d['week'])
        cnt = np.bincount(wi, minlength=len(allweeks)).astype(float)
        bc = mult @ cnt
        H = {'n': int(n), 'release_windows': int((d['nrel'] >= 1).sum()), 'models': {}}
        for key in ('crps', 'tw', 'log'):
            S = np.stack([np.bincount(wi, sc[m, :, COLS[key]], minlength=len(allweeks)) for m in range(len(models))])
            boot[hk, key] = (mult @ S.T) / bc[:, None]  # draws x models: bootstrap means
        y = d['y'].astype(np.float64)
        for mi, m in enumerate(models):
            pit = sc[mi, :, 3]
            hist = np.histogram(pit, bins=20, range=(0, 1))[0] / n
            e = sc[mi, :, 4]
            rel = d['nrel'] >= 1
            H['models'][m] = {
                'crps': float(sc[mi, :, 0].mean()), 'tw': float(sc[mi, :, 1].mean()), 'log': float(sc[mi, :, 2].mean()),
                'crps_skill': float(1 - sc[mi, :, 0].mean() / sc[b0, :, 0].mean()),
                'tw_skill': float(1 - sc[mi, :, 1].mean() / sc[b0, :, 1].mean()),
                'log_diff': float(sc[mi, :, 2].mean() - sc[b0, :, 2].mean()),
                'coverage': {str(c): float(np.mean(np.abs(pit - 0.5) <= c / 2)) for c in COVER},
                'pit_max_dev': float(np.max(np.abs(hist - 0.05))),
                'abs_ratio': float(np.mean(np.abs(y)) / np.mean(e)),
                'abs_mse_rel': float(np.mean((np.abs(y) - e) ** 2) / np.mean((np.abs(y) - sc[b0, :, 4]) ** 2)),
                'crps_skill_release_windows': float(1 - sc[mi, rel, 0].mean() / sc[b0, rel, 0].mean()) if rel.any() else None,
                'crps_skill_no_release': float(1 - sc[mi, ~rel, 0].mean() / sc[b0, ~rel, 0].mean()) if (~rel).any() else None,
            }
        res['horizons'][hk] = H
    # horizon averages over the seven horizons, with joint bootstrap intervals
    hs = [str(h) for h in F.HORIZONS if str(h) in data]
    avg = {}
    for mi, m in enumerate(models):
        sk = {k: np.mean([1 - boot[h, k][:, mi] / boot[h, k][:, b0] for h in hs], 0) for k in ('crps', 'tw')}
        ld = np.mean([boot[h, 'log'][:, mi] - boot[h, 'log'][:, b0] for h in hs], 0)
        avg[m] = {
            'crps_skill': float(np.mean([res['horizons'][h]['models'][m]['crps_skill'] for h in hs])),
            'tw_skill': float(np.mean([res['horizons'][h]['models'][m]['tw_skill'] for h in hs])),
            'log_diff': float(np.mean([res['horizons'][h]['models'][m]['log_diff'] for h in hs])),
            'crps_skill_ci': np.percentile(sk['crps'], [2.5, 97.5]).tolist(),
            'tw_skill_ci': np.percentile(sk['tw'], [2.5, 97.5]).tolist(),
            'log_diff_ci': np.percentile(ld, [2.5, 97.5]).tolist(),
            'group_crps_skill': {g: float(np.mean([res['horizons'][h]['models'][m]['crps_skill'] for h in hks if h in data]))
                                 for g, hks in GROUPS.items() if any(h in data for h in hks)},
        }
        if 'rel' in data:
            r = 1 - boot['rel', 'crps'][:, mi] / boot['rel', 'crps'][:, b0]
            avg[m]['release_crps_skill'] = res['horizons']['rel']['models'][m]['crps_skill']
            avg[m]['release_crps_skill_ci'] = np.percentile(r, [2.5, 97.5]).tolist()
    res['average'] = avg
    return res


def complexity(m):
    """Tie-break order: fewer components first, grid before GBQ."""
    if m.startswith('B'):
        return (0, m)
    if m == 'GBQ':
        return (9, m)
    meth, shape, jump = m.split('_')
    return (1 + METH_C[meth] + SHAPE_C[shape] + JUMP_C[jump], m)


METH_C = {'EWMA': 0, 'GARCH': 1, 'HAR': 1}
SHAPE_C = {'Gauss': 0, 'T': 1, 'FHS': 1}
JUMP_C = {'none': 0, 'name': 1, 'shrunk': 1}


def freeze(res):
    cands = [m for m in res['models'] if not m.startswith('B')]
    avg = res['average']
    picks = {}
    for crit, key in (('best_crps', 'crps_skill'), ('best_log', 'log_diff'), ('best_tw', 'tw_skill'),
                      ('best_release_crps', 'release_crps_skill')):
        best = max(avg[m][key] for m in cands)
        tied = [m for m in cands if abs(avg[m][key] - best) < 1e-12]
        picks[crit] = sorted(tied, key=complexity)[0]
    return picks


def gates(res, frozen):
    """Test gates from the protocol for each frozen model and its own score."""
    key = {'best_crps': ('crps_skill', 'crps_skill_ci'), 'best_log': ('log_diff', 'log_diff_ci'),
           'best_tw': ('tw_skill', 'tw_skill_ci'), 'best_release_crps': ('release_crps_skill', 'release_crps_skill_ci')}
    out = {}
    for crit, m in frozen.items():
        a = res['average'][m]
        est, ci = key[crit]
        g1 = a[ci][0] > 0
        g2 = all(v > 0 for v in a['group_crps_skill'].values())
        cov = {h: res['horizons'][h]['models'][m]['coverage']['0.9'] for h in res['horizons']}
        g3 = all(0.85 <= v <= 0.95 for v in cov.values())
        out[crit] = {'model': m, 'estimate': a[est], 'ci': a[ci], 'gate1_lower_bound_above_zero': g1,
                     'gate2_crps_every_group': g2, 'gate3_coverage_90': g3, 'coverage_90': cov,
                     'passed': bool(g1 and g2 and g3)}
    return out


def markdown(res, picks=None):
    avg = res['average']
    models = sorted(res['models'], key=lambda m: -avg[m]['crps_skill'])
    hs = [h for h in HKEYS if h in res['horizons']]
    L = [f"# Phase 1 scores: {res['sample']}", '',
         'Skill = 1 - mean CRPS / mean CRPS of B0 (EWMA on all returns, Normal). Log = mean log-score difference from B0 '
         '(nats). Averages are over the seven horizons; brackets are weekly-bootstrap 95% intervals.', '',
         '| Model | CRPS skill | tw-CRPS skill | Log diff | Short | Medium | Long | Release day |',
         '|---|---|---|---|---|---|---|---|']
    for m in models:
        a = avg[m]
        g = a['group_crps_skill']
        L.append(f"| {m} | {a['crps_skill']:+.2%} [{a['crps_skill_ci'][0]:+.2%}, {a['crps_skill_ci'][1]:+.2%}] | "
                 f"{a['tw_skill']:+.2%} | {a['log_diff']:+.3f} [{a['log_diff_ci'][0]:+.3f}, {a['log_diff_ci'][1]:+.3f}] | "
                 f"{g.get('short', 0):+.2%} | {g.get('medium', 0):+.2%} | {g.get('long', 0):+.2%} | "
                 f"{g.get('release_day', float('nan')):+.2%} |")
    L += ['', '## Calibration (central 90% interval coverage by horizon; target 0.90)', '',
          '| Model | ' + ' | '.join(hs) + ' |', '|---|' + '---|' * len(hs)]
    for m in models:
        L.append(f'| {m} | ' + ' | '.join(f"{res['horizons'][h]['models'][m]['coverage']['0.9']:.3f}" for h in hs) + ' |')
    L += ['', '## Realized / predicted mean |R| (straddle-payoff calibration; 1.00 is perfect)', '',
          '| Model | ' + ' | '.join(hs) + ' |', '|---|' + '---|' * len(hs)]
    for m in models:
        L.append(f'| {m} | ' + ' | '.join(f"{res['horizons'][h]['models'][m]['abs_ratio']:.3f}" for h in hs) + ' |')
    L += ['', '## Forecast counts', '', '| Horizon | Forecasts | With a release in the window |', '|---|---|---|']
    for h in hs:
        L.append(f"| {h} | {res['horizons'][h]['n']:,} | {res['horizons'][h]['release_windows']:,} |")
    if picks:
        L += ['', '## Freeze rule picks', ''] + [f'- **{k}**: {v}' for k, v in picks.items()]
    return '\n'.join(L) + '\n'


def main():
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument('mode', choices=['dev', 'final'])
    ap.add_argument('--scores', default='../wrds_studies/research8_phase1/scores')
    ap.add_argument('--docs', default='docs/research8/phase1')
    a = ap.parse_args()
    os.makedirs(a.docs, exist_ok=True)
    samples = {'dev': ['dev']} if a.mode == 'dev' else {'test': ['test'], 'time_holdout': ['time_holdout'],
                                                           'name_holdout': ['name_holdout']}
    for label, tags in samples.items():
        models, data, hashes = load(a.scores, a.mode, tags)
        res = summarize(models, data, label)
        picks = freeze(res) if label == 'dev' else None
        res['freeze_picks'] = picks
        if label != 'dev':
            frozen = json.load(open(os.path.join(os.path.dirname(os.path.abspath(__file__)), 'phase1_frozen.json')))['frozen']
            res['gates'] = gates(res, frozen)
        res['private_score_files_sha256'] = hashes
        with open(os.path.join(a.docs, f'{label}.json'), 'w') as s:
            json.dump(res, s, indent=1)
        with open(os.path.join(a.docs, f'{label}.md'), 'w') as s:
            s.write(markdown(res, picks))
            if res.get('gates'):
                s.write('\n## Test gates (frozen models)\n\n| Criterion | Model | Estimate | 95% CI | Gate 1 | Gate 2 | Gate 3 | Passed |\n'
                        '|---|---|---|---|---|---|---|---|\n')
                for c, g in res['gates'].items():
                    s.write(f"| {c} | {g['model']} | {g['estimate']:+.4f} | [{g['ci'][0]:+.4f}, {g['ci'][1]:+.4f}] | "
                            f"{g['gate1_lower_bound_above_zero']} | {g['gate2_crps_every_group']} | {g['gate3_coverage_90']} | "
                            f"{g['passed']} |\n")
        print(label, 'written', picks or '')


if __name__ == '__main__':
    main()

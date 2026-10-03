"""research7 candidate grid; filters are evaluated with research5.candidates.passes."""
import hashlib
import json

from .engine import POST, PRE, THROUGH_NONCAL, base_trades

FILTERS = {
    'pre_long': ('none', 'R<=0.9', 'R<=0.75', 'HR>=1.0', 'TSw<=1.1'),
    'pre_short': ('none', 'R>=1.0', 'R>=1.2', 'TSw>=1.15', 'HR<=1.0'),
    'through_long': ('none', 'R<=0.9', 'R<=0.75', 'HR>=1.0', 'HR>=1.2', 'R<=0.9&HR>=1.0'),
    'through_short': ('none', 'R>=1.0', 'R>=1.2', 'R>=1.4', 'TSw>=1.15', 'TSw>=1.3', 'D<=1.0', 'HR<=0.8', 'HR<=1.0',
                      'R>=1.2&HR<=1.0'),
    'post_iron_fly': ('none', 'JM<=1.0', 'JM>=1.0'),
    'post_vertical': ('none', 'JM>=1.0', 'JM>=1.5'),
    'post_surprise': ('none', 'ASUE>=0.001', 'ASUE>=0.003'),
}
TIERS = ('standard', 'tight')
REPLICATIONS = {
    'research5_long_straddle': 'pre:long_straddle|P-1->P|R<=0.9|tight',
    'research5_long_strangle': 'pre:long_strangle|P-1->P|R<=0.9|tight',
    'research6_double_diagonal_put': 'through:double_diagonal_put_1w|P-1->Q|D<=1.0|tight',
    'research6_double_calendar_2w': 'through:double_calendar_straddle_2w|P->hold_front|R>=1.2|standard',
}


def filter_group(phase, family):
    if phase == 'pre':
        return 'pre_long' if PRE[family] == 'long' else 'pre_short'
    if phase == 'through':
        return 'through_long' if THROUGH_NONCAL.get(family) == 'long' else 'through_short'
    if family == 'post_iron_fly_1x':
        return 'post_iron_fly'
    return 'post_surprise' if family == 'post_surprise_vertical' else 'post_vertical'


def grid():
    out = []
    for phase, family, entry, exit_ in base_trades():
        for flt in FILTERS[filter_group(phase, family)]:
            for tier in TIERS:
                label = f'{phase}:{family}'
                out.append({'family': label, 'entry': entry, 'exit': exit_, 'filter': flt, 'liquidity': tier,
                            'id': f'{label}|{entry}->{exit_}|{flt}|{tier}'})
    return out


def grid_hash():
    return hashlib.sha256(json.dumps([c['id'] for c in grid()]).encode()).hexdigest()


def by_id():
    return {c['id']: c for c in grid()}

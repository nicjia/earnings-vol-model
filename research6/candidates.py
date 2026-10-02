"""research6 candidate grid (filters evaluated with research5.candidates.passes)."""
import hashlib
import json

from .engine import CALENDARS, DIRECTIONAL, FAMILIES, POST, REVERSE, timings

FILTERS = {
    'calendar': ('none', 'R>=1.0', 'R>=1.2', 'TSw>=1.15', 'TSw>=1.3', 'D<=1.0', 'HR<=1.0', 'R>=1.0&D<=1.0'),
    'reverse': ('none', 'R<=0.9', 'TSw<=1.1', 'HR>=1.0'),
    'post_iron_fly': ('none', 'JM<=1.0', 'JM>=1.0'),
    'post_vertical': ('none', 'JM>=1.0', 'JM>=1.5'),
    'directional': ('none', 'DRIFT>=0.25', 'DRIFT>=0.5'),
}
TIERS = ('standard', 'tight')


def filters_for(family):
    if family in CALENDARS:
        return FILTERS['calendar']
    if family in REVERSE:
        return FILTERS['reverse']
    if family == 'post_iron_fly':
        return FILTERS['post_iron_fly']
    if family in POST:
        return FILTERS['post_vertical']
    if family in DIRECTIONAL:
        return FILTERS['directional']
    raise ValueError(family)


def grid():
    out = []
    for family in FAMILIES:
        for entry, exit_ in timings(family):
            for flt in filters_for(family):
                for tier in TIERS:
                    c = {'family': family, 'entry': entry, 'exit': exit_, 'filter': flt, 'liquidity': tier}
                    c['id'] = f'{family}|{entry}->{exit_}|{flt}|{tier}'
                    out.append(c)
    return out


def grid_hash():
    return hashlib.sha256(json.dumps([c['id'] for c in grid()]).encode()).hexdigest()

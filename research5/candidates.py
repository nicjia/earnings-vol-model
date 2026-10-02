"""The pre-registered candidate grid and filter evaluation."""
import hashlib
import json

from .engine import FAMILIES, LONG_VOL, SHORT_VOL, TIMINGS

SHORT_FILTERS = ('none', 'R>=1.0', 'R>=1.2', 'R>=1.4', 'TS>=1.2', 'TS>=1.5', 'HR<=0.8', 'HR<=1.0', 'R>=1.2&HR<=1.0')
LONG_FILTERS = ('none', 'R<=0.9', 'R<=0.75', 'TS<=1.1', 'HR>=1.0', 'HR>=1.2', 'R<=0.9&HR>=1.0')
TIERS = ('standard', 'tight')


def candidate_id(c):
    return f"{c['family']}|{c['entry']}->{c['exit']}|{c['filter']}|{c['liquidity']}"


def grid():
    out = []
    for family in FAMILIES:
        filters = SHORT_FILTERS if family in SHORT_VOL else LONG_FILTERS
        for entry, exit_ in TIMINGS:
            for flt in filters:
                for tier in TIERS:
                    c = {'family': family, 'entry': entry, 'exit': exit_, 'filter': flt, 'liquidity': tier}
                    c['id'] = candidate_id(c)
                    out.append(c)
    return out


def grid_hash():
    return hashlib.sha256(json.dumps([c['id'] for c in grid()]).encode()).hexdigest()


def passes(flt, rec):
    if flt == 'none':
        return True
    for clause in flt.split('&'):
        op = '>=' if '>=' in clause else '<='
        name, threshold = clause.split(op)
        value = rec.get('f_' + name)
        if value is None:
            return False
        if op == '>=' and not value >= float(threshold):
            return False
        if op == '<=' and not value <= float(threshold):
            return False
    return True


def members(c, records):
    """Closed and unresolved trades of a candidate among base records."""
    closed, unresolved = [], 0
    for r in records:
        if r['family'] != c['family'] or r['entry'] != c['entry'] or r['exit'] != c['exit']:
            continue
        status = r.get('status')
        if status not in ('closed', 'unresolved'):
            continue
        if c['liquidity'] not in r['tiers'] or not passes(c['filter'], r):
            continue
        if status == 'closed':
            closed.append(r)
        else:
            unresolved += 1
    return closed, unresolved


def index_records(records):
    by_base = {}
    for r in records:
        by_base.setdefault((r['family'], r['entry'], r['exit']), []).append(r)
    return by_base


def members_indexed(c, by_base):
    return members(c, by_base.get((c['family'], c['entry'], c['exit']), []))

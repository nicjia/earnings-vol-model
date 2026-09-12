from dataclasses import dataclass, asdict
import hashlib
import json


@dataclass(frozen=True)
class Protocol:
    start: str = '2020-01-21'
    end: str = '2020-12-10'
    minimum_history: int = 30
    target_modulus: int = 3
    minimum_references: int = 16
    minimum_expirations: int = 3
    max_references_per_expiry: int = 8
    max_expirations: int = 5
    min_dte: int = 8
    max_dte: int = 90
    maximum_holding_sessions: int = 3
    commission_per_contract: float = .65
    option_slippage_per_share: float = .01
    stock_slippage_bps: float = 2.0
    uncertainty_per_spot: float = .001
    convergence_per_share: float = .02
    cos_terms: int = 128
    max_fit_evaluations: int = 35

    def fingerprint(self):
        return hashlib.sha256(json.dumps(asdict(self),sort_keys=True).encode()).hexdigest()


def is_target(secid, strike_price, modulus=3):
    # Same strike is held out across puts, calls, maturities and dates. In
    # particular, a target call cannot leak through its put-call-parity twin.
    key=f'{int(secid)}:{int(round(strike_price))}'.encode()
    return int.from_bytes(hashlib.sha256(key).digest()[:8],'big') % modulus == 0


STRATEGIES = {
    'single_convergence': 'Individual-option residual convergence',
    'event_calendar': 'Same-earnings-event calendar relative value',
    'weekend_calendar': 'Weekend/holiday calendar relative value',
    'butterfly_shape': 'Distribution-shape butterfly relative value',
    'post_earnings': 'Post-earnings residual repricing',
    'session_rotation': 'Separate overnight/daytime variance positions',
    'pre_earnings': 'Pre-earnings residual convergence, exit before release',
}

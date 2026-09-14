"""Pure pre-trade checks. Prototype: not a production risk system."""
from dataclasses import dataclass
import math
import re


def validate_paper_endpoint(host: str, port: int, account: str) -> None:
    # Ports and prefixes alone do not prove paper mode. Also check the exact
    # managed account returned by TWS, and the visible Paper label in TWS.
    if host != "127.0.0.1" or port not in (7497, 4002):
        raise ValueError("Only localhost paper defaults 7497 / 4002 are accepted.")
    if not re.fullmatch(r"DU[0-9]+", account):
        raise ValueError("Configure the exact DU paper account locally.")


def verify_managed_accounts(expected: str, accounts: list[str]) -> None:
    if set(accounts) != {expected}:
        raise ValueError("Account mismatch or multiple accounts; stop and review TWS.")


@dataclass(frozen=True)
class Limits:
    max_gross: float = 0.80
    max_symbol: float = 0.20
    max_order_usd: float = 1000.0
    max_spread_bps: float = 30.0
    quote_age_seconds: float = 10.0
    clock_tolerance_seconds: float = 2.0


@dataclass(frozen=True)
class Snapshot:
    equity: float
    available_cash: float  # settled and unreserved cash supplied by reconciliation
    gross_usd: float
    symbol_usd: float
    pending_buy_usd: float = 0.0
    pending_symbol_buy_usd: float = 0.0
    sellable_shares: int = 0  # position minus already reserved sell shares
    known: bool = True
    halted: bool = False


@dataclass(frozen=True)
class Intent:
    side: str
    quantity: int
    price_cap: float
    bid: float
    ask: float
    quote_time: float
    decision_time: float
    symbol: str = "DEMO"


def check(intent: Intent, state: Snapshot, limits: Limits = Limits()) -> tuple[bool, str]:
    values = [intent.price_cap, intent.bid, intent.ask, intent.quote_time,
              intent.decision_time, state.equity, state.available_cash,
              state.gross_usd, state.symbol_usd, state.pending_buy_usd,
              state.pending_symbol_buy_usd, *vars(limits).values()]
    if any(not math.isfinite(v) for v in values):
        return False, "nonfinite"
    if not state.known:
        return False, "unknown_account_state"
    if state.halted:
        return False, "halt_latched"
    if intent.side not in {"BUY", "SELL"} or type(intent.quantity) is not int or intent.quantity <= 0:
        return False, "invalid_order"
    if min(intent.price_cap, intent.bid, intent.ask, state.equity) <= 0 or intent.ask < intent.bid:
        return False, "invalid_price_or_equity"
    if min(state.available_cash, state.gross_usd, state.symbol_usd,
           state.pending_buy_usd, state.pending_symbol_buy_usd, state.sellable_shares) < 0:
        return False, "invalid_snapshot"
    if not 0 < limits.max_symbol <= limits.max_gross <= 1 or min(
        limits.max_order_usd, limits.max_spread_bps, limits.quote_age_seconds) <= 0 or limits.clock_tolerance_seconds < 0:
        return False, "invalid_limits"
    age = intent.decision_time - intent.quote_time
    if age < -limits.clock_tolerance_seconds or age > limits.quote_age_seconds:
        return False, "stale_or_future_quote"
    mid = (intent.bid + intent.ask) / 2
    if (intent.ask - intent.bid) / mid * 10000 > limits.max_spread_bps:
        return False, "spread"
    notional = intent.quantity * intent.price_cap
    if notional > limits.max_order_usd:
        return False, "order_cap"
    if intent.side == "SELL":
        return (True, "approved") if intent.quantity <= state.sellable_shares else (False, "short_or_reserved_shares")
    if notional > state.available_cash:
        return False, "cash"
    if state.gross_usd + state.pending_buy_usd + notional > limits.max_gross * state.equity:
        return False, "gross_exposure"
    if state.symbol_usd + state.pending_symbol_buy_usd + notional > limits.max_symbol * state.equity:
        return False, "symbol_exposure"
    return True, "approved"

"""Single-asset trend baseline. Next-bar fills; research only, no broker access.

The CSV contract is date,open,high,low,close,volume for completed daily bars.
SPY is an integration example, not a recommendation. Raw IBKR TRADES data
needs corporate-action/total-return review before investment conclusions.
"""
from dataclasses import dataclass
import csv
from datetime import date, timedelta
import math
import random


@dataclass(frozen=True)
class Bar:
    date: str
    open: float
    high: float
    low: float
    close: float
    volume: float


def load_bars(path: str) -> list[Bar]:
    with open(path, newline="", encoding="utf-8-sig") as f:
        bars = [Bar(r["date"], *[float(r[k]) for k in ("open", "high", "low", "close", "volume")])
                for r in csv.DictReader(f)]
    if not bars:
        raise ValueError("No bars.")
    previous = ""
    for b in bars:
        date.fromisoformat(b.date)
        if b.date <= previous:
            raise ValueError("Dates must be unique and strictly increasing.")
        if not all(math.isfinite(v) for v in (b.open, b.high, b.low, b.close, b.volume)):
            raise ValueError("Nonfinite bar.")
        if min(b.open, b.high, b.low, b.close) <= 0 or b.volume < 0:
            raise ValueError("Invalid bar.")
        if b.low > min(b.open, b.close) or b.high < max(b.open, b.close) or b.low > b.high:
            raise ValueError("Inconsistent OHLC.")
        previous = b.date
    return bars


def synthetic_bars(n=300, seed=42) -> list[Bar]:
    rng, result, previous = random.Random(seed), [], 100.0
    day = date(2023, 1, 2)
    while len(result) < n:
        # Weekdays only. Synthetic calendar intentionally ignores real holidays.
        if day.weekday() < 5:
            opening = previous * math.exp(rng.gauss(0, .003))
            close = opening * math.exp(rng.gauss(.00015, .012))
            result.append(Bar(day.isoformat(), opening, max(opening, close) * 1.004,
                              min(opening, close) * .996, close, 1000000.0))
            previous = close
        day += timedelta(days=1)
    return result


def replay(bars: list[Bar], *, start=60, fast=10, slow=40, initial_cash=10000.0,
           allocation=.20, cost_bps=10.0, minimum_fee=1.0,
           max_drawdown=.08, buy_hold=False, cash_only=False) -> dict:
    if not (1 <= fast < slow <= start < len(bars)):
        raise ValueError("Require 1 <= fast < slow <= start < bar count.")
    if not all(math.isfinite(v) for v in (initial_cash, allocation, cost_bps, minimum_fee, max_drawdown)):
        raise ValueError("Nonfinite replay settings.")
    if initial_cash <= 0 or not 0 <= allocation <= 1 or min(cost_bps, minimum_fee) < 0 or not 0 < max_drawdown < 1:
        raise ValueError("Invalid replay settings.")
    cash, shares, peak, worst, fees, stopped = initial_cash, 0, initial_cash, 0., 0., False
    pending, fills, equity_curve = None, [], []
    for i in range(start, len(bars)):
        b = bars[i]
        # At the next session's opening, apply the quantity decided last close.
        # This is a simplified fill assumption, never proof of an actual fill.
        if pending is not None:
            delta, decision_date = pending
            side = 1 if delta > 0 else -1
            price = b.open * (1 + side * cost_bps / 10000)
            if price <= 0:
                raise ValueError("Invalid stress fill price.")
            if delta > 0:
                delta = min(delta, max(0, math.floor((cash - minimum_fee) / price)))
            else:
                delta = max(delta, -shares)
            if delta:
                cash -= delta * price + minimum_fee
                shares += delta
                fees += minimum_fee
                fills.append({"decision_date": decision_date, "fill_date": b.date,
                              "quantity": delta, "price": price, "fee": minimum_fee})
            pending = None
        equity = cash + shares * b.close
        peak = max(peak, equity)
        drawdown = 1 - equity / peak
        worst = max(worst, drawdown)
        if drawdown >= max_drawdown and not buy_hold:
            stopped = True  # latch persists for the remainder of this replay
        closes = [x.close for x in bars[i-slow+1:i+1]]
        signal = sum(closes[-fast:]) / fast > sum(closes) / slow
        target = 0 if cash_only or stopped else (allocation if buy_hold or signal else 0)
        # Trade only when entering or leaving; avoids artificial daily churn.
        if target == 0 and shares:
            pending = (-shares, b.date)
        elif target > 0 and shares == 0:
            quantity = math.floor(min(equity * target, max(0, cash - minimum_fee)) / b.close)
            if quantity:
                pending = (quantity, b.date)
        equity_curve.append({"date": b.date, "equity": equity, "cash": cash, "shares": shares})
    final = equity_curve[-1]["equity"]
    return {"status": "RESEARCH_ONLY", "net_return": final / initial_cash - 1,
            "max_drawdown": worst, "final_equity": final, "explicit_fees": fees,
            "fill_count": len(fills), "halt_latched": stopped,
            "unfilled_last_decision": pending is not None, "fills": fills,
            "equity_curve": equity_curve,
            "assumptions": {"initial_cash": initial_cash, "allocation_at_entry": allocation,
                "adverse_cost_bps_per_side": cost_bps, "flat_fee_per_fill": minimum_fee,
                "fill": "next completed bar open", "final_positions": "marked, not liquidated",
                "cash_interest": 0, "tax": "excluded", "dividends": "not booked separately",
                "settlement": "not simulated; not suitable for cash-account eligibility",
                "calendar": "input daily bars; source calendar not independently checked"}}


def compare(bars: list[Bar], synthetic: bool) -> dict:
    start = max(60, len(bars) // 2)
    options = {"start": start}
    return {"synthetic_data": synthetic,
            "warning": "Engineering demonstration, not evidence of profitable alpha." if synthetic
                       else "Preliminary baseline; data quality and execution assumptions need validation.",
            "evaluation_start": bars[start].date,
            "strategy": replay(bars, **options),
            "same_entry_allocation_buy_hold": replay(bars, buy_hold=True, **options),
            "cash_zero_interest": replay(bars, cash_only=True, **options),
            "double_adverse_cost_strategy": replay(bars, cost_bps=20, **options)}

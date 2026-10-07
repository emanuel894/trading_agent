from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime
from typing import Mapping, Protocol, Sequence


@dataclass(frozen=True)
class QuoteSnapshot:
    symbol: str
    bid: float
    ask: float
    timestamp: datetime | None


@dataclass(frozen=True)
class BrokerProbe:
    status: str
    broker: str
    mode: str
    account_status: str
    currency: str
    market_is_open: bool
    clock_timestamp: datetime | None
    next_open: datetime | None
    next_close: datetime | None
    positions_count: int
    open_orders_count: int
    quotes: Mapping[str, QuoteSnapshot]


class BrokerAdapter(Protocol):
    """Read-only broker contract used by the foundation stage.

    Order submission is deliberately absent. Execution will be added later behind
    the deterministic risk gate and durable order manager.
    """

    @property
    def broker_name(self) -> str: ...

    @property
    def mode(self) -> str: ...

    def probe(self, symbols: Sequence[str]) -> BrokerProbe: ...

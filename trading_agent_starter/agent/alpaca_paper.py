from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime
import math
import os
from typing import Callable, Sequence

from .broker import BrokerProbe, QuoteSnapshot


def _truthy(value: str | None) -> bool:
    return (value or "").strip().lower() in {"1", "true", "yes", "on"}


def _text(value) -> str:
    if value is None:
        return ""
    return str(getattr(value, "value", value))


def _number(value) -> float:
    result = float(value)
    if not math.isfinite(result):
        raise ValueError("Broker returned a non-finite quote value")
    return result


def _iso(value: datetime | None) -> str | None:
    return value.isoformat() if value is not None else None


def _missing_dependency_error(exc: ModuleNotFoundError) -> RuntimeError:
    missing = exc.name or "unknown"
    return RuntimeError(
        f"Missing Python dependency '{missing}'. Run: pip install -r requirements.txt"
    )


@dataclass(frozen=True)
class AlpacaPaperConfig:
    api_key: str
    secret_key: str
    data_feed: str = "iex"

    @classmethod
    def from_env(cls) -> "AlpacaPaperConfig":
        try:
            from dotenv import load_dotenv

            load_dotenv()
        except ModuleNotFoundError:
            # Environment variables can still be supplied by the shell/host.
            pass

        broker = os.getenv("BROKER", "alpaca").strip().lower()
        if broker != "alpaca":
            raise ValueError("BROKER must be 'alpaca' for the Alpaca Paper probe")
        if not _truthy(os.getenv("ALPACA_PAPER")):
            raise ValueError("ALPACA_PAPER=true is required; live Alpaca is blocked")
        if _truthy(os.getenv("ALPACA_LIVE_TRADE")):
            raise ValueError("ALPACA_LIVE_TRADE must not be enabled")
        if _truthy(os.getenv("TRADING_ENABLED")):
            raise ValueError("TRADING_ENABLED must remain false during the read-only stage")
        if _truthy(os.getenv("ALLOW_PAPER_ORDERS")):
            raise ValueError("ALLOW_PAPER_ORDERS must remain false during the read-only stage")

        api_key = os.getenv("ALPACA_API_KEY", "").strip()
        secret_key = (
            os.getenv("ALPACA_API_SECRET", "").strip()
            or os.getenv("ALPACA_SECRET_KEY", "").strip()
        )
        if not api_key or not secret_key:
            raise ValueError("Missing Alpaca Paper API credentials in local environment")

        data_feed = os.getenv("ALPACA_DATA_FEED", "iex").strip().lower()
        if data_feed != "iex":
            raise ValueError("Foundation 0.2 locks ALPACA_DATA_FEED to 'iex'")
        return cls(api_key=api_key, secret_key=secret_key, data_feed=data_feed)


class AlpacaPaperAdapter:
    """Read-only Alpaca Paper adapter.

    This class intentionally has no order submission method. The real SDK client
    is always constructed with paper=True. Execution belongs to a later phase,
    behind deterministic risk checks and the durable order manager.
    """

    def __init__(
        self,
        config: AlpacaPaperConfig,
        *,
        trading_client=None,
        data_client=None,
        quote_request_factory: Callable[[Sequence[str]], object] | None = None,
        open_orders_request_factory: Callable[[], object] | None = None,
    ):
        self.config = config
        self._trading = trading_client or self._build_trading_client(config)
        self._data = data_client or self._build_data_client(config)
        self._quote_request_factory = quote_request_factory or self._build_quote_request
        self._open_orders_request_factory = (
            open_orders_request_factory or self._build_open_orders_request
        )

    @property
    def broker_name(self) -> str:
        return "alpaca"

    @property
    def mode(self) -> str:
        return "paper-read-only"

    @staticmethod
    def _build_trading_client(config: AlpacaPaperConfig):
        try:
            from alpaca.trading.client import TradingClient
        except ModuleNotFoundError as exc:
            raise _missing_dependency_error(exc) from exc
        # The hard-coded paper=True is a safety boundary for this adapter.
        return TradingClient(config.api_key, config.secret_key, paper=True)

    @staticmethod
    def _build_data_client(config: AlpacaPaperConfig):
        try:
            from alpaca.data.historical import StockHistoricalDataClient
        except ModuleNotFoundError as exc:
            raise _missing_dependency_error(exc) from exc
        return StockHistoricalDataClient(config.api_key, config.secret_key)

    @staticmethod
    def _build_quote_request(symbols: Sequence[str]):
        from alpaca.data.enums import DataFeed
        from alpaca.data.requests import StockLatestQuoteRequest

        return StockLatestQuoteRequest(
            symbol_or_symbols=list(symbols),
            feed=DataFeed.IEX,
        )

    @staticmethod
    def _build_open_orders_request():
        from alpaca.trading.enums import QueryOrderStatus
        from alpaca.trading.requests import GetOrdersRequest

        return GetOrdersRequest(status=QueryOrderStatus.OPEN)

    def probe(self, symbols: Sequence[str]) -> BrokerProbe:
        normalized = tuple(
            dict.fromkeys(symbol.strip().upper() for symbol in symbols if symbol.strip())
        )
        if not normalized:
            raise ValueError("At least one symbol is required for the market-data probe")
        if len(normalized) > 50:
            raise ValueError("Connection probe is limited to 50 symbols")

        account = self._trading.get_account()
        clock = self._trading.get_clock()
        positions = self._trading.get_all_positions()
        open_orders = self._trading.get_orders(
            filter=self._open_orders_request_factory()
        )
        raw_quotes = self._data.get_stock_latest_quote(
            self._quote_request_factory(normalized)
        )

        quotes: dict[str, QuoteSnapshot] = {}
        for symbol in normalized:
            quote = raw_quotes.get(symbol)
            if quote is None:
                raise RuntimeError(f"No latest quote returned for {symbol}")
            quotes[symbol] = QuoteSnapshot(
                symbol=symbol,
                bid=_number(quote.bid_price),
                ask=_number(quote.ask_price),
                timestamp=getattr(quote, "timestamp", None),
            )

        return BrokerProbe(
            status="READ_ONLY_CHECK_PASSED",
            broker=self.broker_name,
            mode=self.mode,
            account_status=_text(getattr(account, "status", "")),
            currency=_text(getattr(account, "currency", "")),
            market_is_open=bool(getattr(clock, "is_open", False)),
            clock_timestamp=getattr(clock, "timestamp", None),
            next_open=getattr(clock, "next_open", None),
            next_close=getattr(clock, "next_close", None),
            positions_count=len(positions),
            open_orders_count=len(open_orders),
            quotes=quotes,
        )


def probe_to_dict(probe: BrokerProbe) -> dict:
    return {
        "status": probe.status,
        "broker": probe.broker,
        "mode": probe.mode,
        "account_status": probe.account_status,
        "currency": probe.currency,
        "market_is_open": probe.market_is_open,
        "clock_timestamp": _iso(probe.clock_timestamp),
        "next_open": _iso(probe.next_open),
        "next_close": _iso(probe.next_close),
        "positions_count": probe.positions_count,
        "open_orders_count": probe.open_orders_count,
        "quotes": {
            symbol: {
                "bid": quote.bid,
                "ask": quote.ask,
                "timestamp": _iso(quote.timestamp),
            }
            for symbol, quote in probe.quotes.items()
        },
    }


def run_from_env(symbols: Sequence[str] = ("SPY", "QQQ")) -> dict:
    config = AlpacaPaperConfig.from_env()
    adapter = AlpacaPaperAdapter(config)
    return probe_to_dict(adapter.probe(symbols))

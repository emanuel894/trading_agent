"""Read-only historical provider. No strategy, risk sizing, or order methods."""
from __future__ import annotations

from datetime import date, datetime, timezone
from pathlib import Path

from .alpaca_paper import AlpacaPaperAdapter, AlpacaPaperConfig, _missing_dependency_error
from .market_data import HistoryRequest, HistorySnapshot, RawBar, Session, normalize_bars, write_snapshot


class AlpacaHistoryProvider:
    def __init__(self, config: AlpacaPaperConfig, *, data_client=None, calendar_client=None):
        if config.data_feed != "iex":
            raise ValueError("Historical foundation requires the IEX feed")
        self._data = data_client if data_client is not None else AlpacaPaperAdapter._build_data_client(config)
        self._calendar = calendar_client if calendar_client is not None else AlpacaPaperAdapter._build_trading_client(config)

    def fetch(self, request: HistoryRequest) -> HistorySnapshot:
        try:
            import pytz
            from alpaca.common.enums import Sort
            from alpaca.data.enums import Adjustment, DataFeed
            from alpaca.data.requests import StockBarsRequest
            from alpaca.data.timeframe import TimeFrame, TimeFrameUnit
            from alpaca.trading.requests import GetCalendarRequest
        except ModuleNotFoundError as exc:
            raise _missing_dependency_error(exc) from exc

        # The pinned SDK documents this calendar coverage. Never silently treat
        # an unsupported year as a market holiday.
        if request.start.date() < date(1970, 1, 1) or request.end.date() > date(2029, 12, 31):
            raise ValueError("Pinned Alpaca calendar supports 1970–2029")
        bars_request = StockBarsRequest(
            symbol_or_symbols=list(request.symbols), start=request.start, end=request.end,
            timeframe=TimeFrame(30, TimeFrameUnit.Minute), feed=DataFeed.IEX,
            adjustment=Adjustment.RAW, asof="-", sort=Sort.ASC,
            # No limit: in alpaca-py this is a TOTAL row cap across all symbols,
            # not a page size. The SDK follows next_page_token automatically.
        )
        try:
            calendar = self._calendar.get_calendar(GetCalendarRequest(
                start=request.start.date(), end=request.end.date()))
            raw = self._data.get_stock_bars(bars_request)
        except Exception:
            # SDK errors can contain request/header details. Never echo them.
            raise RuntimeError("Alpaca history read failed; check local connectivity and data access") from None

        eastern = pytz.timezone("America/New_York")

        def calendar_time(value):
            # Alpaca 0.42.2 Calendar emits naive New York wall times, unlike bars.
            return eastern.localize(value, is_dst=None) if value.utcoffset() is None else value

        try:
            sessions = [Session(calendar_time(day.open), calendar_time(day.close)) for day in calendar]
            rows = []
            for symbol, bars in raw.data.items():
                for bar in bars:
                    if bar.symbol != symbol:
                        raise ValueError("Bar symbol disagrees with response key")
                    rows.append(RawBar(symbol, bar.timestamp, bar.open, bar.high, bar.low, bar.close, bar.volume))
            return normalize_bars(request, sessions, rows, source="alpaca", feed="iex")
        except (AttributeError, TypeError, KeyError):
            raise ValueError("Malformed Alpaca historical response") from None


def run_history(request: HistoryRequest, output: Path) -> dict:
    if request.as_of > datetime.now(timezone.utc):
        raise ValueError("as_of cannot be in the future")
    if output.exists():
        raise ValueError("Output already exists; choose a new snapshot directory")
    provider = AlpacaHistoryProvider(AlpacaPaperConfig.from_env())
    snapshot = provider.fetch(request)
    return write_snapshot(snapshot, output, retrieved_at=datetime.now(timezone.utc))

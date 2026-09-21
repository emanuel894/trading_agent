"""Amendment 003 provider-native daily bars; never regular-session aggregates."""
from datetime import datetime, timedelta
from decimal import Decimal, InvalidOperation
import re

from .audit_market import EASTERN
from .audit_store import AuditFailure, timestamp

LIQUIDITY_VERSION = "alpaca-sip-1day-ny-calendar-v1"
INPUT_VERSION = "adr001-universe-inputs-v2"
CONTRACT = {"provider": "alpaca", "timeframe": "1Day", "feed": "sip",
            "adjustment": "raw", "asof": "-", "session": "PROVIDER_NATIVE_NY_CALENDAR_DAY",
            "liquidity_definition_version": LIQUIDITY_VERSION}
REQUEST = {k: CONTRACT[k] for k in ("timeframe", "feed", "adjustment", "asof")}


def validate_contract(row):
    if any(row.get(k) != v for k, v in CONTRACT.items()):
        raise AuditFailure("UNREGISTERED_PROVIDER_NATIVE_DAILY_CONTRACT")


def daily_date(value):
    # datetime truncates sub-microsecond digits; do not accept a nonzero tail.
    fraction = re.search(r"\.(\d+)", value) if isinstance(value, str) else None
    if fraction and any(c != "0" for c in fraction.group(1)):
        raise AuditFailure("DAILY_TIMESTAMP_NOT_NEW_YORK_MIDNIGHT")
    local = timestamp(value).astimezone(EASTERN)
    if any((local.hour, local.minute, local.second, local.microsecond)):
        raise AuditFailure("DAILY_TIMESTAMP_NOT_NEW_YORK_MIDNIGHT")
    return local.date().isoformat()


def bucket_end(day):
    # Localize the next calendar midnight independently across DST boundaries.
    next_day = datetime.strptime(day, "%Y-%m-%d") + timedelta(days=1)
    return EASTERN.localize(next_day)


def positive(value):
    if isinstance(value, bool) or not isinstance(value, (str, int, float, Decimal)):
        raise AuditFailure("INVALID_DAILY_NUMBER")
    try:
        result = Decimal(str(value))
    except InvalidOperation:
        raise AuditFailure("INVALID_DAILY_NUMBER") from None
    if not result.is_finite() or result <= 0:
        raise AuditFailure("NONPOSITIVE_OR_NONFINITE_DAILY_NUMBER")
    return result


def validate_daily_bar(row, expected_dates=None):
    if not isinstance(row, dict) or not {"t", "o", "h", "l", "c", "v"}.issubset(row):
        raise AuditFailure("MALFORMED_PROVIDER_DAILY_BAR")
    day = daily_date(row["t"])
    if expected_dates is not None and day not in expected_dates:
        raise AuditFailure("DAILY_DATE_OUTSIDE_REQUESTED_SESSIONS")
    opening, high, low, close, volume = [positive(row[k]) for k in ("o", "h", "l", "c", "v")]
    if not low <= min(opening, close) <= max(opening, close) <= high:
        raise AuditFailure("INVALID_DAILY_OHLC_RANGE")
    if volume != volume.to_integral_value():
        raise AuditFailure("NONINTEGER_DAILY_VOLUME")
    return day

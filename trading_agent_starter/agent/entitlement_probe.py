"""Run a minimal read-only historical Alpaca SIP entitlement probe.

This module is deliberately independent of the 10-Q audit context, security
master, status inputs, strategy code, model code, and broker/order code.  It
requests one completed historical window for AAPL and SPY using only the
Alpaca SIP feed.  Every response is retained in the append-only evidence
store and the report never contains credentials or response bodies.

The real-time websocket result is supplied by the separately run probe and is
recorded as ``REALTIME_SIP = NOT_ENTITLED``.  This command never opens a
websocket, submits an order, falls back to IEX, forecasts returns, or invokes
an LLM.
"""
from __future__ import annotations

import argparse
from datetime import timedelta
import json
import math
import os
from pathlib import Path
import re
import time
import uuid
from urllib.parse import parse_qs, urlsplit

from .audit_http import ReadOnlyHTTP
from .audit_market import SIPSource, nanoseconds, validate_bar, validate_quote
from .audit_store import AuditFailure, EvidenceStore, strict_json, timestamp, utc_now


SYMBOLS = ("AAPL", "SPY")
REALTIME_SIP = "NOT_ENTITLED"
PROBE_VERSION = "sip-entitlement-v1"
DEFAULT_LAG_MINUTES = 30
DEFAULT_WINDOW_MINUTES = 5
DEFAULT_HISTORICAL_START = "2025-01-15T15:00:00+00:00"
DEFAULT_HISTORICAL_END = "2025-01-15T15:05:00+00:00"


def credentials_from_env():
    """Return market-data credentials without importing the full audit."""
    try:
        from dotenv import load_dotenv
        load_dotenv()
    except ImportError:
        pass
    for key in ("TRADING_ENABLED", "ALLOW_PAPER_ORDERS", "ALPACA_LIVE_TRADE"):
        if os.getenv(key, "").lower() in {"1", "true", "yes", "on"}:
            raise AuditFailure("READ_ONLY_FLAGS_REQUIRED")
    key = os.getenv("ALPACA_API_KEY") or os.getenv("APCA_API_KEY_ID")
    secret = (os.getenv("ALPACA_API_SECRET") or os.getenv("ALPACA_SECRET_KEY")
              or os.getenv("APCA_API_SECRET_KEY"))
    return (key, secret) if key and secret else None


def completed_window(*, now=None, lag_minutes=DEFAULT_LAG_MINUTES,
                     window_minutes=DEFAULT_WINDOW_MINUTES):
    """Choose a completed UTC window, avoiding a partial current minute.

    The optional explicit window flags make a run reproducible.  The default
    is intentionally at least 30 minutes old so it does not test the latest
    Basic-feed delay boundary.  It is not a trading or regular-session rule.
    """
    if not 1 <= lag_minutes <= 24 * 60 or not 1 <= window_minutes <= 60:
        raise AuditFailure("INVALID_WINDOW_BOUNDS")
    current = timestamp(now or utc_now()).replace(second=0, microsecond=0)
    end = current - timedelta(minutes=lag_minutes)
    start = end - timedelta(minutes=window_minutes)
    if start >= end or end > timestamp(utc_now()):
        raise AuditFailure("MARKET_WINDOW_NOT_COMPLETE")
    return start.isoformat(), end.isoformat()


def default_historical_window():
    """Return a reproducible ordinary-session window known to be complete."""
    start, end = DEFAULT_HISTORICAL_START, DEFAULT_HISTORICAL_END
    if not timestamp(start) < timestamp(end) <= timestamp(utc_now()):
        raise AuditFailure("MARKET_WINDOW_NOT_COMPLETE")
    return start, end


def _request_is_sip(url):
    parsed = urlsplit(url)
    params = parse_qs(parsed.query, keep_blank_values=True)
    if parsed.hostname != "data.alpaca.markets" or params.get("feed") != ["sip"]:
        raise AuditFailure("SIP_FEED_NOT_ENFORCED")
    if any(value.lower() == "iex" for values in params.values() for value in values):
        raise AuditFailure("IEX_FALLBACK_FORBIDDEN")


def _frequency_key(value):
    if value is None:
        return "MISSING"
    if isinstance(value, str) and 0 < len(value) <= 32:
        return value
    return "INVALID"


def _bump(mapping, key):
    mapping[key] = mapping.get(key, 0) + 1


def _quality_template(kind):
    return {
        "data_kind": kind,
        "total_rows_by_symbol": {symbol: 0 for symbol in SYMBOLS},
        "quote_condition_frequencies": {},
        "tape_frequencies": {},
        "exchange_frequencies": {"bid": {}, "ask": {}},
        "locked_quotes": 0,
        "crossed_quotes": 0,
        "zero_bid_ask": 0,
        "zero_size": 0,
        "malformed_rows": 0,
        "strict_execution_quality_pass_rows_by_symbol": {symbol: 0 for symbol in SYMBOLS},
        "strict_execution_quality_pass_rows": 0,
        "strict_policy_rejection_frequencies": {},
        "historical_freshness_check": "NOT_APPLIED",
        "quality_validation_affects_entitlement": False,
    }


def _collect_quality(kind, rows):
    """Collect diagnostics without allowing quality policy to gate access."""
    quality = _quality_template(kind)
    for symbol in SYMBOLS:
        values = rows.get(symbol, [])
        quality["total_rows_by_symbol"][symbol] = len(values)
    if kind != "quotes":
        for symbol in SYMBOLS:
            for row, _, _ in rows.get(symbol, []):
                try:
                    validate_bar(row)
                except (AuditFailure, KeyError, TypeError, ValueError):
                    quality["malformed_rows"] += 1
        return quality

    for symbol in SYMBOLS:
        for row, _, _ in rows.get(symbol, []):
            if not isinstance(row, dict) or not isinstance(row.get("t"), str):
                quality["malformed_rows"] += 1
                continue
            try:
                nanoseconds(row["t"])
            except AuditFailure:
                quality["malformed_rows"] += 1
                continue
            for field in ("c", "z", "bx", "ax", "bp", "ap", "bs", "as"):
                if field not in row:
                    quality["malformed_rows"] += 1
                    break
            else:
                if not isinstance(row["c"], list) or not isinstance(row["z"], str):
                    quality["malformed_rows"] += 1
                    continue
                for condition in row["c"] or [None]:
                    _bump(quality["quote_condition_frequencies"], _frequency_key(condition))
                _bump(quality["tape_frequencies"], _frequency_key(row["z"]))
                _bump(quality["exchange_frequencies"]["bid"], _frequency_key(row["bx"]))
                _bump(quality["exchange_frequencies"]["ask"], _frequency_key(row["ax"]))
                numeric = [row[field] for field in ("bp", "ap", "bs", "as")]
                if any(isinstance(value, bool) or not isinstance(value, (int, float))
                       or not math.isfinite(value) for value in numeric):
                    quality["malformed_rows"] += 1
                    continue
                if row["bp"] == 0 or row["ap"] == 0:
                    quality["zero_bid_ask"] += 1
                if row["bs"] == 0 or row["as"] == 0:
                    quality["zero_size"] += 1
                if row["bp"] == row["ap"]:
                    quality["locked_quotes"] += 1
                elif row["bp"] > row["ap"]:
                    quality["crossed_quotes"] += 1
                try:
                    # validate_quote's freshness rule is intentionally evaluated
                    # at the row timestamp; historical reception age is not
                    # execution quality and cannot be reconstructed here.
                    validate_quote(row, row["t"])
                except AuditFailure as exc:
                    _bump(quality["strict_policy_rejection_frequencies"], str(exc))
                else:
                    quality["strict_execution_quality_pass_rows_by_symbol"][symbol] += 1
                    quality["strict_execution_quality_pass_rows"] += 1
    return quality


def _response_text(store, records):
    """Return a bounded, internal-only response text for classification."""
    chunks = []
    for record in records[-3:]:
        if not record.get("blob_sha"):
            continue
        chunks.append(store.raw(record)[:4096].decode("utf-8", errors="ignore").lower())
    return "\n".join(chunks)


def classify_failure(store, records, failure):
    """Map provider/network outcomes to stable, report-safe categories."""
    metadata = [record.get("metadata", {}) for record in records]
    statuses = {item.get("http_status") for item in metadata}
    text = _response_text(store, records)
    if failure == "SIP_CREDENTIALS_UNAVAILABLE":
        return "CREDENTIALS_UNAVAILABLE", failure
    if 401 in statuses or re.search(r"\bauth(?:entication|orization)?\b|invalid.{0,12}key", text):
        return "AUTHENTICATION_FAILED", failure or "HTTP_401"
    if re.search(r"15[ -]?minute|delayed|delay(?:ed)?[- ]only|latest.{0,12}minute", text):
        return "DELAYED_LIMITED", failure or "DELAYED_PROVIDER_RESPONSE"
    if (403 in statuses or 429 in statuses or re.search(
            r"subscription|entitle|permission|forbidden|not allowed|upgrade|"
            r"not.{0,12}(enabled|included|available|permitted)|"
            r"feed.{0,12}(access|available|enabled)|sip.{0,12}(access|permission|plan|available)", text)):
        return "PROVIDER_RESTRICTION", failure or "PROVIDER_RESTRICTION"
    if failure:
        return "FAILED", failure
    return "OTHER_PROVIDER_RESPONSE", "UNEXPECTED_PROVIDER_RESPONSE"


def _http_records(store, url_prefix):
    return [record for record in store.records("http")
            if record["source_key"].startswith(url_prefix)]


def _provenance(records):
    return [{
        "record_id": record["id"],
        "source_url": record["source_key"],
        "raw_sha256": record.get("blob_sha"),
        "http_status": record["metadata"].get("http_status"),
        "first_observed_at": record["metadata"].get("started_at"),
        "ingestion_complete_at": record["metadata"].get("received_at"),
        "elapsed_seconds": record["metadata"].get("elapsed_seconds"),
    } for record in records]


def _recover_rows(store, records, kind):
    """Recover already-received 200-page rows after a non-quality abort."""
    rows = {symbol: [] for symbol in SYMBOLS}
    for record in records:
        if record["metadata"].get("http_status") != 200 or not record.get("blob_sha"):
            continue
        try:
            body = strict_json(store.raw(record))
        except AuditFailure:
            continue
        batches = body.get(kind) if isinstance(body, dict) else None
        if not isinstance(batches, dict):
            continue
        received = record["metadata"].get("received_at")
        for symbol in SYMBOLS:
            values = batches.get(symbol)
            if not isinstance(values, list):
                continue
            rows[symbol].extend((row, record["id"], received) for row in values)
    return rows


def _is_empty_success(store, records, kind):
    """Recognize a valid 200 response whose requested symbols had no rows."""
    seen, any_page = set(), False
    for record in records:
        if record["metadata"].get("http_status") != 200 or not record.get("blob_sha"):
            return False
        try:
            body = strict_json(store.raw(record))
        except AuditFailure:
            return False
        batches = body.get(kind) if isinstance(body, dict) else None
        if not isinstance(batches, dict):
            return False
        any_page = True
        if any(symbol not in batches or not isinstance(batches[symbol], list) for symbol in SYMBOLS):
            return False
        seen.update(batches)
        if any(batches[symbol] for symbol in SYMBOLS):
            return False
        if body.get("next_page_token"):
            return False
    return any_page and seen == set(SYMBOLS)


def _endpoint_result(store, market, kind, start, end):
    endpoint = f"https://data.alpaca.markets/v2/stocks/{kind}"
    started, tick = utc_now(), time.monotonic()
    result = {
        "endpoint": kind,
        "symbols": list(SYMBOLS),
        "window": {"start": start, "end": end, "completed": True},
        "feed": "sip",
        "quote_contract": "SIP/NBBO" if kind == "quotes" else None,
        "request_ids": [],
        "responses": [],
        "http_statuses": [],
        "rows_by_symbol": {symbol: 0 for symbol in SYMBOLS},
        "basic_access": "FAILED",
        "classification": "FAILED",
        "reason_code": None,
        "started_at": started,
        "finished_at": None,
        "elapsed_seconds": None,
        "no_iex_fallback": True,
        "provider_access": "UNKNOWN",
        "row_coverage": "UNKNOWN",
        "data_quality": _quality_template(kind),
    }
    try:
        rows, request_ids = market.pages(kind, list(SYMBOLS), start, end)
        result["request_ids"] = list(request_ids)
        records = [store.get(record_id) for record_id in request_ids]
        result["responses"] = _provenance(records)
        for record in records:
            _request_is_sip(record["source_key"])
        result["http_statuses"] = [record["metadata"].get("http_status") for record in records]
        if not records or any(status != 200 for status in result["http_statuses"]):
            raise AuditFailure("UNEXPECTED_HTTP_STATUS")
        result["provider_access"] = "SUCCEEDED"
        for symbol, values in rows.items():
            result["rows_by_symbol"][symbol] = len(values)
        result["data_quality"] = _collect_quality(kind, rows)
        if all(result["rows_by_symbol"].values()):
            result["classification"] = "SUCCEEDED_WITH_ROWS"
            result["basic_access"] = "SUCCEEDED"
            result["row_coverage"] = "COMPLETE"
        else:
            result["classification"] = "SUCCEEDED_EMPTY"
            result["basic_access"] = "SUCCEEDED_EMPTY"
            result["row_coverage"] = "PARTIAL_OR_EMPTY"
        result["reason_code"] = None
    except AuditFailure as exc:
        failure = str(exc)
        records = _http_records(store, endpoint)
        result["request_ids"] = [record["id"] for record in records]
        result["responses"] = _provenance(records)
        result["http_statuses"] = [record["metadata"].get("http_status") for record in records]
        feed_valid = True
        for record in records:
            try:
                _request_is_sip(record["source_key"])
            except AuditFailure:
                result["no_iex_fallback"] = False
                feed_valid = False
        recovered = _recover_rows(store, records, kind)
        for symbol, values in recovered.items():
            result["rows_by_symbol"][symbol] = len(values)
        empty_success = _is_empty_success(store, records, kind)
        if (feed_valid and records and all(status == 200 for status in result["http_statuses"])
                and (any(result["rows_by_symbol"].values()) or empty_success)):
            result["provider_access"] = "SUCCEEDED"
            result["data_quality"] = _collect_quality(kind, recovered)
        if not feed_valid:
            classification, reason = "FAILED", "SIP_FEED_NOT_ENFORCED"
        elif all(result["rows_by_symbol"].values()):
            classification, reason = "SUCCEEDED_WITH_ROWS", None
            result["row_coverage"] = "COMPLETE"
            result["basic_access"] = "SUCCEEDED"
        elif any(result["rows_by_symbol"].values()) and result["provider_access"] == "SUCCEEDED":
            classification, reason = "SUCCEEDED_PARTIAL_ROWS", "MISSING_ROWS_FOR_SYMBOL"
            result["row_coverage"] = "PARTIAL"
            result["basic_access"] = "SUCCEEDED"
        elif empty_success:
            classification, reason = "SUCCEEDED_EMPTY", "NO_ROWS_IN_WINDOW"
            result["row_coverage"] = "EMPTY"
            result["basic_access"] = "SUCCEEDED_EMPTY"
        else:
            classification, reason = classify_failure(store, records, failure)
        result["classification"] = classification
        if result["basic_access"] == "FAILED":
            result["basic_access"] = classification
        result["reason_code"] = reason
    finally:
        result["finished_at"] = utc_now()
        result["elapsed_seconds"] = time.monotonic() - tick
    return result


def _historical_summary(results, credentials):
    classes = [result["classification"] for result in results]
    if not credentials:
        status = "CREDENTIALS_UNAVAILABLE"
    elif all(value == "SUCCEEDED_WITH_ROWS" for value in classes):
        status = "SUFFICIENT_FOR_BACKFILL"
    elif any(value == "DELAYED_LIMITED" for value in classes):
        status = "DELAYED_LIMITED"
    elif any(value in {"PROVIDER_RESTRICTION", "AUTHENTICATION_FAILED"} for value in classes):
        status = "NOT_ENTITLED_OR_RESTRICTED"
    elif all(value in {"SUCCEEDED_WITH_ROWS", "SUCCEEDED_PARTIAL_ROWS", "SUCCEEDED_EMPTY"}
             for value in classes):
        status = "HISTORICAL_SIP_ACCESSIBLE_INCOMPLETE"
    else:
        status = "FAILED"
    return {"status": status, "endpoint_classifications": classes,
            "provider_access_succeeded": all(result.get("provider_access") == "SUCCEEDED"
                                               for result in results),
            "access_sufficient_for_backfill": status == "SUFFICIENT_FOR_BACKFILL"}


def run_probe(store_path, *, start=None, end=None):
    store = EvidenceStore(store_path)
    run_id = f"sip-entitlement-{uuid.uuid4().hex}"
    started = utc_now()
    credentials = None
    results = []
    top_failure = None
    try:
        store.verify()
        try:
            credentials = credentials_from_env()
        except AuditFailure as exc:
            top_failure = str(exc)
        if (start is None) != (end is None):
            raise AuditFailure("BOTH_WINDOW_BOUNDS_REQUIRED")
        if start is None:
            start, end = default_historical_window()
        if not timestamp(start) < timestamp(end) <= timestamp(utc_now()):
            raise AuditFailure("MARKET_WINDOW_NOT_COMPLETE")
        if credentials:
            http = ReadOnlyHTTP(
                store,
                user_agent="TradingAgentSIPEntitlementProbe/1.0 (read-only; no orders)",
                credentials=credentials,
                max_requests=100,
            )
            market = SIPSource(store, http)
            for kind in ("bars", "quotes"):
                results.append(_endpoint_result(store, market, kind, start, end))
        else:
            if top_failure is None:
                top_failure = "CREDENTIALS_UNAVAILABLE"
            results = [{
                "endpoint": kind, "symbols": list(SYMBOLS),
                "window": {"start": start, "end": end, "completed": True},
                "feed": "sip", "quote_contract": "SIP/NBBO" if kind == "quotes" else None,
                "request_ids": [], "http_statuses": [],
                "responses": [],
                "rows_by_symbol": {symbol: 0 for symbol in SYMBOLS},
                "data_quality": _quality_template(kind),
                "basic_access": "CREDENTIALS_UNAVAILABLE",
                "classification": "CREDENTIALS_UNAVAILABLE",
                "reason_code": top_failure, "started_at": started,
                "finished_at": utc_now(), "elapsed_seconds": 0.0,
                "no_iex_fallback": True,
            } for kind in ("bars", "quotes")]
        report = {
            "version": PROBE_VERSION,
            "run_id": run_id,
            "probe_started_at": started,
            "probe_finished_at": utc_now(),
            "symbols": list(SYMBOLS),
            "historical_sip": _historical_summary(results, credentials),
            "results": results,
            "data_quality": {result["endpoint"]: result["data_quality"] for result in results},
            "REALTIME_SIP": REALTIME_SIP,
            "real_time_result_source": "separately run websocket probe; supplied result",
            "subscription_action": "NONE_PURCHASED_OR_RECOMMENDED",
            "orders_sent": 0,
            "forecasting": "NOT_RUN",
            "llm": False,
            "execution": "READ_ONLY",
            "no_iex_fallback": True,
            "evidence_integrity_before_report": store.verify(),
        }
        store.append("entitlement_probe_report", run_id, report)
        report["evidence_integrity"] = store.verify()
        path = Path(store_path) / f"report_{run_id}.json"
        with path.open("x", encoding="utf-8") as handle:
            json.dump(report, handle, indent=2, allow_nan=False)
        return report, path, 0 if report["historical_sip"]["access_sufficient_for_backfill"] else 2
    except (AuditFailure, OSError, ValueError, KeyError, TypeError) as exc:
        reason = str(exc) if isinstance(exc, AuditFailure) else "INVALID_INPUT_OR_LOCAL_IO_FAILURE"
        store.append("entitlement_probe_failure", run_id,
                     {"version": PROBE_VERSION, "reason": reason, "at": utc_now(),
                      "REALTIME_SIP": REALTIME_SIP})
        raise
    finally:
        store.close()


def main(argv=None):
    parser = argparse.ArgumentParser(
        description="Read-only historical AAPL/SPY SIP bars and quotes entitlement probe; no IEX, orders, LLM, or strategy")
    parser.add_argument("--store", default=None,
                        help="Evidence directory (default: runs/sip_entitlement_<UTC timestamp>)")
    parser.add_argument("--start", default=None, help="Explicit completed-window UTC ISO timestamp")
    parser.add_argument("--end", default=None, help="Explicit completed-window UTC ISO timestamp")
    args = parser.parse_args(argv)
    if (args.start is None) != (args.end is None):
        print(json.dumps({"status": "STOPPED", "reason": "BOTH_WINDOW_BOUNDS_REQUIRED"}))
        return 2
    store_path = args.store or str(Path("runs") / ("sip_entitlement_" + utc_now().replace(":", "").replace("+00:00", "Z")))
    try:
        report, path, code = run_probe(store_path, start=args.start, end=args.end)
        print(json.dumps({
            "status": report["historical_sip"]["status"],
            "REALTIME_SIP": report["REALTIME_SIP"],
            "window": report["results"][0]["window"],
            "bars": report["results"][0]["classification"],
            "quotes": report["results"][1]["classification"],
            "report": str(path),
        }, indent=2))
        return code
    except (AuditFailure, OSError, ValueError, KeyError, TypeError) as exc:
        reason = str(exc) if isinstance(exc, AuditFailure) else "INVALID_INPUT_OR_LOCAL_IO_FAILURE"
        print(json.dumps({"status": "STOPPED", "reason": reason,
                          "REALTIME_SIP": REALTIME_SIP}))
        return 2


if __name__ == "__main__":
    raise SystemExit(main())

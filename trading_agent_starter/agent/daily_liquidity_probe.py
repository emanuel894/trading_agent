"""Fixed six-bar read-only smoke test. No universe acquisition or cohort write."""
import argparse
from collections import Counter
from pathlib import Path
import uuid
from urllib.parse import urlencode

from .alpaca_daily_contract import CONTRACT, REQUEST, validate_daily_bar
from .audit_http import ReadOnlyHTTP
from .audit_store import AuditFailure, EvidenceStore, canonical, strict_json, utc_now
from .entitlement_probe import credentials_from_env, classify_failure, _provenance

SYMBOLS = ("AAPL", "SPY")
DATES = ("2025-01-13", "2025-01-14", "2025-01-15")
URL = "https://data.alpaca.markets/v2/stocks/bars"
PARAMS = {**REQUEST, "symbols": ",".join(SYMBOLS), "start": "2025-01-13T05:00:00Z",
          "end": "2025-01-16T04:59:59Z", "limit": "100", "sort": "asc"}


def run_probe(http, store):
    """Provider access is independent of OHLCV/date/completeness checks."""
    before = {r["id"] for r in store.records("http")}
    rows = {symbol: [] for symbol in SYMBOLS}
    failure, token, seen = None, None, set()
    try:
        for _ in range(3):
            params = dict(PARAMS)
            if token:
                params["page_token"] = token
            request_url = URL + "?" + urlencode(params)
            record = http.get(request_url, max_bytes=65536)
            if record["source_key"] != request_url or record["metadata"].get("http_status") != 200:
                raise AuditFailure("UNBOUND_PROVIDER_RESPONSE")
            body = strict_json(store.raw(record))
            if (not isinstance(body, dict) or "code" in body or "message" in body
                    or not isinstance(body.get("bars"), dict)
                    or not set(body["bars"]).issubset(SYMBOLS)
                    or any(not isinstance(v, list) for v in body["bars"].values())):
                raise AuditFailure("INVALID_PROVIDER_RESPONSE_STRUCTURE")
            for symbol in SYMBOLS:
                rows[symbol].extend(body["bars"].get(symbol, []))
            if sum(map(len, rows.values())) > 100:
                raise AuditFailure("SMOKE_ROW_BUDGET_EXCEEDED")
            token = body.get("next_page_token")
            if token is None:
                break
            if not isinstance(token, str) or not token or len(token) > 2048 or token in seen:
                raise AuditFailure("INVALID_OR_REPEATED_PAGE_TOKEN")
            seen.add(token)
        else:
            raise AuditFailure("SMOKE_PAGE_BUDGET_EXCEEDED")
    except AuditFailure as exc:
        failure = str(exc)
    records = [r for r in store.records("http") if r["id"] not in before]
    counts = {s: len(rows[s]) for s in SYMBOLS}  # Count every symbol before quality.
    access = ("SUCCEEDED_WITH_ROWS" if all(counts.values()) else "SUCCEEDED_WITH_MISSING_SYMBOL_ROWS")
    if failure:
        access, failure = classify_failure(store, records, failure)
    quality = {}
    for symbol in SYMBOLS:
        dates, errors = [], Counter()
        for row in rows[symbol]:
            try:
                dates.append(validate_daily_bar(row, DATES))
            except (AuditFailure, TypeError, ValueError, KeyError) as exc:
                errors[str(exc) if isinstance(exc, AuditFailure) else "MALFORMED_PROVIDER_DAILY_BAR"] += 1
        missing = sorted(set(DATES) - set(dates))
        duplicates = sorted(day for day, n in Counter(dates).items() if n > 1)
        quality[symbol] = {"rows": counts[symbol], "valid_dates": sorted(dates),
            "missing_dates": missing, "duplicate_dates": duplicates, "rejections": dict(errors),
            "status": "PASS" if not errors and not missing and not duplicates else "UNRESOLVED"}
    passed = access == "SUCCEEDED_WITH_ROWS" and all(q["status"] == "PASS" for q in quality.values())
    report = {"version": "daily-liquidity-smoke-v1", "created_at": utc_now(),
        "status": "PASS" if passed else "UNRESOLVED", "historical_sip_access": access,
        "provider_failure": failure, "contract": CONTRACT, "request": PARAMS,
        "contract_verification": "Explicit authenticated request parameters; provider response does not echo timeframe/feed/adjustment/asof",
        "rows_by_symbol": counts, "data_quality": quality, "provenance": _provenance(records),
        "realtime_sip": "NOT_ENTITLED", "cohort_constructed": False}
    store.append("daily_liquidity_smoke", "AAPL-SPY-2025-01-13-15", report, canonical(report))
    report["store_verification"] = store.verify()
    return report


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--store", default="runs/daily_liquidity_smoke")
    args = parser.parse_args(argv)
    # Credential loading errors are stable codes only; no environment dump.
    try:
        credentials = credentials_from_env()
    except AuditFailure as exc:
        print(canonical({"status": "UNRESOLVED", "reason": str(exc)}).decode())
        return 2
    store = EvidenceStore(args.store)
    try:
        http = ReadOnlyHTTP(store, user_agent="daily-liquidity-smoke/1", credentials=credentials,
                            max_requests=5)
        http.bytes_remaining = 196608
        report = run_probe(http, store)
        output = Path(args.store) / ("daily-smoke-" + uuid.uuid4().hex + ".json")
        with output.open("xb") as handle:
            handle.write(canonical(report) + b"\n")
        print(canonical(report).decode())
        return 0 if report["status"] == "PASS" else 2
    finally:
        store.close()


if __name__ == "__main__":
    raise SystemExit(main())

"""Bounded official-source GET probes, independent of market/order clients."""
from __future__ import annotations

import argparse
from collections import Counter
from datetime import datetime
import json
import re
import time
from urllib.error import HTTPError, URLError
from urllib.parse import parse_qs, urlsplit
from urllib.request import Request, build_opener
import xml.etree.ElementTree as ET

import pytz

from .audit_http import NoRedirect
from .audit_store import AuditFailure, EvidenceStore, canonical, timestamp, utc_now

PUBLIC_URLS = {
    "sec_master_2025q1": "https://www.sec.gov/Archives/edgar/full-index/2025/QTR1/master.zip",
    "sec_master_2025q2": "https://www.sec.gov/Archives/edgar/full-index/2025/QTR2/master.zip",
    "utp_quotes_2015": "https://www.utpplan.com/DOC/uqdfspecification.pdf",
    "utp_quotes_current": "https://www.utpplan.com/DOC/UtpBinaryOutputSpec.pdf",
    "cta_quotes_current": "https://www.ctaplan.com/publicdocs/ctaplan/CQS_Pillar_Output_Specification.pdf",
    "cta_quotes_2015": "https://www.nyse.com/publicdocs/ctaplan/notifications/trader-update/cqs_output_spec_v62_11062015.pdf",
    "alpaca_quote_conditions": "https://docs.alpaca.markets/us/reference/stockmetaconditions-1",
    "alpaca_quote_exchanges": "https://docs.alpaca.markets/us/reference/stockmetaexchanges-1",
    "nyse_calendar_2025": "https://ir.theice.com/press/news-details/2024/NYSE-Group-Announces-2025-2026-and-2027-Holiday-and-Early-Closings-Calendar/default.aspx",
    "nyse_calendar_2025_pdf": "https://s2.q4cdn.com/154085107/files/doc_news/NYSE-Group-Announces-2024-2025-and-2026-Holiday-and-Early-Closings-Calendar-2023.pdf",
    "nasdaq_mourning_2025": "https://www.nasdaqtrader.com/TraderNews.aspx?id=UTP2024-20",
    "nasdaq_search": "https://www.nasdaqtrader.com/Trader.aspx?id=TradingHaltSearch",
    "nasdaq_history": "https://www.nasdaqtrader.com/trader.aspx?id=TradingHaltHistory",
    "nasdaq_rpcclient": "https://www.nasdaqtrader.com/rpcclient.axd",
    "nasdaq_rss_docs": "https://www.nasdaqtrader.com/Trader.aspx?id=TradeHaltRSS",
    "nasdaq_rss_query_semantics": "https://www.nasdaqtrader.com/snippets/tradehaltaccordion.html",
    "nasdaq_halt_fields": "https://www.nasdaqtrader.com/Trader.aspx?id=TradeHaltCodes",
    "nasdaq_rss_terms": "https://www.nasdaqtrader.com/content/administrationsupport/agreementstrading/THRSSFeedTermsCond.pdf",
    "sec_privacy": "https://www.sec.gov/about/privacy-information",
    "sec_developer": "https://www.sec.gov/about/developer-resources",
    "sec_access": "https://www.sec.gov/search-filings/edgar-search-assistance/accessing-edgar-data",
    "sec_suspensions": "https://www.sec.gov/enforcement-litigation/trading-suspensions",
    "sec_form25": "https://www.sec.gov/files/form25.pdf",
    "alpaca_terms": "https://files.alpaca.markets/disclosures/library/TermsAndConditions.pdf",
    "alpaca_stock_schema": "https://docs.alpaca.markets/us/docs/real-time-stock-pricing-data",
}
LARGE_SOURCES = {PUBLIC_URLS[k] for k in ("sec_master_2025q1", "sec_master_2025q2", "utp_quotes_2015",
                 "utp_quotes_current", "cta_quotes_current", "cta_quotes_2015")}


def check_public_url(url):
    if url in PUBLIC_URLS.values():
        return False
    parsed = urlsplit(url)
    if (parsed.scheme != "https" or parsed.netloc != "www.nasdaqtrader.com"
            or parsed.path != "/rss.aspx" or parsed.fragment):
        raise AuditFailure("PUBLIC_URL_NOT_ALLOWLISTED")
    query = parse_qs(parsed.query, keep_blank_values=True)
    if query.get("feed") != ["tradehalts"] or set(query) - {"feed", "haltdate", "resumedate"}:
        raise AuditFailure("PUBLIC_URL_NOT_ALLOWLISTED")
    for key in set(query) - {"feed"}:
        if len(query[key]) != 1 or not re.fullmatch(r"\d{8}", query[key][0]):
            raise AuditFailure("INVALID_HALT_QUERY_DATE")
        try:
            datetime.strptime(query[key][0], "%m%d%Y")
        except ValueError:
            raise AuditFailure("INVALID_HALT_QUERY_DATE") from None
    return True


class PublicProbe:
    def __init__(self, store, *, opener=None, max_requests=20):
        if not 1 <= max_requests <= 20:
            raise AuditFailure("PUBLIC_PROBE_BUDGET_INVALID")
        self.store, self.opener, self.remaining = store, opener or build_opener(NoRedirect()), max_requests

    def fetch(self, key, url):
        rss = check_public_url(url)
        if not self.remaining:
            raise AuditFailure("PUBLIC_PROBE_BUDGET_EXHAUSTED")
        if rss:
            prior = [r for r in self.store.records("public_source")
                     if r["metadata"]["url"].startswith("https://www.nasdaqtrader.com/rss.aspx?")]
            if prior and (timestamp(utc_now()) - timestamp(prior[-1]["metadata"]["received_at"])).total_seconds() < 60:
                raise AuditFailure("NASDAQ_RSS_ONE_REQUEST_PER_MINUTE")
        self.remaining -= 1
        started, tick = utc_now(), time.monotonic()
        byte_cap = 8_000_000 if url in LARGE_SOURCES else 2_000_000
        raw, status, headers, failure = b"", None, {}, None
        try:
            request = Request(url, method="GET", headers={
                "User-Agent": "trading_agent research https://github.com/emanuel894/trading_agent",
                "Accept-Encoding": "identity"})
            with self.opener.open(request, timeout=20) as response:
                status = response.status
                headers = {k.lower(): v for k, v in response.headers.items()
                           if k.lower() in {"content-type", "last-modified", "date", "etag"}}
                raw = response.read(byte_cap + 1)
                if len(raw) > byte_cap:
                    failure, raw = "PUBLIC_SOURCE_BYTE_CAP", raw[:byte_cap]
        except HTTPError as exc:
            status, failure, raw = exc.code, "HTTP_" + str(exc.code), exc.read(65536)
        except AuditFailure as exc:
            failure = str(exc)
        except (OSError, URLError, TimeoutError):
            failure = "PUBLIC_SOURCE_NETWORK_FAILED"
        if status != 200 and failure is None:
            failure = "PUBLIC_SOURCE_HTTP_FAILED"
        record = self.store.append("public_source", key, {
            "url": url, "method": "GET", "started_at": started, "received_at": utc_now(),
            "elapsed_seconds": time.monotonic() - tick, "http_status": status,
            "headers": headers, "failure": failure, "untrusted": True,
            "byte_cap": byte_cap,
            "access_is_rights_grant": False}, raw)
        return record


def eastern_timestamp(day, clock):
    if not day or not clock:
        return None
    try:
        local_date = datetime.strptime(day, "%m/%d/%Y").date()
        naive = datetime.fromisoformat(local_date.isoformat() + "T" + clock)
        if naive.tzinfo is not None:
            raise ValueError()
        return pytz.timezone("America/New_York").localize(naive, is_dst=None).astimezone(pytz.UTC).isoformat()
    except (ValueError, pytz.InvalidTimeError):
        raise AuditFailure("HALT_TIMEZONE_OR_TIME_AMBIGUOUS") from None


def parse_halt_rss(raw):
    if len(raw) > 2_000_000 or re.search(br"<!DOCTYPE|<!ENTITY", raw, re.I):
        raise AuditFailure("UNSAFE_HALT_XML")
    try:
        root = ET.fromstring(raw)
    except ET.ParseError:
        raise AuditFailure("MALFORMED_HALT_XML") from None
    if root.tag != "rss" or root.find("channel") is None:
        raise AuditFailure("INVALID_HALT_RSS_STRUCTURE")
    ns = "{http://www.nasdaqtrader.com/}"
    items = root.findall("./channel/item")
    count = root.findtext("./channel/" + ns + "numItems")
    if count is None or not count.isdigit() or int(count) != len(items):
        raise AuditFailure("HALT_RSS_ITEM_COUNT_MISMATCH")
    rows = []
    for item in items:
        values = {key: item.findtext(ns + key) for key in (
            "IssueSymbol", "IssueName", "Mkt", "ReasonCode", "HaltDate", "HaltTime",
            "ResumptionDate", "ResumptionQuoteTime", "ResumptionTradeTime")}
        if not all(values[k] for k in ("IssueSymbol", "Mkt", "HaltDate", "HaltTime")):
            raise AuditFailure("INCOMPLETE_HALT_ROW")
        values.update(halt_at=eastern_timestamp(values["HaltDate"], values["HaltTime"]),
                      scheduled_quote_resume_at=eastern_timestamp(values["ResumptionDate"], values["ResumptionQuoteTime"]),
                      scheduled_trade_resume_at=eastern_timestamp(values["ResumptionDate"], values["ResumptionTradeTime"]),
                      timestamp_semantics="source-reported initial halt / scheduled resumption; not live receipt",
                      item_pubdate_is_availability=False)
        if values["scheduled_trade_resume_at"] and timestamp(values["scheduled_trade_resume_at"]) < timestamp(values["halt_at"]):
            raise AuditFailure("RESUMPTION_PRECEDES_HALT")
        rows.append(values)
    return {"rows": rows, "count": len(rows),
            "market_frequencies": dict(Counter(r["Mkt"] for r in rows)),
            "halt_dates": sorted({r["HaltDate"] for r in rows}),
            "missing_trade_resumption": sum(not r["scheduled_trade_resume_at"] for r in rows),
            "negative_coverage_certified": False, "live_status_reconstructed": False}


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--store", required=True)
    parser.add_argument("--source", choices=PUBLIC_URLS)
    parser.add_argument("--halt-date", help="MMDDYYYY; one RSS request per minute")
    args = parser.parse_args(argv)
    if bool(args.source) == bool(args.halt_date):
        parser.error("choose one source or one halt date")
    store = EvidenceStore(args.store)
    try:
        key = args.source or "nasdaq_rss_" + args.halt_date
        url = PUBLIC_URLS[args.source] if args.source else "https://www.nasdaqtrader.com/rss.aspx?feed=tradehalts&haltdate=" + args.halt_date
        record = PublicProbe(store, max_requests=1).fetch(key, url)
        result = {"record_id": record["id"], "sha256": record["blob_sha"], **record["metadata"]}
        if args.halt_date and not result["failure"]:
            parsed = parse_halt_rss(store.raw(record))
            store.append("halt_source_diagnostic", record["id"], parsed)
            result.update({k: v for k, v in parsed.items() if k != "rows"})
        print(json.dumps(result, indent=2))
        return 2 if result["failure"] else 0
    except AuditFailure as exc:
        store.append("public_probe_failure", "probe", {"reason": str(exc)})
        print(json.dumps({"failure": str(exc)}))
        return 2
    finally:
        store.close()


if __name__ == "__main__":
    raise SystemExit(main())

"""Fixed IQ-P1 source-only join. No strategy, orders, credentials or CLI defaults.

The Windows private launcher supplies a sole store, resource gate and credential
pair. Development/CI use explicit fixtures. Native rows are never normalized or
interpreted as fills; actual retrieval is never a historical receipt.
"""
from datetime import datetime, timedelta, timezone
from pathlib import Path
import sqlite3
from urllib.parse import parse_qs, urlsplit
from urllib.request import ProxyHandler, build_opener

from .audit_http import NoRedirect, ReadOnlyHTTP
from .audit_market import EASTERN, SIPSource, nanoseconds
from .audit_store import AuditFailure, EvidenceStore, canonical, digest, strict_json, timestamp
from .iqp1_http_budget import IQP1HTTPBudget

PLAN_KEY = IQP1HTTPBudget.KEY


def packet_plan():
    result = []
    for day, close in (("2025-01-15", "16:00:00"), ("2025-03-10", "16:00:00"),
                       ("2025-07-03", "13:00:00")):
        def local(value):
            return EASTERN.localize(datetime.fromisoformat(day + "T" + value), is_dst=None).astimezone(timezone.utc)
        end = local(close)
        for name, kind, start, finish, pages, exclusive in (
            ("bars", "bars", local("09:30:00"), end, 1, True),
            ("original", "quotes", local("10:00:59"), local("10:01:06"), 5, False),
            ("delayed", "quotes", local("10:01:59"), local("10:02:06"), 5, False),
            ("exit", "quotes", end-timedelta(minutes=5, seconds=2), end, 5, True)):
            fmt = lambda dt: dt.strftime("%Y-%m-%dT%H:%M:%SZ")
            # Alpaca's end is inclusive. Preserve the plan's exclusive close at
            # native ns precision rather than fetching the next session/bar.
            request_end = ((finish-timedelta(seconds=1)).strftime("%Y-%m-%dT%H:%M:%S") + ".999999999Z"
                           if exclusive else fmt(finish))
            result.append(dict(id=day+"/"+name, kind=kind, start=fmt(start), end=fmt(finish),
                               request_end=request_end, end_exclusive=exclusive, max_pages=pages))
    return result


def validate_data_request(request):
    """Endpoint, method AND fixed sample allowlist; evaluated before socket use."""
    try:
        url = urlsplit(request.full_url)
        if (request.get_method() != "GET" or request.data is not None
                or url.scheme != "https" or url.netloc != "data.alpaca.markets"
                or url.fragment or url.path not in {"/v2/stocks/bars", "/v2/stocks/quotes"}):
            raise ValueError()
        pairs = parse_qs(url.query, strict_parsing=True, keep_blank_values=True)
        if any(len(values) != 1 for values in pairs.values()):
            raise ValueError()
        q = {key: values[0] for key, values in pairs.items()}
        token = q.pop("page_token", None)
        if token is not None and (not token or len(token) > 4096):
            raise ValueError()
        for p in packet_plan():
            expected = dict(symbols="SPY", start=p["start"], end=p["request_end"],
                            feed="sip", asof="-", sort="asc", limit="10000")
            if p["kind"] == "bars":
                expected.update(timeframe="1Min", adjustment="raw")
            if url.path.endswith("/"+p["kind"]) and q == expected:
                return p["id"]
    except (ValueError, TypeError):
        pass
    raise AuditFailure("IQP1_REQUEST_OUTSIDE_FIXED_DATA_PLAN")


class DataOnlyOpener:
    def __init__(self, resource_gate, *, transport=None):
        # No environment proxy, auth handler, redirect, calendar or broker SDK.
        self.transport = transport or build_opener(ProxyHandler({}), NoRedirect())
        self.resource_gate = resource_gate

    def open(self, request, timeout):
        validate_data_request(request)
        self.resource_gate()
        return self.transport.open(request, timeout=timeout)


def open_cache(root):
    """Reuse EvidenceStore readers without running its creating constructor."""
    root = Path(root).resolve(strict=True) if Path(root).exists() else None
    if root is None or not (root / "evidence.sqlite").is_file() or not (root / "objects").is_dir():
        raise AuditFailure("IQP1_EXISTING_JAN15_CACHE_REQUIRED")
    reader = object.__new__(EvidenceStore)
    reader.root, reader.objects, reader.spool = root, root/"objects", root/"spool"
    reader.db = sqlite3.connect((root/"evidence.sqlite").as_uri()+"?mode=ro", uri=True, timeout=5)
    reader.db.row_factory = sqlite3.Row
    reader.db.execute("PRAGMA query_only=ON")
    return reader


def cache_chain(store, packet, *, fixture_only=False):
    """Require a complete original pagination chain covering the retained window.

    Verify only reused hashes, not an already accepted full archive restoration.
    Ambiguous versions, synthetic evidence and incomplete chains fail closed.
    """
    candidates = []
    for record in store.records("http"):
        u = urlsplit(record["source_key"])
        q = parse_qs(u.query)
        try:
            if (u.scheme == "https" and u.netloc == "data.alpaca.markets"
                    and u.path == "/v2/stocks/quotes" and q.get("feed") == ["sip"]
                    and "SPY" in q["symbols"][0].split(",")
                    and timestamp(q["start"][0]) <= timestamp(packet["start"])
                    and timestamp(q["end"][0]) >= timestamp(packet["end"])):
                candidates.append((record, q))
        except (KeyError, IndexError, AuditFailure):
            continue
    roots = [(r, q) for r, q in candidates if "page_token" not in q]
    if len(roots) != 1:
        raise AuditFailure("IQP1_CACHE_CHAIN_MISSING_OR_AMBIGUOUS")
    r, base = roots[0]
    chain, seen = [], set()
    while len(chain) < 128:
        metadata = r["metadata"]
        envelope = dict(r)
        expected = envelope.pop("record_hash")
        if digest(canonical(envelope)) != expected:
            raise AuditFailure("IQP1_CACHE_RECORD_HASH_MISMATCH")
        fixture = metadata.get("capture_mode") == "fixture"
        if (fixture != fixture_only or metadata.get("http_status") != 200
                or metadata.get("failure") is not None):
            raise AuditFailure("IQP1_CACHE_NOT_REAL_SUCCESSFUL_HTTP")
        if not fixture_only:
            timestamp(metadata.get("received_at"))
            if metadata.get("method") != "GET":
                raise AuditFailure("IQP1_CACHE_ORIGINAL_METHOD_UNKNOWN")
        raw = store.raw(r)
        data = strict_json(raw)
        if not isinstance(data.get("quotes", {}).get("SPY"), list):
            raise AuditFailure("IQP1_CACHE_SPY_QUOTES_MISSING")
        chain.append(r)
        token = data.get("next_page_token")
        if not token:
            return chain
        if not isinstance(token, str) or token in seen:
            break
        seen.add(token)
        expected_q = dict(base, page_token=[token])
        matches = [item for item, query in candidates if query == expected_q]
        if len(matches) != 1:
            break
        r = matches[0]
    raise AuditFailure("IQP1_CACHE_PAGINATION_INCOMPLETE")


def run_pilot(store, cache, credentials, resource_gate, *, fixture_transport=None):
    """Private caller only. Twelve persistent packet identities, one HTTP budget.

    A STARTED packet is not silently retried after interruption. Failed/pending
    calls remain charged. No new-ledger reset, selective replacement or backfill.
    """
    plan = packet_plan()
    plan_hash = digest(canonical(plan))
    prior = store.records("iqp1_plan", PLAN_KEY)
    if prior and prior[0]["metadata"] != {"plan_hash":plan_hash, "packets":plan}:
        raise AuditFailure("IQP1_PLAN_BINDING_CHANGED")
    if not prior:
        store.append("iqp1_plan", PLAN_KEY, {"plan_hash":plan_hash, "packets":plan})
    if store.records("iqp1_started", PLAN_KEY):
        raise AuditFailure("IQP1_ALREADY_STARTED_PRESERVE_LEDGER_OWNER_REVIEW_REQUIRED")
    # Mandatory retained January evidence is checked BEFORE credentials/network.
    chains = [(p, cache_chain(cache, p, fixture_only=fixture_transport is not None)) for p in plan[1:3]]
    unique = {r["blob_sha"]:r for _, chain in chains for r in chain}
    cached_bytes = sum(len(cache.raw(r)) for r in unique.values())
    if cached_bytes >= 2_000_000_000:
        raise AuditFailure("IQP1_RETAINED_BODY_CAP_EXHAUSTED")
    resource_gate()
    if store.records(IQP1HTTPBudget.KIND, PLAN_KEY):
        raise AuditFailure("IQP1_EXISTING_BUDGET_REQUIRES_RECONCILIATION")
    store.append("iqp1_started", PLAN_KEY, {"cached_body_bytes":cached_bytes,
                  "fixture_only":fixture_transport is not None, "executable_admission":"NOT_GRANTED"})
    copied = {}
    for sha, r in unique.items():
        copied[sha] = store.append("iqp1_cached_http", r["source_key"],
                        {"original_record":r, "purpose":"JAN15_REUSE"}, cache.raw(r))["id"]
    for p, chain in chains:
        store.append("iqp1_packet", p["id"], {"state":"REUSED", "records":[copied[r["blob_sha"]] for r in chain]})
    budget = IQP1HTTPBudget.create(store, body_limit=2_000_000_000-cached_bytes)
    opener = DataOnlyOpener(resource_gate, transport=fixture_transport)
    http = ReadOnlyHTTP(store, user_agent="trading-agent/IQP1-source-only", credentials=credentials,
                        max_requests=128, budget=budget, opener=opener)
    source = SIPSource(store, http)
    for p in plan:
        if store.records("iqp1_packet", p["id"]):
            continue
        resource_gate()
        store.append("iqp1_packet", p["id"], {"state":"STARTED", "packet":p})
        try:
            rows, refs = source.pages(p["kind"], ["SPY"], p["start"], p["request_end"], max_pages=p["max_pages"])
            # Raw values and unknown size/status semantics stay intact. Count only.
            store.append("iqp1_packet", p["id"], {"state":"RETAINED", "records":refs,
                         "rows":len(rows["SPY"]), "executable_admission":"NOT_GRANTED"})
        except AuditFailure as exc:
            store.append("iqp1_packet", p["id"], {"state":"FAILED", "reason":str(exc)})
            raise
    result = dict(budget.snapshot(), cached_body_bytes=cached_bytes,
                  status="FIXTURE_ONLY" if fixture_transport else "PARTIAL_SOURCE_EVIDENCE",
                  executable_admission="NOT_GRANTED", logical_packets=12)
    store.append("iqp1_result", PLAN_KEY, result)
    return result

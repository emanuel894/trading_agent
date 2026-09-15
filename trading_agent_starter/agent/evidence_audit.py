"""Run with python -m agent.evidence_audit. Read-only acquisition, never alpha."""
from __future__ import annotations

import argparse
import asyncio
from collections import Counter
from datetime import date, timedelta
import json
import math
import os
from pathlib import Path
import time
import uuid

from .audit_http import ReadOnlyHTTP
from .audit_market import SIPSource, capture_sip
from .audit_sec import SECSource
from .audit_store import AuditFailure, EvidenceStore, VERSION, canonical, digest, strict_json, timestamp, utc_now
from .audit_text import disclosure_map, parse_document, verify_comparable


def code_fingerprint():
    root = Path(__file__).parent
    paths = sorted(root.glob("audit_*.py")) + [Path(__file__)]
    return {path.name: digest(path.read_bytes()) for path in paths}


def load_context(store, path):
    if path is None:
        return {"sources": {}, "instruments": [], "status_intervals": [],
                "prior_reviews": [], "company_disclosures": [], "clock": None}
    path = Path(path)
    raw = path.read_bytes()
    if len(raw) > 2_000_000:
        raise AuditFailure("CONTEXT_FILE_TOO_LARGE")
    value = strict_json(raw)
    keys = {"schema_version", "sources", "instruments", "status_intervals", "prior_reviews",
            "company_disclosures", "clock"}
    if not isinstance(value, dict) or set(value) != keys or value["schema_version"] != VERSION:
        raise AuditFailure("INVALID_CONTEXT_SCHEMA")
    if not all(isinstance(value[k], list) for k in keys - {"schema_version", "clock"}):
        raise AuditFailure("INVALID_CONTEXT_COLLECTION")
    context_record = store.append("context_manifest", str(path.resolve()), {"version": VERSION}, raw)
    sources = {}
    for source in value["sources"]:
        if not {"id", "path", "sha256", "url", "published_at", "reported_observed_at", "rights_ref"} <= source.keys():
            raise AuditFailure("INCOMPLETE_CONTEXT_SOURCE")
        relative = Path(source["path"])
        location = (path.parent / relative).resolve()
        if (relative.is_absolute() or not location.is_relative_to(path.parent.resolve())
                or location.suffix.lower() not in {".json", ".html", ".htm", ".txt", ".csv"}):
            raise AuditFailure("CONTEXT_SOURCE_PATH_REJECTED")
        data = location.read_bytes()
        if len(data) > 15_000_000 or digest(data) != source["sha256"] or source["id"] in sources:
            raise AuditFailure("CONTEXT_SOURCE_HASH_OR_ID_MISMATCH")
        for field in ("published_at", "reported_observed_at"):
            if source[field] is not None:
                timestamp(source[field])
        previous = [r for r in store.records("imported_source", source["id"]) if r["blob_sha"] == digest(data)]
        first_imported = previous[0]["metadata"]["first_imported_at"] if previous else utc_now()
        sources[source["id"]] = store.append("imported_source", source["id"], dict(
            source, manifest_record=context_record["id"], imported_at=utc_now(),
            first_imported_at=first_imported,
            reception_time_independently_verified=False, untrusted=True), data)
    value["sources"] = sources
    value["manifest_id"] = context_record["id"]
    return value


def instrument_at(context, cik, at):
    candidates = [row for row in context["instruments"] if row.get("cik") == cik
                  and timestamp(row["valid_from"]) <= timestamp(at) < timestamp(row["valid_to"])]
    if len(candidates) != 1:
        raise AuditFailure("DATED_INSTRUMENT_MAPPING_UNAVAILABLE")
    row = candidates[0]
    if (not row.get("reviewed_by") or not row.get("instrument_id")
            or row.get("source_id") not in context["sources"]
            or not isinstance(row.get("round_lot_shares"), int) or row["round_lot_shares"] <= 0):
        raise AuditFailure("INSTRUMENT_PROVENANCE_UNVERIFIED")
    return row


def prior_review(context, target, current, inventory_sha, links):
    reviews = [r for r in context["prior_reviews"] if r.get("accession") == target["accession"]]
    if len(reviews) != 1:
        return ["PRIOR_DISCLOSURE_REVIEW_REQUIRED"]
    review = reviews[0]
    if (review.get("text_sha256") != current["view"]["blob_sha"]
            or review.get("inventory_sha256") != inventory_sha or not review.get("reviewed_by")):
        return ["PRIOR_REVIEW_STALE_OR_UNGROUNDED"]
    coverage = review.get("external_search_source_ids", [])
    if not coverage or any(key not in context["sources"] for key in coverage):
        return ["EARLIER_COMPANY_DISCLOSURE_COVERAGE_UNKNOWN"]
    expected = {link["id"] for link in links["links"] if link["new_relative_to_prior_10q"]}
    rows = review.get("paragraph_reviews", [])
    if (not isinstance(rows, list) or len(rows) != len(expected)
            or {r.get("paragraph_id") for r in rows} != expected):
        return ["PRIOR_REVIEW_INCOMPLETE"]
    if any(r.get("relation") not in {"equivalent", "distinct_within_captured_sources"} for r in rows):
        return ["PRIOR_SEMANTIC_EQUIVALENCE_UNRESOLVED"]
    if any(not r.get("rationale") or not r.get("source_ids")
           or any(k not in context["sources"] for k in r["source_ids"]) for r in rows):
        return ["PRIOR_REVIEW_SOURCE_GROUNDING_MISSING"]
    if not any(r["relation"] == "distinct_within_captured_sources" for r in rows):
        return ["NO_DISTINCT_INFORMATION_AFTER_PRIOR_DISCLOSURES"]
    return []


def status_failures(context, symbols, at, mode):
    failures = []
    for symbol in symbols:
        rows = [r for r in context["status_intervals"] if r.get("symbol") == symbol
                and timestamp(r["valid_from"]) <= timestamp(at) < timestamp(r["valid_to"])]
        if len(rows) != 1 or rows[0].get("source_id") not in context["sources"] or not rows[0].get("reviewed_by"):
            failures.append("HISTORICAL_STATUS_PROVENANCE_UNVERIFIED:" + symbol)
        elif rows[0].get("state") != "TRADING":
            failures.append("TRADING_STATUS_NOT_CONFIRMED:" + symbol)
        elif mode == "prospective" and timestamp(context["sources"][rows[0]["source_id"]]["metadata"]["first_imported_at"]) > timestamp(at):
            failures.append("STATUS_SOURCE_IMPORTED_AFTER_ACTION:" + symbol)
    if mode == "prospective":
        clock = context.get("clock")
        if (not isinstance(clock, dict) or clock.get("source_id") not in context["sources"]
                or not isinstance(clock.get("uncertainty_ms"), (int, float))
                or not 0 <= clock["uncertainty_ms"] <= 1000
                or not 0 <= (timestamp(at) - timestamp(clock["measured_at"])).total_seconds() <= 86400):
            failures.append("ABSOLUTE_CLOCK_ACCURACY_UNVERIFIED")
    return failures


def audit_filing(store, sec, market, target, history, context, *, mode, deadline_seconds):
    started, tick = utc_now(), time.monotonic()
    result = {"version": VERSION, "accession": target["accession"], "cik": target["cik"],
              "mode": mode, "status": "ABSTAIN", "reasons": [], "stage_seconds": {},
              "stage_times": {}, "first_observed_at": target["first_observed_at"],
              "accepted_at": target["accepted_at"], "started_at": started,
              "deadline_seconds": deadline_seconds, "deadline_provisional": True,
              "code_sha256": digest(canonical(code_fingerprint())),
              "model": None, "model_start_at": None, "model_end_at": None,
              "token_cost": 0, "forecast": None, "order": None, "alpha_evaluation": "NOT_RUN"}
    observation_gap = (timestamp(target["first_observed_at"]) - timestamp(target["accepted_at"])).total_seconds()
    result["acceptance_to_observation_seconds"] = observation_gap
    result["observation_gap_is_live_latency"] = mode == "prospective"
    if mode == "prospective" and not 0 <= observation_gap <= 300:
        result["reasons"].append("LATE_OR_INCONSISTENT_FIRST_OBSERVATION")

    def stage(name, function):
        begin, counter = utc_now(), time.monotonic()
        try:
            return function()
        finally:
            result["stage_times"][name] = {"start": begin, "end": utc_now()}
            result["stage_seconds"][name] = time.monotonic() - counter

    try:
        prior = sec.comparator(target, history)
        prior_filings = sec.prior_filings(target, prior, history)
        documents = stage("ingestion", lambda: sec.download(target, mode))
        current_doc = next(d for d in documents if d["metadata"]["primary"])
        current = stage("parsing", lambda: parse_document(store, current_doc, mda=True))
        prior_documents = stage("prior_ingestion", lambda: [(f, sec.download(f, mode)) for f in prior_filings])
        prior_doc = next(d for f, docs in prior_documents if f["accession"] == prior["accession"]
                         for d in docs if d["metadata"]["primary"])
        comparator = stage("prior_parsing", lambda: parse_document(store, prior_doc, mda=True))
        stage("fiscal_verification", lambda: verify_comparable(current, comparator))
        parsed_disclosures = []
        prior_parse_tick, prior_parse_start = time.monotonic(), utc_now()
        for filing, docs in prior_documents:
            for doc in docs:
                parsed_disclosures.append(parse_document(store, doc))
        for external in context["company_disclosures"]:
            if external.get("cik") != target["cik"]:
                continue
            source = context["sources"].get(external.get("source_id"))
            if source is None or source["metadata"].get("published_at") is None:
                raise AuditFailure("COMPANY_DISCLOSURE_PROVENANCE_MISSING")
            publication = source["metadata"]["published_at"]
            if timestamp(publication) >= timestamp(target["accepted_at"]):
                continue
            doc = store.append("document", "company/" + external["source_id"], {
                "source": "imported_company_disclosure", "source_url": source["metadata"]["url"],
                "accepted_at": None, "source_publication_at": publication,
                "first_observed_at": source["metadata"]["imported_at"], "capture_mode": "historical_backfill",
                "reported_observed_at": source["metadata"]["reported_observed_at"],
                "source_record": source["id"], "cik": target["cik"], "untrusted": True}, store.raw(source))
            parsed_disclosures.append(parse_document(store, doc))
        result["stage_seconds"]["prior_disclosure_parsing"] = time.monotonic() - prior_parse_tick
        result["stage_times"]["prior_disclosure_parsing"] = {"start": prior_parse_start, "end": utc_now()}
        inventory = sorted([{"sha256": d["document"]["blob_sha"],
                             "source_key": d["document"]["source_key"],
                             "accepted_at": d["document"]["metadata"].get("accepted_at"),
                             "published_at": d["document"]["metadata"].get("source_publication_at")}
                            for d in parsed_disclosures], key=lambda d: d["source_key"])
        inventory_sha = digest(canonical(inventory))
        linkage = stage("deterministic_linkage", lambda: disclosure_map(current, comparator, parsed_disclosures))
        result["prior_disclosure"] = linkage
        result["prior_inventory_sha256"] = inventory_sha
        result["mda_text_sha256"] = current["view"]["blob_sha"]
        result["document_id"], result["prior_comparable_id"] = current_doc["id"], prior_doc["id"]
        result["inventory"] = inventory
        if not linkage["changed_paragraphs"]:
            result["reasons"].append("NO_CHANGE_RELATIVE_TO_PRIOR_10Q")
        result["reasons"].extend(stage("prior_verification", lambda: prior_review(
            context, target, current, inventory_sha, linkage)))
    except AuditFailure as exc:
        result["reasons"].append(str(exc))
    except (KeyError, TypeError, ValueError, StopIteration):
        result["reasons"].append("MALFORMED_DOCUMENT_OR_PROVENANCE")

    # Market acquisition is attempted independently of parsing failure so its
    # measured access/quality result is not hidden behind a text-stage failure.
    try:
        anchor = target["first_observed_at"] if mode == "prospective" else target["accepted_at"]
        ready = (timestamp(anchor) + timedelta(seconds=deadline_seconds)).isoformat()
        result["availability_anchor"] = "observed" if mode == "prospective" else "simulated_from_acceptance"
        instrument = instrument_at(context, target["cik"], ready)
        market_result = stage("market_context", lambda: market.context(instrument["symbol"], ready, mode=mode))
        result["market"] = market_result
        result["instrument"] = instrument
        if instrument_at(context, target["cik"], market_result["actionable_at"]) != instrument:
            result["reasons"].append("INSTRUMENT_MAPPING_CHANGED_BEFORE_ACTION")
        result["reasons"].extend(market_result["failures"])
        result["reasons"].extend(status_failures(context, market_result["symbols"], market_result["actionable_at"], mode))
    except AuditFailure as exc:
        result["reasons"].append(str(exc))
    except (KeyError, TypeError, ValueError):
        result["reasons"].append("MALFORMED_MARKET_CONTEXT")
    result["stage_seconds"]["total"] = time.monotonic() - tick
    result["finished_at"] = utc_now()
    result["reasons"] = sorted(set(result["reasons"]))
    if not result["reasons"]:
        result["status"] = "ELIGIBLE"
    result["eligibility_scope"] = "acquisition research only; not proof of public novelty, fills or alpha"
    if mode == "historical_backfill":
        result["historical_limitation"] = "Reception times and first-served document/bar versions are not reconstructed."
    if mode == "fixture":
        result["measurement_scope"] = "SYNTHETIC_TEST_ONLY"
    record = store.append("audit_result", target["cik"] + "/" + target["accession"], result)
    return dict(result, evidence_record_id=record["id"])


def distribution(values):
    values = sorted(values)
    if not values:
        return None
    return {"n": len(values), "p50": values[math.ceil(0.50 * len(values)) - 1],
            "p95": values[math.ceil(0.95 * len(values)) - 1], "max": values[-1]}


def summarize(results, discovery_failures, *, mode):
    reasons = Counter(reason for r in results for reason in r["reasons"])
    eligible = sum(r["status"] == "ELIGIBLE" for r in results)
    issuers = len({r["cik"] for r in results})
    acquisition = sum("prior_inventory_sha256" in r for r in results)
    markets = sum("market" in r and not r["market"]["failures"] for r in results)
    stages = sorted({k for r in results for k in r["stage_seconds"]})
    return {"version": VERSION, "mode": mode, "filings_attempted": len(results),
            "issuers_attempted": issuers, "fully_linked_document_sets": acquisition,
            "market_contexts_without_feed_errors": markets,
            "eligible": eligible, "abstained": len(results) - eligible,
            "reasons": dict(reasons), "discovery_failures": discovery_failures,
            "measured_stage_seconds": {k: distribution([r["stage_seconds"][k] for r in results
                                                       if k in r["stage_seconds"]]) for k in stages},
            "candidate_gate": ("CONTINUE_RESEARCH_ONLY" if mode != "fixture" and len(results) == 50
                               and issuers >= 25 and acquisition >= 48 and markets >= 48 and eligible >= 10
                               and not discovery_failures else "NOT_PASSED"),
            "deadline_frozen": False, "alpha_research": "NOT_RUN",
            "llm_latency": "NOT_MEASURED_NO_LLM", "latency_scope": "actual local acquisition/processing; not market reaction",
            "fixture_results_are_real_measurements": False}


def credentials_from_env():
    try:
        from dotenv import load_dotenv
        load_dotenv()
    except ImportError:
        pass
    for key in ("TRADING_ENABLED", "ALLOW_PAPER_ORDERS", "ALPACA_LIVE_TRADE"):
        if os.getenv(key, "").lower() in {"1", "true", "yes", "on"}:
            raise AuditFailure("READ_ONLY_FLAGS_REQUIRED")
    key = os.getenv("ALPACA_API_KEY") or os.getenv("APCA_API_KEY_ID")
    secret = os.getenv("ALPACA_API_SECRET") or os.getenv("ALPACA_SECRET_KEY") or os.getenv("APCA_API_SECRET_KEY")
    return (key, secret) if key and secret else None


def main(argv=None):
    parser = argparse.ArgumentParser(description="Bounded read-only 10-Q evidence audit; no LLM or trading")
    parser.add_argument("--store", required=True, help="Persistent audit directory, normally under runs/")
    sub = parser.add_subparsers(dest="command", required=True)
    run = sub.add_parser("run")
    run.add_argument("--ciks", required=True, help="Comma-separated registered CIK sample, maximum 25")
    run.add_argument("--start", required=True)
    run.add_argument("--end", required=True)
    run.add_argument("--mode", choices=["historical_backfill", "prospective"], default="historical_backfill")
    run.add_argument("--context", default=None)
    run.add_argument("--per-issuer", type=int, default=2, choices=[1, 2])
    run.add_argument("--deadline-seconds", type=int, default=600, help="Provisional measurement setting, not optimized on returns")
    run.add_argument("--max-requests", type=int, default=2000)
    run.add_argument("--polls", type=int, default=1)
    run.add_argument("--poll-seconds", type=int, default=60)
    capture = sub.add_parser("capture-sip")
    capture.add_argument("--symbols", required=True)
    capture.add_argument("--seconds", type=int, default=900)
    sub.add_parser("verify")
    args = parser.parse_args(argv)
    store = EvidenceStore(args.store)
    run_id = uuid.uuid4().hex
    try:
        store.verify()
        if args.command == "verify":
            print(json.dumps(store.verify(), indent=2))
            return 0
        credentials = credentials_from_env()
        if args.command == "capture-sip":
            result = asyncio.run(capture_sip(store, credentials, args.symbols.split(","), args.seconds))
            print(json.dumps(result, indent=2))
            return 0
        ciks = [str(int(c)).zfill(10) for c in args.ciks.split(",")]
        start, end = date.fromisoformat(args.start), date.fromisoformat(args.end)
        if (not 1 <= len(ciks) <= 25 or len(set(ciks)) != len(ciks)
                or not 0 <= (end - start).days <= 366 or not 1 <= args.deadline_seconds <= 3600
                or not 1 <= args.polls <= 60 or not 30 <= args.poll_seconds <= 60
                or args.mode != "prospective" and args.polls != 1):
            raise AuditFailure("INVALID_AUDIT_BOUNDS")
        http = ReadOnlyHTTP(store, user_agent=os.getenv("SEC_USER_AGENT",
            "TradingAgentResearch/0.1 (https://github.com/emanuel894/trading_agent)"),
            credentials=credentials, max_requests=args.max_requests)
        sec, market = SECSource(store, http), SIPSource(store, http)
        context = load_context(store, args.context)
        store.append("audit_registration", run_id, {
            "version": VERSION, "ciks": ciks, "start": args.start, "end": args.end,
            "code_files_sha256": code_fingerprint(),
            "per_issuer": args.per_issuer, "selection": "earliest acceptance then accession in date window",
            "mode": args.mode, "context_manifest": context.get("manifest_id"),
            "deadline_seconds": args.deadline_seconds, "deadline_provisional": True,
            "max_requests": args.max_requests, "polls": args.polls, "poll_seconds": args.poll_seconds,
            "alpaca_credentials_present": bool(credentials), "performance_access": False})
        results, failures, latest = [], [], {}
        for poll in range(args.polls):
            sec.cache.clear()  # Re-observe possible source revisions on the next poll.
            for cik in ciks:
                poll_tick, poll_start = time.monotonic(), utc_now()
                try:
                    history = sec.discover(cik, start - timedelta(days=400), end)
                    targets = [f for f in history if f["form"] == "10-Q"
                               and start <= timestamp(f["accepted_at"]).date() <= end][:args.per_issuer]
                    if not targets:
                        raise AuditFailure("NO_TARGET_FILINGS_IN_WINDOW")
                    for target in targets:
                        value = audit_filing(store, sec, market, target, history, context,
                                             mode=args.mode, deadline_seconds=args.deadline_seconds)
                        latest[(cik, target["accession"])] = value
                except AuditFailure as exc:
                    failures.append({"cik": cik, "poll": poll, "reason": str(exc)})
                finally:
                    store.append("discovery_poll", cik, {"run_id": run_id, "poll": poll,
                                 "started_at": poll_start, "finished_at": utc_now(),
                                 "elapsed_seconds": time.monotonic() - poll_tick})
            if poll + 1 < args.polls:
                time.sleep(args.poll_seconds)
        results = list(latest.values())
        report = summarize(results, failures, mode=args.mode)
        report.update(run_id=run_id, integrity=store.verify(), results=results)
        store.append("audit_report", run_id, report)
        path = Path(args.store) / ("report_" + run_id + ".json")
        with path.open("x", encoding="utf-8") as handle:
            json.dump(report, handle, indent=2, allow_nan=False)
        print(json.dumps({k: v for k, v in report.items() if k != "results"}, indent=2))
        print("Audit report: " + str(path))
        return 0 if report["candidate_gate"] == "CONTINUE_RESEARCH_ONLY" else 2
    except (AuditFailure, OSError, ValueError, KeyError, TypeError) as exc:
        reason = str(exc) if isinstance(exc, AuditFailure) else "INVALID_INPUT_OR_LOCAL_IO_FAILURE"
        store.append("audit_failure", run_id, {"reason": reason, "at": utc_now(), "version": VERSION})
        print(json.dumps({"status": "STOPPED", "reason": reason}))
        return 2
    finally:
        store.close()


if __name__ == "__main__":
    raise SystemExit(main())

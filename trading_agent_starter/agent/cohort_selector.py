"""ADR 001 amendment 002: dated monthly universe BEFORE issuer sampling.

Offline, metadata-only constructor. No network, document extraction, market
outcomes or audit execution. Evidence completeness is a reviewed assertion,
not something a hash or a successful API response can establish.
"""
from __future__ import annotations

import argparse
from collections import Counter, defaultdict
from datetime import datetime, timedelta
from decimal import Decimal, InvalidOperation
import json
import os
from pathlib import Path
import re

from .audit_market import EASTERN, choose_action
from .audit_store import AuditFailure, EvidenceStore, canonical, digest, strict_json, timestamp, utc_now

REGISTRATION_SHA = "6d930c58a921bd771ba7a7a43fa767ce0d8fde746bbc88adab73dde3a2d60091"
MONTHS = tuple(f"2025-{month:02d}" for month in range(1, 13))
INPUT_KEYS = {"version", "sources", "population_by_month", "identities", "calendar", "bars", "filing_inventory"}
IDENTITY_KEYS = {"instrument_id", "cik", "issuer", "lineage_id", "share_class", "ticker", "exchange",
                 "valid_from", "valid_to", "known_at", "security_type", "domestic_operating",
                 "shell", "fund", "adr", "listed_since", "evidence_ids"}
BAR_KEYS = {"date", "instrument_id", "ticker", "close", "volume", "feed", "session", "adjustment", "evidence_ids"}
EVENT_KEYS = {"cik", "accession", "form", "accepted_at", "report_date", "evidence_ids"}


class ConstructionBlocked(AuditFailure):
    def __init__(self, blockers):
        self.blockers = blockers
        super().__init__("CORRECTED_COHORT_INPUTS_UNRESOLVED")


def block(instrument, at, field, source):
    raise ConstructionBlocked([{"instrument": instrument, "date": at, "field": field,
                                "missing_source_evidence": source, "status": "UNRESOLVED"}])


def exact_keys(row, keys, label):
    if not isinstance(row, dict) or set(row) != keys:
        raise AuditFailure("INVALID_OR_UNREGISTERED_INPUT_FIELDS:" + label)


def cutoff(month):
    return EASTERN.localize(datetime.fromisoformat(month + "-01T00:00:00"))


def number(value):
    # Decimal strings avoid binary rounding at registered price/DV thresholds.
    if not isinstance(value, str):
        raise AuditFailure("MARKET_NUMBER_MUST_BE_DECIMAL_STRING")
    try:
        result = Decimal(value)
        if not result.is_finite() or result < 0 or len(value) > 40:
            raise InvalidOperation()
        return result
    except InvalidOperation:
        raise AuditFailure("INVALID_UNIVERSE_MARKET_NUMBER") from None


def evidence_sources(bundle, root):
    root, result = Path(root).resolve(), {}
    for source in bundle["sources"]:
        exact_keys(source, {"id", "path", "sha256", "source_url", "owner", "available_at"}, "source")
        key = source["id"]
        if key in result or not re.fullmatch(r"[a-f0-9]{64}", source["sha256"]):
            raise AuditFailure("INVALID_OR_DUPLICATE_SELECTION_SOURCE")
        path = (root / source["path"]).resolve()
        if not path.is_relative_to(root) or not source["owner"] or not source["source_url"].startswith("https://"):
            raise AuditFailure("INVALID_SELECTION_SOURCE_PROVENANCE")
        if not path.is_file():
            block("source:" + key, None, "source_bytes", source["source_url"])
        if digest(path.read_bytes()) != source["sha256"]:
            raise AuditFailure("SELECTION_SOURCE_HASH_MISMATCH:" + key)
        timestamp(source["available_at"])
        result[key] = source
    return result


def refs(ids, sources, instrument, at, field, *, cutoff_at=None):
    if not isinstance(ids, list) or not ids or any(key not in sources for key in ids):
        block(instrument, at, field, "Hash-verified official dated source records")
    if cutoff_at is not None and any(timestamp(sources[key]["available_at"]) > cutoff_at for key in ids):
        block(instrument, at, field, "Evidence publicly available by the relevant historical cutoff")


def reviewed(row, sources, instrument, at, field, *, cutoff_at=None):
    if row.get("complete") is not True or not row.get("reviewed_by") or not row.get("rationale"):
        block(instrument, at, field, "Explicit source-backed completeness review; missing data cannot exclude candidates")
    refs(row.get("evidence_ids"), sources, instrument, at, field, cutoff_at=cutoff_at)


def calendar_sessions(calendar, sources):
    exact_keys(calendar, {"complete", "reviewed_by", "rationale", "evidence_ids", "sessions"}, "calendar")
    reviewed(calendar, sources, "XNYS/XNAS", "2024-10 through 2026-01", "session_calendar")
    sessions = []
    for row in calendar["sessions"]:
        exact_keys(row, {"date", "open", "close"}, "session")
        opening, closing = timestamp(row["open"]), timestamp(row["close"])
        if (not opening < closing or opening.astimezone(EASTERN).date().isoformat() != row["date"]
                or closing.astimezone(EASTERN).date().isoformat() != row["date"]
                or (sessions and opening <= sessions[-1][2])):
            raise AuditFailure("INVALID_SELECTION_SESSION_CALENDAR")
        sessions.append((row["date"], opening, closing))
    return sessions


def identity_index(rows, sources):
    result, lineages = defaultdict(list), {}
    for row in rows:
        exact_keys(row, IDENTITY_KEYS, "identity")
        key = row["instrument_id"]
        if (not key.startswith("research:") or not re.fullmatch(r"\d{10}", row["cik"])
                or not row["lineage_id"] or not row["share_class"] or not row["issuer"]
                or not re.fullmatch(r"[A-Z][A-Z0-9.]{0,9}", row["ticker"])):
            raise AuditFailure("INVALID_DATED_CLASS_IDENTITY")
        if key in lineages and lineages[key] != (row["cik"], row["lineage_id"]):
            raise AuditFailure("INTERNAL_ID_REUSED_FOR_DIFFERENT_LINEAGE")
        lineages[key] = row["cik"], row["lineage_id"]
        if not timestamp(row["valid_from"]) < timestamp(row["valid_to"]):
            raise AuditFailure("INVALID_DATED_CLASS_INTERVAL")
        timestamp(row["known_at"])
        timestamp(row["listed_since"])
        refs(row["evidence_ids"], sources, key, row["valid_from"], "dated_class_interval")
        for other in result[key]:
            if max(timestamp(row["valid_from"]), timestamp(other["valid_from"])) < min(
                    timestamp(row["valid_to"]), timestamp(other["valid_to"])):
                raise AuditFailure("OVERLAPPING_CLASS_INTERVALS")
        result[key].append(row)
    return result


def identity_at(identities, key, at, sources):
    matches = [r for r in identities.get(key, []) if timestamp(r["valid_from"]) <= at < timestamp(r["valid_to"])]
    if not matches:
        block(key, at.isoformat(), "dated_class_interval", "CIK/share-class/ticker/exchange interval covering the timestamp")
    row = matches[0]
    if timestamp(row["known_at"]) > at:
        block(key, at.isoformat(), "identity_known_at", "Class facts known at the historical cutoff")
    refs(row["evidence_ids"], sources, key, at.isoformat(), "dated_class_source", cutoff_at=at)
    return row


def structurally_eligible(row, at):
    key = row["instrument_id"]
    # A proved disqualifying fact is sufficient. Do not demand unrelated facts
    # (or price history) for an instrument already proved to be debt/a fund/etc.
    if ((row["security_type"] and row["security_type"] != "COMMON_STOCK")
            or (row["exchange"] and row["exchange"] not in {"XNYS", "XNAS"})
            or row["domestic_operating"] is False
            or any(row[field] is True for field in ("shell", "fund", "adr"))):
        return False
    for field in ("domestic_operating", "shell", "fund", "adr"):
        if row[field] is not True and row[field] is not False:
            block(key, at.isoformat(), field, "Dated issuer and security classification")
    if not row["security_type"] or not row["exchange"]:
        block(key, at.isoformat(), "class_type_or_exchange", "Dated security classification and primary listing")
    return (row["domestic_operating"] and not any(row[k] for k in ("shell", "fund", "adr"))
            and row["security_type"] == "COMMON_STOCK" and row["exchange"] in {"XNYS", "XNAS"})


def monthly_universes(bundle, sources, identities, sessions):
    if set(bundle["population_by_month"]) != set(MONTHS):
        block("XNYS/XNAS candidate population", "2025-01 through 2025-12", "monthly_population",
              "All twelve complete dated populations, including delisted and renamed classes")
    bars = {}
    for row in bundle["bars"]:
        exact_keys(row, BAR_KEYS, "bar")
        key = row["instrument_id"], row["date"]
        if key in bars:
            raise AuditFailure("DUPLICATE_UNIVERSE_SESSION_BAR")
        bars[key] = row
    memberships = {}
    for month in MONTHS:
        at, population = cutoff(month), bundle["population_by_month"][month]
        exact_keys(population, {"complete", "reviewed_by", "rationale", "evidence_ids", "instrument_ids"}, "population")
        reviewed(population, sources, "XNYS/XNAS population", month, "population_completeness", cutoff_at=at)
        keys = population["instrument_ids"]
        if not keys or len(set(keys)) != len(keys):
            raise AuditFailure("EMPTY_OR_DUPLICATE_UNIVERSE_POPULATION")
        lookback = [s for s in sessions if s[2] < at][-60:]
        if len(lookback) != 60:
            block("XNYS/XNAS", month, "preceding_60_sessions", "Complete official regular-session calendar")
        classes = []
        for key in sorted(keys):
            row = identity_at(identities, key, at, sources)
            if not structurally_eligible(row, at):
                continue
            # A proved recent listing is ineligible. An absent bar is unknown.
            if timestamp(row["listed_since"]) > lookback[0][1]:
                continue
            values, bar_refs = [], set()
            for day, opening, closing in lookback:
                bar = bars.get((key, day))
                if bar is None:
                    block(key, day, "sip_rth_close_volume", "Completed raw SIP regular-session price/volume; no older-session substitution")
                dated = identity_at(identities, key, opening, sources)
                if bar["ticker"] != dated["ticker"]:
                    raise AuditFailure("BAR_HISTORICAL_TICKER_MISMATCH")
                if (bar["feed"], bar["session"], bar["adjustment"]) != ("sip", "RTH", "raw"):
                    raise AuditFailure("UNREGISTERED_UNIVERSE_BAR_CONTRACT")
                refs(bar["evidence_ids"], sources, key, day, "sip_rth_bar", cutoff_at=at)
                close, volume = number(bar["close"]), number(bar["volume"])
                if close <= 0 or volume != volume.to_integral_value():
                    raise AuditFailure("INVALID_UNIVERSE_PRICE_OR_VOLUME")
                values.append(close * volume)
                bar_refs.update(bar["evidence_ids"])
            ordered = sorted(values)
            median = (ordered[29] + ordered[30]) / 2
            if median < Decimal("20000000") or close < Decimal("10"):
                continue
            classes.append({"cik": row["cik"], "instrument_id": key, "ticker": row["ticker"],
                            "exchange": row["exchange"], "lineage_id": row["lineage_id"],
                            "share_class": row["share_class"], "median_dollar_volume": str(median),
                            "prior_close": str(close), "lookback_start": lookback[0][0],
                            "lookback_end": lookback[-1][0], "identity_sha256": digest(canonical(row)),
                            "bar_evidence_ids": sorted(bar_refs)})
        memberships[month] = rank_classes(classes)
    return memberships


def rank_classes(classes):
    """No filing-count input: rank the entire eligible issuer population first."""
    best = {}
    for row in sorted(classes, key=lambda r: (-Decimal(r["median_dollar_volume"]), r["instrument_id"])):
        best.setdefault(row["cik"], row)
    ranked = sorted(best.values(), key=lambda r: (-Decimal(r["median_dollar_volume"]), int(r["cik"]), r["instrument_id"]))
    return [{**r, "rank": i + 1} for i, r in enumerate(ranked[:500])]


def eligible_events(bundle, sources, identities, sessions, memberships):
    inventory = bundle["filing_inventory"]
    exact_keys(inventory, {"complete", "reviewed_by", "rationale", "evidence_ids", "indexed_originals", "events"}, "filing_inventory")
    reviewed(inventory, sources, "SEC original 10-Q population", "2025", "complete_original_filing_inventory")
    expected = []
    for row in inventory["indexed_originals"]:
        exact_keys(row, {"cik", "accession"}, "indexed_original")
        expected.append((row["cik"], row["accession"]))
    actual, by_cik = [], defaultdict(list)
    by_month = {m: {r["cik"]: r for r in rows} for m, rows in memberships.items()}
    for event in inventory["events"]:
        exact_keys(event, EVENT_KEYS, "event")
        cik, accession = event["cik"], event["accession"]
        if (not re.fullmatch(r"\d{10}", cik) or not re.fullmatch(r"\d{10}-\d{2}-\d{6}", accession)
                or event["form"] != "10-Q"):
            raise AuditFailure("INVALID_OR_NONORIGINAL_10Q_EVENT")
        accepted = timestamp(event["accepted_at"])
        if accepted.astimezone(EASTERN).year != 2025:
            raise AuditFailure("EVENT_OUTSIDE_REGISTERED_2025_WINDOW")
        refs(event["evidence_ids"], sources, cik, event["accepted_at"], "SEC_acceptance_metadata")
        actual.append((cik, accession))
        month = accepted.astimezone(EASTERN).strftime("%Y-%m")
        member = by_month[month].get(cik)
        if member is None:
            continue
        action = choose_action((accepted + timedelta(seconds=600)).isoformat(), [(s[1], s[2]) for s in sessions])
        key = member["instrument_id"]
        # Only this month's chosen class. No parent ticker or convenient substitute.
        accepted_identity = identity_at(identities, key, accepted, sources)
        action_identity = identity_at(identities, key, timestamp(action), sources)
        if any(r["cik"] != cik or r["lineage_id"] != member["lineage_id"] for r in (accepted_identity, action_identity)):
            raise AuditFailure("FILING_CLASS_ISSUER_OR_LINEAGE_CONFLICT")
        if not all(structurally_eligible(r, when) for r, when in ((accepted_identity, accepted), (action_identity, timestamp(action)))):
            continue
        by_cik[cik].append({**event, "actionable_at": action, "instrument_id": key,
            "instrument_id_authority": "INTERNAL_RESEARCH", "symbol": action_identity["ticker"],
            "exchange": action_identity["exchange"], "share_class": action_identity["share_class"],
            "lineage_id": action_identity["lineage_id"], "membership_month": month,
            "membership_sha256": digest(canonical(member)), "identity_sha256": digest(canonical(action_identity)),
            "class_binding": "DATED_QUALIFYING_COMMON_CLASS"})
    # Quarter indexes cover every filer. Acceptance metadata is necessary for
    # every issuer ever in the monthly universe, before applying the 25-CIK key.
    # Fetching metadata for provably out-of-universe filers is unnecessary.
    universe_ciks = {r["cik"] for rows in memberships.values() for r in rows}
    expected_universe = {r for r in expected if r[0] in universe_ciks}
    actual_universe = {r for r in actual if r[0] in universe_ciks}
    if (len(set(expected)) != len(expected) or len(set(actual)) != len(actual)
            or expected_universe != actual_universe or not set(actual).issubset(set(expected))):
        raise AuditFailure("INCOMPLETE_OR_CONFLICTING_ORIGINAL_FILING_INVENTORY_NO_REPLACEMENT")
    issuers = sorted((cik for cik, rows in by_cik.items() if len(rows) >= 2), key=int)[:25]
    if len(issuers) != 25:
        block("eligible issuer population", "2025", "25_issuers_with_two_eligible_original_10Qs",
              "Fewer than 25 qualifying issuers; explicit amendment required, no convenient replacement")
    targets = [row for cik in issuers for row in sorted(by_cik[cik], key=lambda r: (timestamp(r["accepted_at"]), r["accession"]))[:2]]
    if len({r["accession"] for r in targets}) != 50:
        raise AuditFailure("DUPLICATE_SELECTED_ORIGINAL_ACCESSION_NO_REPLACEMENT")
    return targets


def build_scope(bundle, root, registration_raw):
    if digest(registration_raw) != REGISTRATION_SHA:
        raise AuditFailure("REGISTERED_SELECTION_CHANGED_EXPLICIT_AMENDMENT_REQUIRED")
    exact_keys(bundle, INPUT_KEYS, "bundle")
    if bundle["version"] != "adr001-universe-inputs-v1":
        raise AuditFailure("INVALID_UNIVERSE_INPUT_VERSION")
    # Enumerate missing monthly population claims together, before loading any
    # candidate's prices. This is construction completeness, not an admission
    # filter based on whether a source download happened to succeed.
    missing = []
    for month in MONTHS:
        population = bundle["population_by_month"].get(month, {})
        if population.get("complete") is not True:
            missing.append({"instrument": "XNYS/XNAS candidate classes (not yet enumerated)",
                "date": cutoff(month).isoformat(), "field": "dated_candidate_population",
                "missing_source_evidence": "Dated class-level exchange roster plus CIK/issuer/class/type/domestic-operating lineage; today's directory is insufficient",
                "status": "UNRESOLVED"})
    if missing:
        raise ConstructionBlocked(missing)
    registration = strict_json(registration_raw)
    sources = evidence_sources(bundle, root)
    sessions = calendar_sessions(bundle["calendar"], sources)
    identities = identity_index(bundle["identities"], sources)
    memberships = monthly_universes(bundle, sources, identities, sessions)
    targets = eligible_events(bundle, sources, identities, sessions, memberships)
    return {"status": "FROZEN", "selection_version": "adr001-universe-selection-v2",
        "selection": "ADR001-COHORT-002: monthly dated top-500 universe, then ascending CIK, earliest two eligible originals",
        "registration_sha256": REGISTRATION_SHA, "window": registration["window"],
        "selection_evidence_hashes": {"registration": REGISTRATION_SHA, "ADR": registration["adr_sha256"],
            "input_bundle": digest(canonical(bundle)), "source_population": digest(canonical(bundle["population_by_month"])),
            "dated_identity_intervals": digest(canonical(bundle["identities"])), "monthly_bar_inputs": digest(canonical(bundle["bars"])),
            "calendar": digest(canonical(bundle["calendar"])), "complete_2025_filing_inventory": digest(canonical(bundle["filing_inventory"])),
            "sources": digest(canonical(bundle["sources"])), "monthly_memberships": digest(canonical(memberships)),
            "selector_code": digest(Path(__file__).read_bytes())},
        "no_replacement": True, "historical_deadline_seconds": 600,
        "availability_anchor": "SIMULATED_FROM_SEC_ACCEPTANCE_NOT_HISTORICAL_RECEIPT",
        "performance_deadline_frozen": False, "monthly_memberships": memberships, "targets": targets,
        "context_instruments": [{"cik": "0000884394", "symbol": "SPY", "instrument_id": "research:cik-0000884394-unit-001",
                                 "actionable_at": at, "role": "REQUIRED_SCOPED_CONTEXT_REVIEW"}
                                for at in sorted({r["actionable_at"] for r in targets})]}


def freeze_scope(scope, store, output):
    # One freeze per immutable evidence store/registration, even under another filename.
    if Path(output).exists() or any(r["metadata"].get("registration_sha256") == REGISTRATION_SHA
                                 for r in store.records("corrected_frozen_cohort")):
        raise AuditFailure("COHORT_ALREADY_FROZEN_EXPLICIT_AMENDMENT_REQUIRED")
    counts = Counter(r["cik"] for r in scope["targets"])
    if len(counts) != 25 or set(counts.values()) != {2} or scope.get("registration_sha256") != REGISTRATION_SHA:
        raise AuditFailure("INVALID_CORRECTED_COHORT")
    sha = digest(canonical(scope))
    document = {"version": "historical-cohort-v2", "frozen_at": utc_now(), "scope_sha256": sha,
                "scope": scope, "amendment": "ADR001-COHORT-002", "audit_executed": False}
    raw = canonical(document) + b"\n"
    record = store.append("corrected_frozen_cohort", sha, {"registration_sha256": REGISTRATION_SHA}, raw)
    path = Path(output)
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("xb") as handle:
        handle.write(raw)
    return {"record_id": record["id"], "scope_sha256": sha, "file_sha256": digest(raw), "path": str(path)}


def verify_frozen_inputs(document, bundle, root, registration_raw):
    rebuilt = build_scope(bundle, root, registration_raw)
    if document["scope"] != rebuilt or document["scope_sha256"] != digest(canonical(rebuilt)):
        raise AuditFailure("UNIVERSE_OR_SELECTION_CHANGED_EXPLICIT_AMENDMENT_AND_SCOPED_REVIEWS_REQUIRED")
    return True


def read_registry(root, relative="config/cohort_scope_registry.json"):
    root = Path(root).resolve()
    path = (root / relative).resolve()
    if not path.is_relative_to(root):
        raise AuditFailure("INVALID_SCOPE_REGISTRY_PATH")
    if not path.is_file():
        block("cohort registration", "2025", "scope_registry", "Amendment 002 and its immutable selection registration")
    registry = strict_json(path.read_bytes())
    if (registry.get("version") != "cohort-scope-registry-v1"
            or registry.get("active_selection_registration_sha256") != REGISTRATION_SHA):
        raise AuditFailure("SCOPE_REGISTRY_REGISTRATION_MISMATCH")
    for path_key, hash_key in (("active_selection_registration_path", "active_selection_registration_sha256"),
                               ("amendment_path", "amendment_sha256")):
        evidence = (root / registry[path_key]).resolve()
        if not evidence.is_relative_to(root) or not evidence.is_file():
            block("cohort registration", "2025", path_key, "Pinned selection registration / scope amendment")
        if digest(evidence.read_bytes()) != registry[hash_key]:
            raise AuditFailure("SCOPE_REGISTRY_EVIDENCE_HASH_MISMATCH")
    return path, registry


def freeze_registered_scope(scope, store, output, root):
    path, registry = read_registry(root)
    # Exclusive writer guard; deletion of a lock after a crash is an explicit
    # recovery operation, never a reason to silently construct another cohort.
    lock = path.with_suffix(".lock")
    with lock.open("xb"):
        pass
    try:
        _, current = read_registry(root)
        if current != registry or registry.get("active_scope_sha256") is not None:
            raise AuditFailure("COHORT_ALREADY_FROZEN_EXPLICIT_AMENDMENT_REQUIRED")
        result = freeze_scope(scope, store, output)
        registry.update(active_scope_sha256=result["scope_sha256"],
                        active_manifest_file_sha256=result["file_sha256"],
                        replacement_status="CORRECTED_SCOPE_FROZEN_PENDING_SCOPED_REVIEW")
        raw = canonical(registry) + b"\n"
        store.append("cohort_scope_registry", REGISTRATION_SHA, {"manifest_record_id": result["record_id"]}, raw)
        temporary = path.with_suffix(".next")
        with temporary.open("xb") as handle:
            handle.write(raw)
            handle.flush()
            os.fsync(handle.fileno())
        temporary.replace(path)
        return result
    finally:
        lock.unlink()


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--inputs", required=True, help="Source-backed dated universe bundle, not a current symbol list")
    parser.add_argument("--root", default=".")
    parser.add_argument("--registration", default="research/cohort_selection_registration_002.json")
    parser.add_argument("--store", required=True)
    parser.add_argument("--output", required=True)
    args = parser.parse_args(argv)
    store = EvidenceStore(args.store)
    input_record = None
    try:
        raw = Path(args.inputs).read_bytes()
        input_record = store.append("corrected_selection_input", digest(raw), {"untrusted": True}, raw)
        scope = build_scope(strict_json(raw), args.root, Path(args.registration).read_bytes())
        result = {"status": "CORRECTED_SCOPE_FROZEN_PENDING_SCOPED_REVIEW",
                  **freeze_registered_scope(scope, store, args.output, args.root)}
        code = 0
    except (AuditFailure, OSError, KeyError, TypeError, ValueError) as exc:
        result = {"status": "BLOCK_HISTORICAL_AUDIT", "cohort_frozen": False,
                  "reason": str(exc) if isinstance(exc, AuditFailure) else "MISSING_OR_MALFORMED_SELECTION_INPUTS",
                  "blockers": getattr(exc, "blockers", []), "prospective": "PROSPECTIVE_ACTIONABILITY_BLOCKED"}
        code = 2
    result.update(audit_executed=False, performance_analysis_executed=False,
                  registration_sha256=REGISTRATION_SHA, selector_code_sha256=digest(Path(__file__).read_bytes()),
                  input_record_id=input_record["id"] if input_record else None)
    store.append("corrected_selection_result", REGISTRATION_SHA, result)
    store.verify()
    store.close()
    print(json.dumps(result, indent=2))
    return code


if __name__ == "__main__":
    raise SystemExit(main())

"""Amendment 003 selector input contract. No acquisition or freeze CLI.

The unchanged v2 selector remains the amendment-002 replay implementation.
Only daily input interpretation changes; identity, calendar, ranking, and event
selection helpers are shared. This module prepares/verifies future scope inputs;
writing or authorizing a real cohort is outside this milestone.
"""
from decimal import Decimal
from pathlib import Path

from . import cohort_selector as legacy
from . import alpaca_daily_contract as daily_contract
from .alpaca_daily_contract import (CONTRACT, INPUT_VERSION, LIQUIDITY_VERSION,
    bucket_end, daily_date, validate_contract)
from .audit_store import AuditFailure, canonical, digest, strict_json, timestamp
from .cohort_selector import (MONTHS, ConstructionBlocked, block, exact_keys,
    cutoff, number, evidence_sources, refs, reviewed, calendar_sessions,
    identity_index, identity_at, structurally_eligible, rank_classes, eligible_events)

REGISTRATION_SHA = "af7e721326576b0e6b131debd1b5f8665c474adc2472ab75d483fb654f35eed2"
INPUT_KEYS = legacy.INPUT_KEYS | {"liquidity_definition_version"}
BAR_KEYS = legacy.BAR_KEYS | {"provider", "timeframe", "asof", "timestamp", "liquidity_definition_version"}


def monthly_universes(bundle, sources, identities, sessions):
    if set(bundle["population_by_month"]) != set(MONTHS):
        block("XNYS/XNAS candidate population", "2025-01 through 2025-12", "monthly_population",
              "All twelve complete dated populations, including delisted and renamed classes")
    bars = {}
    for row in bundle["bars"]:
        exact_keys(row, BAR_KEYS, "provider_daily_bar")
        validate_contract(row)
        if daily_date(row["timestamp"]) != row["date"]:
            raise AuditFailure("DAILY_TIMESTAMP_DATE_MISMATCH")
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
                    block(key, day, "alpaca_sip_1day_close_volume", "Exact preceding session-date provider-native daily bar; no older-session substitution")
                dated = identity_at(identities, key, opening, sources)
                if bar["ticker"] != dated["ticker"]:
                    raise AuditFailure("BAR_HISTORICAL_TICKER_MISMATCH")
                if bucket_end(day) > at:
                    block(key, day, "completed_daily_bucket", "Provider-native New York day must finish before cutoff")
                refs(bar["evidence_ids"], sources, key, day, "alpaca_sip_1day_bar", cutoff_at=at)
                close, volume = number(bar["close"]), number(bar["volume"])
                if close <= 0 or volume <= 0 or volume != volume.to_integral_value():
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


def build_scope(bundle, root, registration_raw):
    if digest(registration_raw) != REGISTRATION_SHA:
        raise AuditFailure("REGISTERED_SELECTION_CHANGED_EXPLICIT_AMENDMENT_REQUIRED")
    exact_keys(bundle, INPUT_KEYS, "bundle")
    if bundle["version"] != INPUT_VERSION:
        raise AuditFailure("INVALID_UNIVERSE_INPUT_VERSION")
    if bundle["liquidity_definition_version"] != LIQUIDITY_VERSION:
        raise AuditFailure("LIQUIDITY_DEFINITION_CHANGED_EXPLICIT_AMENDMENT_REQUIRED")
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
    return {"status": "PREPARED_UNFROZEN", "selection_version": "adr001-universe-selection-v3",
        "selection": "ADR001-LIQUIDITY-003: monthly dated top-500 universe, then ascending CIK, earliest two eligible originals",
        "liquidity_definition_version": LIQUIDITY_VERSION,
        "registration_sha256": REGISTRATION_SHA, "window": registration["window"],
        "selection_evidence_hashes": {"registration": REGISTRATION_SHA, "ADR": registration["adr_sha256"],
            "input_bundle": digest(canonical(bundle)), "source_population": digest(canonical(bundle["population_by_month"])),
            "dated_identity_intervals": digest(canonical(bundle["identities"])), "monthly_bar_inputs": digest(canonical(bundle["bars"])),
            "calendar": digest(canonical(bundle["calendar"])), "complete_2025_filing_inventory": digest(canonical(bundle["filing_inventory"])),
            "sources": digest(canonical(bundle["sources"])), "monthly_memberships": digest(canonical(memberships)),
            "selector_code": digest(Path(__file__).read_bytes()),
            "legacy_shared_selector_code": digest(Path(legacy.__file__).read_bytes()),
            "daily_contract_code": digest(Path(daily_contract.__file__).read_bytes()),
            "liquidity_definition_version": digest(canonical(LIQUIDITY_VERSION)),
            "provider_daily_contract": digest(canonical(CONTRACT))},
        "no_replacement": True, "historical_deadline_seconds": 600,
        "availability_anchor": "SIMULATED_FROM_SEC_ACCEPTANCE_NOT_HISTORICAL_RECEIPT",
        "performance_deadline_frozen": False, "monthly_memberships": memberships, "targets": targets,
        "context_instruments": [{"cik": "0000884394", "symbol": "SPY", "instrument_id": "research:cik-0000884394-unit-001",
                                 "actionable_at": at, "role": "REQUIRED_SCOPED_CONTEXT_REVIEW"}
                                for at in sorted({r["actionable_at"] for r in targets})]}


def verify_frozen_inputs(document, bundle, root, registration_raw):
    rebuilt = build_scope(bundle, root, registration_raw)
    if document["scope"] != rebuilt or document["scope_sha256"] != digest(canonical(rebuilt)):
        raise AuditFailure("UNIVERSE_OR_SELECTION_CHANGED_EXPLICIT_AMENDMENT_AND_SCOPED_REVIEWS_REQUIRED")
    return True


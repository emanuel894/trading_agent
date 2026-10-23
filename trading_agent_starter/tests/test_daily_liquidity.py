"""Synthetic-only amendment 003 tests; no credentials or real acquisition."""
from copy import deepcopy
from datetime import datetime
import io
from pathlib import Path
import tempfile
import unittest
from urllib.error import HTTPError
from urllib.parse import parse_qs, urlsplit

from agent import cohort_selector as legacy
from agent import cohort_selector_v3 as selector
from agent.alpaca_daily_contract import (CONTRACT, INPUT_VERSION, LIQUIDITY_VERSION,
    daily_date, validate_contract, validate_daily_bar)
from agent.audit_http import ReadOnlyHTTP
from agent.audit_market import EASTERN
from agent.audit_store import AuditFailure, EvidenceStore, canonical, digest, strict_json
from agent.daily_liquidity_probe import DATES, run_probe
import test_cohort_selector as legacy_tests


class DailySelectorTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        # Reuse synthetic v2 calendar/classes, not an actual market population.
        legacy_tests.SelectorTests.setUpClass.__func__(cls)
        cls.old = deepcopy(cls.base)
        cls.base.update(version=INPUT_VERSION, liquidity_definition_version=LIQUIDITY_VERSION)
        for bar in cls.base["bars"]:
            bar.update(CONTRACT)
            bar["timestamp"] = EASTERN.localize(datetime.fromisoformat(bar["date"])).isoformat()
        cls.registration = (Path(__file__).parents[1] / "research/cohort_selection_registration_003.json").read_bytes()

    @classmethod
    def tearDownClass(cls):
        cls.temp.cleanup()

    def members(self, bundle):
        sources = legacy.evidence_sources(bundle, self.root)
        return selector.monthly_universes(bundle, sources, legacy.identity_index(bundle["identities"], sources),
                                         legacy.calendar_sessions(bundle["calendar"], sources))

    def test_rth_iex_adjustments_and_symbol_mapping_rejected(self):
        for field, value in (("session", "RTH"), ("feed", "iex"), ("adjustment", "split"),
                             ("adjustment", "all"), ("asof", "2025-01-01"), ("asof", None),
                             ("timeframe", "30Min"), ("provider", "unknown")):
            with self.subTest(field=field, value=value):
                bundle = deepcopy(self.base)
                bundle["bars"][0][field] = value
                with self.assertRaisesRegex(AuditFailure, "UNREGISTERED_PROVIDER_NATIVE"):
                    self.members(bundle)

    def test_missing_exact_session_is_unresolved_not_older_substitution(self):
        bundle = deepcopy(self.base)
        bundle["bars"] = [r for r in bundle["bars"]
                          if not (r["instrument_id"] == "research:test-1" and r["date"] == "2024-12-31")]
        with self.assertRaises(legacy.ConstructionBlocked) as caught:
            self.members(bundle)
        self.assertEqual(caught.exception.blockers[0]["status"], "UNRESOLVED")
        self.assertEqual(caught.exception.blockers[0]["date"], "2024-12-31")

    def test_historical_ticker_binding_remains_required(self):
        bundle = deepcopy(self.base)
        for bar in bundle["bars"]:
            bar["ticker"] = "PARENT_OR_CURRENT_SYMBOL"
        with self.assertRaisesRegex(AuditFailure, "BAR_HISTORICAL_TICKER_MISMATCH"):
            self.members(bundle)

    def test_thresholds_and_ranking_unchanged(self):
        bundle = deepcopy(self.base)
        for bar in bundle["bars"]:
            if bar["instrument_id"] == "research:test-1":
                bar.update(close="10", volume="2000000")  # Exact two boundaries.
            elif bar["instrument_id"] == "research:test-2":
                bar.update(volume="999999")  # Below $20m.
            elif bar["instrument_id"] == "research:test-3":
                bar.update(close="9.99", volume="99999999")  # High liquidity, low price.
        old = deepcopy(self.old)
        for new, previous in zip(bundle["bars"], old["bars"]):
            previous.update(close=new["close"], volume=new["volume"])
        sources = legacy.evidence_sources(old, self.root)
        expected = legacy.monthly_universes(old, sources, legacy.identity_index(old["identities"], sources),
                                           legacy.calendar_sessions(old["calendar"], sources))
        actual = self.members(bundle)
        self.assertEqual(actual, expected)
        keys = {r["instrument_id"] for r in actual["2025-01"]}
        self.assertIn("research:test-1", keys)
        self.assertNotIn("research:test-2", keys)
        self.assertNotIn("research:test-3", keys)
        self.assertIs(selector.rank_classes, legacy.rank_classes)
        rows = [{"cik": str(i), "instrument_id": str(i), "median_dollar_volume": "20000000"}
                for i in range(550, 0, -1)]
        self.assertEqual([r["cik"] for r in selector.rank_classes(rows)], [str(i) for i in range(1, 501)])
        self.assertIs(selector.eligible_events, legacy.eligible_events)

    def test_liquidity_version_bound_to_scope_and_registration(self):
        bundle = deepcopy(self.base)
        scope = selector.build_scope(bundle, self.root, self.registration)
        document = {"scope": scope, "scope_sha256": digest(canonical(scope))}
        self.assertEqual(len(scope["targets"]), 50)  # In-memory synthetic only.
        self.assertEqual(len({r["cik"] for r in scope["targets"]}), 25)
        self.assertEqual(scope["liquidity_definition_version"], LIQUIDITY_VERSION)
        self.assertIn("liquidity_definition_version", scope["selection_evidence_hashes"])
        altered = deepcopy(document)
        altered["scope"]["liquidity_definition_version"] = "another-definition"
        altered["scope_sha256"] = digest(canonical(altered["scope"]))
        with self.assertRaisesRegex(AuditFailure, "UNIVERSE_OR_SELECTION_CHANGED"):
            selector.verify_frozen_inputs(altered, bundle, self.root, self.registration)
        bundle["liquidity_definition_version"] = "another-definition"
        with self.assertRaisesRegex(AuditFailure, "LIQUIDITY_DEFINITION_CHANGED"):
            selector.verify_frozen_inputs(document, bundle, self.root, self.registration)

    def test_prior_artifacts_and_nonliquidity_registration_unchanged(self):
        root = Path(__file__).parents[1]
        amendment = strict_json((root / "research/cohort_liquidity_amendment_003.json").read_bytes())
        for path, sha in amendment["prior_artifacts_unchanged"].items():
            self.assertEqual(digest((root / path).read_bytes()), sha, path)
        old = strict_json((root / "research/cohort_selection_registration_002.json").read_bytes())
        new = strict_json(self.registration)
        for key in old:
            if key not in {"version", "amendment_id", "registered_at", "universe", "freeze"}:
                self.assertEqual(old[key], new[key], key)
        for key in old["universe"]:
            if key != "bar_contract":
                self.assertEqual(old["universe"][key], new["universe"][key], key)


def bar(day):
    return {"t": day + "T05:00:00Z", "o": 20, "h": 22, "l": 19, "c": 21, "v": 1000}


class Response(io.BytesIO):
    status = 200
    headers = {"Content-Type": "application/json"}


class Opener:
    def __init__(self, bodies):
        self.bodies, self.requests = list(bodies), []

    def open(self, request, timeout):
        self.requests.append(request)
        body = self.bodies.pop(0)
        if isinstance(body, Exception):
            raise body
        return Response(canonical(body))


class DailyProbeTests(unittest.TestCase):
    def execute(self, bodies):
        with tempfile.TemporaryDirectory() as tmp:
            store = EvidenceStore(tmp)
            try:
                opener = Opener(bodies)
                http = ReadOnlyHTTP(store, user_agent="TEST", credentials=("SECRET_KEY_TEST", "SECRET_VALUE_TEST"),
                                    max_requests=5, opener=opener, sleep=lambda _: None)
                result = run_probe(http, store)
                raw = b"".join(p.read_bytes() for p in Path(tmp).rglob("*") if p.is_file())
                self.assertNotIn(b"SECRET_KEY_TEST", raw)
                self.assertNotIn(b"SECRET_VALUE_TEST", raw)
                for request in opener.requests:
                    self.assertEqual(request.get_method(), "GET")
                    query = parse_qs(urlsplit(request.full_url).query)
                    for key, value in (("feed", "sip"), ("timeframe", "1Day"), ("adjustment", "raw"), ("asof", "-")):
                        self.assertEqual(query[key], [value])
                    self.assertEqual(query["symbols"], ["AAPL,SPY"])
                self.assertEqual(store.verify()["status"], "VERIFIED")
                return result
            finally:
                store.close()

    def test_paginated_six_bars_request_and_immutable_provenance(self):
        result = self.execute([{"bars": {"AAPL": [bar(d) for d in DATES]}, "next_page_token": "second"},
                               {"bars": {"SPY": [bar(d) for d in DATES]}, "next_page_token": None}])
        self.assertEqual(result["status"], "PASS")
        self.assertEqual(result["historical_sip_access"], "SUCCEEDED_WITH_ROWS")
        self.assertEqual(result["rows_by_symbol"], {"AAPL": 3, "SPY": 3})
        self.assertEqual(len(result["provenance"]), 2)
        self.assertTrue(all(p["raw_sha256"] for p in result["provenance"]))

    def test_bad_aapl_quality_does_not_change_entitlement_or_spy_count(self):
        invalid = bar(DATES[0]); invalid["v"] = 0
        result = self.execute([{"bars": {"AAPL": [invalid], "SPY": [bar(d) for d in DATES]}}])
        self.assertEqual(result["historical_sip_access"], "SUCCEEDED_WITH_ROWS")
        self.assertEqual(result["status"], "UNRESOLVED")
        self.assertEqual(result["rows_by_symbol"]["SPY"], 3)

    def test_explicit_restriction_and_no_fallback(self):
        error = HTTPError("https://data.alpaca.markets/v2/stocks/bars", 403, "Forbidden", {},
                          io.BytesIO(b'{"message":"subscription does not permit querying recent SIP data"}'))
        result = self.execute([error])
        self.assertEqual(result["historical_sip_access"], "PROVIDER_RESTRICTION")
        self.assertEqual(len(result["provenance"]), 1)

    def test_unfinished_pagination_and_missing_dates_fail_closed(self):
        result = self.execute([{"bars": {"AAPL": [bar(DATES[0])]}, "next_page_token": "same"}] * 2)
        self.assertEqual(result["provider_failure"], "INVALID_OR_REPEATED_PAGE_TOKEN")
        self.assertEqual(result["status"], "UNRESOLVED")

    def test_timestamp_dst_and_numeric_validation(self):
        self.assertEqual(daily_date("2025-07-15T04:00:00Z"), "2025-07-15")
        self.assertEqual(daily_date("2025-01-15T05:00:00Z"), "2025-01-15")
        for value in ("2025-07-15T05:00:00Z", "2025-01-15T00:00:00Z", "2025-01-15T05:00:00.000000001Z"):
            with self.assertRaises(AuditFailure):
                daily_date(value)
        for value in (0, -1, float("nan"), float("inf"), True):
            for key in ("o", "h", "l", "c", "v"):
                row = bar(DATES[0]); row[key] = value
                with self.assertRaises(AuditFailure):
                    validate_daily_bar(row)

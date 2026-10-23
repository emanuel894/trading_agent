"""Synthetic selector regressions. No market data, returns or network access."""
from copy import deepcopy
from datetime import datetime, timedelta
from pathlib import Path
import tempfile
import unittest

from agent.audit_market import EASTERN
from agent.audit_store import AuditFailure, EvidenceStore, canonical, digest, strict_json
from agent.cohort_selector import (ConstructionBlocked, MONTHS, build_scope, calendar_sessions,
    evidence_sources, freeze_scope, freeze_registered_scope, identity_index, monthly_universes,
    rank_classes, verify_frozen_inputs)
from agent.dated_source_gate import frozen_scope_check


class SelectorTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.registration = (Path(__file__).parents[1] / "research/cohort_selection_registration_002.json").read_bytes()
        cls.temp = tempfile.TemporaryDirectory()
        cls.root = Path(cls.temp.name)
        (cls.root / "source.txt").write_bytes(b"SYNTHETIC TEST ONLY - NOT REAL UNIVERSE EVIDENCE")
        source = {"id": "synthetic", "path": "source.txt", "sha256": digest((cls.root / "source.txt").read_bytes()),
                  "source_url": "https://example.invalid/synthetic", "owner": "TEST", "available_at": "2024-01-01T00:00:00Z"}
        review = {"complete": True, "reviewed_by": "TEST", "rationale": "Synthetic fixture only", "evidence_ids": ["synthetic"]}
        sessions, day = [], datetime(2024, 9, 1)
        while day < datetime(2026, 1, 10):
            if day.weekday() < 5:
                sessions.append({"date": day.date().isoformat(),
                    "open": EASTERN.localize(day.replace(hour=9, minute=30)).isoformat(),
                    "close": EASTERN.localize(day.replace(hour=16)).isoformat()})
            day += timedelta(days=1)
        identities, bars, events = [], [], []
        for i in range(1, 27):
            cik, key = f"{i:010d}", f"research:test-{i}"
            identities.append({"instrument_id": key, "cik": cik, "issuer": "TEST", "lineage_id": key,
                "share_class": "common", "ticker": f"T{i}", "exchange": "XNYS", "security_type": "COMMON_STOCK",
                "valid_from": "2024-01-01T00:00:00Z", "valid_to": "2026-02-01T00:00:00Z",
                "known_at": "2024-01-01T00:00:00Z", "listed_since": "2024-01-01T00:00:00Z",
                "domestic_operating": True, "shell": False, "fund": False, "adr": False, "evidence_ids": ["synthetic"]})
            for session in sessions:
                if session["date"] <= "2025-11-28":
                    bars.append({"date": session["date"], "instrument_id": key, "ticker": f"T{i}", "close": "20",
                                 "volume": "1000000", "feed": "sip", "session": "RTH", "adjustment": "raw", "evidence_ids": ["synthetic"]})
            # Deliberately H2: no H1 two-filing requirement.
            for j, day in enumerate(("2025-07-15", "2025-10-15", "2025-11-15")):
                events.append({"cik": cik, "accession": f"{i:010d}-25-{j:06d}", "form": "10-Q",
                    "accepted_at": day + "T15:00:00Z", "report_date": "2025-06-30", "evidence_ids": ["synthetic"]})
        cls.base = {"version": "adr001-universe-inputs-v1", "sources": [source], "identities": identities,
            "population_by_month": {m: {**deepcopy(review), "instrument_ids": [r["instrument_id"] for r in identities]} for m in MONTHS},
            "calendar": {**deepcopy(review), "sessions": sessions}, "bars": bars,
            "filing_inventory": {**deepcopy(review), "indexed_originals": [{"cik": r["cik"], "accession": r["accession"]} for r in events], "events": events}}

    @classmethod
    def tearDownClass(cls):
        cls.temp.cleanup()

    def fixture(self):
        return deepcopy(self.base)

    def build(self, bundle):
        return build_scope(bundle, self.root, self.registration)

    def members(self, bundle):
        sources = evidence_sources(bundle, self.root)
        return monthly_universes(bundle, sources, identity_index(bundle["identities"], sources), calendar_sessions(bundle["calendar"], sources))

    def assert_first_issuer_excluded(self, bundle):
        scope = self.build(bundle)
        self.assertEqual(len(scope["targets"]), 50)
        ciks = {r["cik"] for r in scope["targets"]}
        self.assertNotIn("0000000001", ciks)
        self.assertIn("0000000026", ciks)

    def test_no_eligible_listed_common_share_cannot_enter(self):
        bundle = self.fixture()
        bundle["identities"][0]["exchange"] = "UNLISTED"
        self.assert_first_issuer_excluded(bundle)

    def test_listed_debt_is_not_common_stock(self):
        bundle = self.fixture()
        bundle["identities"][0]["security_type"] = "DEBT"
        self.assert_first_issuer_excluded(bundle)

    def test_proved_debt_does_not_require_common_issuer_or_price_facts(self):
        bundle = self.fixture()
        bundle["identities"][0].update(security_type="DEBT", domestic_operating=None, shell=None)
        bundle["bars"] = [r for r in bundle["bars"] if r["instrument_id"] != "research:test-1"]
        self.assert_first_issuer_excluded(bundle)

    def test_subsidiary_cannot_inherit_parent_ticker(self):
        bundle = self.fixture()
        # Subsidiary 1 files, but the only listed class belongs to parent 900.
        bundle["identities"][0]["cik"] = "0000000900"
        self.assert_first_issuer_excluded(bundle)

    def test_universe_filter_precedes_25_issuer_sample(self):
        bundle = self.fixture()
        bundle["identities"][0]["fund"] = True
        self.assert_first_issuer_excluded(bundle)
        scope = self.build(bundle)
        self.assertTrue(all(r["accepted_at"].startswith(("2025-07", "2025-10")) for r in scope["targets"]))
        self.assertEqual({r["actionable_at"] for r in scope["targets"]}, {r["actionable_at"] for r in scope["context_instruments"]})

    def test_changed_membership_invalidates_frozen_scope_even_if_targets_same(self):
        bundle = self.fixture()
        with tempfile.TemporaryDirectory() as tmp:
            store = EvidenceStore(tmp)
            try:
                path = Path(tmp) / "manifest.json"
                freeze_scope(self.build(bundle), store, path)
                document = strict_json(path.read_bytes())
                bundle["population_by_month"]["2025-01"]["instrument_ids"].remove("research:test-26")
                with self.assertRaisesRegex(AuditFailure, "UNIVERSE_OR_SELECTION_CHANGED"):
                    verify_frozen_inputs(document, bundle, self.root, self.registration)
            finally:
                store.close()

    def test_no_success_based_replacement_after_freeze_even_new_filename(self):
        bundle = self.fixture()
        with tempfile.TemporaryDirectory() as tmp:
            store = EvidenceStore(tmp)
            try:
                freeze_scope(self.build(bundle), store, Path(tmp) / "manifest.json")
                bundle["identities"][0]["fund"] = True
                with self.assertRaisesRegex(AuditFailure, "ALREADY_FROZEN_EXPLICIT_AMENDMENT"):
                    freeze_scope(self.build(bundle), store, Path(tmp) / "replacement.json")
                self.assertEqual(len(store.records("corrected_frozen_cohort")), 1)
            finally:
                store.close()

    def test_incomplete_population_blocks_instead_of_dropping_candidates(self):
        bundle = self.fixture()
        bundle["population_by_month"]["2025-01"]["complete"] = False
        with self.assertRaises(ConstructionBlocked) as caught:
            self.build(bundle)
        self.assertEqual(caught.exception.blockers[0]["field"], "dated_candidate_population")

    def test_missing_session_never_substitutes_older_session(self):
        bundle = self.fixture()
        bundle["bars"] = [r for r in bundle["bars"] if not (r["instrument_id"] == "research:test-1" and r["date"] == "2024-12-31")]
        with self.assertRaises(ConstructionBlocked) as caught:
            self.build(bundle)
        self.assertEqual(caught.exception.blockers[0]["date"], "2024-12-31")

    def test_thresholds_and_most_liquid_class(self):
        bundle = self.fixture()
        # The fixture is exactly on both the median threshold and above $10.
        self.assertEqual(len(self.members(bundle)["2025-01"]), 26)
        extra = {**bundle["identities"][0], "instrument_id": "research:other-class", "lineage_id": "other", "ticker": "OTHER"}
        bundle["identities"].append(extra)
        for row in bundle["population_by_month"].values():
            row["instrument_ids"].append(extra["instrument_id"])
        bundle["bars"].extend([{**r, "instrument_id": extra["instrument_id"], "ticker": "OTHER", "volume": "2000000"}
                               for r in list(bundle["bars"]) if r["instrument_id"] == "research:test-1"])
        rows = self.members(bundle)["2025-01"]
        self.assertEqual(rows[0]["instrument_id"], "research:other-class")
        self.assertEqual(len(rows), 26)

    def test_future_evidence_and_iex_are_rejected(self):
        bundle = self.fixture()
        bundle["sources"][0]["available_at"] = "2026-01-01T00:00:00Z"
        with self.assertRaises(ConstructionBlocked):
            self.build(bundle)
        bundle = self.fixture()
        for r in bundle["bars"]:
            r["feed"] = "iex"
        with self.assertRaisesRegex(AuditFailure, "UNREGISTERED_UNIVERSE_BAR_CONTRACT"):
            self.build(bundle)

    def test_selection_cannot_accept_success_or_return_fields(self):
        for field in ("acquisition_success", "future_return", "mda_score"):
            bundle = self.fixture()
            bundle["filing_inventory"]["events"][0][field] = True
            with self.assertRaisesRegex(AuditFailure, "UNREGISTERED_INPUT_FIELDS"):
                self.build(bundle)

    def test_missing_original_event_is_not_silently_skipped(self):
        bundle = self.fixture()
        bundle["filing_inventory"]["events"].pop(0)
        with self.assertRaisesRegex(AuditFailure, "INCOMPLETE_OR_CONFLICTING_ORIGINAL"):
            self.build(bundle)

    def test_top_500_precedes_cik_sampling_and_class_deduplication(self):
        rows = [{"cik": f"{i:010d}", "instrument_id": f"research:{i}",
                 "median_dollar_volume": str(20000000 + i)} for i in range(1, 502)]
        rows.append({**rows[-1], "instrument_id": "research:alternate", "median_dollar_volume": "20000000"})
        ranked = rank_classes(rows)
        self.assertEqual(len(ranked), 500)
        self.assertNotIn("0000000001", {r["cik"] for r in ranked})
        self.assertEqual(ranked[0]["cik"], "0000000501")
        self.assertEqual(len({r["cik"] for r in ranked}), 500)

    def test_prior_close_and_median_thresholds_are_exact(self):
        for close, volume in (("9.999999", "9000000"), ("20", "999999")):
            bundle = self.fixture()
            for bar in bundle["bars"]:
                if bar["instrument_id"] == "research:test-1":
                    bar.update(close=close, volume=volume)
            self.assert_first_issuer_excluded(bundle)

    def test_unknown_identity_blocks_and_conflicting_lineage_fails(self):
        bundle = self.fixture()
        bundle["identities"].pop(0)
        with self.assertRaises(ConstructionBlocked):
            self.build(bundle)
        bundle = self.fixture()
        bundle["identities"].append({**bundle["identities"][0], "cik": "0000000999"})
        with self.assertRaisesRegex(AuditFailure, "ID_REUSED_FOR_DIFFERENT_LINEAGE"):
            self.build(bundle)

    def test_registry_blocks_a_second_freeze_with_a_different_store(self):
        scope = self.build(self.fixture())
        project = Path(__file__).parents[1]
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            for relative in ("config/cohort_scope_registry.json", "research/cohort_scope_amendment_002.json",
                             "research/cohort_selection_registration_002.json"):
                path = root / relative
                path.parent.mkdir(parents=True, exist_ok=True)
                path.write_bytes((project / relative).read_bytes())
            registry_path = root / "config/cohort_scope_registry.json"
            registry = strict_json(registry_path.read_bytes())
            registry["active_scope_sha256"] = None  # Isolated synthetic registry.
            registry_path.write_bytes(canonical(registry))
            for i in range(2):
                store = EvidenceStore(root / f"store{i}")
                try:
                    if i == 0:
                        freeze_registered_scope(scope, store, root / "manifest.json", root)
                    else:
                        with self.assertRaisesRegex(AuditFailure, "ALREADY_FROZEN_EXPLICIT_AMENDMENT"):
                            freeze_registered_scope(scope, store, root / "replacement.json", root)
                finally:
                    store.close()

    def test_v2_gate_rebuilds_selection_and_detects_input_changes(self):
        bundle = self.fixture()
        scope = self.build(bundle)
        project = Path(__file__).parents[1]
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            (root / "source.txt").write_bytes((self.root / "source.txt").read_bytes())
            for relative in ("config/cohort_scope_registry.json", "research/cohort_scope_amendment_002.json",
                             "research/cohort_selection_registration_002.json"):
                path = root / relative
                path.parent.mkdir(parents=True, exist_ok=True)
                path.write_bytes((project / relative).read_bytes())
            registry_path = root / "config/cohort_scope_registry.json"
            registry = strict_json(registry_path.read_bytes())
            registry["active_scope_sha256"] = None
            registry_path.write_bytes(canonical(registry))
            store = EvidenceStore(root / "store")
            try:
                frozen = freeze_registered_scope(scope, store, root / "manifest.json", root)
            finally:
                store.close()
            raw = canonical(bundle)
            (root / "inputs.json").write_bytes(raw)
            packet = {"scope": scope, "frozen_manifest": {"path": "manifest.json", "sha256": frozen["file_sha256"]},
                      "selection_inputs": {"path": "inputs.json", "sha256": digest(raw)}}
            self.assertEqual(frozen_scope_check(packet, root)["status"], "PASS")
            bundle["population_by_month"]["2025-01"]["instrument_ids"].remove("research:test-26")
            raw = canonical(bundle)
            (root / "inputs.json").write_bytes(raw)
            packet["selection_inputs"]["sha256"] = digest(raw)
            with self.assertRaisesRegex(AuditFailure, "UNIVERSE_OR_SELECTION_CHANGED"):
                frozen_scope_check(packet, root)


if __name__ == "__main__":
    unittest.main()

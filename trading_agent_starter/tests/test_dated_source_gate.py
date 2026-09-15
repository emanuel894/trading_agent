"""Synthetic failure-oriented tests; fixtures are not historical evidence."""
from copy import deepcopy
from datetime import date
import io
from pathlib import Path
import tempfile
import unittest
from unittest.mock import patch

from agent.audit_sec import SECSource
from agent.audit_store import AuditFailure, EvidenceStore, canonical, digest, utc_now
from agent.dated_source_gate import (CRITERIA, SCOPED, VERSION, evaluate_packet,
                                    historical_tradability, main)
from agent.dated_source_review import sip_review
from agent.source_probe import PublicProbe, check_public_url, eastern_timestamp, parse_halt_rss
from test_evidence_audit import FixtureHTTP, columns, filing, quote


class DatedGateTests(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.root = Path(self.tmp.name)
        raw = b"Explicit synthetic reviewer assertions; never production evidence"
        (self.root / "source").write_bytes(raw)
        targets = [dict(cik=str(i // 2 + 1).zfill(10), accession=f"{i // 2 + 1:010d}-24-{i:06d}",
                        instrument_id=f"research:{i // 2}", actionable_at="2024-05-15T13:35:01Z") for i in range(50)]
        scope = {"targets": targets, "context_instruments": [{"cik": "0000000026", "symbol": "SPY",
            "instrument_id": "research:25", "actionable_at": "2024-05-15T13:35:01Z"}]}
        self.packet = {"version": VERSION, "scope": scope,
            "evidence": [{"id": "e", "path": "source", "sha256": digest(raw), "kind": "source_review"}],
            "instrument_intervals": [dict(instrument_id=f"research:{i}", cik=str(i+1).zfill(10),
                issuer=f"fixture{i}", share_class="common", ticker="SPY" if i == 25 else f"X{i}", exchange="XNYS",
                lineage_id=f"lineage{i}", id_authority="INTERNAL_RESEARCH", evidence_ids=["e"],
                valid_from="2024-01-01T00:00:00Z", valid_to="2025-01-01T00:00:00Z") for i in range(26)],
            "reviews": {name: {"reviewed_by": "synthetic reviewer", "reviewed_at": utc_now(),
                "scope_sha256": digest(canonical(scope)), "criteria": {k: {
                    "value": True, "evidence_ids": ["e"], "rationale": "Synthetic test assertion"}
                for k in keys}} for name, keys in CRITERIA.items()}}

    def tearDown(self):
        self.tmp.cleanup()

    def result(self):
        return evaluate_packet(self.packet, self.root)

    def test_historical_pass_does_not_require_realtime_sip_or_live_status(self):
        self.packet["reviews"]["prospective_readiness"]["criteria"]["realtime_sip"]["value"] = False
        result = self.result()
        self.assertEqual(result["historical_recommendation"], "RUN_50_HISTORICAL_AUDIT")
        self.assertEqual(result["prospective_recommendation"], "PROSPECTIVE_ACTIONABILITY_BLOCKED")
        self.assertFalse(result["audit_executed"])

    def test_each_missing_historical_review_blocks(self):
        for name in CRITERIA:
            if name == "prospective_readiness":
                continue
            with self.subTest(name=name):
                review = self.packet["reviews"].pop(name)
                self.assertEqual(self.result()["historical_recommendation"], "BLOCK_HISTORICAL_AUDIT")
                self.packet["reviews"][name] = review

    def test_hash_tampering_fails_and_unavailable_evidence_is_unresolved(self):
        (self.root / "source").write_bytes(b"changed")
        self.assertEqual(self.result()["gates"]["source_rights"]["status"], "FAIL")
        (self.root / "source").unlink()
        self.assertEqual(self.result()["gates"]["source_rights"]["status"], "UNRESOLVED")

    def test_scope_change_invalidates_dated_coverage_review(self):
        self.packet["scope"]["targets"][0]["actionable_at"] = "2024-05-16T13:35:01Z"
        result = self.result()
        for name in SCOPED:
            self.assertEqual(result["gates"][name]["status"], "UNRESOLVED")

    def test_no_scope_or_partial_scope_cannot_authorize_fifty(self):
        self.packet["scope"]["targets"] = self.packet["scope"]["targets"][:2]
        self.assertEqual(self.result()["historical_recommendation"], "BLOCK_HISTORICAL_AUDIT")

    def test_owner_access_does_not_prove_quote_quality_or_rights(self):
        self.packet["evidence"][0]["kind"] = "owner_local_observation"
        gates = self.result()["gates"]
        self.assertEqual(gates["historical_sip_access"]["status"], "PASS")
        self.assertEqual(gates["quote_policy_review"]["status"], "UNRESOLVED")
        self.assertEqual(gates["source_rights"]["status"], "UNRESOLVED")

    def test_identity_overlap_and_reused_lineage_fail(self):
        duplicate = deepcopy(self.packet["instrument_intervals"][0])
        duplicate["lineage_id"] = "different class"
        self.packet["instrument_intervals"].append(duplicate)
        result = self.result()["gates"]["instrument_identity"]
        self.assertEqual(result["status"], "FAIL")
        self.assertIn("INTERNAL_ID_REUSED_FOR_DIFFERENT_LINEAGE", result["reasons"])

    def test_evidence_path_escape_is_rejected(self):
        self.packet["evidence"][0]["path"] = "../outside"
        with self.assertRaisesRegex(AuditFailure, "PATH_OR_HASH"):
            self.result()

    def test_missing_packet_is_immutable_failure_with_nonzero_exit(self):
        with patch("builtins.print"):
            code = main(["--packet", str(self.root / "missing"), "--root", str(self.root),
                         "--store", str(self.root / "out")])
        self.assertEqual(code, 2)
        store = EvidenceStore(self.root / "out")
        try:
            self.assertEqual(store.records("dated_source_gate_result")[0]["metadata"]["failure"],
                             "MISSING_OR_MALFORMED_PACKET")
            self.assertEqual(store.verify()["status"], "VERIFIED")
        finally:
            store.close()


class HistoricalTradabilityTests(unittest.TestCase):
    def setUp(self):
        self.context = dict(at="2024-05-15T13:35:01Z",
            listing={"valid_from": "2024-01-01T00:00:00Z", "valid_to": "2025-01-01T00:00:00Z"},
            session={"open": "2024-05-15T13:30:00Z", "close": "2024-05-15T20:00:00Z"},
            quote=quote(), halts=[], conflicts=[], coverage={
                "feed": "sip", "source_record_ids": ["fixture"], "date_scope_complete": True,
                "market_scope_complete": True, "carry_in_resolved": True, "suspensions_reviewed": True})

    def test_historical_rule_can_pass_without_any_live_stream(self):
        result = historical_tradability(**self.context)
        self.assertEqual(result["status"], "PASS")
        self.assertEqual(result["label"], "HISTORICAL_TRADABILITY_RECONSTRUCTION")
        self.assertFalse(result["live_status"])
        self.assertEqual(result["decision_time_eligibility"], "NOT_EVALUATED")

    def test_quote_cannot_prove_no_halt_or_carry_in(self):
        self.context["coverage"]["carry_in_resolved"] = None
        self.assertEqual(historical_tradability(**self.context)["status"], "UNRESOLVED")
        self.context["halts"] = [{"halt_at": "2024-05-14T15:00:00Z"}]
        self.assertEqual(historical_tradability(**self.context)["status"], "FAIL")

    def test_scheduled_or_quote_only_resumption_does_not_close_halt(self):
        halt = {"halt_at": "2024-05-15T13:30:00Z", "scheduled_quote_resume_at": "2024-05-15T13:32:00Z"}
        self.context["halts"] = [halt]
        self.assertEqual(historical_tradability(**self.context)["status"], "FAIL")
        halt["scheduled_trade_resume_at"] = "2024-05-15T13:33:00Z"
        self.assertEqual(historical_tradability(**self.context)["status"], "UNRESOLVED")
        halt.update(actual_trade_resume_at="2024-05-15T13:34:00Z", resume_authoritative=True)
        self.assertEqual(historical_tradability(**self.context)["status"], "PASS")

    def test_future_events_do_not_retroactively_change_admission_context(self):
        self.context["halts"] = [{"halt_at": "2024-05-16T13:30:00Z"}]
        self.context["conflicts"] = [{"valid_from": "2024-05-16T00:00:00Z", "valid_to": "2024-05-17T00:00:00Z"}]
        self.assertEqual(historical_tradability(**self.context)["status"], "PASS")

    def test_wrong_feed_and_locked_quotes_fail_without_touching_entitlement(self):
        self.context["coverage"]["feed"] = "iex"
        self.assertIn("SIP_FEED_NOT_ENFORCED", historical_tradability(**self.context)["failed"])
        self.context["coverage"]["feed"] = "sip"
        self.context["quote"]["ap"] = self.context["quote"]["bp"]
        self.assertEqual(historical_tradability(**self.context)["status"], "FAIL")


def rss(count="1", market="N", trade="11:35:54"):
    return (f'<rss xmlns:n="http://www.nasdaqtrader.com/"><channel><n:numItems>{count}</n:numItems><item>'
            f'<n:IssueSymbol>BRK.A</n:IssueSymbol><n:Mkt>{market}</n:Mkt>'
            '<n:HaltDate>06/03/2024</n:HaltDate><n:HaltTime>09:50:52</n:HaltTime>'
            '<n:ResumptionDate>06/03/2024</n:ResumptionDate>'
            f'<n:ResumptionTradeTime>{trade}</n:ResumptionTradeTime></item></channel></rss>').encode()


class SourceReviewTests(unittest.TestCase):
    def test_non_nasdaq_rows_and_timestamp_semantics(self):
        result = parse_halt_rss(rss())
        self.assertEqual(result["market_frequencies"], {"N": 1})
        self.assertEqual(result["rows"][0]["halt_at"], "2024-06-03T13:50:52+00:00")
        self.assertFalse(result["negative_coverage_certified"])
        self.assertFalse(result["rows"][0]["item_pubdate_is_availability"])

    def test_bad_xml_counts_entities_and_ambiguous_dst_fail(self):
        for raw in [rss(count="2"), b'<!DOCTYPE rss><rss/>', b'<html>not RSS</html>', rss(trade="08:00:00")]:
            with self.assertRaises(AuditFailure):
                parse_halt_rss(raw)
        with self.assertRaisesRegex(AuditFailure, "TIME_AMBIGUOUS"):
            eastern_timestamp("11/03/2024", "01:30:00")

    def test_allowlist_and_rss_rate_limit_fail_before_network(self):
        for url in ["https://data.alpaca.markets/v2/orders", "https://evil.test/rss.aspx?feed=tradehalts",
                    "https://www.nasdaqtrader.com/rss.aspx?feed=tradehalts&haltdate=02312024"]:
            with self.assertRaises(AuditFailure):
                check_public_url(url)
        with tempfile.TemporaryDirectory() as tmp:
            store = EvidenceStore(tmp)
            try:
                url = "https://www.nasdaqtrader.com/rss.aspx?feed=tradehalts&haltdate=06032024"
                store.append("public_source", "prior", {"url": url, "received_at": utc_now()}, rss())
                with self.assertRaisesRegex(AuditFailure, "ONE_REQUEST_PER_MINUTE"):
                    PublicProbe(store).fetch("again", url)
                self.assertEqual(sip_review(store)["data_quality"], None)
            finally:
                store.close()

    def test_transition_report_is_discovered_but_never_an_ordinary_comparator(self):
        with tempfile.TemporaryDirectory() as tmp:
            store = EvidenceStore(tmp)
            try:
                transition = filing(form="10-QT")
                root = {"cik": 320193, "filings": {"recent": columns([transition]), "files": []}}
                rows = SECSource(store, FixtureHTTP(store, [root])).discover("320193", date(2024, 1, 1), date(2024, 12, 31))
                self.assertEqual(rows[0]["form"], "10-QT")
                with self.assertRaisesRegex(AuditFailure, "PRIOR_QUARTER"):
                    SECSource.comparator(filing(report="2025-03-31", accepted="2025-05-15T13:00:00Z"), rows)
            finally:
                store.close()

    def test_sip_review_counts_later_symbol_despite_earlier_bad_quote(self):
        with tempfile.TemporaryDirectory() as tmp:
            store = EvidenceStore(tmp)
            try:
                rows = {"AAPL": [dict(quote(), bp=101)], "SPY": [quote()]}
                store.append("http", "https://data.alpaca.markets/v2/stocks/quotes?feed=sip", {"http_status": 200}, canonical({"quotes": rows}))
                result = sip_review(store)
                self.assertEqual(result["data_quality"]["total_rows_by_symbol"], {"AAPL": 1, "SPY": 1})
                self.assertEqual(result["data_quality"]["strict_policy_pass_rate_at_row_timestamp"], 0.5)
                self.assertFalse(result["historical_entitlement_changed"])
            finally:
                store.close()


if __name__ == "__main__":
    unittest.main()

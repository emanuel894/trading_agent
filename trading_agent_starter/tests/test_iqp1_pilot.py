"""New fixed-pilot wiring tests; all rows/transports are explicit fixtures."""
import io
import json
from pathlib import Path
import tempfile
import unittest
from urllib.request import Request
from unittest.mock import patch

from agent.audit_store import AuditFailure, EvidenceStore, canonical

try:
    from agent import iqp1_pilot as pilot
except ImportError:
    pilot = None


class PilotTests(unittest.TestCase):
    def setUp(self):
        self.assertIsNotNone(pilot, "Fixed Windows pilot source wiring is missing")

    def test_exact_plan_preserves_dst_early_close_and_twelve_packets(self):
        plan = pilot.packet_plan()
        self.assertEqual(len(plan), 12)
        self.assertEqual(plan[0]["start"], "2025-01-15T14:30:00Z")
        self.assertEqual(plan[4]["start"], "2025-03-10T13:30:00Z")
        self.assertEqual(plan[11]["start"], "2025-07-03T16:54:58Z")
        self.assertEqual(plan[11]["end"], "2025-07-03T17:00:00Z")
        self.assertEqual([x["max_pages"] for x in plan[:4]], [1, 5, 5, 5])

    def test_data_gateway_rejects_orders_other_hosts_methods_and_changed_windows(self):
        from urllib.parse import urlencode
        p = pilot.packet_plan()[1]
        query = dict(symbols="SPY", start=p["start"], end=p["end"], feed="sip",
                     asof="-", sort="asc", limit="10000")
        url = "https://data.alpaca.markets/v2/stocks/quotes?" + urlencode(query)
        self.assertEqual(pilot.validate_data_request(Request(url)), p["id"])
        for bad in (Request(url, method="POST"), Request(url.replace("data.alpaca", "paper-api.alpaca")),
                    Request(url.replace("/quotes?", "/orders?")),
                    Request(url.replace("symbols=SPY", "symbols=AAPL")),
                    Request(url + "&feed=iex"), Request(url.replace("https:", "http:"))):
            with self.subTest(url=bad.full_url):
                with self.assertRaises(AuditFailure):
                    pilot.validate_data_request(bad)

    def test_readonly_source_cache_cannot_create_or_modify_evidence(self):
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary) / "source"
            store = EvidenceStore(root)
            record = store.append("fixture", "source", {"capture_mode": "fixture"}, b"retained")
            store.close()
            reader = pilot.open_cache(root,fixture_only=True)
            try:
                self.assertEqual(reader.raw(reader.get(record["id"])), b"retained")
                with self.assertRaises(Exception):
                    reader.append("fixture", "bad", {}, b"must not write")
            finally:
                reader.close()
            with self.assertRaisesRegex(AuditFailure,"ORIGINAL_JAN15_DATABASE_BINDING"):
                pilot.open_cache(root)
            with self.assertRaises(AuditFailure):
                pilot.open_cache(Path(temporary) / "absent")

    def test_cache_reference_rejects_traversal_before_any_file_read(self):
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary)/"cache"
            store = EvidenceStore(root)
            store.close()
            reader = pilot.open_cache(root,fixture_only=True)
            try:
                with patch.object(Path,"read_bytes",side_effect=AssertionError("must not read")):
                    with self.assertRaisesRegex(AuditFailure,"OBJECT_REFERENCE_UNSAFE"):
                        reader.raw({"blob_sha":"../../credential-reference"})
            finally:
                reader.close()

    def test_existing_jan15_chain_covers_both_windows_without_new_http(self):
        from urllib.parse import urlencode
        with tempfile.TemporaryDirectory() as temporary:
            store = EvidenceStore(Path(temporary))
            q = dict(symbols="AAPL,SPY", start="2025-01-15T15:00:00Z",
                     end="2025-01-15T15:05:00Z", feed="sip", asof="-", sort="asc", limit="10000")
            raw = canonical({"quotes": {"SPY": [{"t":"2025-01-15T15:01:03Z"},
                                                 {"t":"2025-01-15T15:02:03Z"}]}, "next_page_token":None})
            r = store.append("http", "https://data.alpaca.markets/v2/stocks/quotes?" + urlencode(q),
                             {"http_status":200,"failure":None,"capture_mode":"fixture"}, raw)
            try:
                for packet in pilot.packet_plan()[1:3]:
                    self.assertEqual([x["id"] for x in pilot.cache_chain(store, packet, fixture_only=True)], [r["id"]])
                with self.assertRaises(AuditFailure):
                    pilot.cache_chain(store, pilot.packet_plan()[1])
            finally:
                store.close()

    def test_fixture_end_to_end_single_ledger_reuse_caps_and_no_restart(self):
        from urllib.parse import urlencode
        from agent.iqp1_http_budget import IQP1HTTPBudget
        class Transport:
            def __init__(self):
                self.urls = []
            def open(self, request, timeout):
                packet_id = pilot.validate_data_request(request)
                p = next(p for p in pilot.packet_plan() if p["id"] == packet_id)
                self.urls.append(request.full_url)
                response = io.BytesIO(canonical({p["kind"]:{"SPY":[{"t":p["start"]}]}, "next_page_token":None}))
                response.status, response.headers = 200, {}
                return response
        with tempfile.TemporaryDirectory() as temporary:
            cache = EvidenceStore(Path(temporary)/"old")
            store = EvidenceStore(Path(temporary)/"sole")
            q = dict(symbols="AAPL,SPY", start="2025-01-15T15:00:00Z", end="2025-01-15T15:05:00Z", feed="sip")
            cache.append("http", "https://data.alpaca.markets/v2/stocks/quotes?"+urlencode(q),
                         {"http_status":200,"failure":None,"capture_mode":"fixture"},
                         canonical({"quotes":{"SPY":[{"t":"2025-01-15T15:01:03Z"}]}}))
            transport = Transport()
            try:
                with patch("agent.audit_http.time.sleep"):
                    result = pilot.run_pilot(store, cache, ("fixture-id", "fixture-secret"),
                                              lambda:None, fixture_transport=transport)
                self.assertEqual(result["status"], "FIXTURE_ONLY")
                self.assertEqual(result["attempts"], 10)
                self.assertEqual(len(transport.urls), 10)
                self.assertFalse(any("15%3A00%3A59" in u or "15%3A01%3A59" in u for u in transport.urls))
                self.assertEqual(result["pending"], [])
                self.assertEqual(result["logical_packets"], 12)
                self.assertEqual(store.verify()["status"], "VERIFIED")
                before = IQP1HTTPBudget(store).snapshot()
                with self.assertRaises(AuditFailure):
                    pilot.run_pilot(store, cache, ("fixture-id", "fixture-secret"), lambda:None, fixture_transport=transport)
                self.assertEqual(before, IQP1HTTPBudget(store).snapshot())
                self.assertNotIn("fixture-secret", json.dumps(store.records()))
            finally:
                cache.close()
                store.close()

    def test_transport_is_never_called_after_gate_denial(self):
        from unittest.mock import Mock
        transport = Mock()
        opener = pilot.DataOnlyOpener(lambda: (_ for _ in ()).throw(AuditFailure("NO_RESERVE")), transport=transport)
        from urllib.parse import urlencode
        p = pilot.packet_plan()[1]
        request = Request("https://data.alpaca.markets/v2/stocks/quotes?"+urlencode(dict(
            symbols="SPY",start=p["start"],end=p["end"],feed="sip",asof="-",sort="asc",limit="10000")))
        with self.assertRaises(AuditFailure):
            opener.open(request, timeout=20)
        transport.open.assert_not_called()


if __name__ == "__main__":
    unittest.main()

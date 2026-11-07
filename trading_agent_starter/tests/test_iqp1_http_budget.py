"""Offline enforcement tests; fake responses never represent actual pilot data."""
from datetime import datetime, timedelta, timezone
import io
from pathlib import Path
import tempfile
import unittest
from concurrent.futures import ThreadPoolExecutor
from threading import Barrier
from unittest.mock import patch
from urllib.error import HTTPError

from agent.audit_http import ReadOnlyHTTP
from agent.audit_market import SIPSource
from agent.audit_store import AuditFailure, EvidenceStore

try:
    from agent.iqp1_http_budget import IQP1HTTPBudget
except ImportError:
    IQP1HTTPBudget = None


URL = "https://data.sec.gov/submissions/CIK0000000001.json"


class FakeResponse(io.BytesIO):
    status = 200
    headers = {}


class FakeOpener:
    def __init__(self, bodies):
        self.bodies, self.calls = list(bodies), 0

    def open(self, request, timeout):
        self.calls += 1
        value = self.bodies.pop(0)
        if isinstance(value, Exception):
            raise value
        return FakeResponse(value)


class IQP1HTTPBudgetTests(unittest.TestCase):
    def setUp(self):
        self.assertIsNotNone(IQP1HTTPBudget, "Durable pilot HTTP accounting is not implemented")
        self.temporary = tempfile.TemporaryDirectory()
        self.addCleanup(self.temporary.cleanup)
        self.root = Path(self.temporary.name) / "store"
        self.store = EvidenceStore(self.root)
        self.addCleanup(self.store.close)
        self.now = datetime(2026, 11, 6, 18, tzinfo=timezone.utc)

    def clock(self):
        return self.now.isoformat()

    def budget(self, **limits):
        return IQP1HTTPBudget.create(self.store, clock=self.clock, **limits)

    def http(self, budget, bodies, **kwargs):
        opener = FakeOpener(bodies)
        client = ReadOnlyHTTP(self.store, user_agent="explicit synthetic accounting test",
                              opener=opener, sleep=lambda _: None, budget=budget, **kwargs)
        return client, opener

    def test_new_http_instances_cannot_reset_persistent_attempts(self):
        budget = self.budget(max_attempts=2)
        for _ in range(2):
            client, _ = self.http(budget, [b"{}"], max_requests=1)
            client.get(URL)
        reopened = IQP1HTTPBudget(self.store, clock=self.clock)
        client, opener = self.http(reopened, [b"never requested"])
        with self.assertRaisesRegex(AuditFailure, "ATTEMPT_BUDGET_EXHAUSTED"):
            client.get(URL)
        self.assertEqual(opener.calls, 0)
        self.assertEqual(reopened.snapshot()["attempts"], 2)
        self.assertEqual(reopened.snapshot()["charged_body_bytes"], 4)

    def test_retries_and_failed_bodies_consume_one_cumulative_budget(self):
        budget = self.budget(max_attempts=2)
        errors = [HTTPError(URL, 500, "synthetic", {}, io.BytesIO(b"err")) for _ in range(3)]
        client, opener = self.http(budget, errors)
        with self.assertRaisesRegex(AuditFailure, "ATTEMPT_BUDGET_EXHAUSTED"):
            client.get(URL)
        self.assertEqual(opener.calls, 2)
        self.assertEqual(budget.snapshot()["attempts"], 2)
        self.assertEqual(budget.snapshot()["retained_body_bytes"], 6)

    def test_pending_reservation_survives_reopen_and_blocks_new_request(self):
        budget = self.budget(body_limit=10)
        token, allowance = budget.reserve(URL, 8)
        other = EvidenceStore(self.root)
        try:
            reopened = IQP1HTTPBudget(other, clock=self.clock)
            self.assertEqual(reopened.snapshot()["charged_body_bytes"], 8)
            self.assertEqual(reopened.snapshot()["pending"], [token])
            with self.assertRaisesRegex(AuditFailure, "UNRECONCILED"):
                reopened.reserve(URL, 2)
        finally:
            other.close()
        self.assertEqual(allowance, 8)

    def test_settlement_requires_matching_persisted_http_evidence_once(self):
        budget = self.budget(body_limit=10)
        token, _ = budget.reserve(URL, 8)
        unrelated = self.store.append("http", URL, {}, b"abc")
        with self.assertRaises(AuditFailure):
            budget.settle(token, unrelated["id"])
        matching = self.store.append("http", URL, {"budget_reservation_id": token}, b"abc")
        budget.settle(token, matching["id"])
        self.assertEqual(budget.snapshot()["charged_body_bytes"], 3)
        with self.assertRaises(AuditFailure):
            budget.settle(token, matching["id"])

    def test_existing_persisted_response_can_reconcile_interrupted_settlement(self):
        budget = self.budget(body_limit=10)
        token, _ = budget.reserve(URL, 8)
        matching = self.store.append("http", URL, {"budget_reservation_id": token}, b"abc")
        reopened = IQP1HTTPBudget(self.store, clock=self.clock)
        reopened.settle(token, matching["id"])
        self.assertEqual(reopened.snapshot()["retained_body_bytes"], 3)
        self.assertEqual(reopened.snapshot()["pending"], [])

    def test_replayed_settlement_without_response_cannot_refund_budget(self):
        budget = self.budget(body_limit=10)
        token, _ = budget.reserve(URL, 8)
        self.store.append(budget.KIND, budget.KEY, {
            "op": "settle", "reservation_id": token, "http_record_id": "missing-response",
            "retained": 0, "at": self.clock(),
        })
        with self.assertRaises(AuditFailure):
            budget.snapshot()

    def test_error_body_cannot_overshoot_remaining_retained_byte_allowance(self):
        budget = self.budget(body_limit=5)
        error = HTTPError(URL, 403, "synthetic", {}, io.BytesIO(b"123456789"))
        client, opener = self.http(budget, [error])
        with self.assertRaisesRegex(AuditFailure, "HTTP_403"):
            client.get(URL)
        self.assertEqual(opener.calls, 1)
        self.assertEqual(budget.snapshot()["retained_body_bytes"], 5)
        self.assertEqual(len(self.store.raw(self.store.records("http")[0])), 5)

    def test_oversize_success_stops_at_reserved_retained_bytes(self):
        budget = self.budget(body_limit=5)
        client, opener = self.http(budget, [b"123456789"])
        with self.assertRaisesRegex(AuditFailure, "RESPONSE_TOO_LARGE"):
            client.get(URL)
        self.assertEqual(budget.snapshot()["charged_body_bytes"], 5)
        with self.assertRaisesRegex(AuditFailure, "BYTE_BUDGET_EXHAUSTED"):
            client.get(URL)
        self.assertEqual(opener.calls, 1)

    def test_deadline_and_clock_regression_block_without_reset(self):
        budget = self.budget(max_seconds=60)
        self.now += timedelta(seconds=60)
        with self.assertRaisesRegex(AuditFailure, "DEADLINE"):
            IQP1HTTPBudget(self.store, clock=self.clock).reserve(URL, 1)
        self.now -= timedelta(seconds=61)
        with self.assertRaisesRegex(AuditFailure, "CLOCK_REGRESSION"):
            budget.reserve(URL, 1)

    def test_initialization_cannot_be_repeated_or_silently_created_on_resume(self):
        with self.assertRaisesRegex(AuditFailure, "NOT_INITIALIZED"):
            IQP1HTTPBudget(self.store, clock=self.clock)
        self.budget()
        with self.assertRaisesRegex(AuditFailure, "ALREADY_INITIALIZED"):
            self.budget()

    def test_stricter_local_transport_budget_is_preserved(self):
        budget = self.budget()
        client, opener = self.http(budget, [b"{}", b"{}"], max_requests=1)
        client.get(URL)
        with self.assertRaisesRegex(AuditFailure, "HTTP_REQUEST_BUDGET_EXHAUSTED"):
            client.get(URL)
        self.assertEqual(opener.calls, 1)
        self.assertEqual(budget.snapshot()["attempts"], 1)

    def test_source_pagination_consumes_the_same_budget(self):
        budget = self.budget(max_attempts=2)
        bodies = [b'{"quotes":{"SPY":[{"t":"2025-01-15T15:00:59Z"}]},"next_page_token":"two"}',
                  b'{"quotes":{"SPY":[{"t":"2025-01-15T15:01:00Z"}]},"next_page_token":null}']
        client, opener = self.http(budget, bodies, credentials=("SYNTHETIC_KEY", "SYNTHETIC_SECRET"))
        rows, records = SIPSource(self.store, client).pages(
            "quotes", ["SPY"], "2025-01-15T15:00:59Z", "2025-01-15T15:01:06Z", max_pages=5)
        self.assertEqual((opener.calls, len(records), len(rows["SPY"])), (2, 2, 2))
        self.assertEqual(budget.snapshot()["attempts"], 2)

    def test_failed_response_persistence_leaves_full_reservation_and_blocks_retry(self):
        budget = self.budget(body_limit=10)
        client, opener = self.http(budget, [b"{}", b"never requested"])
        with patch.object(self.store, "append", side_effect=AuditFailure("SYNTHETIC_STORAGE_FAILURE")):
            with self.assertRaisesRegex(AuditFailure, "STORAGE_FAILURE"):
                client.get(URL)
        reopened = IQP1HTTPBudget(self.store, clock=self.clock)
        self.assertEqual(reopened.snapshot()["charged_body_bytes"], 10)
        self.assertEqual(reopened.snapshot()["attempts"], 1)
        with self.assertRaisesRegex(AuditFailure, "UNRECONCILED"):
            client.get(URL)
        self.assertEqual(opener.calls, 1)

    def test_competing_connections_cannot_reserve_two_concurrent_requests(self):
        self.budget()
        barrier = Barrier(2)
        def reserve():
            store = EvidenceStore(self.root)
            try:
                budget = IQP1HTTPBudget(store, clock=self.clock)
                barrier.wait(timeout=10)
                try:
                    budget.reserve(URL, 10)
                    return "reserved"
                except AuditFailure as error:
                    return str(error)
            finally:
                store.close()
        with ThreadPoolExecutor(max_workers=2) as pool:
            results = list(pool.map(lambda _: reserve(), range(2)))
        self.assertCountEqual(results, ["reserved", "PILOT_HTTP_ATTEMPT_UNRECONCILED"])

    def test_limits_cannot_exceed_the_owner_cap(self):
        for limits in ({"max_attempts":129}, {"body_limit":2_000_000_001}, {"max_seconds":1801}):
            with self.subTest(limits=limits):
                with self.assertRaises(AuditFailure):
                    self.budget(**limits)
        self.assertFalse(self.store.records("iqp1_http_budget"))


if __name__ == "__main__":
    unittest.main()

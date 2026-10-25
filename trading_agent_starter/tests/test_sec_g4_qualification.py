"""Offline adversarial probes; never contact SEC in CI."""
from dataclasses import replace
from datetime import datetime, timedelta, timezone
from email.message import Message
from io import BytesIO
import http.client
from pathlib import Path
import tempfile
import unittest
from unittest.mock import patch

from agent import sec_g4_qualification as g4
from agent.audit_store import AuditFailure, digest
from agent.sec_preservation_offline import Limits
from agent.sec_preservation_offline import ClockSample


class Reply:
    def __init__(self, body=b'abc', status=200, headers=()):
        self.status, self.stream = status, BytesIO(body)
        self.headers = Message()
        for k, v in headers:
            self.headers[k] = v
        self.closed = False
    def read1(self, n):
        return self.stream.read(n)
    def close(self):
        self.closed = True


class Opener:
    def __init__(self, *replies):
        self.replies, self.calls = list(replies), []
    def open(self, request, timeout):
        self.calls.append((request, timeout))
        return self.replies.pop(0)


class WireSocket:
    def __init__(self, raw):
        self.raw = raw
    def makefile(self, *args):
        return BytesIO(self.raw)


def wire(raw):
    response = g4.StrictResponse(WireSocket(raw))
    response.begin()
    return response


class QualificationTests(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.addCleanup(self.tmp.cleanup)
        self.opener = Opener(Reply(headers=(('Content-Length', '3'),)))
        self.now = 0.0
        self.limits = Limits(max_requests=18, max_total_bytes=1000,
                             max_response_bytes=99, max_jobs=6, max_events=100, max_records=1000)
    def sleep(self, seconds):
        self.now += seconds
    def open(self):
        self.q = g4.Qualification(Path(self.tmp.name), authorization_ref='fixture-authorization',
            opener=self.opener, timer=lambda: self.now, sleep=self.sleep, limits=self.limits)
        self.q.clock = lambda: ClockSample(
            (datetime(2026, 10, 21, tzinfo=timezone.utc) + timedelta(seconds=self.now)).isoformat(),
            int(self.now * 1e9), 'fixture-session', None, None)
        self.addCleanup(self.q.close)
        return self.q
    def test_exact_bytes_clocks_and_hash_are_preserved(self):
        q = self.open()
        r = q.fetch(q.plans[0])
        self.assertEqual(q.store.raw(r), b'abc')
        self.assertEqual(r['blob_sha'], digest(b'abc'))
        self.assertIsNotNone(r['metadata']['body_completed'])
        self.assertEqual(r['metadata']['mode'], 'SYNTHETIC_OFFLINE')
        self.assertEqual(r['metadata']['framing'], 'content-length')
        self.assertEqual(q.summary()['control']['bytes_charged'], 3)
        self.assertEqual(q.store.verify()['status'], 'VERIFIED')
    def test_forbidden_stops_all_subsequent_requests(self):
        self.opener = Opener(Reply(status=403), Reply())
        q = self.open()
        q.fetch(q.plans[0])
        with self.assertRaises(AuditFailure):
            q.fetch(q.plans[1])
        self.assertEqual(len(self.opener.calls), 1)
    def test_truncated_or_ambiguous_framing_never_becomes_receipt(self):
        for headers in ((('Content-Length','9'),), (('Content-Length','3'),('Content-Length','3')),
                        (('Content-Length','3'),('Transfer-Encoding','chunked')),
                        (('Content-Encoding','gzip'),),
                        (('Content-Encoding','gzip'),('Content-Encoding','identity'))):
            with self.subTest(headers=headers), tempfile.TemporaryDirectory() as root:
                q = g4.Qualification(root, authorization_ref='fixture', opener=Opener(Reply(headers=headers)))
                try:
                    r = q.fetch(q.plans[0])
                    self.assertIsNone(r['metadata']['document_receipt'])
                    with self.assertRaises(AuditFailure):
                        q.fetch(q.plans[1])
                finally:
                    q.close()
    def test_exact_response_ceiling_is_counted_and_halts(self):
        self.opener = Opener(Reply(b'x' * 200))
        q = self.open()
        r = q.fetch(q.plans[0])
        self.assertEqual(len(q.store.raw(r)), 100)
        self.assertEqual(q.summary()['control']['bytes_charged'], 100)
        self.assertIsNone(r['metadata']['document_receipt'])
        with self.assertRaises(AuditFailure):
            q.fetch(q.plans[1])
    def test_disk_or_reservation_failure_prevents_network(self):
        q = self.open()
        with patch.object(g4.shutil, 'disk_usage', return_value=type('Disk', (), {'free': 0})()):
            with self.assertRaisesRegex(AuditFailure, 'DISK_RESERVE'):
                q.fetch(q.plans[0])
        self.assertEqual(self.opener.calls, [])
    def test_persistence_failure_prevents_next_dispatch(self):
        q = self.open()
        with patch.object(q.store, 'append_in_transaction', side_effect=OSError()):
            with self.assertRaises(AuditFailure):
                q.fetch(q.plans[0])
        with self.assertRaises(AuditFailure):
            q.fetch(q.plans[1])
        self.assertEqual(self.opener.calls, [])
    def test_deadline_prevents_dispatch_and_timeout_is_bounded(self):
        q = self.open()
        self.now = 900
        with self.assertRaisesRegex(AuditFailure, 'DEADLINE'):
            q.fetch(q.plans[0])
        self.assertEqual(self.opener.calls, [])
    def test_retry_after_is_global_and_rate_waits_from_completion(self):
        self.opener = Opener(Reply(status=503, headers=(('Retry-After','7'),)), Reply(), Reply())
        q = self.open()
        q.fetch(q.plans[0])
        q.fetch(q.plans[1])
        self.assertGreaterEqual(self.now, 9)
        self.assertEqual(len(self.opener.calls), 3)
    def test_bad_retry_after_and_redirect_are_terminal(self):
        for status, headers in ((503, (('Retry-After','tomorrow'),)), (302, (('Location','https://evil.test'),))):
            with self.subTest(status=status), tempfile.TemporaryDirectory() as root:
                o = Opener(Reply(status=status, headers=headers))
                q = g4.Qualification(root, authorization_ref='fixture', opener=o)
                try:
                    q.fetch(q.plans[0])
                    with self.assertRaises(AuditFailure):
                        q.fetch(q.plans[1])
                    self.assertEqual(len(o.calls), 1)
                finally:
                    q.close()
    def test_manifest_rejects_new_job_and_existing_root_cannot_reset(self):
        q = self.open()
        with self.assertRaises(AuditFailure):
            q.fetch(g4.plan_request('discovery', start=100))
        q.close()
        with self.assertRaisesRegex(AuditFailure, 'ONE_SHOT'):
            self.open()
    def test_duplicate_request_does_not_fetch_or_reset_version(self):
        q = self.open()
        a = q.fetch(q.plans[0])
        b = q.fetch(q.plans[0])
        self.assertEqual(a['id'], b['id'])
        self.assertEqual(len(self.opener.calls), 1)
    def test_caps_cannot_be_expanded(self):
        self.limits = replace(self.limits, max_requests=19)
        with self.assertRaises(AuditFailure):
            self.open()
    def test_corrupt_cumulative_accounting_stops_before_next_request(self):
        self.opener.replies.append(Reply())
        q = self.open()
        q.fetch(q.plans[0])
        with q.db:
            q.db.execute('UPDATE preservation_control SET requests=0,bytes_charged=0')
        with self.assertRaisesRegex(AuditFailure, 'QUEUE_CORRUPT'):
            q.fetch(q.plans[1])
        self.assertEqual(len(self.opener.calls), 1)
    def test_actual_chunked_and_close_delimited_entity_bytes(self):
        for raw in (b'HTTP/1.1 200 OK\r\nTransfer-Encoding: chunked\r\n\r\n3\r\nabc\r\n0\r\n\r\n',
                    b'HTTP/1.0 200 OK\r\n\r\nabc'):
            with self.subTest(raw=raw), tempfile.TemporaryDirectory() as root:
                q = g4.Qualification(root, authorization_ref='fixture', opener=Opener(wire(raw)))
                try:
                    r = q.fetch(q.plans[0])
                    self.assertEqual(q.store.raw(r), b'abc')
                    self.assertIsNotNone(r['metadata']['document_receipt'])
                finally:
                    q.close()
    def test_actual_truncated_content_length_and_chunked_keep_partial_bytes(self):
        for raw in (b'HTTP/1.1 200 OK\r\nContent-Length: 9\r\n\r\nabc',
                    b'HTTP/1.1 200 OK\r\nTransfer-Encoding: chunked\r\n\r\n3\r\nabc\r\n'):
            with self.subTest(raw=raw), tempfile.TemporaryDirectory() as root:
                q = g4.Qualification(root, authorization_ref='fixture', opener=Opener(wire(raw)))
                try:
                    r = q.fetch(q.plans[0])
                    self.assertEqual(q.store.raw(r), b'abc')
                    self.assertIsNone(r['metadata']['document_receipt'])
                    with self.assertRaises(AuditFailure):
                        q.fetch(q.plans[1])
                finally:
                    q.close()
    def test_chunk_framing_is_not_entity_data_and_missing_trailer_cannot_complete(self):
        for tail in (b'3\r\nabc\r', b'3\r\nabc\r\n0\r\n', b'3\r\nabcXY0\r\n\r\n'):
            with self.subTest(tail=tail), tempfile.TemporaryDirectory() as root:
                raw = b'HTTP/1.1 200 OK\r\nTransfer-Encoding: chunked\r\n\r\n' + tail
                q = g4.Qualification(root, authorization_ref='fixture', opener=Opener(wire(raw)))
                try:
                    r = q.fetch(q.plans[0])
                    self.assertEqual(q.store.raw(r), b'abc')
                    self.assertEqual(r['metadata']['byte_count'], 3)
                    self.assertIsNone(r['metadata']['document_receipt'])
                finally:
                    q.close()
    def test_aggregate_reservation_exhaustion_does_not_send_second_request(self):
        self.limits = replace(self.limits, max_total_bytes=100)
        q = self.open()
        q.fetch(q.plans[0])
        with self.assertRaisesRegex(AuditFailure, 'BYTE_BUDGET_EXHAUSTED'):
            q.fetch(q.plans[1])
        self.assertEqual(len(self.opener.calls), 1)
    def test_request_exhaustion_does_not_send_second_request(self):
        self.limits = replace(self.limits, max_requests=1)
        q = self.open()
        q.fetch(q.plans[0])
        with self.assertRaisesRegex(AuditFailure, 'REQUEST_BUDGET_EXHAUSTED'):
            q.fetch(q.plans[1])
        self.assertEqual(len(self.opener.calls), 1)
    def test_slow_body_crossing_deadline_is_preserved_without_receipt(self):
        reply = Reply()
        original = reply.read1
        def slow(n):
            self.now = 901
            return original(n)
        reply.read1 = slow
        self.opener = Opener(reply)
        q = self.open()
        r = q.fetch(q.plans[0])
        self.assertEqual(q.store.raw(r), b'abc')
        self.assertIsNone(r['metadata']['document_receipt'])
        with self.assertRaises(AuditFailure):
            q.fetch(q.plans[1])
    def test_submissions_selects_exact_original_and_preserves_native_clock(self):
        raw = b'{"cik":700565,"filings":{"recent":{"accessionNumber":["0000950170-25-067613"],"form":["10-Q"],"primaryDocument":["fmbh-20250331.htm"],"acceptanceDateTime":["2025-05-09T17:52:26.000Z"],"filingDate":["2025-05-09"],"reportDate":["2025-03-31"]}}}'
        v = g4.native_metadata(g4.six_plans()[1], raw)
        self.assertEqual(v['acceptance_native'], '2025-05-09T17:52:26.000Z')
        self.assertIsNone(v['resolved_acceptance_utc'])
        with self.assertRaises(AuditFailure):
            g4.native_metadata(g4.six_plans()[1], raw.replace(b'10-Q', b'10-Q/A'))
    def test_accession_index_extracts_size_from_the_size_cell(self):
        raw = b'<table class="tableFile"><tr><th>Seq</th><th>Description</th><th>Document</th><th>Type</th><th>Size</th></tr><tr><td>1</td><td>10-Q</td><td><a>fmbh-20250331.htm</a> iXBRL</td><td>10-Q</td><td>7305910</td></tr></table>'
        v = g4.native_metadata(g4.six_plans()[2], raw)
        self.assertEqual(v['indexed_primary_sizes_native'], ['7305910'])
    def test_atom_dtd_is_rejected_and_publication_keeps_native_precision(self):
        p = g4.six_plans()[0]
        v = g4.native_metadata(p, b'<feed xmlns="http://www.w3.org/2005/Atom"><updated>2026-10-21T12:00:00-04:00</updated></feed>')
        self.assertEqual(v['updated_native'], ['2026-10-21T12:00:00-04:00'])
        with self.assertRaises(AuditFailure):
            g4.native_metadata(p, b'<!DOCTYPE x><feed/>')

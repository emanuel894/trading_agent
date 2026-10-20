"""Issue 41: inert fixtures only; every attempted socket/HTTP call fails."""
from dataclasses import replace
from datetime import datetime, timedelta, timezone
from pathlib import Path
import tempfile
import unittest
from unittest.mock import patch

from agent.audit_store import AuditFailure, canonical
from agent import sec_preactivation_offline as adapter
from agent.sec_preservation_offline import ClockSample, Limits, OfflinePreserver

CIK = '0000000123'
ACC = '0000099999-26-000001'  # accession prefix is the agent, not necessarily issuer CIK


class Clock:
    def __init__(self, session='A'):
        self.now = datetime(2026, 1, 1, tzinfo=timezone.utc)
        self.ns = 0
        self.session = session
    def advance(self, seconds):
        self.now += timedelta(seconds=seconds)
        self.ns += int(seconds * 1e9)
    def __call__(self):
        self.ns += 1
        return ClockSample(self.now.isoformat(), self.ns, self.session, 0, 'synthetic-offset')


def item(form='10-Q', accession=ACC, **extra):
    return dict(cik=CIK, accession=accession, form=form,
                primary_document='synthetic.htm', acceptance=['2025-05-09', '09:52:26'], **extra)


def page(items=(), *, kind='discovery', next_start=None):
    return canonical(dict(schema='sec-preactivation-fixture-v1', kind=kind,
                          items=list(items), next_start=next_start))


class PlannerTests(unittest.TestCase):
    def test_exact_endpoints_and_identity(self):
        poll = adapter.plan_request('discovery', start=100)
        self.assertEqual(poll.url, 'https://www.sec.gov/cgi-bin/browse-edgar?action=getcurrent&type=10-Q&owner=include&start=100&count=100&output=atom')
        self.assertEqual(adapter.plan_request('submissions', cik='123').url,
                         'https://data.sec.gov/submissions/CIK0000000123.json')
        self.assertIn('/123/000009999926000001/', adapter.plan_request(
            'primary', cik=CIK, accession=ACC, filename='synthetic.htm').url)
        self.assertTrue(adapter.plan_request('daily_index', day='2026-01-01').url.endswith(
            '/2026/QTR1/master.20260101.idx'))
        self.assertTrue(adapter.plan_request('quarter_index', day='2026-01-01').url.endswith(
            '/2026/QTR1/master.idx'))

    def test_urls_cannot_gain_authority_from_fixture_input(self):
        valid = adapter.plan_request('primary', cik=CIK, accession=ACC, filename='synthetic.htm')
        for bad in ('http://www.sec.gov/x', valid.url + '?x=1', valid.url + '#x',
                    valid.url.replace('www.sec.gov', 'www.sec.gov.evil.test'),
                    valid.url.replace('https://', 'https://user@'),
                    valid.url.replace('www.sec.gov', 'www.sec.gov:443')):
            with self.subTest(url=bad), self.assertRaises(AuditFailure):
                adapter.validate_plan(replace(valid, url=bad))
        for filename in ('../x.htm', 'https://evil.test/x', '%2e%2e.htm', '.', '', 'x.htm?x=1'):
            with self.subTest(filename=filename), self.assertRaises(AuditFailure):
                adapter.plan_request('primary', cik=CIK, accession=ACC, filename=filename)
        for start in (-100, 1, 500, True):
            with self.assertRaises(AuditFailure):
                adapter.plan_request('discovery', start=start)
        with self.assertRaises(AuditFailure):
            adapter.plan_request('history', cik=CIK, filename='CIK0000009999-submissions-001.json')


class DriverTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.root = Path(self.temp.name) / 'preserve'
        self.clock = Clock()
        self.limits = Limits(max_requests=40, max_total_bytes=200000,
                             max_response_bytes=4096, max_jobs=100,
                             max_events=100, max_records=2000)
        for name in ('socket.socket', 'socket.create_connection',
                     'urllib.request.OpenerDirector.open', 'urllib.request.urlopen',
                     'http.client.HTTPConnection.connect'):
            guard = patch(name, side_effect=AssertionError('NETWORK_FORBIDDEN'))
            guard.start()
            self.addCleanup(guard.stop)
        self.driver = None
    def tearDown(self):
        if self.driver:
            self.driver.close()
        self.temp.cleanup()
    def open(self, fixtures, **options):
        self.fixtures, self.options = fixtures, options
        self.driver = adapter.OfflineSECDriver(self.root, fixtures=fixtures, clock=self.clock,
                                               limits=self.limits, **options)
        return self.driver
    def restart(self):
        self.driver.close()
        utc = self.clock.now
        self.clock = Clock('B')
        self.clock.now = utc
        self.driver = adapter.OfflineSECDriver(self.root, fixtures=self.fixtures,
            clock=self.clock, limits=self.limits, **self.options)
    def step(self):
        self.clock.advance(2)
        return self.driver.step()
    def records(self, name):
        return self.driver.capture.store.records('preactivation.' + name)

    def test_originals_amendments_and_versions_use_existing_preserver(self):
        poll = adapter.plan_request('discovery')
        primary = adapter.plan_request('primary', cik=CIK, accession=ACC, filename='synthetic.htm')
        fixtures = {poll.url: (adapter.FixtureReply(page([item(), item('10-Q/A', '0000099999-26-000002')])),
                               adapter.FixtureReply(page([item()]))),
                    primary.url: (adapter.FixtureReply(b'original bytes'), adapter.FixtureReply(b'revised bytes'))}
        for kind in ('submission', 'accession_index'):
            plan = adapter.plan_request(kind, cik=CIK, accession=ACC)
            fixtures[plan.url] = (adapter.FixtureReply(b'opaque'), adapter.FixtureReply(b'opaque'))
        driver = self.open(fixtures)
        driver.poll(0)
        discovery = self.step()
        self.assertIsInstance(driver.capture, OfflinePreserver)
        self.assertEqual(driver.summary()['known_originals'], 1)
        self.assertEqual(driver.summary()['excluded_forms'], 1)
        for _ in range(3):
            self.step()
        original = driver.capture.store.records('preservation.observation')[1]
        self.assertEqual(driver.capture.store.raw(original), b'original bytes')
        self.clock.advance(60)
        driver.poll(1)
        self.step()
        for _ in range(3):
            self.step()
        observations = driver.capture.store.records('preservation.observation')
        self.assertIn(b'revised bytes', [driver.capture.store.raw(r) for r in observations])
        self.assertEqual(driver.capture.store.raw(original), b'original bytes')
        self.assertIsNone(discovery['metadata']['historical_receipt_utc'])
        self.assertTrue(all(r['metadata']['resolved_acceptance_utc'] is None
                            for r in self.records('assertions')))
        self.assertEqual(driver.summary()['fully_preserved_originals'], 1)
        self.assertEqual(driver.capture.store.verify()['status'], 'VERIFIED')

    def test_pagination_exhaustion_missing_and_out_of_order_polls_are_gaps(self):
        first = adapter.plan_request('discovery')
        second = adapter.plan_request('discovery', start=100)
        self.open({first.url: (adapter.FixtureReply(page(next_start=100)),),
                   second.url: (adapter.FixtureReply(page(next_start=200)),)}, max_pages=2)
        self.clock.advance(120)
        self.driver.poll(2)
        self.step(); self.step()
        reasons = {r['source_key'] for r in self.records('gap')}
        self.assertIn('MISSED_POLL', reasons)
        self.assertIn('PAGE_LIMIT', reasons)
        with self.assertRaises(AuditFailure):
            self.driver.poll(1)
        self.assertIn('OUT_OF_ORDER_POLL', {r['source_key'] for r in self.records('gap')})

    def test_rate_and_retry_after_survive_restart(self):
        plan = adapter.plan_request('daily_index', day='2026-01-01')
        self.open({plan.url: (adapter.FixtureReply(b'busy', status=429, headers=(('Retry-After', '10'),)),
                             adapter.FixtureReply(page(kind='index')))})
        self.driver.enqueue(plan, 'reconcile')
        first = self.step()
        self.assertEqual(first['metadata']['failure'], 'HTTP_429')
        self.assertIsNone(self.driver.step())
        self.restart()
        self.assertIsNone(self.driver.step())
        self.clock.advance(11)
        self.assertIsNotNone(self.driver.step())
        self.assertEqual(self.driver.summary()['control']['requests'], 2)

    def test_process_death_charges_reservation_and_cannot_reset_rate_or_budget(self):
        plan = adapter.plan_request('daily_index', day='2026-01-01')
        self.limits = replace(self.limits, max_requests=1)
        self.open({plan.url: (adapter.FixtureReply(fault='crash'),)})
        self.driver.enqueue(plan, 'index')
        with self.assertRaises(adapter.FixtureCrash):
            self.step()
        self.restart()
        self.clock.advance(2)
        with self.assertRaisesRegex(AuditFailure, 'REQUEST_BUDGET_EXHAUSTED'):
            self.driver.step()
        summary = self.driver.summary()
        self.assertEqual(summary['control']['requests'], 1)
        self.assertEqual(summary['control']['bytes_charged'], 4097)
        self.assertEqual(len(self.records('dispatch')), 1)

    def test_incomplete_redirect_oversize_and_forbidden_responses_do_not_become_receipt(self):
        for reply in (adapter.FixtureReply(b'partial', complete=False),
                      adapter.FixtureReply(b'moved', status=302, headers=(('Location', 'https://evil.test'),)),
                      adapter.FixtureReply(b'x' * 4097), adapter.FixtureReply(b'no', status=403)):
            with self.subTest(status=reply.status):
                root = self.root / str(reply.status) / str(reply.complete)
                plan = adapter.plan_request('primary', cik=CIK, accession=ACC, filename='synthetic.htm')
                driver = adapter.OfflineSECDriver(root, fixtures={plan.url: (reply,)}, clock=self.clock)
                try:
                    driver.enqueue(plan, 'body')
                    self.clock.advance(2)
                    record = driver.step()
                    self.assertIsNone(record['metadata']['document_receipt'])
                    self.assertTrue(driver.summary()['driver_gaps'])
                    if reply.status == 403:
                        with self.assertRaises(AuditFailure):
                            driver.step()
                finally:
                    driver.close()

    def test_untrusted_payload_cursor_and_filename_are_preserved_as_parse_failures(self):
        poll = adapter.plan_request('discovery')
        self.open({poll.url: (adapter.FixtureReply(page(next_start=400)),
                             adapter.FixtureReply(page([dict(item(), primary_document='https://evil.test/x')])) )})
        self.driver.poll(0)
        self.step()
        self.clock.advance(60)
        self.driver.poll(1)
        self.step()
        self.assertEqual(len(self.records('parse_failure')), 2)
        self.assertEqual(self.driver.summary()['known_originals'], 0)
        self.assertEqual(len(self.driver.capture.store.records('preservation.observation')), 2)

    def test_clock_rollback_and_new_session_cannot_bypass_rate(self):
        plan = adapter.plan_request('primary', cik=CIK, accession=ACC, filename='synthetic.htm')
        self.open({plan.url: (adapter.FixtureReply(b'a'), adapter.FixtureReply(b'b'))})
        self.driver.enqueue(plan, 'v1'); self.step()
        self.driver.enqueue(plan, 'v2')
        self.clock.now -= timedelta(seconds=100)
        self.clock.ns += 10**12
        self.assertIsNone(self.driver.step())
        self.assertEqual(self.driver.summary()['control']['requests'], 1)

    def test_program_or_budget_change_on_reopen_is_rejected(self):
        self.open({})
        self.driver.close()
        with self.assertRaisesRegex(AuditFailure, 'DRIVER_BINDING_CHANGED'):
            adapter.OfflineSECDriver(self.root, fixtures={}, clock=self.clock, limits=self.limits, max_pages=1)

    def test_recovery_after_event_commit_does_not_invent_overlap(self):
        poll = adapter.plan_request('discovery')
        self.open({poll.url: (adapter.FixtureReply(page([item()], next_start=100)),)})
        self.driver.poll(0)
        original = self.driver.enqueue
        def fail_before_page(plan, key):
            if key.startswith('page:'):
                raise adapter.FixtureCrash()
            return original(plan, key)
        with patch.object(self.driver, 'enqueue', side_effect=fail_before_page):
            with self.assertRaises(adapter.FixtureCrash):
                self.step()
        self.restart()
        self.assertTrue(any(r['metadata']['plan']['start'] == 100 for r in self.records('request')))

    def test_server_retry_after_pauses_all_dispatch_and_survives_reopen(self):
        plan = adapter.plan_request('daily_index', day='2026-01-01')
        self.open({plan.url: (adapter.FixtureReply(b'busy', status=503, headers=(('Retry-After', '20'),)),
                             adapter.FixtureReply(page(kind='index')))})
        self.driver.enqueue(plan, 'index')
        self.step()
        self.restart()
        self.clock.advance(3)
        self.assertIsNone(self.driver.step())
        self.assertEqual(self.driver.summary()['control']['requests'], 1)
        self.clock.advance(20)
        self.assertIsNotNone(self.driver.step())

    def test_missing_and_conflicting_identity_never_discards_raw(self):
        plan = adapter.plan_request('discovery')
        self.open({plan.url: (adapter.FixtureReply(page([item(), item('10-Q/A')])),)})
        self.driver.poll(0)
        record = self.step()
        self.assertIsNotNone(record['metadata']['document_receipt'])
        self.assertEqual(self.driver.capture.events()[0]['conflict'], 1)
        self.assertEqual(self.driver.summary()['fully_preserved_originals'], 0)

    def test_cross_issuer_submissions_are_quarantined(self):
        plan = adapter.plan_request('submissions', cik='999')
        self.open({plan.url: (adapter.FixtureReply(page([item()], kind='submissions')),)})
        self.driver.enqueue(plan, 'issuer-root')
        self.step()
        self.assertEqual(self.driver.summary()['known_originals'], 0)
        self.assertEqual(len(self.records('parse_failure')), 1)

    def test_primary_cannot_alias_submission_or_index_role(self):
        for filename in (ACC + '.txt', ACC + '-index.html'):
            with self.assertRaises(AuditFailure):
                adapter.plan_request('primary', cik=CIK, accession=ACC, filename=filename)

    def test_duplicate_fixture_headers_are_rejected(self):
        plan = adapter.plan_request('discovery')
        with self.assertRaises(AuditFailure):
            self.open({plan.url: (adapter.FixtureReply(headers=(('Retry-After', '1'), ('retry-after', '20'))),)})

    def test_dispatch_reservation_without_request_cannot_be_reused_after_crash(self):
        plan = adapter.plan_request('daily_index', day='2026-01-01')
        self.limits = replace(self.limits, max_requests=1)
        self.open({plan.url: (adapter.FixtureReply(page(kind='index')),)})
        self.driver.enqueue(plan, 'index')
        with patch.object(self.driver.capture, 'run_one', side_effect=adapter.FixtureCrash):
            with self.assertRaises(adapter.FixtureCrash):
                self.step()
        self.restart()
        self.clock.advance(2)
        with self.assertRaisesRegex(AuditFailure, 'REQUEST_BUDGET_EXHAUSTED'):
            self.driver.step()
        self.assertEqual(self.driver.summary()['control']['requests'], 0)

    def test_planned_job_recovers_without_new_job_or_version_identity(self):
        plan = adapter.plan_request('daily_index', day='2026-01-01')
        self.open({plan.url: (adapter.FixtureReply(page(kind='index')),)})
        with patch.object(self.driver.capture, 'enqueue', side_effect=adapter.FixtureCrash):
            with self.assertRaises(adapter.FixtureCrash):
                self.driver.enqueue(plan, 'index')
        self.restart()
        self.assertEqual(len(self.driver.capture.jobs()), 1)
        self.assertEqual(len(self.records('request')), 1)
        self.step()
        self.assertEqual(self.driver.summary()['control']['requests'], 1)

    def test_unsupported_retry_after_is_a_durable_operator_stop(self):
        plan = adapter.plan_request('daily_index', day='2026-01-01')
        self.open({plan.url: (adapter.FixtureReply(status=503, headers=(('Retry-After', 'tomorrow'),)),)})
        self.driver.enqueue(plan, 'index')
        self.step()
        with self.assertRaisesRegex(AuditFailure, 'RETRY_AFTER_UNSUPPORTED'):
            self.driver.step()
        self.driver.close()
        with self.assertRaisesRegex(AuditFailure, 'RETRY_AFTER_UNSUPPORTED'):
            adapter.OfflineSECDriver(self.root, fixtures=self.fixtures, clock=self.clock, limits=self.limits)

    def test_byte_reservation_exhaustion_does_not_invoke_fixture_transport(self):
        plan = adapter.plan_request('daily_index', day='2026-01-01')
        self.limits = replace(self.limits, max_total_bytes=4096)
        self.open({plan.url: (adapter.FixtureReply(page(kind='index')),)})
        self.driver.enqueue(plan, 'index')
        with patch.object(self.driver.capture, 'transport', side_effect=AssertionError('NO_DISPATCH')):
            with self.assertRaisesRegex(AuditFailure, 'BYTE_BUDGET_EXHAUSTED'):
                self.step()
        self.assertEqual(self.driver.summary()['control']['requests'], 0)

    def test_missing_primary_and_index_only_discovery_remain_explicit(self):
        plan = adapter.plan_request('daily_index', day='2026-01-01')
        self.open({plan.url: (adapter.FixtureReply(page([dict(item(), primary_document=None)], kind='index')),)})
        self.driver.enqueue(plan, 'index')
        self.step()
        self.assertEqual(self.driver.summary()['known_originals'], 1)
        self.assertEqual(self.driver.summary()['late_discovered'], 1)
        self.assertIn('PRIMARY_NAME_UNAVAILABLE', {r['source_key'] for r in self.records('gap')})

    def test_rate_waits_from_completion_not_only_early_dispatch_journal(self):
        plan = adapter.plan_request('primary', cik=CIK, accession=ACC, filename='synthetic.htm')
        self.open({plan.url: (adapter.FixtureReply(b'first'), adapter.FixtureReply(b'second'))})
        self.driver.enqueue(plan, 'v1')
        original = self.driver.capture.transport
        def slow_fixture(uri, limit):
            self.clock.advance(0.75)
            return original(uri, limit)
        with patch.object(self.driver.capture, 'transport', side_effect=slow_fixture):
            self.step()
        self.driver.enqueue(plan, 'v2')
        self.clock.advance(0.35)
        self.assertIsNone(self.driver.step())
        self.assertEqual(self.driver.summary()['control']['requests'], 1)

    def test_caught_process_death_requires_reopen_and_retains_attempt(self):
        plan = adapter.plan_request('primary', cik=CIK, accession=ACC, filename='synthetic.htm')
        self.open({plan.url: (adapter.FixtureReply(fault='crash'), adapter.FixtureReply(b'recovered'))})
        self.driver.enqueue(plan, 'body')
        with self.assertRaises(adapter.FixtureCrash):
            self.step()
        self.clock.advance(10)
        with self.assertRaisesRegex(AuditFailure, 'DRIVER_STEP_INTERRUPTED'):
            self.driver.step()
        self.restart()
        record = self.step()
        self.assertEqual(self.driver.capture.store.raw(record), b'recovered')
        self.assertEqual(self.driver.summary()['control']['requests'], 2)

    def test_only_inert_fixture_data_is_accepted_and_no_real_uri_reaches_preserver(self):
        with self.assertRaises(AuditFailure):
            self.open(lambda url, limit: b'network')
        self.open({})
        plan = adapter.plan_request('primary', cik=CIK, accession=ACC, filename='synthetic.htm')
        with self.assertRaises(AuditFailure):
            self.driver.enqueue(replace(plan, url='https://evil.test'), 'untrusted')
        with self.assertRaises(AuditFailure):
            self.driver.capture.enqueue(plan.url, 'primary', 'real-url')
        self.driver.enqueue(plan, 'absent-fixture')
        result = self.step()
        self.assertEqual(result['metadata']['failure'], 'UNAUTHORIZED_FIXTURE_REQUEST')


if __name__ == '__main__':
    unittest.main()

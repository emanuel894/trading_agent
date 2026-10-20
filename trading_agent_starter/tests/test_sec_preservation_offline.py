"""Synthetic only: no source acquisition, registration, or timing qualification."""
from dataclasses import replace
from pathlib import Path
import shutil
import sqlite3
import tempfile
import unittest
from unittest.mock import patch

from agent.audit_store import AuditFailure, digest
from agent.sec_preservation_offline import (ClockSample, Limits, OfflinePreserver, Response)

CIK = '0000000123'
ACC = '0000000123-26-000001'
DISC = 'fixture://sec/discovery'
PRIMARY = 'fixture://sec/primary'
SUBMISSION = 'fixture://sec/submission'


class FakeClock:
    def __init__(self, session='session-A', uncertainty=0.1):
        self.tick = 0
        self.utc = '2026-10-20T12:00:00Z'
        self.session = session
        self.uncertainty = uncertainty
    def __call__(self):
        self.tick += 1
        return ClockSample(self.utc, self.tick, self.session,
                           self.uncertainty, 'fixture-offset-measurement')


class FakeTransport:
    def __init__(self):
        self.results = []
        self.calls = []
    def __call__(self, uri, limit):
        self.calls.append((uri, limit))
        result = self.results.pop(0)
        if isinstance(result, Exception):
            raise result
        return result


def claim(form='10-Q', cik=CIK, accession=ACC):
    return dict(cik=cik, accession=accession, form=form, representations=[
        dict(role='primary', uri=PRIMARY), dict(role='submission', uri=SUBMISSION)])


class OfflineTests(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.root = Path(self.tmp.name) / 'capture'
        self.transport = FakeTransport()
        self.clock = FakeClock()
        self.limits = Limits(max_requests=40, max_total_bytes=10000,
                             max_response_bytes=64, max_jobs=50, max_events=20,
                             max_records=500, max_attempts=3)
        self.capture = self.open()
    def open(self):
        return OfflinePreserver(self.root, transport=self.transport,
                                clock=self.clock, limits=self.limits)
    def restart(self):
        self.capture.close()
        self.clock = FakeClock('session-B')
        self.capture = self.open()
    def tearDown(self):
        self.capture.close()
        self.tmp.cleanup()
    def response(self, raw=b'body', status=200, headers=None, complete=True):
        return Response(status, headers or {}, [raw], complete)
    def discovery(self, claims=None, role='discovery', request='poll-1'):
        self.capture.enqueue(DISC, role, request)
        self.transport.results.append(self.response(b'raw-discovery'))
        obs = self.capture.run_one()
        keys = self.capture.parse_discovery(obs['id'], claims or [claim()])
        return obs, keys
    def records(self, kind):
        return self.capture.store.records('preservation.' + kind)

    def test_duplicates_are_observations_not_new_events_or_receipt_rewrites(self):
        obs, keys = self.discovery()
        first_event = self.capture.events()[0]
        self.transport.results.extend([self.response(), self.response(b'submission')])
        first = self.capture.run_one()
        self.capture.run_one()
        self.capture.enqueue(PRIMARY, 'primary', 'revision-2', keys[0])
        self.transport.results.append(self.response())
        second = self.capture.run_one()
        self.assertEqual(second['blob_sha'], first['blob_sha'])
        self.assertEqual(second['previous_version'], first['id'])
        self.assertNotEqual(second['id'], first['id'])
        self.assertEqual(self.capture.parse_discovery(obs['id'], [claim()]), keys)
        self.assertEqual(self.capture.events()[0]['first_discovery'], first_event['first_discovery'])
        self.assertEqual(self.capture.summary()['known_originals'], 1)
        self.assertEqual(len(self.records('observation')), 4)

    def test_changed_representations_append_and_never_rewrite_frozen_version(self):
        _, keys = self.discovery()
        self.transport.results.extend([self.response(b'direct'), self.response(b'embedded')])
        primary = self.capture.run_one()
        submission = self.capture.run_one()
        frozen = self.capture.store.get(primary['id'])
        self.capture.enqueue(PRIMARY, 'primary', 'revision-2', keys[0])
        self.transport.results.append(self.response(b'corrected'))
        corrected = self.capture.run_one()
        self.assertNotEqual(primary['blob_sha'], submission['blob_sha'])
        self.assertEqual(corrected['previous_version'], primary['id'])
        self.assertEqual(self.capture.store.get(primary['id']), frozen)
        self.assertEqual(self.capture.store.raw(primary), b'direct')
        self.assertIsNone(corrected['metadata']['source_revision_at'])

    def test_amendment_and_transition_are_retained_but_never_targets(self):
        self.discovery([claim('10-Q/A'), claim('10-QT', accession='0000000123-26-000002')])
        self.assertEqual(self.capture.summary()['known_originals'], 0)
        self.assertEqual(self.capture.summary()['excluded_forms'], 2)
        self.assertIsNone(self.capture.run_one())

    def test_conflicting_identity_preserves_raw_and_quarantines_original(self):
        obs, _ = self.discovery()
        self.transport.results.extend([self.response(), self.response()])
        self.capture.run_one()
        self.capture.run_one()
        self.capture.enqueue(DISC, 'discovery', 'poll-2')
        self.transport.results.append(self.response(b'conflicting-source'))
        second = self.capture.run_one()
        self.capture.parse_discovery(second['id'], [claim(cik='999')])
        self.assertTrue(self.capture.events()[0]['conflict'])
        self.assertEqual(self.capture.summary()['known_originals'], 1)
        self.assertEqual(self.capture.store.raw(obs), b'raw-discovery')
        self.assertEqual(self.capture.store.raw(second), b'conflicting-source')
        self.assertTrue(self.records('identity_conflict'))

    def test_acceptance_conflict_date_only_and_dst_never_become_receipt(self):
        obs, _ = self.discovery()
        native = [dict(value='2026-11-01T01:30:00', precision='second',
                       zone='America/New_York', qualified=False, span='fixture:1'),
                  dict(value='2026-11-01', precision='date', zone=None,
                       qualified=False, span='fixture:2')]
        result = self.capture.assess(obs['id'], acceptance=native)
        self.assertIsNone(result['metadata']['resolved_acceptance_utc'])
        self.assertEqual(result['metadata']['acceptance_assertions'], native)
        self.assertIsNone(result['metadata']['historical_receipt_utc'])
        self.assertNotEqual(obs['metadata']['body_completed'], result['metadata']['parse_completed'])
        self.assertEqual(result['metadata']['admission'], 'NOT_ASSESSED')
        conflicting = [dict(value='2026-10-20T09:00:00Z', precision='second',
                            qualified=True, zone='UTC', span='a'),
                       dict(value='2026-10-20T10:00:00Z', precision='second',
                            qualified=True, zone='UTC', span='b')]
        self.assertIsNone(self.capture.assess(obs['id'], acceptance=conflicting)
                          ['metadata']['resolved_acceptance_utc'])

    def test_timeout_partial_oversize_and_size_conflict_have_no_full_receipt(self):
        def partial():
            yield b'partial'
            raise TimeoutError()
        cases = [(TimeoutError(), 'TRANSPORT_ERROR'),
                 (Response(200, {}, partial()), 'TRANSPORT_ERROR'),
                 (self.response(b'x' * 65), 'RESPONSE_TOO_LARGE'),
                 (self.response(b'body', headers={'content-length': '99'}), 'SIZE_CONFLICT'),
                 (self.response(b'partial', complete=False), 'PARTIAL_BODY')]
        for i, (response, expected) in enumerate(cases):
            with self.subTest(expected=expected):
                # Different roots isolate each retry schedule from the next case.
                self.capture.close()
                self.root = Path(self.tmp.name) / str(i)
                self.capture = self.open()
                self.capture.enqueue(PRIMARY, 'primary', str(i))
                self.transport.results.append(response)
                record = self.capture.run_one()
                self.assertEqual(record['metadata']['failure'], expected)
                self.assertIsNone(record['metadata']['document_receipt'])
                self.assertIsNone(record['metadata']['body_completed'])
                self.assertIn(self.capture.jobs()[0]['state'], {'PENDING', 'FAILED'})
                if i == 1:
                    self.assertEqual(self.capture.store.raw(record), b'partial')

    def test_429_has_durable_backoff_and_403_stops_without_more_calls(self):
        self.capture.enqueue(DISC, 'discovery', 'poll')
        self.transport.results.append(self.response(status=429, headers={'retry-after': '10'}))
        self.capture.run_one()
        self.restart()
        self.assertIsNone(self.capture.run_one())
        self.assertEqual(len(self.transport.calls), 1)
        self.assertEqual(self.capture.jobs()[0]['attempts'], 1)
        # Separate forbidden response has a durable global stop.
        self.capture.enqueue(PRIMARY, 'primary', 'forbidden')
        self.transport.results.append(self.response(status=403))
        self.capture.run_one()
        self.restart()
        with self.assertRaisesRegex(AuditFailure, 'HTTP_403'):
            self.capture.run_one()
        self.assertEqual(len(self.transport.calls), 2)

    def test_attempt_budget_survives_crashes_without_reset_or_false_completion(self):
        self.capture.enqueue(PRIMARY, 'primary', 'one')
        for attempt in range(3):
            with patch.object(self.capture, '_receive', side_effect=SystemExit('crash')):
                with self.assertRaises(SystemExit):
                    self.capture.run_one()
            self.restart()
            self.assertEqual(self.capture.jobs()[0]['attempts'], attempt + 1)
        self.assertEqual(self.capture.jobs()[0]['state'], 'FAILED')
        self.assertIsNone(self.capture.run_one())
        self.assertEqual(len(self.records('recovery')), 3)
        self.assertEqual(self.transport.calls, [])

    def test_crash_at_finalization_and_before_commit_leaves_orphan_not_complete(self):
        self.capture.enqueue(PRIMARY, 'primary', 'one')
        self.transport.results.append(self.response())
        original = self.capture.store.append_in_transaction
        def crash(kind, *args, **kwargs):
            result = original(kind, *args, **kwargs)
            if kind == 'preservation.observation':
                raise SystemExit('crash before commit')
            return result
        with patch.object(self.capture.store, 'append_in_transaction', side_effect=crash):
            with self.assertRaises(SystemExit):
                self.capture.run_one()
        self.restart()
        self.assertEqual(self.capture.jobs()[0]['state'], 'PENDING')
        self.assertEqual(self.records('observation'), [])
        self.assertTrue(self.records('orphan'))
        self.transport.results.append(self.response())
        self.assertIsNotNone(self.capture.run_one())
        self.restart()
        self.assertEqual(self.capture.jobs()[0]['state'], 'COMPLETE')
        self.assertIsNone(self.capture.run_one())

    def test_spool_orphans_quarantined_and_disk_full_fails_closed(self):
        (self.capture.store.spool / 'interrupted').write_bytes(b'partial')
        self.restart()
        self.assertTrue(self.records('orphan'))
        self.assertFalse(list(self.capture.store.spool.iterdir()))
        self.capture.enqueue(PRIMARY, 'primary', 'one')
        self.transport.results.append(self.response())
        with patch.object(self.capture.store, '_finalize_blob', side_effect=OSError('disk full')):
            with self.assertRaisesRegex(AuditFailure, 'STORAGE_FAILURE'):
                self.capture.run_one()
        self.assertNotEqual(self.capture.jobs()[0]['state'], 'COMPLETE')
        self.assertTrue(self.records('storage_failure'))
        self.restart()
        with self.assertRaisesRegex(AuditFailure, 'STORAGE_FAILURE'):
            self.capture.run_one()
        self.assertEqual(len(self.transport.calls), 1)

    def test_gaps_late_index_recovery_failures_stay_in_denominator(self):
        self.capture.note_gap('MISSED_POLL', {'scheduled': 'fixture'})
        self.capture.note_gap('PAGINATION_EXHAUSTED', {'overlap': False})
        self.discovery(role='index')
        self.transport.results.extend([self.response(status=404), self.response()])
        self.capture.run_one()
        self.capture.run_one()
        report = self.capture.summary()
        self.assertEqual(report['known_originals'], 1)
        self.assertEqual(report['late_discovered'], 1)
        self.assertEqual(report['fully_preserved_originals'], 0)
        self.assertEqual(report['failed_jobs'], 1)
        self.assertEqual(report['gaps'], 2)

    def test_resource_caps_and_config_binding_survive_reopen(self):
        self.capture.close()
        self.limits = replace(self.limits, max_requests=1)
        self.root = Path(self.tmp.name) / 'limited'
        self.capture = self.open()
        self.capture.enqueue(PRIMARY, 'primary', 'one')
        self.transport.results.append(self.response())
        self.capture.run_one()
        self.restart()
        self.capture.enqueue(SUBMISSION, 'submission', 'two')
        with self.assertRaisesRegex(AuditFailure, 'REQUEST_BUDGET_EXHAUSTED'):
            self.capture.run_one()
        self.assertEqual(len(self.transport.calls), 1)
        self.capture.close()
        self.limits = replace(self.limits, max_requests=10)
        with self.assertRaisesRegex(AuditFailure, 'CONFIG_BINDING_CHANGED'):
            self.open()

    def test_single_writer_corrupt_blob_and_verified_backup_restore(self):
        with self.assertRaisesRegex(AuditFailure, 'WRITER_ALREADY_OPEN'):
            self.open()
        self.capture.enqueue(PRIMARY, 'primary', 'one')
        self.transport.results.append(self.response())
        record = self.capture.run_one()
        backup = Path(self.tmp.name) / 'backup'
        backup.mkdir()
        destination = sqlite3.connect(backup / 'evidence.sqlite')
        try:
            self.capture.store.db.backup(destination)
        finally:
            destination.close()
        with self.assertRaises(sqlite3.ProgrammingError):
            destination.execute('SELECT 1')
        shutil.copytree(self.capture.store.objects, backup / 'objects')
        self.capture.close()
        self.root = backup
        self.capture = self.open()
        self.assertEqual(self.capture.store.raw(record), b'body')
        self.assertEqual(self.capture.store.verify()['status'], 'VERIFIED')
        self.capture.close()
        (backup / 'objects' / record['blob_sha']).write_bytes(b'corrupt')
        with self.assertRaisesRegex(AuditFailure, 'BLOB_HASH_MISMATCH'):
            self.open()

    def test_clock_uncertainty_and_reboot_flag_timing_without_dropping_bytes(self):
        self.clock.uncertainty = 2.0
        self.capture.enqueue(PRIMARY, 'primary', 'one')
        self.transport.results.append(self.response())
        record = self.capture.run_one()
        self.assertIn('CLOCK_UNCERTAIN', record['metadata']['timing_flags'])
        self.assertEqual(self.capture.store.raw(record), b'body')
        self.assertIsNotNone(record['metadata']['document_receipt'])
        self.restart()
        self.capture.enqueue(PRIMARY, 'primary', 'two')
        self.transport.results.append(self.response(b'revised'))
        revised = self.capture.run_one()
        self.assertEqual(revised['metadata']['request_started']['session'], 'session-B')
        self.assertEqual(record['metadata']['request_started']['session'], 'session-A')

    def test_no_network_env_or_default_transport_and_live_uri_rejected(self):
        with patch('socket.socket', side_effect=AssertionError('network')), \
             patch('urllib.request.urlopen', side_effect=AssertionError('network')), \
             patch('os.getenv', side_effect=AssertionError('env')):
            self.discovery()
            with self.assertRaisesRegex(AuditFailure, 'OFFLINE_URI_REQUIRED'):
                self.capture.enqueue('https://www.sec.gov/example', 'primary', 'real')
            with self.assertRaises(TypeError):
                OfflinePreserver(Path(self.tmp.name) / 'default')
        self.assertEqual(self.capture.summary()['mode'], 'SYNTHETIC_OFFLINE')

    def test_changed_submission_and_index_versions_preserve_old_observations(self):
        first = []
        for role in ('submission', 'index'):
            self.capture.enqueue('fixture://sec/' + role, role, 'first')
            self.transport.results.append(self.response(b'old-' + role.encode()))
            old = self.capture.run_one()
            self.capture.enqueue('fixture://sec/' + role, role, 'second')
            self.transport.results.append(self.response(b'new-' + role.encode()))
            new = self.capture.run_one()
            self.assertEqual(new['previous_version'], old['id'])
            self.assertEqual(self.capture.store.raw(old), b'old-' + role.encode())
            first.append(old)
        self.assertEqual(len(self.records('observation')), 4)

    def test_original_asserted_after_amendment_stays_in_conflict_denominator(self):
        self.discovery([claim('10-Q/A')])
        self.capture.enqueue(DISC, 'discovery', 'poll-2')
        self.transport.results.append(self.response())
        obs = self.capture.run_one()
        self.capture.parse_discovery(obs['id'], [claim()])
        self.assertEqual(self.capture.summary()['known_originals'], 1)
        self.assertEqual(self.capture.summary()['fully_preserved_originals'], 0)

    def test_complete_receipt_is_per_hash_and_not_changed_by_duplicate(self):
        self.capture.enqueue(PRIMARY, 'primary', 'one')
        self.transport.results.append(self.response())
        first = self.capture.run_one()
        self.capture.enqueue(PRIMARY, 'primary', 'two')
        self.transport.results.append(self.response())
        duplicate = self.capture.run_one()
        self.assertEqual(duplicate['metadata']['first_version_receipt'],
                         first['metadata']['document_receipt'])
        self.assertNotEqual(duplicate['metadata']['document_receipt'],
                            duplicate['metadata']['first_version_receipt'])

    def test_byte_job_event_and_record_limits_stop_without_hidden_work(self):
        for limit, overrides, expected in [
            ('bytes', {'max_total_bytes': 64}, 'BYTE_BUDGET_EXHAUSTED'),
            ('jobs', {'max_jobs': 1}, 'JOB_BUDGET_EXHAUSTED'),
            ('events', {'max_events': 1}, 'CLAIM_BUDGET_EXHAUSTED'),
            ('records', {'max_records': 1}, 'RECORD_BUDGET_EXHAUSTED')]:
            with self.subTest(limit=limit):
                self.capture.close()
                self.root = Path(self.tmp.name) / limit
                original = self.limits
                self.limits = replace(original, **overrides)
                self.capture = self.open()
                self.capture.enqueue(DISC, 'discovery', 'one')
                with self.assertRaisesRegex(AuditFailure, expected):
                    if limit in {'bytes', 'records'}:
                        self.capture.run_one()
                    elif limit == 'jobs':
                        self.capture.enqueue(PRIMARY, 'primary', 'two')
                    else:
                        self.transport.results.append(self.response())
                        obs = self.capture.run_one()
                        self.capture.parse_discovery(obs['id'], [claim(), claim(accession='0000000123-26-000002')])
                if limit in {'bytes', 'records'}:
                    self.assertNotEqual(self.capture.jobs()[0]['state'], 'COMPLETE')
                self.limits = original

    def test_clock_step_and_invalid_derived_parse_preserve_raw_failure(self):
        self.capture.enqueue(DISC, 'discovery', 'one')
        self.transport.results.append(self.response())
        samples = iter([ClockSample('2026-10-20T12:00:00Z', 10, 'a', .1, 'measure'),
                        ClockSample('2026-10-20T11:59:59Z', 11, 'a', .1, 'measure'),
                        ClockSample('2026-10-20T11:59:59Z', 12, 'a', .1, 'measure'),
                        ClockSample('2026-10-20T11:59:59Z', 13, 'a', .1, 'measure')])
        self.capture.clock = lambda: next(samples)
        obs = self.capture.run_one()
        self.capture.clock = self.clock
        self.assertIn('CLOCK_DISCONTINUITY', obs['metadata']['timing_flags'])
        with self.assertRaisesRegex(AuditFailure, 'INVALID_IDENTITY_ASSERTION'):
            self.capture.parse_discovery(obs['id'], [claim(cik='invalid')])
        self.assertTrue(self.records('parse_failure'))
        self.assertEqual(self.capture.store.raw(obs), b'body')
        self.assertEqual(self.capture.summary()['unparsed_discovery_responses'], 1)

    def test_crash_before_finalization_and_unwritable_failure_log_stops(self):
        self.capture.enqueue(PRIMARY, 'primary', 'one')
        self.transport.results.append(self.response())
        with patch.object(self.capture.store, '_finalize_blob', side_effect=SystemExit('crash')):
            with self.assertRaises(SystemExit):
                self.capture.run_one()
        self.restart()
        self.assertEqual(self.capture.jobs()[0]['state'], 'PENDING')
        self.transport.results.append(self.response())
        with patch.object(self.capture.store, 'append_in_transaction', side_effect=sqlite3.OperationalError('disk')):
            with self.assertRaisesRegex(AuditFailure, 'STORAGE_FAILURE'):
                self.capture.run_one()
        with self.assertRaisesRegex(AuditFailure, 'STORAGE_FAILURE'):
            self.capture.run_one()
        self.assertNotEqual(self.capture.jobs()[0]['state'], 'COMPLETE')

    def test_transient_attempts_exhaust_and_unsupported_retry_after_fails_closed(self):
        self.capture.enqueue(PRIMARY, 'primary', 'retry')
        for second in (0, 10, 20):
            self.clock.utc = f'2026-10-20T12:00:{second:02d}Z'
            self.transport.results.append(TimeoutError())
            self.capture.run_one()
        self.assertEqual(self.capture.jobs()[0]['state'], 'FAILED')
        self.assertEqual(len(self.records('observation')), 3)
        self.capture.enqueue(SUBMISSION, 'submission', 'retry-after')
        self.transport.results.append(self.response(status=429, headers={'retry-after': 'tomorrow'}))
        obs = self.capture.run_one()
        self.assertEqual(obs['metadata']['retry_policy_failure'], 'RETRY_AFTER_UNSUPPORTED')
        self.assertEqual(self.capture.jobs()[-1]['state'], 'FAILED')

    def test_full_preservation_requires_all_representations_and_no_conflict(self):
        assertion = claim()
        assertion['representations'].append({'role': 'accession_index', 'uri': 'fixture://sec/accession-index'})
        self.discovery([assertion])
        self.transport.results.extend([self.response(b'primary'), self.response(b'submission'), self.response(b'index')])
        self.capture.run_one()
        self.capture.run_one()
        self.assertEqual(self.capture.summary()['fully_preserved_originals'], 0)
        self.capture.run_one()
        self.assertEqual(self.capture.summary()['fully_preserved_originals'], 1)

    def test_changed_parse_binding_rejected_without_rewriting_first_inventory(self):
        obs, keys = self.discovery()
        with self.assertRaisesRegex(AuditFailure, 'PARSE_BINDING_CHANGED'):
            self.capture.parse_discovery(obs['id'], [claim('10-Q/A')])
        self.assertEqual(self.capture.parse_discovery(obs['id'], [claim()]), keys)
        self.assertEqual(self.capture.events()[0]['form'], '10-Q')

    def test_queue_corruption_is_not_repaired_into_false_success(self):
        self.capture.enqueue(PRIMARY, 'primary', 'one')
        with self.capture.store.transaction():
            self.capture.db.execute("UPDATE preservation_jobs SET state='COMPLETE'")
        self.capture.close()
        with self.assertRaisesRegex(AuditFailure, 'QUEUE_CORRUPT'):
            self.open()

    def test_metadata_bound_and_storage_failure_before_enqueue_are_fail_closed(self):
        with self.assertRaisesRegex(AuditFailure, 'METADATA_TOO_LARGE'):
            self.capture.note_gap('large', {'unexpected': 'x' * 65537})
        self.assertEqual(self.records('gap'), [])
        with patch.object(self.capture.store, 'append_in_transaction', side_effect=sqlite3.OperationalError('disk')):
            with self.assertRaisesRegex(AuditFailure, 'STORAGE_FAILURE'):
                self.capture.enqueue(PRIMARY, 'primary', 'one')
        with self.assertRaisesRegex(AuditFailure, 'STORAGE_FAILURE'):
            self.capture.run_one()
        self.assertEqual(self.transport.calls, [])

    def test_retained_configuration_and_code_provenance_are_in_each_observation(self):
        self.capture.enqueue(PRIMARY, 'primary', 'one')
        self.transport.results.append(self.response())
        obs = self.capture.run_one()
        self.assertEqual(len(obs['metadata']['code_hash']), 64)
        self.assertEqual(obs['metadata']['config_hash'], self.capture.summary()['control']['binding'])
        self.assertEqual(obs['metadata']['rights_reference'], 'synthetic-fixtures-only')

    def test_review_projection_tampering_is_detected_on_reopen(self):
        for name, sql in [
            ('bytes', 'UPDATE preservation_control SET bytes_charged=-100'),
            ('lost-job', "UPDATE preservation_jobs SET state='FAILED' WHERE role='primary'"),
            ('denominator', 'UPDATE preservation_events SET target=0'),
            ('deleted-job', "DELETE FROM preservation_jobs WHERE role='primary'"),
            ('parse-cache', 'DELETE FROM preservation_parsed')]:
            with self.subTest(name=name):
                self.capture.close()
                self.root = Path(self.tmp.name) / name
                self.capture = self.open()
                self.discovery()
                with self.capture.store.transaction():
                    self.capture.db.execute(sql)
                self.capture.close()
                candidate = None
                try:
                    with self.assertRaisesRegex(AuditFailure, 'QUEUE_CORRUPT'):
                        candidate = self.open()
                finally:
                    if candidate is not None:
                        candidate.close()

    def test_review_403_with_oversized_or_partial_body_always_stops_requests(self):
        for name, response in [('oversized', self.response(b'x' * 65, status=403)),
                               ('partial', self.response(b'partial', status=403, complete=False))]:
            with self.subTest(name=name):
                self.transport.results.clear()
                self.capture.close()
                self.root = Path(self.tmp.name) / name
                self.capture = self.open()
                self.capture.enqueue(PRIMARY, 'primary', 'one')
                self.capture.enqueue(SUBMISSION, 'submission', 'two')
                self.transport.results.append(response)
                record = self.capture.run_one()
                self.assertEqual(record['metadata']['http_status'], 403)
                self.transport.results.append(self.response())
                with self.assertRaisesRegex(AuditFailure, 'HTTP_403'):
                    self.capture.run_one()
                self.restart()
                with self.assertRaisesRegex(AuditFailure, 'HTTP_403'):
                    self.capture.run_one()

    def test_review_detected_blob_corruption_halts_subsequent_requests(self):
        self.capture.enqueue(PRIMARY, 'primary', 'one')
        self.transport.results.append(self.response(b'same'))
        first = self.capture.run_one()
        (self.capture.store.objects / first['blob_sha']).write_bytes(b'corrupt')
        self.capture.enqueue(PRIMARY, 'primary', 'two')
        self.capture.enqueue(SUBMISSION, 'submission', 'three')
        self.transport.results.append(self.response(b'same'))
        with self.assertRaisesRegex(AuditFailure, 'BLOB_HASH_MISMATCH'):
            self.capture.run_one()
        before = len(self.transport.calls)
        self.transport.results.append(self.response())
        with self.assertRaises(AuditFailure):
            self.capture.run_one()
        self.assertEqual(len(self.transport.calls), before)
        self.assertEqual(self.capture.summary()['control']['halted'], 'BLOB_HASH_MISMATCH')

    def test_review_large_header_is_bounded_failure_with_body_evidence(self):
        self.capture.enqueue(PRIMARY, 'primary', 'one')
        self.transport.results.append(self.response(b'important body', headers={'etag': 'x' * 65537}))
        record = self.capture.run_one()
        self.assertEqual(self.capture.store.raw(record), b'important body')
        self.assertEqual(record['metadata']['failure'], 'RESPONSE_METADATA_LIMIT')
        self.assertTrue(record['metadata']['headers_truncated'])
        self.assertEqual(len(record['metadata']['headers']['etag']), 2048)
        self.assertEqual(self.capture.jobs()[0]['state'], 'FAILED')
        self.assertIsNone(record['metadata']['document_receipt'])

    def test_review_assessment_detected_corruption_halts_all_later_requests(self):
        self.capture.enqueue(PRIMARY, 'primary', 'one')
        self.transport.results.append(self.response(b'retained'))
        first = self.capture.run_one()
        self.capture.enqueue(SUBMISSION, 'submission', 'two')
        (self.capture.store.objects / first['blob_sha']).write_bytes(b'corrupt')
        with self.assertRaisesRegex(AuditFailure, 'BLOB_HASH_MISMATCH'):
            self.capture.assess(first['id'], acceptance=[])
        calls = len(self.transport.calls)
        self.transport.results.append(self.response(b'different'))
        with self.assertRaisesRegex(AuditFailure, 'BLOB_HASH_MISMATCH'):
            self.capture.run_one()
        self.assertEqual(len(self.transport.calls), calls)
        self.assertEqual(self.capture.summary()['control']['halted'], 'BLOB_HASH_MISMATCH')

    def test_assessment_missing_blob_is_storage_failure_and_halts_requests(self):
        self.capture.enqueue(PRIMARY, 'primary', 'one')
        self.transport.results.append(self.response())
        record = self.capture.run_one()
        (self.capture.store.objects / record['blob_sha']).unlink()
        with self.assertRaisesRegex(AuditFailure, 'STORAGE_FAILURE'):
            self.capture.assess(record['id'], acceptance=[])
        self.assertEqual(self.capture.summary()['control']['halted'], 'STORAGE_FAILURE')

    def test_parse_failure_record_storage_error_blocks_calls_and_restart(self):
        for failure in (sqlite3.OperationalError, OSError):
            with self.subTest(failure=failure.__name__):
                self.capture.close()
                self.root = Path(self.tmp.name) / ('parse-failure-' + failure.__name__)
                self.capture = self.open()
                self.capture.enqueue(DISC, 'discovery', 'poll')
                self.transport.results.append(self.response(b'discovery-body'))
                observation = self.capture.run_one()
                self.capture.enqueue(PRIMARY, 'primary', 'pending')
                original = self.capture.store.append_in_transaction
                def fail_record(kind, *args, **kwargs):
                    if kind == 'preservation.parse_failure':
                        raise failure('synthetic failure-log storage error')
                    return original(kind, *args, **kwargs)
                calls = len(self.transport.calls)
                with patch.object(self.capture.store, 'append_in_transaction', side_effect=fail_record):
                    with self.assertRaisesRegex(AuditFailure, 'STORAGE_FAILURE'):
                        self.capture.parse_discovery(observation['id'], [claim(cik='invalid')])
                self.assertEqual(self.records('parse_failure'), [])
                self.assertEqual(self.capture.store.raw(observation), b'discovery-body')
                for reopened in (False, True):
                    if reopened:
                        self.restart()
                    with self.assertRaisesRegex(AuditFailure, 'STORAGE_FAILURE'):
                        self.capture.run_one()
                    with self.assertRaisesRegex(AuditFailure, 'STORAGE_FAILURE'):
                        self.capture.parse_discovery(observation['id'], [claim()])
                    self.assertEqual(self.capture.summary()['control']['halted'], 'STORAGE_FAILURE')
                    self.assertEqual(self.capture.summary()['control']['requests'], 1)
                    self.assertEqual(len(self.transport.calls), calls)
                    self.assertEqual(self.capture.jobs()[-1]['state'], 'PENDING')

    def test_storage_failure_record_error_blocks_calls_and_restart(self):
        for failure in (sqlite3.OperationalError, OSError):
            with self.subTest(failure=failure.__name__):
                self.capture.close()
                self.root = Path(self.tmp.name) / ('storage-failure-' + failure.__name__)
                self.capture = self.open()
                self.capture.enqueue(PRIMARY, 'primary', 'pending')
                self.transport.results.append(self.response())
                original = self.capture.store.append_in_transaction
                def fail_record(kind, *args, **kwargs):
                    if kind == 'preservation.storage_failure':
                        raise failure('synthetic failure-log storage error')
                    return original(kind, *args, **kwargs)
                with patch.object(self.capture.store, '_finalize_blob', side_effect=OSError('synthetic disk full')), \
                     patch.object(self.capture.store, 'append_in_transaction', side_effect=fail_record):
                    with self.assertRaisesRegex(AuditFailure, 'STORAGE_FAILURE'):
                        self.capture.run_one()
                calls = len(self.transport.calls)
                self.assertEqual(self.records('storage_failure'), [])
                for reopened in (False, True):
                    if reopened:
                        self.restart()
                    with self.assertRaisesRegex(AuditFailure, 'STORAGE_FAILURE'):
                        self.capture.run_one()
                    self.assertEqual(self.capture.summary()['control']['halted'], 'STORAGE_FAILURE')
                    self.assertEqual(self.capture.jobs()[0]['attempts'], 1)
                    self.assertNotEqual(self.capture.jobs()[0]['state'], 'COMPLETE')
                    self.assertEqual(len(self.transport.calls), calls)

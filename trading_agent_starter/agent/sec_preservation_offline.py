"""SEC preservation boundary for SYNTHETIC OFFLINE exercises only.

No default clock, transport, network client, environment reads, scheduler or CLI.
URIs are fixture://sec/... only. Callers inject response streams and clock samples.
This is capture bookkeeping, not the event-evidence envelope or an admission engine.
The existing EvidenceStore owns raw objects, append-only records and verification.
One writer holds an OS lock; queue transitions share the evidence transaction.
Power-loss durability of the filesystem/drive, especially Windows directory flush,
remains unqualified. A synthetic success says nothing about SEC completeness.
"""
from __future__ import annotations

from contextlib import contextmanager
from dataclasses import asdict, dataclass
from datetime import timedelta
import math
import os
from pathlib import Path
import re
import sqlite3
from urllib.parse import urlsplit
import uuid

from .audit_store import AuditFailure, EvidenceStore, canonical, digest, timestamp


@dataclass(frozen=True)
class ClockSample:
    utc: str
    monotonic_ns: int
    session: str
    uncertainty_seconds: float | None
    measurement_ref: str | None


@dataclass(frozen=True)
class Limits:
    max_requests: int = 100
    max_total_bytes: int = 1_000_000
    max_response_bytes: int = 4096
    max_jobs: int = 100
    max_events: int = 100
    max_records: int = 2000
    max_attempts: int = 3


@dataclass(frozen=True)
class Response:
    status: int
    headers: dict
    chunks: object
    complete: bool = True


class OfflinePreserver:
    """Explicit step-driven harness. A supplied callable is trusted test code.

    max_total_bytes counts received bytes (including a one-byte oversize probe).
    An interrupted request retains its full reservation: no silent budget reset.
    Metadata has separate record/claim/job caps. No real-world capacity is claimed.
    """
    ROLES = {'discovery', 'index', 'primary', 'submission', 'accession_index'}

    def __init__(self, root, *, transport, clock, limits=Limits()):
        if not callable(transport) or not callable(clock):
            raise AuditFailure('INJECTION_REQUIRED')
        if (any(type(v) is not int or v < 1 for v in asdict(limits).values())
                or limits.max_attempts > 3):
            raise AuditFailure('INVALID_LIMITS')
        self.root = Path(root)
        self.root.mkdir(mode=0o700, parents=True, exist_ok=True)
        self.transport, self.clock, self.limits = transport, clock, limits
        self.store = None
        self._lock = None
        self._broken = None
        try:
            self._lock_writer()
            self.store = EvidenceStore(self.root)
            self.db = self.store.db
            self.db.executescript('''
              CREATE TABLE IF NOT EXISTS preservation_control (
                id INTEGER PRIMARY KEY CHECK(id=1), binding TEXT NOT NULL,
                requests INTEGER NOT NULL, bytes_charged INTEGER NOT NULL,
                halted TEXT);
              CREATE TABLE IF NOT EXISTS preservation_events (
                event_key TEXT PRIMARY KEY, accession TEXT NOT NULL UNIQUE,
                cik TEXT NOT NULL, form TEXT NOT NULL, target INTEGER NOT NULL,
                first_discovery TEXT NOT NULL REFERENCES records(id),
                late INTEGER NOT NULL, conflict INTEGER NOT NULL DEFAULT 0);
              CREATE TABLE IF NOT EXISTS preservation_jobs (
                job_id TEXT PRIMARY KEY, event_key TEXT REFERENCES preservation_events(event_key),
                uri TEXT NOT NULL, role TEXT NOT NULL, state TEXT NOT NULL,
                attempts INTEGER NOT NULL DEFAULT 0, not_before TEXT,
                observation TEXT REFERENCES records(id), failure TEXT);
              CREATE TABLE IF NOT EXISTS preservation_parsed (
                observation TEXT PRIMARY KEY REFERENCES records(id),
                claims_hash TEXT NOT NULL,
                result TEXT NOT NULL);
            ''')
            self.code_hash = digest(Path(__file__).read_bytes()
                                    + Path(__file__).with_name('audit_store.py').read_bytes())
            binding = digest(canonical({'mode': 'SYNTHETIC_OFFLINE', 'version': 1,
                                        'limits': asdict(limits), 'code_hash': self.code_hash}))
            with self.store.transaction():
                self.db.execute('INSERT OR IGNORE INTO preservation_control VALUES (1,?,0,0,NULL)',
                                (binding,))
                if self._control()['binding'] != binding:
                    raise AuditFailure('CONFIG_BINDING_CHANGED')
            if self.db.execute('PRAGMA quick_check').fetchone()[0] != 'ok':
                raise AuditFailure('DATABASE_CORRUPT')
            self.store.verify()
            self._verify_queue()
            self._recover()
        except BaseException:
            self.close()
            raise

    def _lock_writer(self):
        self._lock = (self.root / '.preservation.lock').open('a+b')
        self._lock.seek(0, os.SEEK_END)
        if self._lock.tell() == 0:
            self._lock.write(b'0')
            self._lock.flush()
        self._lock.seek(0)
        try:
            if os.name == 'nt':
                import msvcrt
                msvcrt.locking(self._lock.fileno(), msvcrt.LK_NBLCK, 1)
            else:
                import fcntl
                fcntl.flock(self._lock.fileno(), fcntl.LOCK_EX | fcntl.LOCK_NB)
        except OSError:
            self._lock.close()
            self._lock = None
            raise AuditFailure('WRITER_ALREADY_OPEN') from None

    def close(self):
        if self.store is not None:
            self.store.close()
            self.store = None
        if self._lock is not None:
            self._lock.close()  # Kernel releases the lock on process death too.
            self._lock = None

    def _control(self):
        return self.db.execute('SELECT * FROM preservation_control WHERE id=1').fetchone()

    def _sample(self):
        sample = self.clock()
        if (not isinstance(sample, ClockSample) or not sample.session
                or type(sample.monotonic_ns) is not int or sample.monotonic_ns < 0):
            raise AuditFailure('INVALID_CLOCK_SAMPLE')
        timestamp(sample.utc)
        if not sample.utc.endswith(('Z', '+00:00')):
            raise AuditFailure('UTC_CLOCK_REQUIRED')
        uncertainty = sample.uncertainty_seconds
        if uncertainty is not None and (not math.isfinite(uncertainty) or uncertainty < 0):
            raise AuditFailure('INVALID_CLOCK_UNCERTAINTY')
        return asdict(sample)

    @staticmethod
    def _uri(uri):
        if not isinstance(uri, str) or len(uri) > 2048:
            raise AuditFailure('OFFLINE_URI_REQUIRED')
        value = urlsplit(uri)
        if (value.scheme != 'fixture' or value.netloc != 'sec'
                or not re.fullmatch(r'/[A-Za-z0-9_./-]+', value.path)
                or '..' in value.path or value.query or value.fragment):
            raise AuditFailure('OFFLINE_URI_REQUIRED')

    def _append(self, kind, key, metadata, raw=None):
        if len(canonical(metadata)) > 65536:
            raise AuditFailure('METADATA_TOO_LARGE')
        count = self.db.execute("SELECT count(*) FROM records WHERE kind LIKE 'preservation.%'").fetchone()[0]
        if count >= self.limits.max_records:
            raise AuditFailure('RECORD_BUDGET_EXHAUSTED')
        return self.store.append_in_transaction('preservation.' + kind, key,
            dict(metadata, mode='SYNTHETIC_OFFLINE', code_hash=self.code_hash,
                 config_hash=self._control()['binding'], rights_reference='synthetic-fixtures-only'), raw)

    @contextmanager
    def _public_transaction(self):
        try:
            with self.store.transaction():
                yield
        except (OSError, sqlite3.Error):
            self._broken = 'STORAGE_FAILURE'
            try:
                with self.store.transaction():
                    self.db.execute("UPDATE preservation_control SET halted='STORAGE_FAILURE' WHERE id=1")
            except (OSError, sqlite3.Error):
                pass
            raise AuditFailure('STORAGE_FAILURE') from None
        except AuditFailure as exc:
            if str(exc).endswith('BUDGET_EXHAUSTED'):
                self._halt(str(exc))
            raise

    def _verify_queue(self):
        """Fail closed if mutable indexes disagree with append-only facts."""
        expected_jobs, expected_events, expected_parsed = {}, {}, {}
        requests, charged, must_halt = 0, 0, False
        ceiling = self.limits.max_response_bytes + 1
        try:
            for record in self.store.records():
                kind = record['kind'].removeprefix('preservation.')
                meta, key = record['metadata'], record['source_key']
                if not record['kind'].startswith('preservation.'):
                    continue
                if kind == 'queued':
                    identity = digest(canonical([meta['event_key'], meta['uri'],
                                                 meta['role'], meta['request_key']]))
                    if key != identity or key in expected_jobs:
                        raise AuditFailure('QUEUE_CORRUPT')
                    expected_jobs[key] = dict(job_id=key, event_key=meta['event_key'],
                        uri=meta['uri'], role=meta['role'], state='PENDING', attempts=0,
                        not_before=None, observation=None, failure=None)
                    self._uri(meta['uri'])
                elif kind == 'attempt':
                    job = expected_jobs[key]
                    if job['state'] != 'PENDING' or meta['attempt'] != job['attempts'] + 1:
                        raise AuditFailure('QUEUE_CORRUPT')
                    job.update(state='INFLIGHT', attempts=meta['attempt'])
                    requests += 1
                    charged += ceiling
                elif kind == 'observation':
                    job = expected_jobs[meta['job_id']]
                    if (job['state'] != 'INFLIGHT' or meta['attempt'] != job['attempts']
                            or any(meta[k] != job[k] for k in ('uri', 'role', 'event_key'))
                            or meta['byte_count'] != len(self.store.raw(record))
                            or not 0 <= meta['byte_count'] <= ceiling):
                        raise AuditFailure('QUEUE_CORRUPT')
                    job.update(state=meta['queue_state'], observation=record['id'],
                               failure=meta['failure'], not_before=meta['retry_not_before'])
                    charged -= ceiling - meta['byte_count']
                    must_halt |= meta['http_status'] == 403
                elif kind == 'recovery':
                    job = expected_jobs[key]
                    state = 'FAILED' if job['attempts'] >= self.limits.max_attempts else 'PENDING'
                    if job['state'] != 'INFLIGHT' or meta['state'] != state:
                        raise AuditFailure('QUEUE_CORRUPT')
                    job.update(state=state, failure='CRASH_INTERRUPTED')
                elif kind == 'storage_failure':
                    expected_jobs[key].update(state='QUARANTINED', failure='STORAGE_FAILURE')
                    must_halt = True
                elif kind == 'discovery':
                    claim = meta['assertion']
                    cik = str(claim['cik']).zfill(10)
                    accession, form = claim['accession'], claim['form']
                    event = expected_events.get(accession)
                    if event is None:
                        source = self.store.get(meta['source_observation'])
                        expected_events[accession] = dict(event_key='SEC:' + cik + ':' + accession,
                            accession=accession, cik=cik, form=form, target=int(form == '10-Q'),
                            first_discovery=record['id'], late=int(source['metadata']['role'] == 'index'), conflict=0)
                    elif event['cik'] != cik or event['form'] != form:
                        event.update(conflict=1, target=max(event['target'], int(form == '10-Q')))
                elif kind == 'parse_completed':
                    expected_parsed[key] = dict(observation=key, claims_hash=meta['claims_hash'],
                                                result=canonical(meta['event_keys']).decode())
            actual_jobs = {j['job_id']: j for j in self.jobs()}
            actual_events = {e['accession']: e for e in self.events()}
            actual_parsed = {r['observation']: dict(r) for r in self.db.execute('SELECT * FROM preservation_parsed')}
            control = self._control()
            if (actual_jobs != expected_jobs or actual_events != expected_events
                    or actual_parsed != expected_parsed or control['requests'] != requests
                    or control['bytes_charged'] != charged or requests > self.limits.max_requests
                    or charged > self.limits.max_total_bytes or (must_halt and not control['halted'])):
                raise AuditFailure('QUEUE_CORRUPT')
        except (KeyError, TypeError, ValueError):
            raise AuditFailure('QUEUE_CORRUPT') from None

    def _halt(self, reason):
        self._broken = reason
        with self.store.transaction():
            self.db.execute('UPDATE preservation_control SET halted=? WHERE id=1', (reason,))

    def _ready(self):
        if self._broken:
            raise AuditFailure(self._broken)
        reason = self._control()['halted']
        if reason:
            raise AuditFailure(reason)

    def _recover(self):
        # Never adopt bytes as a completed observation without the DB commit.
        quarantine = self.root / 'quarantine'
        quarantine.mkdir(mode=0o700, exist_ok=True)
        referenced = {r[0] for r in self.db.execute('SELECT blob_sha FROM records WHERE blob_sha IS NOT NULL')}
        orphans = list(self.store.spool.iterdir()) + [
            p for p in self.store.objects.iterdir() if p.name not in referenced]
        for path in orphans:
            target = quarantine / uuid.uuid4().hex
            with self.store.transaction():
                self._append('orphan', str(path.relative_to(self.root)), {
                    'disposition': 'QUARANTINED_NOT_RECEIPT', 'retained_path': str(target.relative_to(self.root))})
                # Commit record before moving: a crash can leave an extra orphan
                # record, never an invented complete object. Preserve both paths.
            path.rename(target)
            self.store.sync_directory(quarantine)
            self.store.sync_directory(path.parent)
        with self.store.transaction():
            for row in self.db.execute("SELECT * FROM preservation_jobs WHERE state='INFLIGHT'").fetchall():
                state = 'FAILED' if row['attempts'] >= self.limits.max_attempts else 'PENDING'
                self._append('recovery', row['job_id'], {'failure': 'CRASH_INTERRUPTED',
                             'attempts': row['attempts'], 'state': state})
                self.db.execute('UPDATE preservation_jobs SET state=?,failure=? WHERE job_id=?',
                                (state, 'CRASH_INTERRUPTED', row['job_id']))

    def _enqueue(self, uri, role, request_key, event_key):
        self._uri(uri)
        if role not in self.ROLES or not isinstance(request_key, str) or not 1 <= len(request_key) <= 256:
            raise AuditFailure('INVALID_JOB')
        identity = digest(canonical([event_key, uri, role, request_key]))
        existing = self.db.execute('SELECT job_id FROM preservation_jobs WHERE job_id=?', (identity,)).fetchone()
        if existing:
            return identity
        if self.db.execute('SELECT count(*) FROM preservation_jobs').fetchone()[0] >= self.limits.max_jobs:
            raise AuditFailure('JOB_BUDGET_EXHAUSTED')
        self._append('queued', identity, {'uri': uri, 'role': role, 'event_key': event_key,
                                         'request_key': request_key})
        self.db.execute('INSERT INTO preservation_jobs (job_id,event_key,uri,role,state) VALUES (?,?,?,?,?)',
                        (identity, event_key, uri, role, 'PENDING'))
        return identity

    def enqueue(self, uri, role, request_key, event_key=None):
        self._ready()
        with self._public_transaction():
            return self._enqueue(uri, role, request_key, event_key)

    def jobs(self):
        return [dict(r) for r in self.db.execute('SELECT * FROM preservation_jobs ORDER BY rowid')]

    def events(self):
        return [dict(r) for r in self.db.execute('SELECT * FROM preservation_events ORDER BY rowid')]

    def _receive(self, job, started):
        raw = bytearray()
        status, headers, failure, body_completed = None, {}, None, None
        header_receipt = None
        headers_truncated = False
        try:
            response = self.transport(job['uri'], self.limits.max_response_bytes + 1)
            if not isinstance(response, Response):
                raise AuditFailure('INVALID_FIXTURE_RESPONSE')
            status = response.status
            for name in ('content-type', 'content-length', 'date', 'etag',
                         'last-modified', 'retry-after', 'content-encoding'):
                values = [str(v) for k, v in response.headers.items() if str(k).lower() == name]
                if values:
                    value = values[0]
                    headers_truncated |= len(value) > 2048 or len(values) > 1
                    headers[name] = value[:2048]
            header_receipt = self._sample()
            for chunk in response.chunks:
                if not isinstance(chunk, bytes):
                    raise AuditFailure('INVALID_RESPONSE_CHUNK')
                available = self.limits.max_response_bytes + 1 - len(raw)
                raw.extend(chunk[:available])
                if len(chunk) > available or len(raw) > self.limits.max_response_bytes:
                    failure = 'RESPONSE_TOO_LARGE'
                    break
            if failure is None:
                if not response.complete:
                    failure = 'PARTIAL_BODY'
                elif 'content-length' in headers and headers['content-length'] != str(len(raw)):
                    failure = 'SIZE_CONFLICT'
                else:
                    body_completed = self._sample()
            if failure is None and headers_truncated:
                failure = 'RESPONSE_METADATA_LIMIT'
            if failure is None and status != 200:
                failure = 'HTTP_' + str(status)
        except (OSError, TimeoutError):
            failure = 'TRANSPORT_ERROR'
        except AuditFailure as exc:
            failure = str(exc)
        ended = self._sample()
        samples = [s for s in (started, header_receipt, body_completed, ended) if s]
        flags = []
        if any(s['uncertainty_seconds'] is None or s['uncertainty_seconds'] > 1
               or not s['measurement_ref'] for s in samples):
            flags.append('CLOCK_UNCERTAIN')
        if any(a['session'] != b['session'] or a['monotonic_ns'] > b['monotonic_ns']
               or timestamp(a['utc']) > timestamp(b['utc']) for a, b in zip(samples, samples[1:])):
            flags.append('CLOCK_DISCONTINUITY')
        return bytes(raw), dict(request_started=started, header_receipt=header_receipt,
            body_completed=body_completed, document_receipt=body_completed if status == 200 and not failure else None,
            retrieval_completed=body_completed, attempt_ended=ended, http_status=status,
            headers=headers, headers_truncated=headers_truncated, failure=failure, timing_flags=flags, source_revision_at=None,
            historical_receipt_utc=None, transport_encoding='injected identity bytes')

    def run_one(self):
        self._ready()
        started = self._sample()
        row = self.db.execute("SELECT * FROM preservation_jobs WHERE state='PENDING' "
                              'AND (not_before IS NULL OR not_before<=?) ORDER BY rowid LIMIT 1',
                              (timestamp(started['utc']).isoformat(),)).fetchone()
        if row is None:
            return None
        job = dict(row)
        # Reserve before invoking untrusted/injected transport. Crashes consume
        # this request and its byte ceiling; completion refunds only unused bytes.
        try:
            with self.store.transaction():
                control = self._control()
                if control['requests'] >= self.limits.max_requests:
                    raise AuditFailure('REQUEST_BUDGET_EXHAUSTED')
                if control['bytes_charged'] + self.limits.max_response_bytes + 1 > self.limits.max_total_bytes:
                    raise AuditFailure('BYTE_BUDGET_EXHAUSTED')
                self._append('attempt', job['job_id'], {'started': started, 'attempt': job['attempts'] + 1})
                self.db.execute("UPDATE preservation_jobs SET state='INFLIGHT',attempts=attempts+1 WHERE job_id=?",
                                (job['job_id'],))
                self.db.execute('UPDATE preservation_control SET requests=requests+1,bytes_charged=bytes_charged+? WHERE id=1',
                                (self.limits.max_response_bytes + 1,))
            raw, metadata = self._receive(job, started)
            failure = metadata['failure']
            retry = failure in {'TRANSPORT_ERROR', 'HTTP_429', 'HTTP_500', 'HTTP_502', 'HTTP_503', 'HTTP_504'}
            delay = 2 ** job['attempts'] if retry else 0
            if failure == 'HTTP_429':
                value = metadata['headers'].get('retry-after')
                if value is not None:
                    if not value.isdigit() or int(value) > 900:
                        retry, delay = False, 0
                        metadata['retry_policy_failure'] = 'RETRY_AFTER_UNSUPPORTED'
                    else:
                        delay = max(delay, int(value))
            state = 'COMPLETE' if not failure else ('PENDING' if retry and job['attempts'] + 1 < self.limits.max_attempts else 'FAILED')
            not_before = (timestamp(metadata['attempt_ended']['utc']) + timedelta(seconds=delay)).isoformat() if retry else None
            metadata.update(queue_state=state, retry_not_before=not_before)
            key = canonical([job['event_key'], job['role'], job['uri']]).decode()
            prior = [r for r in self.store.records('preservation.observation', key)
                     if r['blob_sha'] == digest(raw) and r['metadata']['document_receipt']]
            metadata['first_version_receipt'] = (prior[0]['metadata']['document_receipt']
                if prior else metadata['document_receipt'])
            with self.store.transaction():
                record = self._append('observation', key, dict(metadata, job_id=job['job_id'],
                                      attempt=job['attempts'] + 1, method='GET',
                                      event_key=job['event_key'], role=job['role'], uri=job['uri'],
                                      byte_count=len(raw)), raw)
                self.db.execute('UPDATE preservation_jobs SET state=?,observation=?,failure=?,not_before=? WHERE job_id=?',
                                (state, record['id'], failure, not_before, job['job_id']))
                self.db.execute('UPDATE preservation_control SET bytes_charged=bytes_charged-? WHERE id=1',
                                (self.limits.max_response_bytes + 1 - len(raw),))
                if metadata['http_status'] == 403:
                    self.db.execute("UPDATE preservation_control SET halted='HTTP_403' WHERE id=1")
            return record
        except AuditFailure as exc:
            if str(exc).endswith('BUDGET_EXHAUSTED') or str(exc) in {
                    'BLOB_HASH_MISMATCH', 'RECORD_CHAIN_MISMATCH'}:
                self._halt(str(exc))
            raise
        except (OSError, sqlite3.Error):
            self._broken = 'STORAGE_FAILURE'
            try:
                with self.store.transaction():
                    self._append('storage_failure', job['job_id'], {'failure': 'STORAGE_FAILURE', 'state': 'QUARANTINED'})
                    self.db.execute("UPDATE preservation_jobs SET state='QUARANTINED',failure='STORAGE_FAILURE' WHERE job_id=?", (job['job_id'],))
                    self.db.execute("UPDATE preservation_control SET halted='STORAGE_FAILURE' WHERE id=1")
            except (OSError, sqlite3.Error, AuditFailure):
                pass  # Cannot claim durable failure logging when storage is broken.
            raise AuditFailure('STORAGE_FAILURE') from None

    def parse_discovery(self, observation_id, claims):
        self._ready()
        observation = self.store.get(observation_id)
        if (observation['kind'] != 'preservation.observation'
                or observation['metadata']['role'] not in {'discovery', 'index'}
                or observation['metadata']['failure']):
            raise AuditFailure('COMPLETE_DISCOVERY_REQUIRED')
        claims_hash = digest(canonical(claims))
        previous = self.db.execute('SELECT * FROM preservation_parsed WHERE observation=?', (observation_id,)).fetchone()
        if previous:
            if previous['claims_hash'] != claims_hash:
                raise AuditFailure('PARSE_BINDING_CHANGED')
            from .audit_store import strict_json
            return strict_json(previous['result'])
        if not isinstance(claims, list) or len(claims) > self.limits.max_events:
            raise AuditFailure('CLAIM_BUDGET_EXHAUSTED')
        parsed = self._sample()
        keys = []
        try:
            with self._public_transaction():
                for claim in claims:
                    cik = str(claim['cik'])
                    accession, form = claim['accession'], claim['form']
                    if (not re.fullmatch(r'\d{1,10}', cik) or int(cik) == 0
                            or not isinstance(accession, str) or not re.fullmatch(r'\d{10}-\d{2}-\d{6}', accession)
                            or not isinstance(form, str) or not 1 <= len(form) <= 32):
                        raise AuditFailure('INVALID_IDENTITY_ASSERTION')
                    cik = cik.zfill(10)
                    key = 'SEC:' + cik + ':' + accession
                    record = self._append('discovery', accession, {'source_observation': observation_id,
                        'assertion': claim, 'response_body_receipt': observation['metadata']['body_completed'],
                        'parse_completed': parsed, 'historical_receipt_utc': None})
                    existing = self.db.execute('SELECT * FROM preservation_events WHERE accession=?', (accession,)).fetchone()
                    if existing and (existing['cik'] != cik or existing['form'] != form):
                        self._append('identity_conflict', accession, {'assertion_record': record['id'], 'prior_event': existing['event_key']})
                        self.db.execute('UPDATE preservation_events SET conflict=1,target=max(target,?) WHERE accession=?',
                                        (int(form == '10-Q'), accession))
                        keys.append(existing['event_key'])
                        continue
                    if not existing:
                        if self.db.execute('SELECT count(*) FROM preservation_events').fetchone()[0] >= self.limits.max_events:
                            raise AuditFailure('EVENT_BUDGET_EXHAUSTED')
                        self.db.execute('INSERT INTO preservation_events VALUES (?,?,?,?,?,?,?,0)',
                            (key, accession, cik, form, int(form == '10-Q'), record['id'],
                             int(observation['metadata']['role'] == 'index')))
                    keys.append(key)
                    if form == '10-Q':
                        representations = claim.get('representations', [])
                        if len(representations) > 3:
                            raise AuditFailure('REPRESENTATION_BUDGET_EXHAUSTED')
                        for representation in representations:
                            if representation['role'] not in {'primary', 'submission', 'accession_index'}:
                                raise AuditFailure('INVALID_REPRESENTATION')
                            self._enqueue(representation['uri'], representation['role'], observation_id, key)
                self._append('parse_completed', observation_id, {'claims_hash': claims_hash,
                             'event_keys': keys, 'parse_completed': parsed})
                self.db.execute('INSERT INTO preservation_parsed VALUES (?,?,?)',
                                (observation_id, claims_hash, canonical(keys).decode()))
        except (KeyError, TypeError, AuditFailure) as exc:
            reason = str(exc) if isinstance(exc, AuditFailure) else 'INVALID_DISCOVERY_ASSERTION'
            with self.store.transaction():
                self._append('parse_failure', observation_id, {'failure': reason, 'parse_completed': parsed})
            raise AuditFailure(reason) from None
        return keys

    def assess(self, observation_id, *, acceptance):
        self._ready()
        record = self.store.get(observation_id)
        self.store.raw(record)
        if not isinstance(acceptance, list) or len(acceptance) > 10:
            raise AuditFailure('INVALID_ACCEPTANCE_ASSERTIONS')
        resolved = []
        for assertion in acceptance:
            try:
                value = assertion['value']
                if (assertion.get('qualified') is True and assertion.get('precision') == 'second'
                        and assertion.get('zone') and assertion.get('span')
                        and isinstance(value, str) and re.search(r'(Z|[+-]\d{2}:\d{2})$', value)):
                    resolved.append(timestamp(value).isoformat())
                else:
                    resolved.append(None)
            except (KeyError, TypeError, AuditFailure):
                resolved.append(None)
        utc = resolved[0] if resolved and None not in resolved and len(set(resolved)) == 1 else None
        with self._public_transaction():
            return self._append('assessment', observation_id, {'source_observation': observation_id,
                'acceptance_assertions': acceptance, 'resolved_acceptance_utc': utc,
                'historical_receipt_utc': None, 'parse_completed': self._sample(), 'admission': 'NOT_ASSESSED'})

    def note_gap(self, reason, details):
        self._ready()
        if not isinstance(reason, str) or not 1 <= len(reason) <= 64:
            raise AuditFailure('INVALID_GAP')
        with self._public_transaction():
            return self._append('gap', reason, {'reason': reason, 'details': details, 'observed': self._sample()})

    def summary(self):
        events, jobs = self.events(), self.jobs()
        parsed = {r[0] for r in self.db.execute('SELECT observation FROM preservation_parsed')}
        unparsed = sum(r['metadata']['role'] in {'discovery', 'index'}
                       and r['id'] not in parsed and not r['metadata']['failure']
                       for r in self.store.records('preservation.observation'))
        complete = 0
        for event in events:
            required = [j for j in jobs if j['event_key'] == event['event_key']]
            # Minimum preserved representations are explicit, not an empty-set pass.
            roles = {j['role'] for j in required if j['state'] == 'COMPLETE'}
            if event['target'] and not event['conflict'] and {'primary', 'submission', 'accession_index'} <= roles:
                complete += 1
        return dict(mode='SYNTHETIC_OFFLINE', known_originals=sum(e['target'] for e in events),
            excluded_forms=sum(not e['target'] for e in events), fully_preserved_originals=complete,
            late_discovered=sum(e['late'] and e['target'] for e in events),
            failed_jobs=sum(j['state'] in {'FAILED', 'QUARANTINED'} for j in jobs),
            pending_jobs=sum(j['state'] in {'PENDING', 'INFLIGHT'} for j in jobs),
            unparsed_discovery_responses=unparsed,
            parse_failures=len(self.store.records('preservation.parse_failure')),
            gaps=len(self.store.records('preservation.gap')), control=dict(self._control()))

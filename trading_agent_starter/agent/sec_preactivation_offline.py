"""Issue 41 preactivation seam: SYNTHETIC ONLY, no HTTP client or live CLI.

SEC URLs are candidate request plans, never passed to a transport. The only
response schema is sec-preactivation-fixture-v1, NOT SEC Atom/JSON/index parsing.
Actual endpoint/query/field/representation semantics remain UNQUALIFIED.
Existing OfflinePreserver owns queue, byte/request reservations, retries, raw
versions and recovery; its fixture:// restriction is unchanged. Clock callables
are trusted test code. Response programs accept inert values, never callables.

Planning examples (not approved budgets), with 3 attempts/job and 4096-byte body:
jobs = polls*pages + accessions*3*versions + reconciliation_jobs.
Low (2,1,2,1,1): 9 jobs / 27 attempts / 110619 reserved payload bytes.
Normal (3,2,4,2,2): 32 jobs / 96 attempts / 393312 bytes.
Stress (5,5,10,3,3): 118 jobs / 354 attempts / 1450338 bytes.
These assume supplied fixture counts, not measured SEC volume. Add separately
bounded metadata (<=64KiB/record in each journal), SQLite/index/journal and backup
footprints; physical storage/backup overhead is UNMEASURED. No approval of #40's
250k requests/100GB/200GB/retention, host capacity, or G3/G4 activation follows.
"""
from dataclasses import asdict, dataclass
from datetime import date, timedelta
import math
from pathlib import Path
import re
import sqlite3

from .audit_store import AuditFailure, canonical, digest, strict_json, timestamp
from .sec_preservation_offline import ClockSample, Limits, OfflinePreserver, Response

SCHEMA = 'sec-preactivation-fixture-v1'


def _cik(value):
    if not isinstance(value, str) or not re.fullmatch(r'[0-9]{1,10}', value) or int(value) == 0:
        raise AuditFailure('INVALID_CIK')
    return value.zfill(10)


def _name(value):
    if (not isinstance(value, str) or len(value) > 150 or '..' in value
            or not re.fullmatch(r'[A-Za-z0-9][A-Za-z0-9_.-]*', value)):
        raise AuditFailure('UNSAFE_SEC_FILENAME')
    return value


@dataclass(frozen=True)
class RequestPlan:
    kind: str
    url: str
    role: str
    cik: str | None = None
    accession: str | None = None
    filename: str | None = None
    start: int = 0
    day: str | None = None

    @property
    def fixture_uri(self):
        return 'fixture://sec/preactivation/' + digest(self.url.encode('ascii'))


def plan_request(kind, *, cik=None, accession=None, filename=None, start=0, day=None):
    """Exact canonical plan, not authority to fetch. Unused arguments fail closed."""
    if type(start) is not int:
        raise AuditFailure('INVALID_PAGE')
    if type(kind) is not str:
        raise AuditFailure('UNQUALIFIED_ENDPOINT_OR_ARGUMENTS')
    if kind == 'discovery' and cik is accession is filename is day is None:
        if start not in (0, 100, 200, 300, 400):
            raise AuditFailure('INVALID_PAGE')
        url = ('https://www.sec.gov/cgi-bin/browse-edgar?action=getcurrent&type=10-Q&owner=include'
               f'&start={start}&count=100&output=atom')
        role = 'discovery'
    elif kind in {'submissions', 'history'} and accession is day is None and start == 0:
        cik = _cik(cik)
        if kind == 'submissions' and filename is None:
            filename_part = f'CIK{cik}.json'
        elif kind == 'history' and re.fullmatch(r'CIK' + cik + r'-submissions-[0-9]{3}\.json', _name(filename)):
            filename_part = filename
        else:
            raise AuditFailure('SEC_HISTORY_IDENTITY_MISMATCH')
        url, role = 'https://data.sec.gov/submissions/' + filename_part, 'discovery'
    elif kind in {'primary', 'submission', 'accession_index'} and day is None and start == 0:
        cik = _cik(cik)
        if not isinstance(accession, str) or not re.fullmatch(r'[0-9]{10}-[0-9]{2}-[0-9]{6}', accession):
            raise AuditFailure('INVALID_ACCESSION')
        if kind == 'primary':
            tail = _name(filename)
            if tail in (accession + '.txt', accession + '-index.html'):
                raise AuditFailure('REPRESENTATION_ROLE_ALIAS')
        elif filename is None:
            tail = accession + ('.txt' if kind == 'submission' else '-index.html')
        else:
            raise AuditFailure('UNEXPECTED_FILENAME')
        url = f"https://www.sec.gov/Archives/edgar/data/{int(cik)}/{accession.replace('-', '')}/{tail}"
        role = kind
    elif kind in {'daily_index', 'quarter_index'} and cik is accession is filename is None and start == 0:
        try:
            parsed = date.fromisoformat(day)
            if parsed.isoformat() != day:
                raise ValueError
        except (ValueError, TypeError):
            raise AuditFailure('INVALID_INDEX_DATE') from None
        quarter = (parsed.month - 1) // 3 + 1
        directory = 'daily-index' if kind == 'daily_index' else 'full-index'
        tail = f'master.{parsed:%Y%m%d}.idx' if kind == 'daily_index' else 'master.idx'
        url = f'https://www.sec.gov/Archives/edgar/{directory}/{parsed.year}/QTR{quarter}/{tail}'
        role = 'index'
    else:
        raise AuditFailure('UNQUALIFIED_ENDPOINT_OR_ARGUMENTS')
    return RequestPlan(kind, url, role, cik, accession, filename, start, day)


def validate_plan(plan):
    if type(plan) is not RequestPlan or plan != plan_request(
            plan.kind, cik=plan.cik, accession=plan.accession, filename=plan.filename,
            start=plan.start, day=plan.day):
        raise AuditFailure('UNTRUSTED_SEC_REQUEST_PLAN')
    return plan


@dataclass(frozen=True)
class FixtureReply:
    body: bytes = b''
    status: int = 200
    headers: tuple = ()
    complete: bool = True
    fault: str | None = None


class FixtureCrash(BaseException):
    """Simulated process death, intentionally outside normal transport retries."""


@dataclass(frozen=True)
class FilingAssertion:
    cik: str
    accession: str
    form: str
    primary_document: str | None
    acceptance_native: tuple

    @classmethod
    def from_fixture(cls, value):
        if type(value) is not dict or set(value) - {'cik', 'accession', 'form', 'primary_document', 'acceptance'}:
            raise AuditFailure('UNQUALIFIED_ASSERTION_FIELDS')
        cik = _cik(value.get('cik'))
        accession, form = value.get('accession'), value.get('form')
        plan_request('submission', cik=cik, accession=accession)
        if not isinstance(form, str) or not re.fullmatch(r'[A-Za-z0-9/-]{1,32}', form):
            raise AuditFailure('INVALID_FORM_ASSERTION')
        filename = value.get('primary_document')
        if filename is not None:
            _name(filename)
        acceptance = value.get('acceptance', [])
        if (type(acceptance) is not list or len(acceptance) > 10
                or any(type(v) is not str or len(v) > 128 for v in acceptance)):
            raise AuditFailure('INVALID_ACCEPTANCE_ASSERTIONS')
        return cls(cik, accession, form, filename, tuple(acceptance))


class OfflineSECDriver:
    """Explicit calls only. New journal records reuse the existing evidence DB.

    Separate driver dispatch reservations are conservative: a crash between this
    journal and the existing request reservation consumes a dispatch slot. Neither
    slot nor retry/rate state is reset on reopen. No timer, sleep or HTTP fallback.
    """
    def __init__(self, root, *, fixtures, clock, limits=Limits(), max_pages=2,
                 max_cycles=3, start_utc='2026-01-01T00:00:00Z'):
        self.capture, self._broken, self._active = None, None, None
        if type(fixtures) is not dict:
            raise AuditFailure('INERT_FIXTURE_PROGRAM_REQUIRED')
        self.fixtures = {}
        for url, replies in fixtures.items():
            if type(url) is not str or type(replies) is not tuple:
                raise AuditFailure('INERT_FIXTURE_PROGRAM_REQUIRED')
            for reply in replies:
                if (type(reply) is not FixtureReply or type(reply.body) is not bytes
                        or type(reply.status) is not int or not 100 <= reply.status <= 599
                        or type(reply.complete) is not bool or type(reply.headers) is not tuple
                        or any(type(h) is not tuple or len(h) != 2 or any(type(s) is not str for s in h)
                               for h in reply.headers) or reply.fault not in (None, 'timeout', 'crash')):
                    raise AuditFailure('INERT_FIXTURE_PROGRAM_REQUIRED')
                if len({h[0].lower() for h in reply.headers}) != len(reply.headers):
                    raise AuditFailure('DUPLICATE_FIXTURE_HEADERS')
            self.fixtures[url] = replies
        if type(max_pages) is not int or not 1 <= max_pages <= 5 or type(max_cycles) is not int or not 1 <= max_cycles <= 10:
            raise AuditFailure('INVALID_DRIVER_LIMITS')
        self.max_pages, self.max_cycles, self.start = max_pages, max_cycles, timestamp(start_utc)
        self.clock = clock
        try:
            self.capture = OfflinePreserver(root, transport=self._fixture_transport, clock=clock, limits=limits)
            program = {u: [dict(asdict(r), body=r.body.hex()) for r in rs] for u, rs in self.fixtures.items()}
            binding = digest(canonical(dict(version=SCHEMA, code=digest(Path(__file__).read_bytes()),
                program=program, max_pages=max_pages, max_cycles=max_cycles, start=self.start.isoformat())))
            prior = self._records('binding')
            if prior and prior[0]['metadata']['binding'] != binding:
                raise AuditFailure('DRIVER_BINDING_CHANGED')
            if not prior:
                self._record('binding', SCHEMA, dict(binding=binding))
            self.boot = self._sample()
            self._ready()
            # Recover planned-but-not-enqueued work without changing its key.
            for record in self._records('request'):
                self._restore_request(record['metadata'])
            for record in self._records('cycle'):
                self.enqueue(plan_request('discovery'), f"poll:{record['metadata']['cycle']}:0")
            self._drain()
        except BaseException:
            self.close()
            raise

    def close(self):
        if self.capture:
            self.capture.close()

    def _records(self, kind):
        return self.capture.store.records('preactivation.' + kind)

    def _record(self, kind, key, metadata):
        try:
            count = sum(r['kind'].startswith('preactivation.') for r in self.capture.store.records())
            if count >= self.capture.limits.max_records or len(canonical(metadata)) > 65536:
                raise AuditFailure('DRIVER_RECORD_BUDGET_EXHAUSTED')
            return self.capture.store.append('preactivation.' + kind, key,
                dict(metadata, mode='SYNTHETIC_OFFLINE', source_qualification='UNQUALIFIED'))
        except (OSError, sqlite3.Error, AuditFailure):
            self._broken = 'DRIVER_STORAGE_OR_RECORD_LIMIT'
            raise

    def _ready(self):
        if self._broken or self._records('halt'):
            raise AuditFailure(self._broken or self._records('halt')[-1]['source_key'])
        if self.capture.summary()['control']['halted']:
            raise AuditFailure(self.capture.summary()['control']['halted'])

    def _sample(self):
        value = self.clock()
        if (type(value) is not ClockSample or type(value.monotonic_ns) is not int or value.monotonic_ns < 0
                or not value.session or value.uncertainty_seconds is None
                or not math.isfinite(value.uncertainty_seconds) or not 0 <= value.uncertainty_seconds <= 1
                or not value.measurement_ref):
            raise AuditFailure('UNQUALIFIED_DRIVER_CLOCK')
        timestamp(value.utc)
        return value

    def _gap(self, reason, **details):
        self._record('gap', reason, details)

    def _halt(self, reason):
        self._record('halt', reason, {})
        self._broken = reason

    def _restore_request(self, metadata):
        plan = validate_plan(RequestPlan(**metadata['plan']))
        return self.capture.enqueue(plan.fixture_uri, plan.role, metadata['request_key'])

    def enqueue(self, plan, request_key):
        self._ready()
        validate_plan(plan)
        if not isinstance(request_key, str) or not 1 <= len(request_key) <= 200:
            raise AuditFailure('INVALID_DRIVER_REQUEST_KEY')
        prior = self.capture.store.records('preactivation.request', request_key)
        value = dict(plan=asdict(plan), request_key=request_key)
        if prior:
            if prior[0]['metadata']['plan'] != value['plan']:
                raise AuditFailure('REQUEST_KEY_REBOUND')
        else:
            self._record('request', request_key, value)
        return self._restore_request(value)

    def poll(self, cycle):
        self._ready()
        if type(cycle) is not int or not 0 <= cycle < self.max_cycles:
            raise AuditFailure('POLL_LIMIT')
        now = self._sample()
        if timestamp(now.utc) < self.start + timedelta(seconds=60 * cycle):
            raise AuditFailure('POLL_NOT_DUE')
        cycles = {r['metadata']['cycle'] for r in self._records('cycle')}
        if cycle not in cycles:
            if cycles and cycle < max(cycles):
                self._gap('OUT_OF_ORDER_POLL', cycle=cycle)
                raise AuditFailure('OUT_OF_ORDER_POLL')
            for skipped in range(max(cycles, default=-1) + 1, cycle):
                self._gap('MISSED_POLL', cycle=skipped)
            self._record('cycle', str(cycle), dict(cycle=cycle, scheduled=(self.start + timedelta(seconds=60 * cycle)).isoformat()))
        return self.enqueue(plan_request('discovery'), f'poll:{cycle}:0')

    def _plans(self):
        result = {}
        for record in self._records('plan') + self._records('request'):
            plan = validate_plan(RequestPlan(**record['metadata']['plan']))
            result[plan.fixture_uri] = plan
        return result

    def _fixture_transport(self, uri, limit):
        if self._active is None or uri != self._active[0]:
            raise AuditFailure('UNAUTHORIZED_FIXTURE_REQUEST')
        plan, occurrence = self._plans()[uri], self._active[1]
        replies = self.fixtures.get(plan.url, ())
        if occurrence >= len(replies):
            raise AuditFailure('UNAUTHORIZED_FIXTURE_REQUEST')
        reply = replies[occurrence]
        if reply.fault == 'crash':
            raise FixtureCrash()
        if reply.fault == 'timeout':
            raise TimeoutError()
        return Response(reply.status, dict(reply.headers), (reply.body,), reply.complete)

    def _prior_poll_records(self, observation):
        # Follow durable page ancestry to the poll's cycle marker. Only evidence
        # committed before that marker can establish overlap, including on replay.
        # Unscoped discovery requests have no qualified prior-poll frontier.
        for _ in range(self.max_pages):
            queued = self.capture.store.records('preservation.queued', observation['metadata']['job_id'])
            key = queued[0]['metadata']['request_key']
            match = re.fullmatch(r'poll:([0-9]+):0', key)
            if match:
                cycles = self.capture.store.records('preactivation.cycle', match[1])
                if cycles:
                    prior = set()
                    for record in self.capture.store.records():
                        if record['id'] == cycles[0]['id']:
                            return prior
                        prior.add(record['id'])
                break
            if not key.startswith('page:'):
                break
            observation = self.capture.store.get(key[5:])
        return set()

    def _parse(self, observation, plan):
        raw = self.capture.store.raw(observation)
        value = strict_json(raw)
        expected = 'index' if plan.role == 'index' else plan.kind
        if (type(value) is not dict or set(value) != {'schema', 'kind', 'items', 'next_start'}
                or value['schema'] != SCHEMA or value['kind'] != expected
                or type(value['items']) is not list or len(value['items']) > 100):
            raise AuditFailure('UNQUALIFIED_FIXTURE_SCHEMA')
        cursor = value['next_start']
        if cursor is not None and (plan.kind != 'discovery' or type(cursor) is not int or cursor != plan.start + 100):
            raise AuditFailure('UNTRUSTED_PAGE_CURSOR')
        assertions = [FilingAssertion.from_fixture(v) for v in value['items']]
        if plan.cik is not None and any(a.cik != plan.cik for a in assertions):
            raise AuditFailure('SEC_CIK_MISMATCH')
        prior = self._prior_poll_records(observation) if plan.kind == 'discovery' else set()
        old = {(e['cik'], e['accession'], e['form']) for e in self.capture.events()
               if not e['conflict'] and e['first_discovery'] in prior}
        overlap = any((a.cik, a.accession, a.form) in old and a.form == '10-Q' for a in assertions)
        claims = []
        for assertion in assertions:
            representations = []
            if assertion.form == '10-Q':
                for kind in ('primary', 'submission', 'accession_index'):
                    if kind == 'primary' and assertion.primary_document is None:
                        self._gap('PRIMARY_NAME_UNAVAILABLE', observation=observation['id'])
                        continue
                    request = plan_request(kind, cik=assertion.cik, accession=assertion.accession,
                        filename=assertion.primary_document if kind == 'primary' else None)
                    self._record('plan', request.fixture_uri, dict(plan=asdict(request)))
                    representations.append(dict(role=request.role, uri=request.fixture_uri))
            claims.append(dict(cik=assertion.cik, accession=assertion.accession,
                               form=assertion.form, representations=representations))
        self.capture.parse_discovery(observation['id'], claims)
        self._record('assertions', observation['id'], dict(source_observation=observation['id'],
            assertions=[asdict(a) for a in assertions], resolved_acceptance_utc=None, historical_receipt_utc=None))
        if plan.kind == 'discovery':
            if not overlap:
                if cursor is None:
                    self._gap('OVERLAP_NOT_ESTABLISHED', observation=observation['id'])
                elif cursor // 100 >= self.max_pages:
                    self._gap('PAGE_LIMIT', observation=observation['id'])
                else:
                    # Durable key derives from its parent observation. Replay is idempotent.
                    self.enqueue(plan_request('discovery', start=cursor), 'page:' + observation['id'])

    def _drain(self):
        processed = {r['source_key'] for r in self._records('processed')}
        plans = self._plans()
        for observation in self.capture.store.records('preservation.observation'):
            meta = observation['metadata']
            if observation['id'] in processed or meta['uri'] not in plans:
                continue
            plan = plans[meta['uri']]
            if meta['failure']:
                self._gap('REQUEST_FAILURE', observation=observation['id'], failure=meta['failure'])
            elif plan.role in {'discovery', 'index'}:
                try:
                    self._parse(observation, plan)
                except AuditFailure as exc:
                    if self._broken:
                        raise
                    self._record('parse_failure', observation['id'], dict(failure=str(exc)))
                    self._gap('PARSE_FAILURE', observation=observation['id'])
            if meta['http_status'] in {429, 500, 502, 503, 504}:
                retry_after = meta['headers'].get('retry-after')
                if retry_after is not None:
                    if not retry_after.isascii() or not retry_after.isdigit() or int(retry_after) > 900:
                        self._halt('RETRY_AFTER_UNSUPPORTED')
                    else:
                        until = timestamp(meta['attempt_ended']['utc']) + timedelta(seconds=int(retry_after))
                        self._record('pause', observation['id'], dict(not_before=until.isoformat()))
            self._record('processed', observation['id'], {})

    def step(self):
        self._ready()
        try:
            return self._step()
        except BaseException:
            self._broken = self._broken or 'DRIVER_STEP_INTERRUPTED'
            raise

    def _step(self):
        self._drain()
        now = self._sample()
        if any(timestamp(r['metadata']['not_before']) > timestamp(now.utc) for r in self._records('pause')):
            return None
        due = [j for j in self.capture.jobs() if j['state'] == 'PENDING'
               and (j['not_before'] is None or timestamp(j['not_before']) <= timestamp(now.utc))]
        if not due:
            return None
        dispatches = self._records('dispatch')
        if len(dispatches) >= self.capture.limits.max_requests:
            self._halt('REQUEST_BUDGET_EXHAUSTED')
            raise AuditFailure('REQUEST_BUDGET_EXHAUSTED')
        if (now.session != self.boot.session or now.monotonic_ns - self.boot.monotonic_ns < 10**9):
            return None
        anchors = [r['metadata']['sample'] for r in dispatches[-1:]]
        observations = self.capture.store.records('preservation.observation')
        if observations:
            anchors.append(observations[-1]['metadata']['attempt_ended'])
        for anchor in anchors:
            previous = ClockSample(**anchor)
            if previous.uncertainty_seconds is None or previous.uncertainty_seconds > 1:
                raise AuditFailure('UNQUALIFIED_COMPLETION_CLOCK')
            reserve = 1 + previous.uncertainty_seconds + now.uncertainty_seconds
            if ((timestamp(now.utc) - timestamp(previous.utc)).total_seconds() < reserve
                    or (now.session == previous.session and (now.monotonic_ns - previous.monotonic_ns) / 1e9 < reserve)):
                return None
        job = due[0]
        if job['uri'] not in self._plans():
            self._halt('UNPLANNED_JOB')
            raise AuditFailure('UNPLANNED_JOB')
        occurrence = sum(r['metadata']['uri'] == job['uri'] for r in dispatches)
        self._record('dispatch', job['job_id'], dict(uri=job['uri'], sample=asdict(now)))
        self._active = job['uri'], occurrence
        try:
            result = self.capture.run_one()
        finally:
            self._active = None
        self._drain()
        return result

    def summary(self):
        return dict(self.capture.summary(), driver_gaps=len(self._records('gap')),
                    dispatch_reservations=len(self._records('dispatch')), endpoint_qualification='UNQUALIFIED')

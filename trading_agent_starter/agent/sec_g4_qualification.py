"""Issue40 ONE-SHOT diagnostic adapter, not a collector or scientific registration.

Reuses PR43 canonical plans and OfflinePreserver's queue/reservations/recovery.
The inherited offline binding hashes its engine/limits; a separate G4 binding
pins this adapter, manifest, authority, mode and clock. No fixture becomes live.
No scheduler, pagination, credentials, automatic restart or source admission.
"""
from dataclasses import asdict
from datetime import datetime, timezone
from email.utils import parsedate_to_datetime
from html.parser import HTMLParser
import http.client
import os
from pathlib import Path
import re
import shutil
import sqlite3
import time
from urllib.error import HTTPError
from urllib.request import Request, build_opener
import uuid
import xml.etree.ElementTree as ET

from .audit_http import NoRedirect
from .audit_store import AuditFailure, canonical, digest, strict_json, timestamp
from .sec_preactivation_offline import plan_request, validate_plan
from .sec_preservation_offline import ClockSample, Limits, OfflinePreserver, Response

AUTHORITY = 'https://github.com/emanuel894/trading_agent/issues/40#issuecomment-6317975636'
USER_AGENT = 'emanuel894 trading_agent bounded SEC research contact https://github.com/emanuel894/trading_agent/issues/40'
# One counted oversize byte is INCLUDED in the 40MB ceiling, never added to it.
CAPS = Limits(max_requests=18, max_total_bytes=100_000_000,
              max_response_bytes=39_999_999, max_jobs=6, max_events=100, max_records=1000)
DISK_RESERVE = 5_000_000_000


def six_plans():
    identity = dict(cik='0000700565', accession='0000950170-25-067613')
    return (plan_request('discovery'), plan_request('submissions', cik=identity['cik']),
            plan_request('accession_index', **identity), plan_request('submission', **identity),
            plan_request('primary', **identity, filename='fmbh-20250331.htm'),
            plan_request('daily_index', day='2025-05-09'))


class TextOnly(HTMLParser):
    def __init__(self):
        super().__init__()
        self.parts = []
    def handle_data(self, data):
        self.parts.append(data.strip())


def native_metadata(plan, raw):
    """Inert diagnostic extraction only; no links, automatic enqueue or admission."""
    result = dict(resolved_acceptance_utc=None, historical_receipt_utc=None)
    if plan.kind == 'discovery':
        if re.search(br'<!\s*(DOCTYPE|ENTITY)', raw, re.I):
            raise AuditFailure('UNSAFE_XML')
        try:
            root = ET.fromstring(raw)
        except ET.ParseError:
            raise AuditFailure('NATIVE_ATOM_INVALID') from None
        atom = '{http://www.w3.org/2005/Atom}'
        if root.tag != atom + 'feed':
            raise AuditFailure('NATIVE_ATOM_INVALID')
        entries = root.findall(atom + 'entry')
        if len(entries) > 100:
            raise AuditFailure('DISCOVERY_PAGE_LIMIT')
        result.update(entries=len(entries), updated_native=[x.text for x in root.iter(atom + 'updated')],
                      publication_native=[x.text for x in root.iter(atom + 'published')])
    elif plan.kind == 'submissions':
        value = strict_json(raw)
        if str(value.get('cik')).zfill(10) != plan.cik:
            raise AuditFailure('SEC_CIK_MISMATCH')
        recent = value['filings']['recent']
        ids = recent['accessionNumber']
        if ids.count('0000950170-25-067613') != 1:
            raise AuditFailure('TARGET_ORIGINAL_UNAVAILABLE')
        n = ids.index('0000950170-25-067613')
        if recent['form'][n] != '10-Q' or recent['primaryDocument'][n] != 'fmbh-20250331.htm':
            raise AuditFailure('TARGET_ORIGINAL_MISMATCH')
        for field in ('form', 'primaryDocument', 'filingDate', 'reportDate'):
            result[field] = recent[field][n]
        result['acceptance_native'] = recent['acceptanceDateTime'][n]
        result['acceptance_semantics'] = 'Native string only; no cross-source resolution'
    elif plan.kind == 'accession_index':
        parser = TextOnly()
        parser.feed(raw.decode('utf-8', errors='strict'))
        parts = [p for p in parser.parts if p]
        for field in ('Accepted', 'Filing Date', 'Period of Report'):
            positions = [i for i, p in enumerate(parts[:-1]) if p == field]
            result[field] = [parts[i + 1] for i in positions]
        result['indexed_primary_sizes_native'] = [parts[i + 2] for i, p in enumerate(parts[:-2])
            if p == 'fmbh-20250331.htm']
    elif plan.kind == 'submission':
        header = raw.split(b'<DOCUMENT>', 1)[0]
        result['acceptance_native'] = [m.decode('ascii') for m in
            re.findall(br'<ACCEPTANCE-DATETIME>([0-9]+)', header)]
        result['acceptance_timezone'] = None
        result['embedded_primary'] = []
        for document in raw.split(b'<DOCUMENT>')[1:]:
            before, sep, body = document.partition(b'<TEXT>')
            if sep and re.search(br'<FILENAME>fmbh-20250331\.htm\s', before):
                body, end, _ = body.partition(b'</TEXT>')
                if not end:
                    raise AuditFailure('EMBEDDED_PRIMARY_INCOMPLETE')
                result['embedded_primary'].append(dict(bytes=len(body), sha256=digest(body),
                    semantics='Exact bytes between TEXT tags, including boundary newlines'))
    elif plan.kind == 'daily_index':
        rows = raw.decode('utf-8', errors='strict').splitlines()
        result['target_rows_native'] = [row for row in rows if
            '0000950170-25-067613' in row or '000095017025067613' in row]
    else:
        result['opaque_primary'] = True
    return result


class Qualification(OfflinePreserver):
    def __init__(self, root, *, authorization_ref, opener=None, timer=time.monotonic,
                 sleep=time.sleep, limits=CAPS):
        if (not authorization_ref or any(v > asdict(CAPS)[k] for k, v in asdict(limits).items())):
            raise AuditFailure('G4_AUTHORITY_OR_CAP_CONFLICT')
        self.plans = six_plans()
        self.by_url = {p.url: p for p in self.plans}
        self.mode = 'BOUNDED_REAL_SOURCE_QUALIFICATION' if opener is None else 'SYNTHETIC_OFFLINE'
        if opener is None and authorization_ref != AUTHORITY:
            raise AuditFailure('G4_AUTHORITY_MISMATCH')
        self.timer, self.sleep = timer, sleep
        self.started = timer()
        self.session = uuid.uuid4().hex
        self.last_end = self.started - 2
        self.trace, self.current_response = {}, None
        self.storage_samples = []
        self.opener = opener or build_opener(NoRedirect())
        self.root = Path(root)
        self.root.mkdir(parents=True, exist_ok=True)
        self._disk()
        super().__init__(root, transport=self._http, clock=self._clock, limits=limits)
        try:
            if self.store.records('g4.binding'):
                raise AuditFailure('G4_ONE_SHOT_ALREADY_USED')
            self.store.append('g4.binding', 'issue40', dict(mode=self.mode, authority=authorization_ref,
                plans=[asdict(p) for p in self.plans], limits=asdict(limits), adapter_sha256=digest(Path(__file__).read_bytes()),
                user_agent=USER_AGENT, deadline_seconds=900, disk_reserve=DISK_RESERVE,
                session=self.session, clock_offset_seconds=None, clock_uncertainty_seconds=None,
                engine_binding_semantics='Inherited offline engine/limits hash; actual mode is this G4 binding'))
            self._footprint()
        except BaseException:
            self.close()
            raise

    def _clock(self):
        return ClockSample(datetime.now(timezone.utc).isoformat(), time.monotonic_ns(),
                           self.session, None, None)

    def _uri(self, uri):
        if uri not in self.by_url:
            raise AuditFailure('G4_URL_OUTSIDE_MANIFEST')

    def _append(self, kind, key, metadata, raw=None):
        if len(canonical(metadata)) > 65536 or len(self.store.records()) >= self.limits.max_records:
            raise AuditFailure('RECORD_BUDGET_EXHAUSTED')
        record = self.store.append_in_transaction('preservation.' + kind, key,
            dict(metadata, mode=self.mode, code_hash=self.code_hash, config_hash=self._control()['binding'],
                 rights_reference='SEC public diagnostic; no general redistribution/retention grant inferred'), raw)
        self._footprint()
        return record

    def _footprint(self):
        files = {}
        for p in self.root.rglob('*'):
            if p.is_file():
                s = p.stat()
                files[str(p.relative_to(self.root))] = dict(apparent=s.st_size,
                    allocated=s.st_blocks * 512 if hasattr(s, 'st_blocks') else None)
        self.storage_samples.append(files)
        return files

    def _disk(self):
        # Emergency reserve plus conservative two-object/spool/backup allowance.
        if shutil.disk_usage(self.root).free < DISK_RESERVE + 4 * 40_000_000 + 20_000_000:
            raise AuditFailure('G4_DISK_RESERVE_INSUFFICIENT')

    def _time_left(self):
        left = 900 - (self.timer() - self.started)
        if left <= 0:
            raise AuditFailure('G4_DEADLINE')
        return left

    def _http(self, url, limit):
        self._uri(url)
        self._disk()
        timeout = min(20, self._time_left())
        request = Request(url, headers={'User-Agent': USER_AGENT, 'Accept-Encoding': 'identity'}, method='GET')
        self.trace = dict(request_headers=dict(request.header_items()), headers_all=[], framing=None)
        try:
            response = self.opener.open(request, timeout=timeout)
        except HTTPError as error:
            response = error
        self.current_response = response
        self.trace['headers_all'] = list(response.headers.items())
        self.trace['http_header_sample'] = asdict(self._clock())
        headers = {k.lower(): v for k, v in response.headers.items()}
        counts = [k.lower() for k, _ in self.trace['headers_all']]
        length, transfer, encoding = headers.get('content-length'), headers.get('transfer-encoding'), headers.get('content-encoding')
        self.trace['framing'] = 'chunked' if transfer else ('content-length' if length is not None else 'close-delimited')
        def chunks():
            received = 0
            problem = None
            if (counts.count('content-length') > 1 or counts.count('transfer-encoding') > 1
                    or (length is not None and (not re.fullmatch(r'[0-9]+', length) or transfer))
                    or transfer not in (None, 'chunked') or encoding not in (None, 'identity')):
                problem = 'G4_UNPRESERVABLE_ENCODING_OR_FRAMING'
            while received < limit:
                self._time_left()
                self._disk()
                try:
                    chunk = response.read1(min(65536, limit - received))
                except http.client.IncompleteRead as exc:
                    if exc.partial:
                        received += len(exc.partial)
                        yield exc.partial
                    raise AuditFailure('PARTIAL_BODY') from None
                except http.client.HTTPException:
                    raise AuditFailure('PARTIAL_BODY') from None
                if not chunk:
                    if problem:
                        raise AuditFailure(problem)
                    if length is not None and received != int(length):
                        raise AuditFailure('PARTIAL_BODY')
                    return
                received += len(chunk)
                yield chunk
            raise AuditFailure('RESPONSE_TOO_LARGE')
        return Response(response.status, headers, chunks())

    def _receive(self, job, started):
        self.trace = {}
        try:
            raw, meta = super()._receive(job, started)
            meta.update(self.trace, transport_encoding='Exact HTTP entity bytes; transfer framing removed, no content decoding')
            if meta['failure'] is None:
                try:
                    self._time_left()
                except AuditFailure:
                    meta.update(failure='G4_DEADLINE', body_completed=None, document_receipt=None)
            return raw, meta
        finally:
            if self.current_response is not None:
                self.current_response.close()
                self.current_response = None

    def fetch(self, plan):
        self._ready()
        validate_plan(plan)
        if plan not in self.plans:
            raise AuditFailure('G4_JOB_OUTSIDE_MANIFEST')
        try:
            job_id = self.enqueue(plan.url, plan.role, plan.kind)
            while True:
                job = next(j for j in self.jobs() if j['job_id'] == job_id)
                if job['state'] == 'COMPLETE':
                    return self.store.get(job['observation'])
                if job['state'] != 'PENDING':
                    raise AuditFailure('G4_JOB_FAILED')
                pause = max(0, self.last_end + 2 - self.timer())
                if pause:
                    if pause >= self._time_left():
                        raise AuditFailure('G4_DEADLINE')
                    self.sleep(pause)
                self._time_left()
                self._disk()
                record = self.run_one()
                if record is None:
                    raise AuditFailure('G4_UNEXPECTED_QUEUE_STATE')
                self.last_end = self.timer()
                self.store.verify()
                meta = record['metadata']
                status, failure = meta['http_status'], meta['failure']
                if status == 403:
                    return record  # inherited durable halt already prevents every later fetch
                if failure is None:
                    return record
                if failure not in {'TRANSPORT_ERROR', 'HTTP_429', 'HTTP_500', 'HTTP_502', 'HTTP_503', 'HTTP_504'}:
                    self._halt(failure)
                    return record
                value = meta['headers'].get('retry-after')
                delay = 2 ** (meta['attempt'] - 1)
                if value is not None:
                    try:
                        delay = max(delay, int(value) if value.isdigit() else
                            (parsedate_to_datetime(value) - datetime.now(timezone.utc)).total_seconds())
                        if delay > 900 or delay < 0:
                            raise ValueError
                    except (ValueError, TypeError, OverflowError):
                        self._halt('RETRY_AFTER_UNSUPPORTED')
                        return record
                if job['attempts'] + 1 >= self.limits.max_attempts:
                    self._halt('G4_RETRIES_EXHAUSTED')
                    return record
                # The engine's UTC not_before and this global pause must both expire.
                if delay + 2 >= self._time_left():
                    self._halt('G4_DEADLINE')
                    return record
                self.sleep(delay + 2)
        except BaseException:
            self._broken = self._broken or 'G4_STOPPED'
            raise

    def summary(self):
        result = super().summary()
        result.update(mode=self.mode, elapsed_seconds=self.timer() - self.started,
                      storage_samples=self.storage_samples, disk_free_bytes=shutil.disk_usage(self.root).free,
                      backup_measured=False, external_spend_usd=0)
        return result

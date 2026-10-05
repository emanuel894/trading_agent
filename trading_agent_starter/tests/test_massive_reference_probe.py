"""Mocked GET responses: no real API key, identity screening, or network."""
from copy import deepcopy
import io
import json
from pathlib import Path
import tempfile
import unittest
from unittest.mock import patch
from urllib.error import HTTPError, URLError
from urllib.parse import parse_qs, urlsplit

from agent import massive_reference_probe as probe
from agent.audit_store import AuditFailure, EvidenceStore, canonical


KEY = 'synthetic-secret-never-persist'


class Response(io.BytesIO):
    status = 200


class Opener:
    def __init__(self, responses):
        self.responses, self.calls = list(responses), []

    def open(self, req, timeout):
        self.calls.append(req)
        value = self.responses.pop(0)
        if isinstance(value, Exception):
            raise value
        return Response(value if isinstance(value, bytes) else canonical(value))


class ReferenceProbeTests(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.store = EvidenceStore(self.tmp.name)
        self.addCleanup(self.tmp.cleanup)
        self.addCleanup(self.store.close)
        self.body = {'status':'OK','request_id':'synthetic-request', 'results':[
            {**probe.EXPECTED, 'share_class_figi':'SYNTHETIC-CLASS', 'last_updated_utc':'2026-09-01T00:00:00Z'}]}

    def run_responses(self, values):
        self.opener = Opener(values)
        self.http = probe.ReferenceHTTP(self.store, KEY, opener=self.opener, sleep=lambda _:None)
        return probe.run_probe(self.http, self.store)

    def test_four_gets_exact_contract_and_immutable_provenance(self):
        result = self.run_responses([self.body]*4)
        self.assertEqual(result['status'],'PASS')
        self.assertEqual(result['eligibility_decision'],'UNRESOLVED')
        self.assertFalse(result['ledger_modified'])
        self.assertEqual(result['requests_made'],4)
        self.assertEqual(result['store_verification']['status'],'VERIFIED')
        for day, req in zip(probe.registration()['pilot']['dates'], self.opener.calls):
            self.assertEqual(req.get_method(),'GET')
            self.assertEqual(req.get_header('Authorization'),'Bearer '+KEY)
            self.assertEqual(urlsplit(req.full_url).hostname,'api.massive.com')
            self.assertEqual(urlsplit(req.full_url).path,'/v3/reference/tickers')
            self.assertEqual(parse_qs(urlsplit(req.full_url).query),
                {'ticker':['FMBH'],'market':['stocks'],'active':['true'],'limit':['10'],'date':[day]})
        with self.assertRaisesRegex(AuditFailure,'BUDGET_OR_ORDER'):
            self.http.get('2025-05-09')
        self.assertEqual(len(self.opener.calls),4)
        for r in self.store.records('massive_reference_http'):
            self.assertEqual(self.store.raw(r), canonical(self.body))
            self.assertIsNone(r['metadata']['source_times']['known_at'])
        for p in Path(self.tmp.name).rglob('*'):
            if p.is_file(): self.assertNotIn(KEY.encode(),p.read_bytes())

    def test_stop_pagination_ambiguity_missing_and_identifier_disagreement(self):
        cases=[]
        b=deepcopy(self.body); b['next_url']='https://api.massive.com/next'; cases.append((b,'UNEXPECTED_PAGINATION'))
        b=deepcopy(self.body); b['results']*=2; cases.append((b,'AMBIGUOUS_MULTIPLE_ROWS'))
        b=deepcopy(self.body); b['results']=[]; cases.append((b,'MISSING_RESULT'))
        for field in probe.EXPECTED:
            b=deepcopy(self.body); b['results'][0][field]='wrong'; cases.append((b,'IDENTIFIER_DISAGREEMENT:'+field))
        for body, reason in cases:
            with self.subTest(reason=reason):
                r=self.run_responses([body])
                self.assertEqual(r['stop_reason'],reason)
                self.assertEqual(r['requests_made'],1)
                self.assertEqual(r['dates'][0]['access'],'HTTP_200')
                self.assertEqual(len(r['unrequested_dates']),3)

    def test_optional_missing_fields_are_not_invented(self):
        b=deepcopy(self.body); del b['results'][0]['share_class_figi']; del b['results'][0]['last_updated_utc']
        r=self.run_responses([b]*4)
        self.assertEqual(r['status'],'PASS')
        self.assertEqual(r['dates'][0]['missing_fields'],['share_class_figi','last_updated_utc'])
        self.assertNotIn('share_class_figi',r['dates'][0]['fields'])

    def test_missing_required_field_stops_and_remains_missing(self):
        b=deepcopy(self.body); del b['results'][0]['cik']
        r=self.run_responses([b])
        self.assertEqual(r['stop_reason'],'MISSING_IDENTITY_FIELD:cik')
        self.assertIn('cik',r['dates'][0]['missing_fields'])

    def test_figi_change_stops_without_deciding_ineligibility(self):
        b=deepcopy(self.body); b['results'][0]['share_class_figi']='ANOTHER-CLASS'
        r=self.run_responses([self.body,b])
        self.assertEqual(r['requests_made'],2)
        self.assertEqual(r['stop_reason'],'IDENTIFIER_DISAGREEMENT:share_class_figi')
        self.assertEqual(r['eligibility_decision'],'UNRESOLVED')

    def test_access_errors_no_retry_or_redirect_following(self):
        for code, reason in [(401,'AUTH_OR_ACCESS_REJECTED'),(403,'AUTH_OR_ACCESS_REJECTED'),
                             (429,'RATE_LIMITED'),(302,'REDIRECT_REJECTED'),(500,'PROVIDER_HTTP_FAILURE')]:
            error=HTTPError('https://api.massive.com',code,'ignored secret '+KEY,{},io.BytesIO(b'{"error":"rejected"}'))
            r=self.run_responses([error])
            self.assertEqual(r['stop_reason'],reason)
            self.assertEqual(r['requests_made'],1)
        self.assertIsNone(probe.NoRedirect().redirect_request(None,None,302,'',{},'https://other.test'))

    def test_malformed_network_and_byte_limit_fail_closed(self):
        for b, reason in [(b'{broken','MALFORMED_JSON'),(URLError(KEY),'NETWORK_READ_FAILED'),
                          (b'X'*262145,'RESPONSE_BYTE_LIMIT')]:
            r=self.run_responses([b]); self.assertEqual(r['stop_reason'],reason)
            self.assertEqual(r['requests_made'],1)
            self.assertNotIn(KEY,canonical(r).decode())

    def test_secret_echo_is_not_persisted_even_json_escaped(self):
        for raw in (canonical({'request_id':KEY}),
                    ('{"request_id":"'+''.join('\\u%04x'%ord(c) for c in KEY)+'"}').encode()):
            r=self.run_responses([raw]); self.assertEqual(r['stop_reason'],'SECRET_ECHO_BLOCKED')
        for p in Path(self.tmp.name).rglob('*'):
            if p.is_file(): self.assertNotIn(KEY.encode(),p.read_bytes())

    def test_credentials_env_and_local_file_no_interpolation(self):
        with patch.dict('os.environ',{},clear=True), patch.object(probe,'dotenv_values',return_value={'MASSIVE_API_KEY':KEY}) as read:
            self.assertEqual(probe.credentials_from_env(),KEY)
            self.assertFalse(read.call_args.kwargs['interpolate'])
        with patch.dict('os.environ',{},clear=True), patch.object(probe,'dotenv_values',return_value={}):
            with self.assertRaisesRegex(AuditFailure,'UNAVAILABLE'): probe.credentials_from_env()
        with patch.dict('os.environ',{'MASSIVE_API_KEY':KEY},clear=True), patch.object(probe,'dotenv_values',return_value={}):
            self.assertEqual(probe.credentials_from_env(),KEY)

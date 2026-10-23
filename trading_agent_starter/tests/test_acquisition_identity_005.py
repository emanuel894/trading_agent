"""Synthetic source reviews only; never fetch data or alter candidate decisions."""
from copy import deepcopy
from pathlib import Path
import tempfile
import unittest

from agent import acquisition_identity as identity
from agent.acquisition_registration import PURPOSE
from agent.audit_store import AuditFailure, EvidenceStore, canonical, digest


class Identity005Tests(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.store = EvidenceStore(self.tmp.name)
        self.addCleanup(self.tmp.cleanup)
        self.addCleanup(self.store.close)
        self.times = {k: None for k in identity.CLOCK_KEYS}
        self.retrieved = "2026-10-05T12:00:00Z"
        self.raw = b'Synthetic issuer 9000000001 class A historical ticker TEST on 2025-05-01'
        self.source_meta = {"source_times": self.times, "retrieved_at": self.retrieved,
                            "historical_state_semantics": "historical_valid_state",
                            "valid_time": {"resolution": "date", "date": "2025-05-01"}}
        self.ref = self.capture(self.raw, self.source_meta)
        self.docs = self.capture(b'Synthetic provider defines historical valid state for historical_ticker',
                                {"historical_state_semantics":"historical_valid_state",
                                 "field_scope":["historical_ticker"],"resolution":"date"})
        self.review = self.capture(b'Synthetic reviewer binds historical ticker and confirms full class lineage')
        self.e = {"cik": "9000000001", "research_id": "research:synthetic:A",
                  "field": "historical_ticker", "value": "TEST", "source_record": self.ref,
                  "source_times": deepcopy(self.times), "retrieved_at": self.retrieved,
                  "semantics": {"kind": "historical_valid_state", "field_scope": ["historical_ticker"],
                                "documentation": self.docs}, "review_record": self.review,
                  "reviewer": "synthetic", "rationale": "Synthetic bounded source review",
                  "lineage_complete": True, "class_set_complete": True, "transitions_resolved": True,
                  "valid_time": {"resolution": "date", "date": "2025-05-01"}}
        self.req = {k: self.e[k] for k in ("cik", "research_id", "field")}
        self.req.update(resolution="date", date="2025-05-01")

    def capture(self, raw, metadata=None):
        record = self.store.append("synthetic", digest(raw), metadata or {}, raw)
        return {"record_id": record["id"], "sha256": digest(raw), "span": raw.decode()}

    def validate(self, e=None, req=None, **kw):
        return identity.validate_structural(e or self.e, req or self.req, self.store, purpose=PURPOSE, **kw)

    def test_later_retrieval_and_unknown_knowledge_pass_structural_only(self):
        before = canonical(self.e)
        result = self.validate()
        self.assertEqual(result["status"], "PASS")
        self.assertIsNone(result["eligibility_decision"])
        self.assertEqual(canonical(self.e), before)
        self.assertIsNone(self.e["source_times"]["known_at"])

    def test_current_only_and_later_sec_retrofill_are_rejected(self):
        for kind in ("current_only", "sec_period_date_retrofill", "historical_date_parameter"):
            e = deepcopy(self.e); e["semantics"]["kind"] = kind
            self.assertEqual(self.validate(e)["status"], "UNRESOLVED")

    def test_current_or_sec_retrofill_cannot_be_relabelled_by_caller(self):
        for kind in ('current_only', 'sec_period_date_retrofill'):
            e=deepcopy(self.e)
            e['source_record']=self.capture(self.raw+kind.encode(),
                {**self.source_meta, 'historical_state_semantics':kind})
            self.assertEqual(self.validate(e)['status'],'UNRESOLVED')

    def test_semantics_must_cover_field_and_grounded_document(self):
        e = deepcopy(self.e); e["semantics"]["field_scope"] = ["issuer_identity"]
        self.assertEqual(self.validate(e)["status"], "UNRESOLVED")
        e = deepcopy(self.e); e["semantics"]["documentation"]["span"] = "Invented words"
        self.assertEqual(self.validate(e)["status"], "UNRESOLVED")

    def test_date_only_cannot_prove_intraday_or_midnight(self):
        for at in ("2025-05-01T00:00:00-04:00", "2025-05-01T10:03:00-04:00"):
            req = {**self.req, "resolution": "instant", "at": at}
            self.assertEqual(self.validate(req=req)["reason"], "EXACT_INSTANT_CORROBORATION_UNRESOLVED")

    def test_independent_exact_corroboration_required(self):
        req = {**self.req, "resolution": "instant", "at": "2025-05-01T10:03:00-04:00"}
        c = deepcopy(self.e)
        interval = self.capture(b'Synthetic independent exact validity 2025-05-01T13:00:00Z through 15:00:00Z')
        c['valid_time'] = {"resolution": "interval", "from": "2025-05-01T13:00:00Z",
                           "to": "2025-05-01T15:00:00Z", "interval_evidence": interval}
        self.assertEqual(self.validate(req=req, corroboration=c)["status"], "UNRESOLVED")
        c['source_record'] = self.capture(b'Synthetic independent interval source',
                                         {**self.source_meta, 'valid_time':c['valid_time']})
        c['semantics']['documentation'] = self.capture(b'Synthetic exact-time historical source semantics',
             {"historical_state_semantics":"historical_valid_state", "field_scope":["historical_ticker"],"resolution":"interval"})
        self.assertEqual(self.validate(req=req, corroboration=c)["status"], "PASS")
        c['value'] = 'OTHER'
        self.assertEqual(self.validate(req=req, corroboration=c)["status"], "UNRESOLVED")

    def test_missing_lineage_class_set_or_transitions_block(self):
        for field in ('lineage_complete', 'class_set_complete', 'transitions_resolved'):
            e = deepcopy(self.e); e[field] = None
            self.assertEqual(self.validate(e)["status"], "UNRESOLVED")

    def test_no_parent_ticker_substitution(self):
        e = deepcopy(self.e); e['cik'] = '9000000002'
        self.assertEqual(self.validate(e)["status"], "FAIL")

    def test_revision_metadata_cannot_be_dropped_or_query_time_fabricated(self):
        e = deepcopy(self.e)
        e['source_times']['revised_at'] = '2026-09-01T12:00:00Z'
        e['source_record'] = self.capture(self.raw+b' revised', {**self.source_meta,
                                                               'source_times':deepcopy(e['source_times'])})
        self.assertEqual(self.validate(e)['status'], 'PASS')
        e['source_times']['revised_at'] = None
        self.assertEqual(self.validate(e)['status'], 'FAIL')
        e = deepcopy(self.e); e['source_times']['known_at'] = '2025-05-01T00:00:00Z'
        self.assertEqual(self.validate(e)['status'], 'FAIL')

    def test_disclosures_features_and_all_excluded_fields_still_need_knowledge(self):
        for field in identity.registration()['excluded_fields']:
            e = deepcopy(self.e); e['field'] = field
            self.assertEqual(identity.validate_decision_time(e, '2025-05-09T14:03:00Z', self.store)['status'], 'UNRESOLVED')
            self.assertEqual(self.validate(e)['status'], 'UNRESOLVED')
        e['source_times']['known_at'] = '2025-05-09T14:04:00Z'
        e['source_times']['available_at'] = '2025-05-09T14:04:00Z'
        e['source_record'] = self.capture(self.raw+b' late disclosure', {'source_times':e['source_times'], 'retrieved_at':self.retrieved})
        self.assertEqual(identity.validate_decision_time(e, '2025-05-09T14:03:00Z', self.store)['status'], 'UNRESOLVED')
        self.assertEqual(identity.validate_decision_time(e, '2025-05-09T14:05:00Z', self.store)['status'], 'PASS')

    def test_no_economic_exception_and_protected_artifacts_unchanged(self):
        with self.assertRaisesRegex(AuditFailure, 'OUTSIDE_PURPOSE'):
            identity.validate_structural(self.e, self.req, self.store, purpose='ADR_TOP500')
        reg = identity.registration()
        for name, expected in reg['protected_sha256'].items():
            self.assertEqual(digest((identity.ROOT/name).read_bytes()), expected)
        with self.assertRaisesRegex(AuditFailure, 'REGISTRATION_CHANGED'):
            identity.registration(identity.REGISTRATION_PATH.read_bytes()+b' ')

import unittest
from agent.audit_store import AuditFailure
from agent.cohort_sources import identity_anchors


class IdentityAnchorTests(unittest.TestCase):
    def test_combined_filing_parent_symbol_does_not_bind_to_subsidiary(self):
        raw = b'''<xbrli:context id="parent"><xbrli:entity>
          <xbrli:identifier scheme="http://www.sec.gov/CIK">1126956</xbrli:identifier>
          </xbrli:entity></xbrli:context>
          <ix:nonNumeric name="dei:Security12bTitle" contextRef="parent">Common Stock</ix:nonNumeric>
          <ix:nonNumeric name="dei:TradingSymbol" contextRef="parent">SR</ix:nonNumeric>
          <ix:nonNumeric name="dei:SecurityExchangeName" contextRef="parent">NYSE</ix:nonNumeric>'''
        result = identity_anchors(raw, "0000003146")
        self.assertEqual(result["cover_groups"][0]["entity_cik"], "0001126956")
        self.assertFalse(result["cover_groups"][0]["target_entity_match"])
        self.assertFalse(result["listing_interval_proven"])

    def test_missing_context_stays_unresolved_and_conflicting_entity_fails(self):
        raw = b'<ix:nonNumeric name="dei:Security12bTitle" contextRef="unknown">Common</ix:nonNumeric>'
        self.assertEqual(identity_anchors(raw, "0000000001")["unresolved_contexts"], ["unknown"])
        raw = b'<context id="x"><identifier>1</identifier></context><context id="x"><identifier>2</identifier></context>'
        with self.assertRaisesRegex(AuditFailure, "CONFLICTING_CONTEXT_ENTITY"):
            identity_anchors(raw, "0000000001")

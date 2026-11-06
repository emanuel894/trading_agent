"""Regression: credential fixtures must not discover a developer's .env."""
import unittest
from unittest.mock import patch


class TestSecretIsolation(unittest.TestCase):
    def test_credential_tests_do_not_discover_local_dotenv(self):
        from test_alpaca_paper import AlpacaConfigTests
        from test_evidence_audit import EntitlementProbeTests
        suite = unittest.TestSuite([
            unittest.defaultTestLoader.loadTestsFromTestCase(AlpacaConfigTests),
            EntitlementProbeTests('test_missing_credentials_never_makes_http_request'),
        ])
        # Fail before opening any file or socket; no real credentials are read.
        with patch('dotenv.main.find_dotenv', side_effect=AssertionError('DOTENV_DISCOVERY_FORBIDDEN')), \
             patch('socket.create_connection', side_effect=AssertionError('NETWORK_FORBIDDEN')):
            result = unittest.TestResult()
            suite.run(result)
        self.assertEqual(len(result.errors), 0, 'Credential fixtures attempted dotenv discovery')
        self.assertEqual(len(result.failures), 0, 'Credential fixture failed without local dotenv')

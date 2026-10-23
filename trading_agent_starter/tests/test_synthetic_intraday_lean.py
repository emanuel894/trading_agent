"""New integration only; never launches accepted LEAN qualification cases."""
import copy
import hashlib
import json
from pathlib import Path
import subprocess
import sys
from dataclasses import replace
from datetime import timedelta
import unittest
from research.lean_intraday_integration_20261023 import integration as m


class SyntheticIntradayTests(unittest.TestCase):
    def test_retained_new_native_pairs_and_accounting(self):
        root=Path(m.__file__).parent
        for name,digest in json.loads((root/'evidence-sha256.json').read_text()).items():
            self.assertEqual(hashlib.sha256((root/name).read_bytes()).hexdigest(),digest)
        evidence=root/'evidence/accepted'
        receipt=json.loads((evidence/'receipt.json').read_text())
        self.assertEqual(receipt['status'],'SYNTHETIC_INTRADAY_INTEGRATION_PASS')
        self.assertEqual(len(receipt['attempts']),8)
        for name,inputs in m.scenarios().items():
            paths=[evidence/'outputs'/f'INTRADAY_{name}-{repeat}.json' for repeat in (1,2)]
            self.assertEqual(paths[0].read_bytes(),paths[1].read_bytes())
            m.check_native(json.loads(paths[0].read_text()),m.decide(*inputs)['signal'])

    def test_optimized_runner_rejected_before_runtime_access(self):
        result = subprocess.run([sys.executable,'-O','-m',
                                 'research.lean_intraday_integration_20261023.run'],
                                capture_output=True,text=True)
        self.assertNotEqual(result.returncode,0)
        self.assertIn('Assertions must be enabled',result.stderr)
        self.assertNotIn('FileNotFoundError',result.stderr)

    def test_input_order_does_not_change_signal(self):
        sessions, bars, releases = m.fixture()
        self.assertEqual(m.decide(sessions,bars,releases),
                         m.decide(sessions,tuple(reversed(bars)),tuple(reversed(releases))))

    def test_hand_computable_feature_to_intent(self):
        sessions, bars, releases = m.fixture()
        decision = m.decide(sessions, bars, releases)
        self.assertEqual(decision['sma_3'], 102)
        self.assertEqual(decision['sma_5'], 101.2)
        self.assertEqual(decision['rate_change_pp'], '-0.25')
        self.assertTrue(decision['signal'])
        case = m.native_case('baseline', decision)
        self.assertEqual(case['steps'][0]['qty'], '9')
        self.assertEqual(case['start_ns'], 1736175600000000000)

    def test_future_revision_does_not_change_frozen_decision(self):
        sessions, bars, releases = m.fixture()
        original = m.decide(sessions, bars, releases)
        revised_bar = replace(bars[-1], evidence_id='synthetic:minute:5:r2',
                              close=10000, high=10001, previous_version=bars[-1].evidence_id,
                              clocks=m.clocks(m.CUTOFF + timedelta(seconds=1), revised=True))
        revised_release = replace(releases[-1], evidence_id='synthetic:release:B:r2',
                                  text='Target range: 9.00 to 9.25 percent.',
                                  previous_version=releases[-1].evidence_id,
                                  clocks=m.clocks(m.CUTOFF + timedelta(seconds=1), revised=True))
        self.assertEqual(original, m.decide(sessions, bars+(revised_bar,), releases+(revised_release,)))

    def test_missing_bar_abstains_without_forward_fill(self):
        sessions, bars, releases = m.fixture()
        d = m.decide(sessions, bars[:-1], releases)
        self.assertFalse(d['signal'])
        self.assertIsNone(d['sma_3'])
        self.assertFalse(any(s['op']=='order' for s in m.native_case('gap', d)['steps']))

    def test_verified_at_cutoff_and_unknown_receipt_abstain(self):
        sessions, bars, releases = m.fixture()
        for c in (replace(releases[-1].clocks, verified=m.CUTOFF),
                  replace(releases[-1].clocks, received=None)):
            d = m.decide(sessions, bars, releases[:-1]+(replace(releases[-1],clocks=c),))
            self.assertFalse(d['signal'])
            self.assertIsNone(d['rate_change_pp'])

    def test_future_bar_cannot_supply_feature(self):
        sessions, bars, releases = m.fixture()
        later = m.CUTOFF + timedelta(minutes=1)
        future = replace(bars[-1], evidence_id='synthetic:future', end=later,
                         close=9999,high=10000,clocks=m.clocks(later))
        self.assertEqual(m.decide(sessions,bars,releases),
                         m.decide(sessions+(later,),bars+(future,),releases))

    def test_native_accounting_oracle_rejects_omitted_costs(self):
        output = {'case_complete':True,'execution_complete':True,'provider_calls':0,
                  'network_denied':{'non_loopback_interfaces':0,'testnet_socket_result':'NetworkUnreachable'},
                  'native':{'gate_calls':1,'open_orders':0,'quantities':{'I1':'9'},'cash':'9098.36991'},
                  'business':{'fills':[{'quantity':'9','price':'100.07001','fee':'1'}],
                              'decisions':[{'allowed':True}]}}
        m.check_native(output, True)
        for path,value in (('price','100.02'),('fee','0'),('quantity','10')):
            altered=copy.deepcopy(output);altered['business']['fills'][0][path]=value
            with self.assertRaises(AssertionError):m.check_native(altered,True)
        altered=copy.deepcopy(output);altered['provider_calls']=1
        with self.assertRaises(AssertionError):m.check_native(altered,True)

    def test_zero_order_oracle_rejects_unexpected_execution(self):
        output={'case_complete':True,'execution_complete':True,'provider_calls':0,
                'network_denied':{'non_loopback_interfaces':0,'testnet_socket_result':'NetworkUnreachable'},
                'native':{'gate_calls':0,'open_orders':0,'quantities':{'I1':'0'},'cash':'10000'},
                'business':{'fills':[],'decisions':[]}}
        m.check_native(output,False)
        output['native']['gate_calls']=1
        with self.assertRaises(AssertionError):m.check_native(output,False)

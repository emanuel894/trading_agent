import hashlib
import json
from pathlib import Path
import tempfile
import unittest
from urllib.parse import urlencode
from agent.audit_store import EvidenceStore
from research.sip_lean_bridge_20261024 import bridge as b

START='2025-01-15T15:00:00Z'
END='2025-01-15T15:05:00Z'


def store_fixture(root, *, end_token=None, quote_change=None, other_only_first_page=False, cycle=False):
    store=EvidenceStore(root)
    bar={'t':START,'o':100,'h':101,'l':99,'c':100,'v':100}
    incomplete={**bar,'t':END}
    quote={'t':'2025-01-15T15:00:00.123456789Z','bp':100,'ap':100.02,
           'bs':2,'as':3,'c':['R'],'z':'B','bx':'P','ax':'P'}
    if quote_change:quote.update(quote_change)
    for kind,payload in [('bars',{'bars':{'SPY':[bar,incomplete]},'next_page_token':None}),
                         ('quotes',{'quotes':{'SPY':[quote,quote]},'next_page_token':end_token})]:
        params={'feed':'sip','asof':'-','sort':'asc','start':START,'end':END}
        if kind=='bars':params.update(timeframe='1Min',adjustment='raw')
        if kind=='quotes' and cycle:
            for current,nxt in ((None,'A'),('A','B'),('B','A')):
                qp=dict(params)
                if current is not None:qp['page_token']=current
                store.append('http','https://data.alpaca.markets/v2/stocks/quotes?'+urlencode(qp),
                             {'http_status':200},raw=json.dumps({'quotes':{'SPY':[quote]},'next_page_token':nxt}).encode())
            params['page_token']='A'
        if kind=='quotes' and other_only_first_page:
            store.append('http','https://data.alpaca.markets/v2/stocks/quotes?'+urlencode(params),
                         {'http_status':200},raw=json.dumps({'quotes':{'AAPL':[quote]},'next_page_token':'continue'}).encode())
            params['page_token']='continue'
        store.append('http','https://data.alpaca.markets/v2/stocks/'+kind+'?'+urlencode(params),
                     {'http_status':200,'received_at':'2026-09-15T12:00:00Z'},
                     raw=json.dumps(payload).encode())
    store.close()
    return hashlib.sha256((Path(root)/'evidence.sqlite').read_bytes()).hexdigest()


class SIPLeanBridgeTests(unittest.TestCase):
    def test_cyclic_page_chain_fails_closed(self):
        with tempfile.TemporaryDirectory() as d:
            h=store_fixture(d,cycle=True)
            with self.assertRaises(b.BridgeBlocked):b.project(d,expected_sha=h)

    def test_other_symbol_only_first_page_does_not_truncate_spy(self):
        with tempfile.TemporaryDirectory() as d:
            h=store_fixture(d,other_only_first_page=True)
            self.assertEqual(len(b.project(d,expected_sha=h)['quotes']),1)

    def test_missing_store_does_not_initialize_database(self):
        with tempfile.TemporaryDirectory() as d:
            p=Path(d)/'missing'
            with self.assertRaises(b.BridgeBlocked):b.project(p)
            self.assertFalse(p.exists())

    def test_projection_is_deterministic_preserves_precision_and_unknowns(self):
        with tempfile.TemporaryDirectory() as d:
            h=store_fixture(d);first=b.project(d,expected_sha=h)
            self.assertEqual(b.encode(first),b.encode(b.project(d,expected_sha=h)))
            self.assertEqual(len(first['bars']),1)
            self.assertEqual(len(first['quotes']),1)
            q=first['quotes'][0]
            self.assertEqual(q['source_ns'],1736953200123456789)
            self.assertIsNone(q['historical_received_at'])
            self.assertEqual(first['status'],'UNQUALIFIED')
            self.assertEqual(first['quote_size_units'],'UNQUALIFIED_PROVIDER_NATIVE')
            self.assertEqual(first['duplicate_quotes'],1)
            self.assertEqual(h,hashlib.sha256((Path(d)/'evidence.sqlite').read_bytes()).hexdigest())
            self.assertEqual(b.ceil_ns(q['source_ns']),1736953200123456800)

    def test_missing_or_tampered_object_blocks(self):
        for missing in (True,False):
            with tempfile.TemporaryDirectory() as d:
                h=store_fixture(d);p=next((Path(d)/'objects').iterdir())
                if missing:p.unlink()
                else:p.write_bytes(b'changed')
                with self.assertRaises(b.BridgeBlocked):b.project(d,expected_sha=h)

    def test_database_identity_and_empty_page_chain_block(self):
        with tempfile.TemporaryDirectory() as d:
            h=store_fixture(d,end_token='missing-page')
            with self.assertRaises(b.BridgeBlocked):b.project(d,expected_sha='0'*64)
            with self.assertRaises(b.BridgeBlocked):b.project(d,expected_sha=h)

    def test_invalid_quote_is_recorded_as_rejection_not_execution(self):
        with tempfile.TemporaryDirectory() as d:
            h=store_fixture(d,quote_change={'bp':100.02})
            p=b.project(d,expected_sha=h)
            self.assertEqual(p['quotes'],[])
            self.assertEqual(p['rejections']['LOCKED_OR_CROSSED_QUOTE'],2)

    def test_observation_only_preserves_ties_without_choosing_a_state(self):
        rows=[{'source_ns':1,'bid':'1'},{'source_ns':1,'bid':'2'}]
        output,_=b.unique_rows(rows,observation_only=True)
        self.assertEqual(len(output),2)
        self.assertTrue(all(r['same_time_variants']==2 for r in output))
        self.assertEqual(output,b.unique_rows(list(reversed(rows)),observation_only=True)[0])

    def test_ambiguous_rows_block(self):
        with tempfile.TemporaryDirectory() as d:
            h=store_fixture(d)
            # Pure reducer must never resolve conflicting same-nanosecond quotes by input order.
            with self.assertRaises(b.BridgeBlocked):
                b.unique_rows([{'source_ns':1,'bid':'1'},{'source_ns':1,'bid':'2'}])

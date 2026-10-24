from copy import deepcopy
from datetime import datetime, timezone
from zoneinfo import ZoneInfo
import unittest
from research.sip_lean_bridge_20261024.engine import prepare as p


def sample():
    return {'scope':'PRIVATE_OBSERVATION_COMPATIBILITY_ONLY','status':'UNQUALIFIED',
            'rights':'UNRESOLVED','orders_enabled':False,'historical_receipt_proven':False,
            'symbol':'SPY','provider':'alpaca','feed':'sip',
            'quote_size_units':'UNQUALIFIED_PROVIDER_NATIVE',
            'bars':[{'source_ns':p.ns('2025-01-15T15:00:00Z'),'open':'100','high':'101','low':'99','close':'100','volume':'7'}],
            'quotes':[{'source_ns':p.ns('2025-01-15T15:00:00.123456789Z'),'bid':'100','ask':'100.02','bid_size':'2','ask_size':'3','conditions':['R'],'tape':'B','bid_exchange':'P','ask_exchange':'P','same_time_variants':1}]}


def sessions():
    return [p.session('2025-01-15T14:30:00Z','2025-01-15T21:00:00Z','diagnostic-session')]


class EnginePreparationTests(unittest.TestCase):
    def test_bar_delivered_at_completion_and_quote_rounds_up(self):
        result=p.prepare(sample(),sessions())
        self.assertEqual(result['events'],2)
        self.assertEqual(result['batches'][0]['native_ns'],p.ns('2025-01-15T15:00:00.123456800Z'))
        self.assertEqual(result['batches'][1]['native_ns'],p.ns('2025-01-15T15:01:00Z'))
        self.assertFalse(result['batches'][0]['payload'][0]['execution_admitted'])
        self.assertIsNone(result['batches'][0]['payload'][0]['historical_received_at'])

    def test_source_ties_and_precision_collisions_are_atomic(self):
        source=sample();q=source['quotes'][0]
        source['quotes'] += [{**q,'bid':'99.99'},{**q,'source_ns':q['source_ns']+1}]
        r=p.prepare(source,sessions());self.assertEqual(len(r['batches'][0]['payload']),3)
        self.assertEqual(len({e['source_ns'] for e in r['batches'][0]['payload']}),2)
        self.assertEqual(r['batch_order'],'ATOMIC_NO_WITHIN_BATCH_EXECUTION_ORDER')

    def test_missing_session_and_unknown_executable_state_fail_closed(self):
        with self.assertRaises(p.PreparationBlocked):p.prepare(sample(),[])
        s=sample();s['status']='TRADABLE'
        with self.assertRaises(p.PreparationBlocked):p.prepare(s,sessions())

    def test_outside_session_and_future_bar_are_rejected_not_filled(self):
        s=sample();s['quotes'][0]['source_ns']=p.ns('2025-01-15T14:29:00Z')
        r=p.prepare(s,sessions());self.assertEqual(r['rejections'],{'OUTSIDE_SESSION':1})
        s=sample();s['bars'][0]['source_ns']=p.ns('2025-01-15T21:00:00Z')
        r=p.prepare(s,sessions());self.assertEqual(r['rejections'],{'OUTSIDE_SESSION':1})
        s=sample();s['bars'][0]['source_ns']=p.ns('2025-01-15T20:59:30Z')
        r=p.prepare(s,sessions());self.assertEqual(r['rejections'],{'INVALID_BAR':1})

    def test_dst_and_early_close_boundaries(self):
        ny=ZoneInfo('America/New_York')
        a=datetime(2025,3,7,9,30,tzinfo=ny).astimezone(timezone.utc)
        b=datetime(2025,3,10,9,30,tzinfo=ny).astimezone(timezone.utc)
        self.assertEqual((a.hour,b.hour),(14,13))
        s=sample();s['quotes']=[];s['bars'][0]['source_ns']=p.ns('2025-07-03T16:59:00Z')
        r=p.prepare(s,[p.session('2025-07-03T13:30:00Z','2025-07-03T17:00:00Z','synthetic-early-close')])
        self.assertEqual(r['events'],1);self.assertEqual(r['batches'][0]['native_ns'],p.ns('2025-07-03T17:00:00Z'))

    def test_gap_and_later_revision_cannot_rewrite_prior_preparation(self):
        s=sample();first=p.prepare(s,sessions());frozen=p.encode(first)
        later=deepcopy(s);later['bars'][0]['close']='100.5'
        self.assertNotEqual(frozen,p.encode(p.prepare(later,sessions())))
        self.assertEqual(frozen,p.encode(first))
        self.assertEqual(p.prepare({'bars':[],**{k:v for k,v in s.items() if k!='bars'}},sessions())['events'],1)

    def test_bad_quote_unknown_size_and_ordering_repeatability(self):
        s=sample();s['quotes'][0]['ask']='99'
        r=p.prepare(s,sessions());self.assertEqual(r['rejections'],{'INVALID_QUOTE':1})
        s=sample();a=p.prepare(s,sessions());b=p.prepare(s,sessions())
        self.assertEqual(p.encode(a),p.encode(b))
        self.assertEqual(a['execution_policy'],'DENY_ALL')

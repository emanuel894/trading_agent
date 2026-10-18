import copy,json,unittest
from pathlib import Path
import compare
ROOT=Path(__file__).parent
class ComparatorTests(unittest.TestCase):
 def test_contract_mutations_are_rejected(self):
  expected=json.loads((ROOT/'fixtures/Q07_first.expected.json').read_text())
  self.assertTrue(compare.compare_business(expected,expected))
  for key,value in [('cash','10000'),('quantity','0'),('admitted',False),('reason','STALE'),('native_order_statuses',['Filled','Submitted']),('decision_receipt_ns',0),('clock_mode','prospective')]:
   with self.subTest(key=key):
    bad=copy.deepcopy(expected);bad[key]=value
    with self.assertRaises(compare.GateMismatch):compare.compare_business(bad,expected)
  for key,value in [('event_ns',1736175601000000000),('available_ns',1736175601000000000),('dispatch_ns',1736175601000000001),('price','100.02'),('instrument','I2'),('quote_id','cheaper'),('fee','0')]:
   with self.subTest(fill_key=key):
    bad=copy.deepcopy(expected);bad['fill'][key]=value
    with self.assertRaises(compare.GateMismatch):compare.compare_business(bad,expected)
 def test_extra_missing_fields_rejected(self):
  for bad in [{'a':1,'extra':0},{}]:
   with self.assertRaises(compare.GateMismatch):compare.compare_business(bad,{'a':1})
if __name__=='__main__':unittest.main(verbosity=2)

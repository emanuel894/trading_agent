import copy,json,unittest,tempfile
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
class NativeComparatorTests(unittest.TestCase):
 def test_native_contradictions_rejected(self):
  baseline=json.loads((ROOT/'evidence/Q04_before.attempt005.json').read_text())
  baseline['native_open_orders']=0
  with tempfile.TemporaryDirectory() as tmp:
   out=Path(tmp)/'out.json';oracle=ROOT/'fixtures_v2/Q04_before.expected.json';inp=ROOT/'fixtures/input.json'
   out.write_text(json.dumps(baseline));self.assertTrue(compare.compare_file(out,oracle,inp))
   mutations=[]
   for key,value in [('native_open_orders',1),('fixture_manifest_sha256','0'*64)]:
    bad=copy.deepcopy(baseline);bad[key]=value;mutations.append(bad)
   for key,value in [('quantity','1'),('price','100'),('fee','1'),('order_id',2),('utc','2025-01-07T14:30:00.0000000Z')]:
    bad=copy.deepcopy(baseline);bad['native_orders'][-1][key]=value;mutations.append(bad)
   bad=copy.deepcopy(baseline);bad['native_orders'].pop(1);mutations.append(bad)
   for i,bad in enumerate(mutations):
    with self.subTest(mutation=i):
     out.write_text(json.dumps(bad))
     with self.assertRaises(compare.GateMismatch):compare.compare_file(out,oracle,inp)
if __name__=='__main__':unittest.main(verbosity=2)

"""Adversarial native ledger tests, independent of adapter implementation."""
import copy,importlib.util,json,unittest
from pathlib import Path
R=Path(__file__).resolve().parent;s=importlib.util.spec_from_file_location('stage_compare',R/'compare.py');g=importlib.util.module_from_spec(s);s.loader.exec_module(g)
class NativeLedgerTests(unittest.TestCase):
 def sample(self,cid):
  c=next(c for c in json.loads((R/'fixtures/input.json').read_text())['cases'] if c['case_id']==cid);e=json.loads((R/'fixtures'/c['oracle']).read_text())
  native=[]
  for f in e['fills']:native.append(dict(order_id=f['order_id'],sid='SID1',status='PartiallyFilled',quantity=f['quantity'],price=f['price'],fee=f['fee'],utc=g.prior.native_utc((f['available_ns']+99)//100*100)))
  native.append(dict(order_id=1,sid='SID1',status='Canceled',quantity='0',price='0',fee='0',utc=g.prior.native_utc(c['decision_ns'])))
  journal=[dict(record=r,admitted_ns=r['available_ns'],dispatch_ns=(r['available_ns']+99)//100*100) for r in sorted(c['events'],key=lambda x:(x['available_ns'],x['sequence'],x['id']))]
  a=dict(execution_complete=True,engine_status='Completed',native_end_observed=True,network_denied=dict(non_loopback_interfaces=0,testnet_socket_result='NetworkUnreachable'),business=copy.deepcopy(e),crosswalk=[dict(instrument=i,engine_sid=s) for i,s in [('I1','SID1'),('I2','SID2'),('I3','SID3')]],native_orders=native,native_open_orders=0,envelope_journal=journal)
  return a,e,c
 def test_reordered_partial_projection_requires_native_exactly_once_accounting(self):
  a,e,c=self.sample('Q19_reordered_duplicates');self.assertTrue(g.assess(a,e,c))
  mutations=[]
  for key,value in [('quantity','10'),('fee','1'),('sid','SID2'),('utc','2025-01-06T15:00:00.0000000Z')]:
   b=copy.deepcopy(a);b['native_orders'][1][key]=value;mutations.append(b)
  b=copy.deepcopy(a);b['native_orders'].insert(1,b['native_orders'][0]);mutations.append(b)
  b=copy.deepcopy(a);b['envelope_journal'][0]['record']['receipt_ns']=c['decision_ns'];mutations.append(b)
  for b in mutations:
   with self.assertRaises(g.Mismatch):g.assess(b,e,c)
 def test_fee_correction_requires_one_delta_without_extra_execution(self):
  a,e,c=self.sample('Q20_partial_correction');self.assertTrue(g.assess(a,e,c))
  for key,value in [('fee_adjustments',['1']),('cash','9698.58997'),('fees','2.2')]:
   b=copy.deepcopy(a);b['business']['snapshots'][-1][key]=value
   with self.assertRaises(g.Mismatch):g.assess(b,e,c)
  b=copy.deepcopy(a);b['native_orders'].insert(0,b['native_orders'][0])
  with self.assertRaises(g.Mismatch):g.assess(b,e,c)
if __name__=='__main__':unittest.main()

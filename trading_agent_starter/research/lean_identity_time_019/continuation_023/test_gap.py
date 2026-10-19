"""Adversarial checks for gaps previously invisible to frozen subchecks."""
import copy,importlib.util,json,unittest
from pathlib import Path
R=Path(__file__).resolve().parent
s=importlib.util.spec_from_file_location('gap_compare',R/'compare.py');g=importlib.util.module_from_spec(s);s.loader.exec_module(g)
class GapOracleTests(unittest.TestCase):
 def test_integral_native_state_and_single_owner_are_verified(self):
  case=next(c for c in json.loads((R/'fixtures/input.json').read_text())['cases'] if c.get('split_coupling'))
  expected=json.loads((R/'fixtures/Q11_integral_coupling.expected.json').read_text())
  actual={'gap':copy.deepcopy(expected),'native_orders':[{'status':'Submitted','quantity':'0','price':'0','fee':'0'}], 'native_open_orders':1}
  self.assertTrue(g.compare_gap(actual,case,expected))
  for key,value in [('quantity','40'),('cash','10100'),('pending_quantity','2'),('reserved_notional','100'),('applications',2),('owner','native_and_projection')]:
   bad=copy.deepcopy(actual);bad['gap']['split'][key]=value
   with self.subTest(key=key),self.assertRaises(g.GateMismatch):g.compare_gap(bad,case,expected)
  bad=copy.deepcopy(actual);bad['native_orders'].append({'status':'Filled','quantity':'2','price':'100','fee':'1'})
  with self.assertRaises(g.GateMismatch):g.compare_gap(bad,case,expected)
 def test_typed_admission_cannot_pass_by_ignoring_or_backdating_records(self):
  case=next(c for c in json.loads((R/'fixtures/input.json').read_text())['cases'] if c['case_id']=='Q09_typed_historical')
  expected=json.loads((R/'fixtures/Q09_typed_historical.expected.json').read_text())
  records=case['future_records'];known=[];journal=[]
  # Independent fixed expected evolution for the four frozen future types.
  state=dict(q0_ask='100',symbol_version=None,action_version=None,prediction_version=None,projections=dict(symbol=None,action=None,prediction=None))
  for i,r in enumerate(records):
   before=copy.deepcopy(state);before['asof_ns']=r['available_ns']-1
   if i==0:state['q0_ask']='1'
   else:state[r['kind']+'_version']=r['id'];state['projections'][r['kind']]=r['payload']
   after=copy.deepcopy(state);after['asof_ns']=r['available_ns']
   journal.append(dict(record=r,admitted_ns=r['available_ns'],dispatch_ns=r['available_ns'],before=before,after=after))
  gap=dict(metadata_rejected=False,business_prefix=expected['business'],knowledge=journal,history=[case['decision_quote'],records[0]],factor_controls=[],decoy_journal=[],raw_normalization=[])
  actual=dict(business=expected['business'],gap=gap)
  self.assertTrue(g.compare_gap(actual,case,expected))
  mutants=[]
  bad=copy.deepcopy(actual);bad['gap']['knowledge']=[];mutants.append(bad)
  bad=copy.deepcopy(actual);bad['gap']['knowledge'][0]['admitted_ns']-=1;mutants.append(bad)
  bad=copy.deepcopy(actual);bad['gap']['knowledge'][0]['record']['receipt_ns']=records[0]['available_ns'];mutants.append(bad)
  bad=copy.deepcopy(actual);bad['gap']['knowledge'][0]['before']['q0_ask']='1';mutants.append(bad)
  bad=copy.deepcopy(actual);bad['gap']['history'][0]['ask']='1';mutants.append(bad)
  bad=copy.deepcopy(actual);bad['gap']['business_prefix']['cash']='9999';mutants.append(bad)
  bad=copy.deepcopy(actual);bad['gap']['knowledge'][2]['after']['projections']['action']=None;mutants.append(bad)
  for i,bad in enumerate(mutants):
   with self.subTest(mutation=i),self.assertRaises(g.GateMismatch):g.compare_gap(bad,case,expected)
 def test_factor_and_decoy_must_enter_observed_public_paths(self):
  case=next(c for c in json.loads((R/'fixtures/input.json').read_text())['cases'] if c['case_id']=='Q11_ingress_raw')
  expected=json.loads((R/'fixtures/Q11_ingress_raw.expected.json').read_text());r=case['factors'][0];d=case['adjusted_decoy']
  prefix=copy.deepcopy(expected['business']);prefix['raw_marks']=['100']
  control=dict(record=r,admitted_ns=r['available_ns'],dispatch_ns=r['available_ns'],provider_calls=1,mode='Adjusted',scale='0.5',bid='50',ask='50.01',normalized_probe=dict(case['factor_probe'],normalization='Adjusted',bid='50',ask='50.01'),admission_result='NORMALIZATION',native_price_before='100',native_price_after='100')
  gap=dict(metadata_rejected=False,business_prefix=prefix,factor_controls=[control],decoy_journal=[dict(id=d['id'],admitted_ns=d['available_ns'],dispatch_ns=d['available_ns'],result='NORMALIZATION',native_price_before='100',native_price_after='100')],raw_normalization=[dict(id=e['id'],provider_calls=0,bid=e['bid'],ask=e['ask'],mode='Raw') for e in case['events']])
  actual=dict(business=expected['business'],gap=gap)
  self.assertTrue(g.compare_gap(actual,case,expected))
  for key,value in [('provider_calls',0),('admission_result',None),('scale','1'),('native_price_after','50')]:
   bad=copy.deepcopy(actual);bad['gap']['factor_controls'][0][key]=value
   with self.subTest(key=key),self.assertRaises(g.GateMismatch):g.compare_gap(bad,case,expected)
  bad=copy.deepcopy(actual);bad['gap']['decoy_journal']=[]
  with self.assertRaises(g.GateMismatch):g.compare_gap(bad,case,expected)
  bad=copy.deepcopy(actual);bad['gap']['raw_normalization'][0]['bid']='50'
  with self.assertRaises(g.GateMismatch):g.compare_gap(bad,case,expected)
if __name__=='__main__':unittest.main()

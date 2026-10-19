"""Adversarial tests for the independent qualification comparator, not engine economics."""
import copy, importlib.util, json, types, unittest
from pathlib import Path
R=Path(__file__).resolve().parent

def load(name):
 p=R/(name+'.py')
 if not p.exists():return types.SimpleNamespace(GateMismatch=ValueError,exact=lambda a,b:None,evaluate=lambda a,c:None)
 s=importlib.util.spec_from_file_location(name,p);m=importlib.util.module_from_spec(s);s.loader.exec_module(m);return m
C=load('compare');E=load('evaluate')
class GateTests(unittest.TestCase):
 def baseline(self):
  c=next(c for c in json.loads((R/'fixtures/input.json').read_text())['cases'] if c['case_id']=='Q21_compete')
  business=json.loads((R/'fixtures/Q21_compete.expected.json').read_text())
  native=dict(end_observed=True,status='Completed',crosswalk={f'I{i}':f'SID{i}' for i in range(1,8)},quantities={f'I{i}':'0' for i in range(1,8)},cash='1000',gate_calls=2,events=[dict(intent='A',instrument='I1',sid='SID1',status='Submitted',quantity='0',price='0',fee='0'),dict(intent='B',instrument='I2',sid='SID2',status='Invalid',quantity='0',price='0',fee='0')])
  return c,business,native
 def test_native_gate_cannot_be_skipped(self):
  c,b,n=self.baseline();n['gate_calls']=1
  with self.assertRaises(C.GateMismatch):C.reconcile(b,n,c)
 def test_native_cash_cannot_diverge_from_export(self):
  c,b,n=self.baseline();n['cash']='1001'
  with self.assertRaises(C.GateMismatch):C.reconcile(b,n,c)
 def test_native_quantity_cannot_be_fabricated(self):
  c,b,n=self.baseline();n['quantities']['I1']='1'
  with self.assertRaises(C.GateMismatch):C.reconcile(b,n,c)
 def test_incomplete_output_rejected(self):
  c,b,n=self.baseline()
  with self.assertRaises(C.GateMismatch):C.assess({'case_complete':False},b,c)
 def test_prior_failure_denominator_cannot_be_dropped(self):
  c=next(c for c in json.loads((R/'fixtures/input.json').read_text())['cases'] if c['case_id']=='Q33_unresolved')
  expected=json.loads((R/'fixtures/Q33_unresolved.expected.json').read_text());raw={'arms':{a:dict(accounting=expected['arms'][a]['accounting'],diagnostics={}) for a in ['A','B','C','N']},'reused_outcome':dict(denominator=0,failures=0,unresolved_claim=dict(status='UNKNOWN',terminal_value=None))}
  with self.assertRaises(C.GateMismatch):C.exact(E.evaluate(raw,c),expected)
 def test_wrong_cash_is_rejected(self):
  with self.assertRaises(C.GateMismatch):C.exact({'cash':'1000'},{'cash':'1001'})
 def test_missing_or_extra_fields_are_rejected(self):
  for actual in [{},{'x':1,'extra':0}]:
   with self.assertRaises(C.GateMismatch):C.exact(actual,{'x':1})
 def test_decimal_string_format_has_no_tolerance(self):
  with self.assertRaises(C.GateMismatch):C.exact('99.90','99.9')
 def test_types_are_exact(self):
  with self.assertRaises(C.GateMismatch):C.exact(True,1)
 def test_order_is_exact(self):
  with self.assertRaises(C.GateMismatch):C.exact(['I2','I1'],['I1','I2'])
 def test_unresolved_and_costs_are_preserved(self):
  c={'arm_mode':'unresolved','run_cost':'0.25'}
  raw={'arms':{a:{'accounting':{'cash':'9000'},'diagnostics':{'equity':99999,'sharpe':42}} for a in ['A','B','C','N']},'reused_outcome':dict(denominator=1,failures=1,unresolved_claim=dict(status='UNKNOWN',terminal_value=None))}
  result=E.evaluate(raw,c)
  self.assertIsNotNone(result,'Evaluator must produce independent records')
  self.assertEqual(result['arms']['N']['evaluation'],dict(opportunities=1,failures=1,run_cost='0.25',terminal_value=None,status='unresolved'))
  altered=copy.deepcopy(raw);altered['arms']['A']['diagnostics']={'equity':-999999,'sharpe':-100}
  self.assertEqual(E.evaluate(altered,c),result)
 def test_arm_leakage_rejected(self):
  raw={'arms':{a:{'accounting':{'cash':'10000'},'diagnostics':{}} for a in ['A','B','C','N']}}
  raw['arms']['C']['accounting']['cash']='10001'
  with self.assertRaises((ValueError,AssertionError)):E.evaluate(raw,{'arm_mode':'no_fill','run_cost':'0.25'})

if __name__=='__main__':unittest.main()

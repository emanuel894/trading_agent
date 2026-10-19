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
  raw={'arms':{a:{'accounting':{'cash':'9000'},'diagnostics':{'equity':99999,'sharpe':42}} for a in ['A','B','C','N']}}
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

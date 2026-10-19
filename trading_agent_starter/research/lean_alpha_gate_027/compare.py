"""Exact external oracles plus native trade-accounting reconciliation."""
from pathlib import Path
from decimal import Decimal as D
import hashlib, importlib.util, json
R=Path(__file__).resolve().parent
class GateMismatch(ValueError):pass
def require(ok,message):
 if not ok:raise GateMismatch(message)
def exact(a,b,path='$'):
 require(type(a) is type(b),path+': type differs')
 if isinstance(b,dict):
  require(set(a)==set(b),path+': fields differ')
  for k in b:exact(a[k],b[k],path+'.'+k)
 elif isinstance(b,list):
  require(len(a)==len(b),path+': length differs')
  for i,(x,y) in enumerate(zip(a,b)):exact(x,y,path+f'[{i}]')
 else:require(a==b,path+f': {a!r} != {b!r}')
def assess(actual,expected,case):
 require(actual.get('case_complete') is True,'Incomplete case: '+str(actual.get('technical_error')))
 exact(actual['network_denied'],dict(non_loopback_interfaces=0,testnet_socket_result='NetworkUnreachable'))
 if case['fixture']=='Q32' and case['ingress']!='complete':
  require(actual.get('execution_complete') is False,'Rejected ingress published scientific output')
  exact(dict(guard_error=actual['guard_error'],provider_calls=actual['provider_calls'],business=actual.get('business')),expected)
  require(actual.get('native_submissions',0)==0,'Guard failure submitted an order')
  return True
 require(actual.get('execution_complete') is True,'Native execution incomplete')
 raw=actual['business']
 if case['fixture']=='Q33':
  s=importlib.util.spec_from_file_location('gate_evaluator',R/'evaluate.py');m=importlib.util.module_from_spec(s);s.loader.exec_module(m)
  business=m.evaluate(raw,case)
  for arm in ['A','B','C','N']:reconcile(raw['arms'][arm]['accounting'],actual['native'][arm],case)
 else:business=raw;reconcile(raw,actual['native'],case)
 exact(business,expected)
 return True
def reconcile(business,native,case):
 require(native['end_observed'] is True and native['status']=='Completed','Native completion missing')
 require(len(native['crosswalk'])==7 and len(set(native['crosswalk'].values()))==7,'Research identity collapsed')
 fills=[e for e in native['events'] if e['status'] in ['Filled','PartiallyFilled']]
 projected=[dict(id=e['intent'],quantity=e['quantity'],price=e['price'],fee=e['fee']) for e in fills]
 exact(projected,business['fills'])
 cash=D(case['cash'])-sum((D(e['quantity'])*D(e['price'])+D(e['fee']) for e in fills),D(0))
 require(cash==D(native['cash']),'Native cash does not reconcile')
 for instrument in native['quantities']:
  seed=sum((D(h['qty']) for h in case['holdings'] if h['instrument']==instrument),D(0))
  quantity=seed+sum((D(e['quantity']) for e in fills if e['instrument']==instrument),D(0))
  require(quantity==D(native['quantities'][instrument]),'Native quantity changed outside fills: '+instrument)
 if business['snapshots']:
  last=business['snapshots'][-1]
  require(D(last['cash'])==D(native['cash']) and D(last['quantity'])==D(native['quantities']['I1']),'Exporter differs from native final holdings/cash')
 for e in native['events']:
  require(e['sid']==native['crosswalk'][e['instrument']],'Native identity mismatch')
  if e not in fills:require(all(D(e[k])==0 for k in ['quantity','price','fee']),'Nonfill produced economics')
def compare_file(output,oracle,input_path):
 a=json.loads(Path(output).read_text());bundle=json.loads(Path(input_path).read_text());case=next(c for c in bundle['cases'] if c['case_id']==a['case_id'])
 require(a['source_pin']==bundle['source_pin'],'Source binding changed')
 require(a['input_sha256']==hashlib.sha256(Path(input_path).read_bytes()).hexdigest(),'Input binding changed')
 require(a['fixture_manifest_sha256']==hashlib.sha256((Path(input_path).parent/'manifest.json').read_bytes()).hexdigest(),'Manifest binding changed')
 return assess(a,json.loads(Path(oracle).read_text()),case)

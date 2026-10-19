"""Exact independent business and native pipeline reconciliation; no tolerances."""
from pathlib import Path
from decimal import Decimal as D
import datetime,hashlib,importlib.util,json
R=Path(__file__).resolve().parent
s=importlib.util.spec_from_file_location('prior_exact_oracle',R.parent/'lean_identity_time_019/compare.py');prior=importlib.util.module_from_spec(s);s.loader.exec_module(prior)
Mismatch=prior.GateMismatch
exact=prior.compare_business

def require(value,message):
 if not value:raise Mismatch(message)
def assess(actual,expected,case):
 require(actual.get('execution_complete') is True,'Native execution incomplete: '+str(actual.get('technical_error')))
 require(actual.get('engine_status')=='Completed' and actual.get('native_end_observed') is True,'Native completion missing')
 exact(actual['network_denied'],dict(non_loopback_interfaces=0,testnet_socket_result='NetworkUnreachable'))
 exact(actual['business'],expected)
 cross=actual['crosswalk'];require(len(cross)==3 and {r['instrument'] for r in cross}=={'I1','I2','I3'} and len({r['engine_sid'] for r in cross})==3,'Stable identities collapsed')
 sid=next(r['engine_sid'] for r in cross if r['instrument']=='I1')
 native=[e for e in actual['native_orders'] if e['status'] in ['Filled','PartiallyFilled']]
 require(len(native)==len(expected['fills']),'Native fill count differs from admitted execution ledger')
 for e,f in zip(native,expected['fills']):
  ns=(f['available_ns']+99)//100*100
  exact({k:e[k] for k in ['order_id','sid','quantity','price','fee','utc']},dict(order_id=f['order_id'],sid=sid,quantity=f['quantity'],price=f['price'],fee=f['fee'],utc=prior.native_utc(ns)))
 for e in actual['native_orders']:
  require(e['sid']==sid,'Native order remapped identity')
  if e not in native:require(all(D(e[k])==0 for k in ['quantity','price','fee']),'Nonfill emitted economic fill/fee')
 last=expected['snapshots'][-1]
 require(actual['native_open_orders']==sum(o['status'] not in ['Filled','Canceled','Invalid'] for o in last['orders']),'Native pending order lost/leaked')
 for order in last['orders']:
  rows=[e for e in actual['native_orders'] if e['order_id']==order['id']]
  require(rows and rows[-1]['status']==order['status'],'Native terminal order status differs')
 if case['fixture'] in ['Q16','Q17','Q18','Q19','Q20']:
  require(D(case['seed'])+sum((D(e['quantity']) for e in native),D(0))==D(last['I1_quantity']),'Native quantities do not reconcile')
  corrections=sum((D(v) for v in last.get('fee_adjustments',[])),D(0))
  fees=sum((D(e['fee']) for e in native),D(0))+corrections
  require(fees==D(last['fees']),'Incremental/corrected fees do not reconcile')
  cash=D(case['cash'])-sum((D(e['quantity'])*D(e['price'])+D(e['fee']) for e in native),D(0))-corrections
  require(cash==D(last['cash']),'Native cash does not reconcile with executions/fee evidence')
 events=sorted(case['events'],key=lambda e:(max(e['available_ns'],e['receipt_ns'] or e['available_ns']),e['sequence'],e['id']))
 journal=[]
 for e in events:
  ns=max(e['available_ns'],e['receipt_ns'] or e['available_ns'])
  journal.append(dict(record=e,admitted_ns=ns,dispatch_ns=(ns+99)//100*100))
 exact(actual['envelope_journal'],journal)
 return True

def compare_file(output,oracle,input_path):
 actual=json.loads(Path(output).read_text());bundle=json.loads(Path(input_path).read_text());case=next(c for c in bundle['cases'] if c['case_id']==actual['case_id'])
 require(actual['source_pin']==bundle['source_pin'],'Native source pin binding')
 require(actual['input_sha256']==hashlib.sha256(Path(input_path).read_bytes()).hexdigest(),'Native input binding')
 require(actual['fixture_manifest_sha256']==hashlib.sha256((Path(input_path).parent/'manifest.json').read_bytes()).hexdigest(),'Native fixture manifest binding')
 return assess(actual,json.loads(Path(oracle).read_text()),case)

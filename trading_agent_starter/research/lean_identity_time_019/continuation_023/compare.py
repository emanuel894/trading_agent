"""Independent exact oracle for only the three Issue23 gaps."""
from pathlib import Path
from decimal import Decimal
import hashlib,importlib.util,json
R=Path(__file__).resolve().parent
s=importlib.util.spec_from_file_location('issue19_compare',R.parent/'compare.py');original=importlib.util.module_from_spec(s);s.loader.exec_module(original)
GateMismatch=original.GateMismatch
compare_business=original.compare_business
D=1736175600000000000

def ceil(ns):return (ns+99)//100*100
def admission(r):return max(r['available_ns'],r.get('receipt_ns') or r['available_ns'])
def num(x):return format(Decimal(x).normalize(),'f')
def require(condition,message):
 if not condition:raise GateMismatch(message)
def view(ns,records,q):
 eligible=[r for r in records if admission(r)<=ns]
 correction=next((r for r in reversed(eligible) if r['kind']=='correction'),q)
 result=dict(asof_ns=ns,q0_ask=correction['ask'] if admission(q)<=ns else None,projections={kind:next((r['payload'] for r in reversed(eligible) if r['kind']==kind),None) for kind in ['symbol','action','prediction']})
 for kind in ['symbol','action','prediction']:
  result[kind+'_version']=next((r['version_id'] for r in reversed(eligible) if r['kind']==kind),None)
 return result

def compare_gap(actual,case,expected):
 gap=actual['gap']
 if case.get('split_coupling'):
  compare_business(gap,expected)
  require(actual['native_open_orders']==1,'Integral pending order lost')
  require(any(e['status']=='Submitted' for e in actual['native_orders']),'No native pending order')
  require(not any(e['status'] in ['Filled','PartiallyFilled'] or Decimal(e['quantity']) or Decimal(e['price']) or Decimal(e['fee']) for e in actual['native_orders']),'Unexpected native split fill/cash fee')
  return True
 compare_business(actual['business'],expected['business'])
 require(gap['metadata_rejected']==(case['normalization']!='Raw'),'Normalization metadata disposition')
 if case['normalization']!='Raw':
  for key in ['factor_controls','decoy_journal','raw_normalization','knowledge']:compare_business(gap[key],[])
  require(actual['native_orders']==[],'Mismatched metadata reached native order')
  return True
 if case['fixture']=='Q09':
  compare_business(gap['business_prefix'],expected['business'])
  records=sorted(case['future_records'],key=lambda r:(admission(r),r['sequence'],r['id']))
  known=[];journal=[]
  for r in records:
   before=view(admission(r)-1,known,case['decision_quote']);known.append(r)
   journal.append(dict(record=r,admitted_ns=admission(r),dispatch_ns=ceil(admission(r)),before=before,after=view(admission(r),known,case['decision_quote'])))
  compare_business(gap['knowledge'],journal)
  compare_business(gap['history'],[case['decision_quote']]+[r for r in records if r['kind']=='correction'])
  compare_business(gap['factor_controls'],[]);compare_business(gap['decoy_journal'],[])
 else:
  controls=gap['factor_controls'];require(len(controls)==len(case['factors']),'Factor inputs silently unused')
  for actual_control,r in zip(controls,case['factors']):
   before=actual_control['native_price_before'];factor=Decimal(r['factor'])
   probe=dict(case['factor_probe'],normalization='Adjusted',bid=num(Decimal(case['factor_probe']['bid'])*factor),ask=num(Decimal(case['factor_probe']['ask'])*factor))
   compare_business(actual_control,dict(record=r,admitted_ns=admission(r),dispatch_ns=ceil(admission(r)),provider_calls=1,mode='Adjusted',scale=num(factor),bid=num(100*factor),ask=num(Decimal('100.02')*factor),normalized_probe=probe,admission_result='NORMALIZATION',native_price_before=before,native_price_after=before))
  decoy=case['adjusted_decoy'];require(len(gap['decoy_journal'])==1,'Adjusted decoy silently unused')
  compare_business(gap['decoy_journal'],[dict(id=decoy['id'],admitted_ns=admission(decoy),dispatch_ns=ceil(admission(decoy)),result='NORMALIZATION',native_price_before='100',native_price_after='100')])
  compare_business(gap['raw_normalization'],[dict(id=e['id'],provider_calls=0,bid=num(e['bid']),ask=num(e['ask']),mode='Raw') for e in case['events']])
  # The pre-action output prefix is an immutable snapshot, distinct from the later raw50 mark.
  prefix=json.loads(json.dumps(expected['business']));prefix['raw_marks']=['100']
  compare_business(gap['business_prefix'],prefix)
 return True

def compare_file(output,oracle,input_path):
 actual=json.loads(Path(output).read_text());bundle=json.loads(Path(input_path).read_text())
 case=next(c for c in bundle['cases'] if c['case_id']==actual['case_id'])
 expected=json.loads(Path(oracle).read_text())
 require(actual.get('execution_complete') is True,'Native incomplete: '+str(actual.get('technical_error')))
 require(actual.get('engine_status')=='Completed' and actual.get('native_end_observed') is True,'Native engine/end incomplete')
 compare_business(actual['network_denied'],dict(non_loopback_interfaces=0,testnet_socket_result='NetworkUnreachable'))
 require(actual['input_sha256']==hashlib.sha256(Path(input_path).read_bytes()).hexdigest(),'Input binding')
 require(actual['fixture_manifest_sha256']==hashlib.sha256((Path(input_path).parent/'manifest.json').read_bytes()).hexdigest(),'Manifest binding')
 require(actual['source_pin']==bundle['source_pin'],'Source pin')
 require(len(actual['crosswalk'])==3 and len({r['engine_sid'] for r in actual['crosswalk']})==3,'Stable identities collapsed')
 for row,external in zip(actual['crosswalk'],bundle['identities']):compare_business({k:v for k,v in row.items() if k!='engine_sid'},external)
 sid=next(r['engine_sid'] for r in actual['crosswalk'] if r['instrument']=='I1')
 for e in actual['native_orders']:require(e['sid']==sid and e['order_id']==1,'Native order identity')
 if not case.get('split_coupling'):
  require(actual['native_open_orders']==0,'Native pending order left')
  compare_business([e['status'] for e in actual['native_orders']],actual['business']['native_order_statuses'])
  for e in actual['native_orders']:
   ns=case['decision_ns'];quantity=price=fee='0'
   if e['status']=='Filled':
    fill=actual['business']['fill'];ns=fill['dispatch_ns'];quantity=fill['quantity'];price=fill['price'];fee=fill['fee']
   compare_business({k:e[k] for k in ['quantity','price','fee','utc']},dict(quantity=quantity,price=price,fee=fee,utc=original.native_utc(ceil(ns))))
 return compare_gap(actual,case,expected)

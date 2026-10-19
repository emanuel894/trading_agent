from pathlib import Path
import json,hashlib
from decimal import Decimal as V
R=Path('/workspace/trading_agent/trading_agent_starter/research/lean_actions_execution_024');F=R/'fixtures';F.mkdir(exist_ok=True)
if (F/'manifest.json').exists():raise SystemExit('Frozen v1 exists; create a versioned amendment')
D=1736175600000000000
cases=[]
def ev(kind,t,**kw):return dict(id=kw.pop('id',kind),kind=kind,event_ns=D+int(t*10**9),available_ns=D+int(t*10**9),receipt_ns=None,clock_mode='simulated_historical',sequence=kw.pop('sequence',1),**kw)
def case(cid,row,variant,cash='10000',seed='0',events=None,**kw):
 c=dict(case_id=cid,fixture=row,variant=variant,decision_ns=D,cash=cash,seed=seed,events=events or [],**kw);cases.append(c);return c
def n(v):return format(V(str(v)).normalize(),'f')
def snap(label,cash='10000',q='0',avg=None,q2='0',avg2=None,fees='0',orders=None,**extra):return dict(label=label,cash=n(cash),I1_quantity=n(q),I1_average=n(avg if avg is not None else ('100' if V(q) else '0')),I2_quantity=n(q2),I2_average=n(avg2 if avg2 is not None else ('100' if V(q2) else '0')),fees=n(fees),orders=orders or [],**extra)
def order(q,filled='0',status='Submitted',limit=None,id=1):return dict(id=id,quantity=n(q),filled=n(filled),status=status,limit=None if limit is None else n(limit))
def freeze(c,expected):c['oracle']=c['case_id']+'.expected.json';(F/c['oracle']).write_text(json.dumps(expected,indent=2)+'\n')
# Q12 reverse sequence: every cash amount must be evidenced, never cached-price fallback.
c=case('Q12_reverse_claim','Q12','reverse',seed='3',events=[ev('reverse',3600,factor='2',claim='0.5',whole='1',post_price='200',evidence='E-REVERSE'),ev('reverse_duplicate',3600,sequence=2),ev('split_warning',3600,sequence=3),ev('settle_claim',7200,amount='37',evidence='E-CIL'),ev('settle_claim_duplicate',7200,sequence=2)])
freeze(c,{'snapshots':[snap('reverse',q='1',avg='200',claim='0.5',claim_value=None,encumbered=True,valuation_entry_allowed=False,action_applications=1),snap('duplicate_warning',q='1',avg='200',claim='0.5',claim_value=None,encumbered=True,valuation_entry_allowed=False,action_applications=1),snap('settled',cash='10037',q='1',avg='200',claim='0',claim_value='37',encumbered=False,valuation_entry_allowed=True,action_applications=1,settlement_applications=1)],'fills':[]})
# Q13 payable vs absent evidence.
for missing in [False,True]:
 events=[ev('dividend',3600,distribution='2',post_price='98',evidence='E-DIV',payable_ns=None if missing else D+172800_000_000_000),ev('dividend_duplicate',3600,sequence=2)]
 if not missing:events += [ev('dividend_pay',172800,evidence='E-PAY'),ev('dividend_pay_duplicate',172800,sequence=2)]
 c=case('Q13_'+('missing_payable' if missing else 'payable'),'Q13','missing' if missing else 'known',cash='9000',seed='10',events=events)
 ss=[snap('ex_duplicate',cash='9020',q='10',receivable='20',encumbrance='20',spendable='9000',economic_nav='10000',request9001=False,raw_bid='98',dividend_applications=1,payment_applications=0,payable_ns=None if missing else D+172800_000_000_000)]
 if not missing:ss.append(snap('paid_duplicate',cash='9020',q='10',receivable='0',encumbrance='0',spendable='9020',economic_nav='10000',request9001=True,raw_bid='98',dividend_applications=1,payment_applications=1,payable_ns=D+172800_000_000_000))
 freeze(c,{'snapshots':ss,'fills':[]})
# Q14 known conversion vs missing/conflict, tax allocation stays null.
for variant in ['known','missing','conflicting']:
 events=[ev('merger',3600,ratio='0.5' if variant!='missing' else None,cash_per_share='7' if variant!='missing' else None,evidence='E-M' if variant!='missing' else None,conflict=variant=='conflicting',successor='I2' if variant!='missing' else None,post_price='180')]
 if variant=='known':events += [ev('merger_pay',7200,amount='70',evidence='E-M-PAY'),ev('merger_pay_duplicate',7200,sequence=2)]
 c=case('Q14_'+variant,'Q14',variant,cash='9000',seed='10',events=events)
 if variant=='known':
  common=dict(q='0',avg='0',q2='5',avg2='200',lineage='I1->I2',original_cost='1000',native_carry_book_cost='1000',I2_raw_bid='180',tax_basis_allocation=None,economic_value='970',valuation_entry_allowed=True,unresolved=False)
  ss=[snap('converted',cash='9000',receivable='70',payment_applications=0,**common),snap('paid_duplicate',cash='9070',receivable='0',payment_applications=1,**common)]
 else:ss=[snap('unresolved',cash='9000',q='10',receivable=None,lineage=None,tax_basis_allocation=None,economic_value=None,valuation_entry_allowed=False,unresolved=True)]
 freeze(c,{'snapshots':ss,'fills':[]})
# Q15 a tempting old quote would fill the limit if mapping guard failed.
for variant in ['exact','date_only','overlap']:
 c=case('Q15_'+variant,'Q15',variant,seed='10',events=[ev('rename',3600,ticker='NEW',resolution=variant,evidence='E-NAME'),ev('quote',3600.000001,id='old_quote',ticker='AAA',bid='89.99',ask='90',size='1000'),ev('quote',3600.000002,id='new_quote',ticker='NEW',bid='100',ask='100.02',size='1000')])
 if variant=='exact':ss=[snap('mapped',q='10',orders=[order(5,limit=100)],mapping_version=2,ticker='NEW',stable_sid=True,stable_order=True,stable_intent=True,unresolved=False),snap('quotes',q='10',orders=[order(5,limit=100)],quote_results=['old_quote:SYMBOL_INTERVAL','new_quote:ADMITTED'],mapping_version=2,ticker='NEW',unresolved=False)]
 else:ss=[snap('unresolved',q='10',mapping_version=1,ticker='AAA',unresolved=True,entry_allowed=False)]
 c['initial_mapping']=dict(available_ns=D-1_000_000_000,ticker='AAA',resolution=variant,effective_date='2025-01-06',evidence='E-MAP-INITIAL')
 freeze(c,{'snapshots':ss,'fills':[]})
# Q16 four entry variants and a separate pending due-exit track.
for variant in ['resume','no_resume','unknown','no_fresh','exit']:
 events=[]
 if variant!='unknown':events.append(ev('halt',.5))
 events.append(ev('quote',1,id='q1_halted',bid='100',ask='100.02',size='1000',session='RTH'))
 if variant in ['resume','no_fresh','exit']:events.append(ev('resume',3))
 if variant in ['resume','exit']:
  if variant=='exit':events.append(ev('quote',3.05,id='extended_decoy',bid='200',ask='200.02',size='1000',session='EXT'))
  events.append(ev('quote',3.1,id='resumed_fresh',bid='100',ask='100.02',size='1000',session='RTH'))
 events.append(ev('deadline',5.000001))
 if variant=='no_fresh':events.append(ev('quote',6,id='late_fresh',bid='100',ask='100.02',size='1000',session='RTH'))
 c=case('Q16_'+variant,'Q16',variant,seed='5' if variant=='exit' else '0',events=events,initial_status='UNKNOWN' if variant=='unknown' else 'TRADABLE')
 if variant in ['resume','exit']:
  buy=variant=='resume';price='100.07001' if buy else '99.95';qty='5' if buy else '-5';cash='9498.64995' if buy else '10498.75'
  ss=[snap('halted',q='5' if not buy else '0',orders=[order(qty)],status='HALTED',executable_quote=None),snap('resumed',q='5' if not buy else '0',orders=[order(qty)],status='TRADABLE',executable_quote=None),snap('finished',cash=cash,q='5' if buy else '0',avg=price if buy else '0',fees='1',orders=[order(qty,qty,'Filled')],status='TRADABLE',deadline_ns=D+5_000_000_000)]
  fills=[dict(order_id=1,quote_id='resumed_fresh',quantity=qty,price=price,fee='1',available_ns=D+3_100_000_000)]
 elif variant=='unknown':ss=[snap('finished',status='UNKNOWN',entry_allowed=False,deadline_ns=D+5_000_000_000)];fills=[]
 else:
  ss=[snap('halted',orders=[order(5)],status='HALTED',executable_quote=None)]
  if variant=='no_fresh':ss.append(snap('resumed',orders=[order(5)],status='TRADABLE',executable_quote=None))
  ss.append(snap('finished',orders=[order(5,status='Canceled')],status='TRADABLE' if variant=='no_fresh' else 'HALTED',deadline_ns=D+5_000_000_000));fills=[]
 freeze(c,{'snapshots':ss,'fills':fills})
# Q17 baseline buy5bps reused; other three hook combinations reset independently.
for side,bps in [('sell',5),('buy',10),('sell',10)]:
 price={'sell5':'99.95','buy10':'100.12002','sell10':'99.90'}[side+str(bps)];qty='5' if side=='buy' else '-5';cash=V(10000)-V(qty)*V(price)-1
 c=case(f'Q17_{side}_{bps}','Q17','fill',seed='5' if side=='sell' else '0',side=side,bps=bps,events=[ev('quote',1,id='q1',bid='100',ask='100.02',size='1000',session='RTH')])
 freeze(c,{'snapshots':[snap('filled',cash=cash,q='5' if side=='buy' else '0',avg=price if side=='buy' else '0',fees='1',orders=[order(qty,qty,'Filled')],stock_slippage='0')],'fills':[dict(order_id=1,quote_id='q1',quantity=qty,price=price,fee='1',available_ns=D+1_000_000_000)]})
# Q18 independent event replenishes capacity, repeated scans never do.
c=case('Q18_shared_capacity','Q18','capacity',events=[ev('quote',1,id='budget_q1',bid='100',ask='100.02',size='50',session='RTH'),ev('quote',2,id='budget_q2',bid='100',ask='100.02',size='50',session='RTH')])
freeze(c,{'snapshots':[snap('same_event_scans',cash='9698.78997',q='3',avg='100.07001',fees='1',orders=[order(3,3,'Filled'),order(3,status='Canceled',id=2)],remaining_capacity='2',rejected_intent=2),snap('new_event',cash='9397.57994',q='6',avg='100.07001',fees='2',orders=[order(3,3,'Filled'),order(3,status='Canceled',id=2),order(3,3,'Filled',id=3)],remaining_capacity='2')],'fills':[dict(order_id=i,quote_id=q,quantity='3',price='100.07001',fee='1',available_ns=D+t*10**9) for i,q,t in [(1,'budget_q1',1),(3,'budget_q2',2)]]})
# Q19 all records in a frozen same-availability batch; physical order is not causal authority.
for adv in [False,True]:
 events=[ev('execution',1,id='e1',sequence=1,qty='4',price='100.07001',verified_fee='0'),ev('cancel_request',1,sequence=2),ev('execution',1,id='e2',sequence=3,qty='2',price='100.07001',verified_fee='0'),ev('cancel_ack',1,sequence=4)]
 if adv:events=[events[3],events[2],events[0],events[1],events[2].copy(),events[0].copy(),events[3].copy(),ev('stale_status',1,sequence=5,status='Submitted')]
 c=case('Q19_'+('reordered_duplicates' if adv else 'canonical'),'Q19','adversarial' if adv else 'canonical',events=events)
 ss=[snap('partial1',cash='9598.71996',q='4',avg='100.07001',fees='1',orders=[order(10,4,'PartiallyFilled')],reservation='600.42006',lifecycle='PARTIAL'),snap('cancel_requested',cash='9598.71996',q='4',avg='100.07001',fees='1',orders=[order(10,4,'CancelPending')],reservation='600.42006',lifecycle='CANCEL_PENDING'),snap('partial2',cash='9398.57994',q='6',avg='100.07001',fees='1',orders=[order(10,6,'PartiallyFilled')],reservation='400.28004',lifecycle='CANCEL_PENDING'),snap('canceled',cash='9398.57994',q='6',avg='100.07001',fees='1',orders=[order(10,6,'Canceled')],reservation='0',lifecycle='CANCELED')]
 freeze(c,{'snapshots':ss,'fills':[dict(order_id=1,quote_id=id,quantity=qty,price='100.07001',fee=fee,available_ns=D+1_000_000_000) for id,qty,fee in [('e1','4','1'),('e2','2','0')]]})
# Q20 exact verified fees and cumulative/append-only correction.
for total in ['0','1','1.25']:
 fee=max(V(1),V(total));c=case('Q20_total_'+total.replace('.','_'),'Q20','total',verified_total=total,events=[ev('quote',1,id='q1',bid='100',ask='100.02',size='1000',session='RTH')])
 freeze(c,{'snapshots':[snap('filled',cash=V(10000)-V('100.07001')-fee,q='1',avg='100.07001',fees=fee,orders=[order(1,1,'Filled')],verified_total=total)],'fills':[dict(order_id=1,quote_id='q1',quantity='1',price='100.07001',fee=n(fee),available_ns=D+1_000_000_000)]})
for variant in ['no_fill','missing','unbounded']:
 c=case('Q20_'+variant,'Q20',variant,fee_bound=None if variant in ['missing','unbounded'] else '1',events=[ev('deadline',5.000001)])
 freeze(c,{'snapshots':[snap('finished',orders=[order(1,status='Canceled')] if variant=='no_fill' else [],fee_state='NO_FILL' if variant=='no_fill' else 'UNRESOLVED',entry_allowed=variant=='no_fill')],'fills':[]})
c=case('Q20_partial_correction','Q20','partial',events=[ev('execution',1,id='f1',qty='1',price='100.07001',verified_fee='0.40'),ev('execution',2,id='f2',qty='1',price='100.07001',verified_fee='0.80'),ev('execution',3,id='f3',qty='1',price='100.07001',verified_fee='1.20'),ev('cancel_request',4),ev('cancel_ack',5),ev('fee_correction',6,id='fee-v2',verified_fee='1.10',evidence='E-FEE-CORR'),ev('fee_correction',6,id='fee-v2',sequence=2,verified_fee='1.10',evidence='E-FEE-CORR')])
ss=[]
for i,fee in enumerate(['1','1','1.2'],1):ss.append(snap('partial'+str(i),cash=V(10000)-i*V('100.07001')-V(fee),q=str(i),avg='100.07001',fees=fee,orders=[order(10,i,'PartiallyFilled')],cumulative_fee=fee))
ss += [snap('canceled',cash='9698.58997',q='3',avg='100.07001',fees='1.2',orders=[order(10,3,'Canceled')],cumulative_fee='1.2'),snap('corrected_duplicate',cash='9698.68997',q='3',avg='100.07001',fees='1.1',orders=[order(10,3,'Canceled')],cumulative_fee='1.1',fee_adjustments=['-0.1'],fee_correction_applications=1)]
freeze(c,{'snapshots':ss,'fills':[dict(order_id=1,quote_id='f'+str(i),quantity='1',price='100.07001',fee=fee,available_ns=D+i*10**9) for i,fee in enumerate(['1','0','0.2'],1)]})
for c in cases:
 c['decision_quote']=ev('quote',-.5,id='q0',bid='99.99',ask='100',size='1000',normalization='Raw',unit='shares',conditions=['R'],gap=False,source='SIP_FIXTURE',tape='A',exchange='N',session='RTH')
 if c['fixture']=='Q19':c['fee_bound']='1'
 if c['fixture']=='Q20' and c['variant']=='partial':c['fee_bound']='1.2'
 if c['fixture']=='Q20' and c['variant']=='unbounded':c['fee_evidence']=dict(verified=True,bound=None,evidence='E-UNBOUNDED-FEE')
 for e in c['events']:
  if e['kind']=='quote':e.update(normalization='Raw',unit='shares',conditions=['R'],gap=False,source='SIP_FIXTURE',tape='A',exchange='N',session=e.get('session','RTH'))
 original={e['kind']:e for e in c['events'] if not e['kind'].endswith('_duplicate')}
 for i,e in enumerate(c['events']):
  if e['kind'].endswith('_duplicate'):
   kind=e['kind'].removesuffix('_duplicate')
   target={'settle_claim':'settle_claim','dividend':'dividend','dividend_pay':'dividend_pay','merger_pay':'merger_pay','reverse':'reverse'}[kind]
   c['events'][i]=dict(original[target],delivery_sequence=2)
  if e['kind']=='fee_correction' and e.get('sequence')==2:
   c['events'][i]=dict(e,sequence=1,delivery_sequence=2)
for c in cases:
 p=F/c['oracle'];oracle=json.loads(p.read_text())
 times={}
 for e in c['events']:
  k=e['kind'];t=e['available_ns']
  if k=='reverse':times.update(reverse=t,duplicate_warning=t)
  if k=='settle_claim':times['settled']=t
  if k=='dividend':times['ex_duplicate']=t
  if k=='dividend_pay':times['paid_duplicate']=t
  if k=='merger':times.update(converted=t,unresolved=t)
  if k=='merger_pay':times['paid_duplicate']=t
  if k=='rename':times.update(mapped=t,unresolved=t)
  if k=='quote':
   if e['id']=='new_quote':times['quotes']=t
   if e['id']=='q1_halted':times['halted']=t
   if c['fixture'] in ['Q17','Q20']:times['filled']=t
   if e['id']=='budget_q1':times['same_event_scans']=t
   if e['id']=='budget_q2':times['new_event']=t
  if k=='resume':times['resumed']=t
  if k=='deadline':times['finished']=t
  if k=='execution':
   if c['fixture']=='Q19':times.update(partial1=t,partial2=t,cancel_requested=t,canceled=t)
   else:times['partial'+e['id'][-1]]=t
  if k=='cancel_ack' and c['fixture']=='Q20':times['canceled']=t
  if k=='fee_correction':times['corrected_duplicate']=t
 for snapshot in oracle['snapshots']:
  if c['fixture']=='Q12':snapshot['native_profit']='0'
  t=times[snapshot['label']];snapshot['at_ns']=t;snapshot['native_dispatch_ns']=(t+99)//100*100
 p.write_text(json.dumps(oracle,indent=2)+'\n')
assert len(cases)==27,len(cases)
bundle=dict(schema_version='issue24-v1',capture_mode='fixture',rights_ref='synthetic-owned',source_pin='d4cac37514427c84d40064cecbf3f0e6be4b0137',decision_ns=D,calendar=dict(zone='America/New_York',sessions=['2025-01-06','2025-01-07','2025-01-08'],regular_open='09:30',regular_close='16:00'),cases=cases)
(F/'input.json').write_text(json.dumps(bundle,indent=2)+'\n')
(F/'manifest.json').write_text(json.dumps(dict(version='issue24-v1',sha256={p.name:hashlib.sha256(p.read_bytes()).hexdigest() for p in sorted(F.iterdir()) if p.name!='manifest.json'}),indent=2)+'\n')
print('Frozen',len(cases),'cases')

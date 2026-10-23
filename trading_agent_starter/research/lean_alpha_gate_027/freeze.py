"""Authored independent matrix oracles. Never read native output to generate expectations."""
from pathlib import Path
import copy, datetime as dt, hashlib, json
R=Path(__file__).resolve().parent
PIN='d4cac37514427c84d40064cecbf3f0e6be4b0137'
def ns(s): return int(dt.datetime.fromisoformat(s.replace('Z','+00:00')).timestamp())*10**9
D=ns('2025-01-06T15:00:00Z')
def step(op,at=0,**kw): return dict(op=op,at_ns=D+at,**kw)
def order(id='A',qty='1',instrument='I1',price='100.07001',fee='1',route='direct'):
 return step('order',id=id,qty=qty,instrument=instrument,price=price,fee=fee,route=route)
def decision(id='A',allow=True,reason='OK',qty='1',gross=None,symbol=None):
 return dict(id=id,allowed=allow,reason=reason,quantity=qty if allow else None,gross_ok=gross,symbol_ok=symbol)
def snap(label='final',cash='10000',reserve='0',qty='0',sell='0',daily=False,drawdown=False,pending=False):
 from decimal import Decimal as X
 def num(x): return format(x,'f').rstrip('0').rstrip('.') if '.' in format(x,'f') else format(x,'f')
 return dict(label=label,cash=cash,reserved_cash=reserve,free_cash=num(X(cash)-X(reserve)),quantity=qty,reserved_sell=sell,daily=daily,drawdown=drawdown,pending_exit=pending)
def business(decisions=(),snapshots=(),fills=(),ranked=(),due=None):
 return dict(decisions=list(decisions),snapshots=list(snapshots),fills=list(fills),ranked=list(ranked),due_ns=due)
CASES=[];ORACLES={}
def case(id,steps,expected,*,cash='10000',holdings=(),checks=('cash',),mark='100',**kw):
 c=dict(case_id=id,fixture=id[:3],cash=cash,holdings=list(holdings),checks=list(checks),mark=mark,steps=steps,**kw)
 CASES.append(c);ORACLES[id]=expected
def finish(steps): return steps+[step('snapshot',at=max([s['at_ns']-D for s in steps]+[0])+100,label='final')]

# Q21: isolated cash policy units through the native submission boundary.
for name,extra,ss in [('compete',[],[snap(cash='1000',reserve='601')]),
 ('request',[step('cancel_request',id='A')],[snap(cash='1000',reserve='601')]),
 ('ack',[step('cancel_request',id='A'),step('cancel_ack',id='A'),step('cancel_ack',id='A')],[snap(cash='1000')]),
 ('reject',[step('reject',id='A'),step('reject',id='A')],[snap(cash='1000')])]:
 case('Q21_'+name,finish([step('batch',intents=[order('B',qty='6',price='100',instrument='I2'),order(qty='6',price='100')])]+extra),business([decision(qty='6'),decision('B',False,'CASH')],ss),cash='1000')
case('Q21_unfilled_sale',finish([order('S','-5','I2','100'),step('batch',intents=[order('B','6','I3','100'),order(qty='6',price='100')])]),business([decision('S',qty='-5'),decision(qty='6'),decision('B',False,'CASH')],[snap(cash='1000',reserve='601')]),cash='1000',holdings=[dict(instrument='I2',qty='5',mark='100')])
case('Q21_exact_cash',finish([step('batch',intents=[order('B','1','I2','1'),order(qty='6',price='100')])]),business([decision(qty='6'),decision('B',False,'CASH')],[snap(cash='601',reserve='601')]),cash='601')
for field,reason in [('price','PRICE_BOUND'),('fee','FEE_BOUND')]:
 o=order();o[field]=None
 case('Q21_unknown_'+field,finish([o]),business([decision(allow=False,reason=reason)],[snap()]))

# Q22: assert each cap predicate even when issuer-overlap also rejects.
limits=('cash','limits')
def holding(i,q): return dict(instrument=i,qty=str(q),mark='1')
def limit_case(name,seed,proposed,allow,reason='OK',gross=True,symbol=True,pre=(),instrument='I1'):
 from decimal import Decimal as X
 total=sum((X(h['qty']) for h in seed),X(0));cash=str(X(10000)-total)
 initial_i1=next((h['qty'] for h in seed if h['instrument']=='I1'),'0')
 dec=list(pre[1]) if pre else []
 ops=list(pre[0]) if pre else []
 ops.append(order(qty=str(proposed),instrument=instrument,price='1'))
 reserve=str(X(proposed)+1) if allow and X(proposed)>0 else '0'
 if pre and pre[2]:reserve=str(X(reserve)+X(pre[2]))
 case('Q22_'+name,finish(ops),business(dec+[decision(allow=allow,reason=reason,qty=str(proposed),gross=gross,symbol=symbol)],[snap(cash=cash,reserve=reserve,qty=initial_i1)]),cash=cash,holdings=seed,checks=limits,mark='1')
limit_case('gross_over',[holding('I2',3000),holding('I4',2999)],2,False,'GROSS',False)
limit_case('gross_exact',[holding('I2',3000),holding('I4',2998)],2,True)
limit_case('symbol_over',[holding('I1',999)],2,False,'SYMBOL',True,False)
limit_case('symbol_exact_flat',[],1000,True)
limit_case('symbol_exact_overlap',[holding('I1',998)],2,False,'ISSUER')
limit_case('sixth',[holding(i,10) for i in ['I2','I4','I5','I6','I7']],2,False,'POSITIONS')
limit_case('issuer_other_class',[holding('I3',10)],2,False,'ISSUER')
limit_case('pending_buy',[],2,False,'ISSUER',pre=([order('P','2','I3','1')],[decision('P',qty='2',gross=True,symbol=True)],'3'))
limit_case('pending_sell',[holding('I2',3000),holding('I4',2999)],2,False,'GROSS',False,pre=([order('S','-500','I2','1')],[decision('S',qty='-500',gross=True,symbol=True)],'0'))
limit_case('short',[],-1,False,'SELL_SHARES')
limit_case('pending_gross',[holding('I2',3000),holding('I4',2997)],2,False,'GROSS',False,pre=([order('P','2','I5','1')],[decision('P',qty='2',gross=True,symbol=True)],'3'))

# Q23: frozen adverse bound is independent of q1.
for name,sigma,q,ask,reserve,cash,reason in [
 ('sigma05','0.05','4','100.02','401.28004','9598.71996','OK'),
 ('sigma01','0.01','9','100.02','901.63009','9098.36991','OK'),
 ('above_ceiling','0.05','4','100.03','401.28004','10000','OK'),
 ('zero','0',None,'100.02','0','10000','VOLATILITY'),
 ('null',None,None,'100.02','0','10000','VOLATILITY')]:
 ops=[step('sized_order',id='A',sigma=sigma,price='100.07001',fee='1',instrument='I1'),step('snapshot',label='frozen'),step('quote',at=10**9,bid='100',ask=ask,size='1000',status='TRADABLE')]
 ok=q is not None;filled=ok and name!='above_ceiling'
 ds=[decision(qty=q,allow=ok,reason=reason,gross=True if ok else None,symbol=True if ok else None)]
 cash0='10000';qs=q if filled else '0';rc='0' if filled else reserve
 fs=[dict(id='A',quantity=q,price='100.07001',fee='1')] if filled else []
 case('Q23_'+name,finish(ops),business(ds,[snap('frozen',reserve=reserve),snap(cash=cash,reserve=rc,qty=qs)],fs),checks=('cash','limits','halts'))
case('Q23_tie',finish([step('rank',candidates=[dict(instrument='I2',score='2'),dict(instrument='I1',score='2')])]),business(snapshots=[snap()],ranked=['I1','I2']))

# Q24: calendar inputs are frozen session close instants, not inferred UTC offsets.
calendars={
 'five':(['2025-01-06T21:00:00Z','2025-01-07T21:00:00Z','2025-01-08T21:00:00Z','2025-01-09T21:00:00Z','2025-01-10T21:00:00Z'],5,'2025-01-10T20:55:00Z'),
 'one':(['2025-01-06T21:00:00Z'],1,'2025-01-06T20:55:00Z'),
 'early':(['2025-11-21T21:00:00Z','2025-11-24T21:00:00Z','2025-11-25T21:00:00Z','2025-11-26T21:00:00Z','2025-11-28T18:00:00Z'],5,'2025-11-28T17:55:00Z'),
 'dst':(['2025-03-06T21:00:00Z','2025-03-07T21:00:00Z','2025-03-10T20:00:00Z','2025-03-11T20:00:00Z','2025-03-12T20:00:00Z'],5,'2025-03-12T19:55:00Z')}
for name in ['five','one','early','dst','halt','no_quote']:
 closes,horizon,due_s=calendars.get(name,calendars['five']);due=ns(due_s)
 start=ns(closes[0][:10]+'T15:00:00Z');until=due+10**9
 ops=[dict(op='schedule',at_ns=start,horizon=horizon,closes_ns=[ns(x) for x in closes]),dict(op='due',at_ns=due),dict(op='quote',at_ns=due+999999999,bid='100',ask='100.02',size='1000',status='TRADABLE'),dict(op='snapshot',at_ns=due+999999999,label='before_eligible')]
 if name=='halt':ops+=[dict(op='quote',at_ns=until,bid='100',ask='100.02',size='1000',status='HALTED'),dict(op='snapshot',at_ns=until,label='waiting'),dict(op='quote',at_ns=until+10**9,bid='100',ask='100.02',size='1000',status='TRADABLE')]
 elif name=='no_quote':ops+=[dict(op='snapshot',at_ns=until,label='waiting')]
 else:ops+=[dict(op='quote',at_ns=until,bid='100',ask='100.02',size='1000',status='TRADABLE')]
 last=max(x['at_ns'] for x in ops)+100;ops+=[dict(op='snapshot',at_ns=last,label='final')]
 sn=[snap('before_eligible',cash='9500',qty='5',sell='5',pending=True)]
 if name in ['halt','no_quote']:sn+=[snap('waiting',cash='9500',qty='5',sell='5',pending=True)]
 filled=name!='no_quote';sn+=[snap(cash='9998.75' if filled else '9500',qty='0' if filled else '5',sell='0' if filled else '5',pending=not filled)]
 case('Q24_'+name,ops,business([decision('EXIT',qty='-5')],sn,[dict(id='EXIT',quantity='-5',price='99.95',fee='1')] if filled else [],due=due),cash='9500',holdings=[dict(instrument='I1',qty='5',mark='100')],start_ns=start)

# Q25: risk observations update native holdings marks; fresh valid exits remain possible.
for name,equity,daily,drawdown in [('daily','9800',True,False),('daily_below','9800.01',False,False),('drawdown','9200',True,True),('drawdown_below','9200.01',True,False),('unknown',None,False,False)]:
 ops=[step('mark',equity=equity,mark_ref='E-Q25-'+name),order('D',instrument='I2'),dict(order('T',instrument='I2'),route='target'),dict(order('H',instrument='I2'),route='setholdings'),step('snapshot',label='entry_checked'),step('due',at=2*10**9),step('quote',at=3*10**9,bid='100',ask='100.02',size='1000',status='TRADABLE')]
 allowed=not daily and equity is not None
 reason='OK' if allowed else 'NAV_UNKNOWN' if equity is None else 'DAILY_HALT'
 # Positive SetHoldings/target control is separate: below-boundary entry uses direct route,
 # while threshold negatives exercise actual native APIs for all three entry paths.
 if allowed:ops=[ops[0],ops[1]]+ops[4:]
 ids=['D'] if allowed else ['D','T','H']
 ds=[decision(i,allowed,reason,'1',True if allowed else None,True if allowed else None) for i in ids]+[decision('EXIT',qty='-5',gross=True,symbol=True)]
 sn=[snap('entry_checked',cash='9000',reserve='101.07001' if allowed else '0',qty='5',daily=daily,drawdown=drawdown),snap(cash='9498.75',reserve='101.07001' if allowed else '0',qty='0',daily=daily,drawdown=drawdown)]
 if name=='daily_below':
  ops.append(dict(order('POST',instrument='I2'),at_ns=D+3*10**9));ds.append(decision('POST',False,'DAILY_HALT'));sn[-1]['daily']=True
 case('Q25_'+name,finish(ops),business(ds,sn,[dict(id='EXIT',quantity='-5',price='99.95',fee='1')]),cash='9000',holdings=[dict(instrument='I1',qty='5',mark='200')],checks=('cash','limits','halts'),exit_due_ns=D+2*10**9)
for name,equity,explicit,day,dd in [('midnight_daily','9800',False,True,False),('new_session_daily','9800',True,False,False),('new_session_drawdown','9200',True,False,True)]:
 ops=[step('mark',equity=equity,mark_ref='E-Q25-'+name),step('session',at=ns('2025-01-07T14:30:00Z' if explicit else '2025-01-07T00:00:00Z')-D,explicit=explicit,session_id='2025-01-07'),dict(order(instrument='I2'),at_ns=ns('2025-01-07T15:00:00Z'))]
 reason='DAILY_HALT' if day else 'DRAWDOWN_HALT' if dd else 'OK'
 case('Q25_'+name,finish(ops),business([decision(allow=not(day or dd),reason=reason,gross=True if not(day or dd) else None,symbol=True if not(day or dd) else None)],[snap(cash='9000',reserve='101.07001' if not(day or dd) else '0',qty='5',daily=day,drawdown=dd)]),cash='9000',holdings=[dict(instrument='I1',qty='5',mark='200')],checks=('cash','limits','halts'))

# Q26: scripted local executions enter native accounting, never sidecar holding edits.
ops=[order('S','-4'),order('B','-3'),order('ENTRY',instrument='I2'),step('cancel_request',id='S'),step('snapshot',label='request'),step('execution',at=10**9,id='S',execution_id='e1',qty='-2',price='99.95',fee='1'),step('snapshot',at=10**9,label='partial'),step('execution',at=10**9,id='S',execution_id='e1',qty='-2',price='99.95',fee='1'),step('cancel_ack',at=2*10**9,id='S'),step('cancel_ack',at=2*10**9,id='S')]
case('Q26_sequence',finish(ops),business([decision('S',qty='-4'),decision('B',False,'SELL_SHARES'),decision('ENTRY',False,'DAILY_HALT')],[snap('request',cash='5000',qty='5',sell='4',daily=True),snap('partial',cash='5198.9',qty='3',sell='2',daily=True),snap(cash='5198.9',qty='3',daily=True)],[dict(id='S',quantity='-2',price='99.95',fee='1')]),cash='5000',holdings=[dict(instrument='I1',qty='5',mark='100')],daily=True,scripted=True,checks=('cash','halts'),day_start='5500',high_water='5500',initial_halt=dict(kind='seed_latch',reason='DAILY_LOSS',at_ns=D-10**9,ref='E-Q26-initial-halt'))
for state in ['STALE','AMBIGUOUS']:
 case('Q26_'+state.lower(),finish([order('S','-4')]),business([decision('S',False,'DESTINATION_STATE')],[snap(cash='5000',qty='5')]),cash='5000',holdings=[dict(instrument='I1',qty='5',mark='100')],destination_state=state)

# Q32: expected rejection records carry no scientific/business output.
for mode in ['complete','empty','missing','tampered','config_tampered','download','history']:
 err={'empty':'EMPTY_STORE','missing':'MISSING_INPUT','tampered':'HASH_MISMATCH','config_tampered':'HASH_MISMATCH','download':'PROVIDER_DENIED','history':'PROVIDER_DENIED'}.get(mode)
 case('Q32_'+mode,finish([]),dict(guard_error=err,provider_calls=1 if mode in ['download','history'] else 0,business=None) if err else business(snapshots=[snap()]),ingress=mode)

# Q33: each arm owns a separate native algorithm. No model/forecast is evaluated.
for mode in ['fill','no_fill','unresolved']:
 ops=[order(qty='5')]
 cash='10000';seed=[];fills=[];ds=[decision(qty='5')];q='0'
 if mode=='fill':
  ops+=[step('quote',at=10**9,bid='100',ask='100.02',size='1000',status='TRADABLE')];cash='9498.64995';q='5';fills=[dict(id='A',quantity='5',price='100.07001',fee='1')]
 elif mode=='no_fill':ops+=[step('cancel_request',at=5*10**9,id='A'),step('cancel_ack',at=5*10**9,id='A')]
 else:ops=[];cash='9000';seed=[dict(instrument='I1',qty='10',mark='100')];q='10';ds=[]
 b=business(ds,[snap(cash=cash,qty=q)],fills)
 expected=dict(arms={a:dict(accounting=copy.deepcopy(b),evaluation=dict(opportunities=1,failures=1 if mode=='unresolved' else 0,run_cost='0.25',terminal_value=None,status=mode)) for a in ['A','B','C','N']},diagnostic_invariance=True)
 claim_path='../lean_terminal_017/evidence/Q01_explicit_unknown.attempt09.json'
 claim=dict(path=claim_path,sha256=hashlib.sha256((R/claim_path).read_bytes()).hexdigest()) if mode=='unresolved' else None
 case('Q33_'+mode,finish(ops),expected,cash='9000' if mode=='unresolved' else '10000',holdings=seed,arm_mode=mode,run_cost='0.25',reused_claim=claim)

# Provenance fields are authored from fixture source instants, never engine dispatch.
for c in CASES:
 quotes=[s for s in c['steps'] if s['op']=='quote']
 for i,s in enumerate(quotes,1):s['quote_id']=c['case_id']+'-q'+str(i)
 bs=[a['accounting'] for a in ORACLES[c['case_id']]['arms'].values()] if c['fixture']=='Q33' else [ORACLES[c['case_id']]]
 for b in bs:
  if 'snapshots' not in b:continue
  b['risk_records']=[]
  for f in b['fills']:
   if c['fixture']=='Q26':source_id='e1';at=D+10**9
   else:
    eligible=(b['due_ns']+10**9) if c['fixture']=='Q24' else D+(3 if c['fixture']=='Q25' else 1)*10**9
    source=next(s for s in quotes if s['status']=='TRADABLE' and s['at_ns']>=eligible);source_id=source['quote_id'];at=source['at_ns']
   f.update(source_id=source_id,source_ns=at,native_dispatch_ns=((at+99)//100)*100)
  if c['fixture']=='Q26' and c.get('initial_halt'):b['risk_records']=[c['initial_halt']]
  if c['fixture']=='Q25':
   mark=c['steps'][0];equity=mark['equity'];ref=mark['mark_ref'];name=c['case_id'][4:]
   rows=[dict(kind='mark',at_ns=D,ref=ref,equity=equity)]
   initial_daily=name!='daily_below' and name!='unknown';initial_dd=name in ['drawdown','new_session_drawdown']
   for triggered,reason in [(initial_daily,'DAILY_LOSS'),(initial_dd,'DRAWDOWN')]:
    if triggered:rows.append(dict(kind='latch',reason=reason,at_ns=D,ref=ref,equity=equity,day_start='10000',high_water='10000'))
   if name=='daily_below':rows.append(dict(kind='latch',reason='DAILY_LOSS',at_ns=D+3*10**9,ref='fill:EXIT',equity='9498.75',day_start='10000',high_water='10000'))
   session=next((s for s in c['steps'] if s['op']=='session' and s['explicit']),None)
   if session:rows.append(dict(kind='session_reset',at_ns=session['at_ns'],session_id=session['session_id'],day_start=equity,high_water='10000',previous_daily=True))
   b['risk_records']=rows

def main():
 dest=R/'fixtures'
 if (dest/'manifest.json').exists(): raise SystemExit('Frozen manifest exists; version rather than overwrite')
 dest.mkdir(exist_ok=True)
 files={'input.json':dict(source_pin=PIN,seed=894,capture_mode='fixture',cases=CASES),'config.json':dict(trading_enabled=False,allow_paper_orders=False,alpaca_live_trade=False,network='none',source_pin=PIN)}
 files.update({cid+'.expected.json':e for cid,e in ORACLES.items()})
 for name,obj in files.items(): (dest/name).write_text(json.dumps(obj,indent=2,ensure_ascii=False)+'\n')
 manifest={name:hashlib.sha256((dest/name).read_bytes()).hexdigest() for name in sorted(files)}
 (dest/'manifest.json').write_text(json.dumps(dict(sha256=manifest),indent=2)+'\n')
 print(len(CASES),'frozen new cases; no native execution')
if __name__=='__main__':main()

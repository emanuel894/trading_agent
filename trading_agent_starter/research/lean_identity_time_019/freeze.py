"""Author the synthetic test vector bundle before execution; never read host output."""
from pathlib import Path
from copy import deepcopy
from decimal import Decimal
import hashlib
import json

ROOT = Path(__file__).parent / 'fixtures_v2'
D = 1736175600000000000  # 2025-01-06T15:00:00Z
S = 1_000_000_000
B = D + 84600*S  # Jan7 14:30Z


def quote(id, offset, ask='100.02', bid='100', **kw):
    q = dict(id=id, kind='quote', instrument='I1', event_ns=D+offset,
             available_ns=D+offset, receipt_ns=None, sequence=1,
             bid=bid, ask=ask, size='1000', unit='shares', factor=None,
             unit_evidence=None, conditions=['R'], gap=False, normalization='Raw',
             source='SIP_FIXTURE', tape='A', exchange='N', evidence='E-'+id)
    q.update(kw)
    return q


def dec(value):
    return format(Decimal(value).normalize(), 'f')


cases, expected = [], {}


def add(name, *, group=None, decision=None, events=None, fill='q1', price='100.07001',
        reason=None, quantity=5, seed=0, **kw):
    group = group or name[:3]
    c = dict(case_id=name, fixture=group, decision_ns=D, status='TRADABLE',
             decision_quote=quote('q0', -S//2, ask='100', bid='99.99'),
             events=events if events is not None else [quote('q1', S)],
             quantity=str(quantity), seed_quantity=str(seed), mapping='valid',
             normalization='Raw', structural=None, factors=[], future_records=[])
    if decision is not None:
        c['decision_quote'].update(decision)
    c.update(kw)
    admitted = reason is None or reason in ('NO_VALID_QUOTE', 'CAPACITY', 'CONFLICT')
    filled = fill is not None and admitted
    actual_fill = None
    if filled:
        q = next(q for q in c['events'] if q['id'] == fill)
        actual_fill = dict(quote_id=fill, instrument='I1', event_ns=q['event_ns'],
                           available_ns=q['available_ns'], receipt_ns=q['receipt_ns'],
                           dispatch_ns=((q['available_ns']+99)//100)*100,
                           quantity=str(quantity), price=price, fee='1')
    cash = Decimal('10000')-Decimal(price)*quantity-1 if filled else Decimal('10000')
    exp = dict(admitted=admitted, reason=reason, fill=actual_fill,
               cash=dec(cash), quantity=dec(Decimal(seed)+(quantity if filled else 0)),
               native_order_statuses=(['Submitted', 'Filled'] if filled else
                   ['Submitted', 'CancelPending', 'Canceled'] if admitted else []),
               decision_receipt_ns=c['decision_quote']['receipt_ns'],
               clock_mode='simulated_historical' if c['decision_quote']['receipt_ns'] is None else 'prospective',
               routes=[], structural=None, raw_marks=[])
    exp['contract_state'] = 'ABORTED_CONFLICT' if reason == 'CONFLICT' else 'COMPLETE'
    if actual_fill:
        actual_fill.update(evidence=q['evidence'], source=q['source'], tape=q['tape'],
            precision='nanosecond',clock_mode='simulated_historical' if q['receipt_ns'] is None else 'prospective')
    if group == 'Q04':
        t = c['decision_ns']; selected = 'I1' if t < B else 'I2'
        if c['mapping'] == 'valid':
            c['events'][0]['instrument'] = selected
            c['events'] += [quote('class_quote',t-D+S, instrument='I3', sequence=2)]
            c['events'] += [quote('other_listing',t-D+S,instrument='I2' if selected=='I1' else 'I1',sequence=3)]
        c['decision_quote']['instrument'] = selected
        if selected=='I2':
            c['decision_quote'].update(event_ns=t,available_ns=t)
        exp['routes'] = [selected] if c['mapping'] == 'valid' else []
        exp['held_identity'] = 'I1'; exp['class_separate'] = True
        exp['held_quantity'] = '10'
        if actual_fill: actual_fill['instrument'] = selected
    if group == 'Q05': exp['structural'] = c['structural']
    if group == 'Q11': exp['raw_marks'] = ['100','50'] if c['normalization']=='Raw' else []
    cases.append(c); expected[name] = exp
    return c


# Q04: half-open interval is evaluated using int64 ns, never SymbolCache/current ticker.
for label, t in [('before',B-1),('at',B),('after',B+1)]:
    add('Q04_'+label, seed=10, decision_ns=t,
        decision={'event_ns':t-S//2,'available_ns':t-S//2},
        events=[quote('q1',t-D+S)],fill=None if label=='before' else 'q1',
        reason='NO_VALID_QUOTE' if label=='before' else None)
for kind in ('missing','overlap'):
    add('Q04_'+kind, seed=10, mapping=kind, decision_ns=B,
        fill=None, reason='IDENTITY_UNRESOLVED')

# Q05: structural fixture evidence is not knowledge/quote/status evidence.
struct = dict(valid_from_ns=D-1800*S, valid_to_ns=B, publication_ns=None,
              retrieved_utc='2026-10-18T00:00:00Z', receipt_ns=None,
              resolution='exact_interval', capture_mode='fixture', admission='fixture_only')
add('Q05_structural_unknown_publication',structural=struct)
add('Q05_date_only',structural={**struct,'resolution':'date_only'},fill=None,reason='IDENTITY_UNRESOLVED')
add('Q05_conflicting_class',structural={**struct,'conflicting_class':True},fill=None,reason='IDENTITY_UNRESOLVED')
add('Q05_late_halt',status='UNKNOWN',events=[dict(id='halt',kind='halt',event_ns=D-S,
    available_ns=D+2*S,receipt_ns=None,sequence=2,evidence='E-H'),quote('q1',S)],fill=None,reason='STATUS_UNKNOWN',structural=struct)

# Q06: each malformed/boundary input has no substitute decision quote; q1 remains fixed.
add('Q06_age_exact',decision={'event_ns':D-2*S,'available_ns':D-2*S})
add('Q06_age_plus_ns',decision={'event_ns':D-2*S-1,'available_ns':D-2*S-1},fill=None,reason='STALE')
add('Q06_future_availability',decision={'available_ns':D+1},fill=None,reason='UNAVAILABLE')
add('Q06_spread_exact',decision={'bid':'99.9','ask':'100.1'})
add('Q06_spread_over',decision={'bid':'99.9','ask':'100.1001'},fill=None,reason='SPREAD')
for name,bid,ask in [('locked','100','100'),('crossed','101','100'),('zero_bid','0','100'),('zero_ask','99','0'),('nan_bid','NaN','100'),('nan_ask','99','NaN')]:
    add('Q06_'+name,decision={'bid':bid,'ask':ask},fill=None,reason='MALFORMED_PRICE')
for name,conditions in [('mixed',['R','X']),('missing',None)]:
    add('Q06_conditions_'+name,decision={'conditions':conditions},fill=None,reason='CONDITION')
add('Q06_unknown_status',status='UNKNOWN',fill=None,reason='STATUS_UNKNOWN')

# Q07: first valid source-native quote, with inclusive delay/deadline.
q07=[quote('pre',S-1,'90','89.99'),quote('crossed',S,'100','101'),
     quote('first',S+1),quote('cheaper',2*S,'90','89.99')]
add('Q07_first',events=q07,fill='first')
add('Q07_deadline_exact',events=[quote('q1',5*S)])
add('Q07_deadline_plus_ns',events=[quote('late',5*S+1)],fill=None,reason='NO_VALID_QUOTE')
add('Q07_missing',events=[],fill=None,reason='NO_VALID_QUOTE')

# Q08: same 100ns tick, reversed physical order; availability wins over sequence/event.
qa=quote('seq1',S+1,sequence=1);qb=quote('seq2',S+2,'100.03',sequence=2)
add('Q08_event_order',events=[qb,qa],fill='seq1')
ra={**qa,'available_ns':D+S+80,'receipt_ns':D+S+80};rb={**qb,'available_ns':D+S+20,'receipt_ns':D+S+20}
add('Q08_receipt_order',events=[ra,rb],fill='seq2',price='100.080015')
for qn,hn,label in [(20,30,'quote_before_halt'),(30,20,'halt_before_quote')]:
    q=quote('q1',S,available_ns=D+S+qn)
    h=dict(id='halt',kind='halt',event_ns=D+S+hn,available_ns=D+S+hn,receipt_ns=None,sequence=2,evidence='E-H')
    add('Q08_'+label,events=[q,h],fill='q1' if qn<hn else None,reason=None if qn<hn else 'NO_VALID_QUOTE')
add('Q08_late_receipt',events=[quote('late',S,available_ns=D+6*S,receipt_ns=D+6*S)],fill=None,reason='NO_VALID_QUOTE')
add('Q08_stale_event',events=[quote('old',-2*S,available_ns=D+S)],fill=None,reason='NO_VALID_QUOTE')
add('Q08_duplicate',events=[qa,deepcopy(qa)],fill='seq1')
# Simultaneous conflicting versions abort before either payload is used; file permutations agree.
conflicting=[qa,{**qa,'ask':'100.03'},quote('must_not_consume',2*S)]
add('Q08_conflict',events=conflicting,fill=None,reason='CONFLICT')
add('Q08_conflict_reversed',events=list(reversed(conflicting)),fill=None,reason='CONFLICT')
add('Q08_tie_sequence',events=[{**qb,'available_ns':D+S+2},{**qa,'available_ns':D+S+2}],fill='seq1')
add('Q08_tie_event_id',events=[{**qb,'id':'z','sequence':1,'available_ns':D+S+2},
    {**qa,'id':'a','sequence':1,'available_ns':D+S+2}],fill='a')

# Q09: paired prefix invariance; appended versions stay outside the earlier business prefix.
add('Q09_baseline',events=deepcopy(q07),fill='first')
add('Q09_future_append',events=deepcopy(q07)+[quote('future',6*S,'1','0.9999')],fill='first',
    future_records=[dict(id='q0-v2',kind='correction',available_ns=D+10*S,revision_of='q0',ask='1'),
                    dict(id='symbol-v2',kind='symbol',available_ns=D+11*S),
                    dict(id='action-v2',kind='action',available_ns=D+12*S),
                    dict(id='prediction',kind='prediction',available_ns=D+13*S)])
add('Q09_prospective',decision={'receipt_ns':D+S//10,'available_ns':D+S//10},events=deepcopy(q07),fill=None,reason='UNAVAILABLE')

# Q10: capacity uses verified same-side shares, separately from decision validity.
add('Q10_five_shares',events=[quote('q1',S,size='50')])
add('Q10_six_shares',events=[quote('q1',S,size='50')],quantity=6,fill=None,reason='CAPACITY')
add('Q10_round_lot',events=[quote('q1',S,size='0.5',unit='round_lot',factor='100',unit_evidence='E-UNIT')])
for label,kw in [('unknown_factor',dict(size='0.5',unit='round_lot')),('missing_unit',dict(unit=None)),
                 ('zero',dict(size='0')),('negative',dict(size='-1')),('nan',dict(size='NaN')),
                 ('tape_gap',dict(gap=True)),('source_gap',dict(gap=True,source='GAPPED')),
                 ('sequence_gap',dict(gap=True,sequence=3)),('conditions',dict(conditions=['R','X']))]:
    add('Q10_'+label,events=[quote('q1',S,**kw)],fill=None,reason='NO_VALID_QUOTE')
add('Q10_trade_bar_only',events=[dict(id='trade',kind='trade',event_ns=D+S,available_ns=D+S,receipt_ns=None,sequence=1,price='90',evidence='E-T'),
    dict(id='bar',kind='bar',event_ns=D+2*S,available_ns=D+2*S,receipt_ns=None,sequence=2,price='90',evidence='E-B')],fill=None,reason='NO_VALID_QUOTE')

# Q11: raw ingress and seeded raw marks; Q12 action/accounting explicitly not executed.
factor=dict(id='F1',available_ns=D-S,effective_ns=D+3600*S,factor='0.5')
raw=[quote('q1',S),quote('post_raw',3600*S,'50.01','50')]
add('Q11_raw',seed=10,events=raw,factors=[factor],
    adjusted_decoy=quote('adjusted_prior',-S,'50.01','50',normalization='Adjusted'))
add('Q11_wrong_metadata',seed=10,normalization='Adjusted',events=raw,factors=[factor],fill=None,reason='NORMALIZATION')
add('Q11_future_factor',seed=10,events=raw,factors=[factor,{**factor,'id':'F2','available_ns':D+7200*S,'factor':'0.25'}],
    adjusted_decoy=quote('adjusted_prior',-S,'50.01','50',normalization='Adjusted'))

bundle=dict(schema_version=1,capture_mode='fixture',rights_ref='synthetic-created-for-issue19',
            decision_origin_ns=D,identity_boundary_ns=B,source_pin='d4cac37514427c84d40064cecbf3f0e6be4b0137',
            identities=[dict(instrument='I1',issuer='U1',class_id='A',listing='L1',ticker='AAA',start_ns=D-1800*S,end_ns=B,engine_date='2025-01-01'),
                        dict(instrument='I2',issuer='U2',class_id='B',listing='L2',ticker='AAA',start_ns=B,end_ns=B+86400*S,engine_date='2025-01-07'),
                        dict(instrument='I3',issuer='U1',class_id='B',listing='L3',ticker='AAB',start_ns=D-1800*S,end_ns=B+86400*S,engine_date='2025-01-01')],cases=cases)
for c in cases:
    c['identities']=deepcopy(bundle['identities'])
    if c['mapping']=='missing':
        c['identities']=[r for r in c['identities'] if r['instrument']!='I2']
    if c['mapping']=='overlap': c['identities'][0]['end_ns']=B+S
    e=expected[c['case_id']]
    e['positions']={'I1':c['seed_quantity'],'I2':'0','I3':'0'}
    if e['fill']:
        inst=e['fill']['instrument'];e['positions'][inst]=dec(Decimal(e['positions'][inst])+Decimal(c['quantity']))
    e['initial_average']='100' if c['seed_quantity']!='0' else '0'
ROOT.mkdir(exist_ok=True)
def write(p,x):p.write_text(json.dumps(x,indent=2,allow_nan=False)+'\n')
write(ROOT/'input.json',bundle)
for k,v in expected.items():write(ROOT/(k+'.expected.json'),v)
files=sorted(ROOT.glob('*.json'))
write(ROOT/'manifest.json',dict(sha256={p.name:hashlib.sha256(p.read_bytes()).hexdigest() for p in files if p.name!='manifest.json'}))
print('Frozen',len(cases),'variants; engine runs not executed')

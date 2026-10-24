"""Frozen retrospective observation admission into the no-order native lifecycle.

Consumes the already verified private projection, not a provider or credential.
"""
from collections import Counter
from hashlib import sha256
from decimal import Decimal, InvalidOperation
from agent.audit_market import nanoseconds as ns
from research.sip_lean_bridge_20261024.bridge import encode, ceil_ns

MINUTE=60_000_000_000


class PreparationBlocked(Exception):
    pass


def session(opened, closed, evidence):
    result={'open_ns':ns(opened),'close_ns':ns(closed),'evidence':evidence}
    if result['open_ns']>=result['close_ns'] or not evidence:raise PreparationBlocked('INVALID_SESSION')
    return result


def prepare(source, sessions):
    required={'scope':'PRIVATE_OBSERVATION_COMPATIBILITY_ONLY','status':'UNQUALIFIED',
              'orders_enabled':False,'historical_receipt_proven':False,'symbol':'SPY',
              'provider':'alpaca','feed':'sip','quote_size_units':'UNQUALIFIED_PROVIDER_NATIVE'}
    if any(source.get(k)!=v for k,v in required.items()):raise PreparationBlocked('OBSERVATION_SCOPE_REQUIRED')
    if not sessions:raise PreparationBlocked('SESSION_REQUIRED')
    sessions=sorted(sessions,key=lambda x:x['open_ns'])
    for i,s in enumerate(sessions):
        if (not s.get('evidence') or s['open_ns']>=s['close_ns']
            or (i and sessions[i-1]['close_ns']>s['open_ns'])):raise PreparationBlocked('INVALID_SESSION')
    groups={};reject=Counter();total=0
    for kind in ('bars','quotes'):
        for index,row in enumerate(source[kind]):
            total+=1
            if total>50000:raise PreparationBlocked('EVENT_CAP')
            start=row['source_ns'];at=start+(MINUTE if kind=='bars' else 0)
            try:
                fields=('open','high','low','close','volume') if kind=='bars' else ('bid','ask','bid_size','ask_size')
                numbers={k:Decimal(row[k]) for k in fields}
                if any(not n.is_finite() or n<0 or (n==0 and k!='volume') for k,n in numbers.items()):raise ValueError()
                if kind=='bars':
                    if (start%MINUTE or not numbers['low']<=min(numbers['open'],numbers['close'])<=max(numbers['open'],numbers['close'])<=numbers['high']):raise ValueError()
                elif (numbers['bid']>=numbers['ask'] or row['conditions']!=['R'] or row['tape'] not in ('A','B','C')
                      or not row['bid_exchange'] or not row['ask_exchange']
                      or (numbers['ask']-numbers['bid'])*10000>20*(numbers['ask']+numbers['bid'])/2):raise ValueError()
            except (ValueError,TypeError,KeyError,InvalidOperation):
                reject['INVALID_BAR' if kind=='bars' else 'INVALID_QUOTE']+=1;continue
            s=next((s for s in sessions if s['open_ns']<=start and (at<=s['close_ns'] if kind=='bars' else at<s['close_ns'])),None)
            if s is None:reject['OUTSIDE_SESSION']+=1;continue
            event={'kind':kind,'source_index':index,'source_ns':start,'emission_ns':at,
                   'historical_received_at':None,'availability_proven':False,'execution_admitted':False,
                   'state':'UNQUALIFIED','size_units':'UNQUALIFIED_PROVIDER_NATIVE',
                   'source_row_sha256':sha256(encode(row)).hexdigest(),
                   'data':{k:row[k] for k in fields}}
            if kind=='quotes':event['same_time_variants']=row['same_time_variants']
            groups.setdefault(ceil_ns(at),[]).append(event)
    batches=[];trace=bytearray()
    for slot,events in sorted(groups.items()):
        events.sort(key=lambda e:(e['emission_ns'],e['kind'],e['source_row_sha256'],e['source_index']))
        digest=sha256(encode(events).rstrip(b'\n')).hexdigest()
        batches.append({'native_ns':slot,'payload':events,'payload_sha256':digest})
        trace.extend(f'{slot}|{digest}\n'.encode())
    if not batches:raise PreparationBlocked('NO_OBSERVATIONS')
    result={'version':'SIP_NATIVE_OBSERVATION_ENGINE_V1','mode':'OBSERVATION_ONLY',
            'execution_policy':'DENY_ALL','identity':'ARCHIVE_DIAGNOSTIC_ALIAS_NOT_HISTORICAL_LISTING',
            'historical_receipt_proven':False,'source_projection_sha256':sha256(encode(source)).hexdigest(),
            'sessions':sessions,'batch_order':'ATOMIC_NO_WITHIN_BATCH_EXECUTION_ORDER',
            'batches':batches,'events':sum(len(b['payload']) for b in batches),
            'expected_trace_sha256':sha256(trace).hexdigest(),'rejections':dict(sorted(reject.items()))}
    if len(encode(result))>50*1024*1024:raise PreparationBlocked('BYTE_CAP')
    return result

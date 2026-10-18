"""Independent exact comparison. No time/price/order tolerances or output sorting."""
import json
import hashlib
from pathlib import Path

class GateMismatch(AssertionError):
    pass

def compare_business(actual, expected, path='$'):
    if type(actual) is not type(expected):
        raise GateMismatch(f'{path}: type {type(actual).__name__} != {type(expected).__name__}')
    if isinstance(expected, dict):
        if actual.keys() != expected.keys():
            raise GateMismatch(f'{path}: keys differ {set(actual)^set(expected)}')
        for key in expected:
            compare_business(actual[key], expected[key], path+'.'+key)
    elif isinstance(expected, list):
        if len(actual) != len(expected):
            raise GateMismatch(f'{path}: list lengths differ')
        for i, (a,e) in enumerate(zip(actual,expected)):
            compare_business(a,e,f'{path}[{i}]')
    elif actual != expected:
        raise GateMismatch(f'{path}: {actual!r} != {expected!r}')
    return True

def compare_file(output, oracle, input_path=None):
    actual=json.loads(Path(output).read_text())
    if not actual.get('execution_complete'):
        raise GateMismatch('Native execution incomplete: '+str(actual.get('technical_error')))
    if actual.get('network_denied') != {'non_loopback_interfaces':0,'testnet_socket_result':'NetworkUnreachable'}:
        raise GateMismatch('Runtime network-denial sentinel failed')
    if actual.get('engine_status') != 'Completed' or not actual.get('native_end_observed'):
        raise GateMismatch('Native AlgorithmManager end not observed')
    compare_business(actual['business'],json.loads(Path(oracle).read_text()))
    if input_path is not None:
        bundle=json.loads(Path(input_path).read_text())
        if actual['input_sha256']!=hashlib.sha256(Path(input_path).read_bytes()).hexdigest():
            raise GateMismatch('Input binding mismatch')
        if actual['source_pin']!=bundle['source_pin']:
            raise GateMismatch('Source pin mismatch')
        case=next(c for c in bundle['cases'] if c['case_id']==actual['case_id'])
        crosswalk=actual['crosswalk']
        if len({r['engine_sid'] for r in crosswalk})!=3:
            raise GateMismatch('Engine identities collapsed')
        for native,external in zip(crosswalk,bundle['identities']):
            compare_business({k:v for k,v in native.items() if k!='engine_sid'},external)
        target=actual['business']['routes'][0] if actual['business']['routes'] else 'I1'
        target_sid=next(r['engine_sid'] for r in crosswalk if r['instrument']==target)
        for order in actual['native_orders']:
            if order['sid']!=target_sid:
                raise GateMismatch('Native order SID is not the admitted instrument')
        events=sorted(case['events'],key=lambda e:(e['available_ns'],e['sequence'],e['id']))
        consumed=[];seen={}
        i=0
        while i<len(events):
            e=events[i];key=(e['available_ns'],e['sequence'],e['id'])
            group=[x for x in events[i:] if (x['available_ns'],x['sequence'],x['id'])==key]
            raw=json.dumps(e,separators=(',',':'),ensure_ascii=False)
            conflict=len({json.dumps(x,separators=(',',':'),ensure_ascii=False) for x in group})>1
            if conflict or (e['id'] in seen and seen[e['id']]!=raw):
                consumed.append(dict(id=e['id'],result='CONFLICT',available_ns=e['available_ns'],dispatch_ns=((e['available_ns']+99)//100)*100))
                break
            if e['id'] in seen:
                row=dict(id=e['id'],result='DUPLICATE',available_ns=e['available_ns'],dispatch_ns=((e['available_ns']+99)//100)*100)
            else:
                row={k:e[k] for k in ['id','kind','event_ns','available_ns','receipt_ns','sequence']}
                row['dispatch_ns']=((e['available_ns']+99)//100)*100
                row['sha256']=hashlib.sha256(raw.encode()).hexdigest()
                seen[e['id']]=raw
            consumed.append(row);i+=1
        compare_business(actual['envelope_journal'],consumed,'$.envelope_journal')
    return True

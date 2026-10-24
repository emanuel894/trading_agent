"""Offline, source-bound SIP observation projection. No acquisition or orders."""
import argparse
from collections import Counter
import hashlib
import json
from pathlib import Path
import sqlite3
from urllib.parse import urlsplit, parse_qs

from agent.audit_store import EvidenceStore, AuditFailure, strict_json
from agent.audit_market import nanoseconds, validate_bar, validate_quote

ORIGINAL_DB_SHA='4ac083a8c23c2c24c4bd0d4bb08467f43d626d5dd959bab4b2e8561a9272f7c7'
START=1736953200000000000
END=1736953500000000000


class BridgeBlocked(Exception):
    pass


def encode(value):
    return json.dumps(value,sort_keys=True,separators=(',',':'),allow_nan=False).encode()+b'\n'


def ceil_ns(value):
    return ((value+99)//100)*100


class ReadOnlyEvidence(EvidenceStore):
    """Reuse existing verification/get/raw methods without initializing a store."""
    def __init__(self, root):
        self.root=Path(root).resolve()
        self.objects=self.root/'objects'
        db=self.root/'evidence.sqlite'
        if not db.is_file() or db.is_symlink() or not self.objects.is_dir() or self.objects.is_symlink():
            raise BridgeBlocked('EXISTING_DATABASE_AND_OBJECTS_REQUIRED')
        self.db=sqlite3.connect(db.as_uri()+'?mode=ro',uri=True)
        self.db.row_factory=sqlite3.Row

    def raw(self, record):
        sha=record['blob_sha']
        if not isinstance(sha,str) or len(sha)!=64 or any(c not in '0123456789abcdef' for c in sha):
            raise BridgeBlocked('INVALID_OBJECT_REFERENCE')
        p=self.objects/sha
        if p.is_symlink() or not p.is_file() or p.stat().st_size>40_000_000:
            raise BridgeBlocked('RAW_OBJECT_MISSING_OR_UNSAFE')
        return super().raw(record)


def unique_rows(rows, *, observation_only=False):
    selected={};duplicates=0;times={}
    for row in rows:
        basis={k:v for k,v in row.items() if k!='source_refs'}
        key=(row['source_ns'],encode(basis))
        prior=selected.get(key)
        if prior is None:
            selected[key]={**row,'source_refs':list(row.get('source_refs',[]))}
            times.setdefault(row['source_ns'],set()).add(key)
        else:
            prior['source_refs'].extend(row.get('source_refs',[]));duplicates+=1
    if not observation_only and any(len(v)>1 for v in times.values()):
        raise BridgeBlocked('AMBIGUOUS_SAME_TIMESTAMP')
    result=[]
    for key in sorted(selected):
        row=selected[key]
        row['source_refs'].sort(key=lambda r:(r['record_id'],r['row_index']))
        if observation_only:row['same_time_variants']=len(times[row['source_ns']])
        result.append(row)
    # Tie serialization by content is NOT evidence of temporal ordering.
    return result,duplicates


def project(root, *, expected_sha=ORIGINAL_DB_SHA):
    db=Path(root)/'evidence.sqlite'
    if not db.is_file() or db.is_symlink():raise BridgeBlocked('EXISTING_DATABASE_REQUIRED')
    if hashlib.sha256(db.read_bytes()).hexdigest()!=expected_sha:raise BridgeBlocked('DATABASE_BINDING_CHANGED')
    store=ReadOnlyEvidence(root)
    try:
        if store.db.execute('pragma integrity_check').fetchone()[0]!='ok':raise BridgeBlocked('SQLITE_INTEGRITY')
        verified=store.verify()
        if not verified['records']:raise BridgeBlocked('EMPTY_STORE')
        rows={'bars':[],'quotes':[]};expected={};complete=set();rejected=Counter();excluded=0;seen=Counter();tokens={'bars':set(),'quotes':set()};pages=Counter()
        for record in store.records('http'):
            url=urlsplit(record['source_key']);q=parse_qs(url.query,keep_blank_values=True)
            if url.scheme!='https' or url.netloc!='data.alpaca.markets' or url.path not in ('/v2/stocks/bars','/v2/stocks/quotes'):
                raise BridgeBlocked('UNDECLARED_SOURCE')
            kind=url.path.rsplit('/',1)[1]
            pages[kind]+=1
            if pages[kind]>50:raise BridgeBlocked('PAGE_CAP_EXCEEDED')
            if (record['metadata'].get('http_status')!=200 or q.get('feed')!=['sip']
                or q.get('asof')!=['-'] or q.get('sort')!=['asc']
                or len(q.get('start',[]))!=1 or len(q.get('end',[]))!=1
                or nanoseconds(q['start'][0])!=START or nanoseconds(q['end'][0])!=END):
                raise BridgeBlocked('SOURCE_CONTRACT_CHANGED')
            if kind=='bars' and (q.get('timeframe')!=['1Min'] or q.get('adjustment')!=['raw']):
                raise BridgeBlocked('BAR_CONTRACT_CHANGED')
            token=q.get('page_token',[None])
            if len(token)!=1 or token[0]!=expected.get(kind) or kind in complete:
                raise BridgeBlocked('PAGE_CHAIN_MISMATCH')
            payload=strict_json(store.raw(record));batch=payload.get(kind)
            if not isinstance(batch,dict) or any(k not in {'SPY','AAPL'} or not isinstance(v,list) for k,v in batch.items()):raise BridgeBlocked('MALFORMED_SYMBOL_ROWS')
            nxt=payload.get('next_page_token')
            if nxt is not None and (not isinstance(nxt,str) or not nxt or nxt==token[0]):raise BridgeBlocked('INVALID_PAGE_TOKEN')
            if nxt is not None:
                if nxt in tokens[kind]:raise BridgeBlocked('REPEATED_PAGE_TOKEN')
                tokens[kind].add(nxt)
            expected[kind]=nxt
            if nxt is None:complete.add(kind)
            for index,row in enumerate(batch.get('SPY',[])):
                seen[kind]+=1
                ns=nanoseconds(row['t'])
                if not START<=ns<=END:raise BridgeBlocked('ROW_OUTSIDE_WINDOW')
                ref={'record_id':record['id'],'blob_sha256':record['blob_sha'],'row_index':index}
                common={'source_ns':ns,'historical_received_at':None,'source_refs':[ref]}
                if kind=='bars':
                    validate_bar(row)
                    if ns+60_000_000_000>END:excluded+=1;continue
                    rows[kind].append({**common,'open':str(row['o']),'high':str(row['h']),
                                       'low':str(row['l']),'close':str(row['c']),'volume':str(row['v'])})
                else:
                    try:validate_quote(row,row['t'])  # screening only; NOT decision-age or receipt proof
                    except AuditFailure as error:rejected[str(error)]+=1;continue
                    rows[kind].append({**common,'bid':str(row['bp']),'ask':str(row['ap']),
                                       'bid_size':str(row['bs']),'ask_size':str(row['as']),
                                       'tape':row['z'],'conditions':row['c'],'bid_exchange':row['bx'],'ask_exchange':row['ax']})
        if complete!={'bars','quotes'} or not all(seen[k] for k in ('bars','quotes')):raise BridgeBlocked('INCOMPLETE_PAGE_CHAIN')
        bars,dbars=unique_rows(rows['bars']);quotes,dquotes=unique_rows(rows['quotes'],observation_only=True)
        return {'scope':'PRIVATE_OBSERVATION_COMPATIBILITY_ONLY','provider':'alpaca','feed':'sip',
                'symbol':'SPY','status':'UNQUALIFIED','rights':'UNRESOLVED',
                'quote_size_units':'UNQUALIFIED_PROVIDER_NATIVE','historical_receipt_proven':False,
                'database_sha256':expected_sha,'verified_chain':verified,'bars':bars,'quotes':quotes,
                'duplicate_bars':dbars,'duplicate_quotes':dquotes,
                'ambiguous_quote_timestamps':len({q['source_ns'] for q in quotes if q['same_time_variants']>1}),
                'tie_order':'CONTENT_SERIALIZATION_ONLY_NOT_CAUSAL_ORDER','excluded_incomplete_bars':excluded,
                'rejections':dict(sorted(rejected.items())),'orders_enabled':False}
    except (AuditFailure,KeyError,TypeError,ValueError,OSError,sqlite3.Error) as error:
        raise BridgeBlocked('SOURCE_VERIFICATION_OR_SCHEMA_FAILED') from error
    finally:store.close()


def main():
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--store',required=True);parser.add_argument('--output',required=True)
    args=parser.parse_args();output=Path(args.output).resolve();repo=Path(__file__).resolve().parents[3]
    if repo==output or repo in output.parents:raise BridgeBlocked('PRIVATE_OUTPUT_OUTSIDE_CHECKOUT_REQUIRED')
    result=project(args.store);data=encode(result)
    with output.open('xb') as file:file.write(data)
    print(json.dumps({'status':'OBSERVATION_PROJECTION_ONLY','sha256':hashlib.sha256(data).hexdigest(),
                      'bars':len(result['bars']),'quotes':len(result['quotes']),'rights':'UNRESOLVED','orders':0}))


if __name__=='__main__':main()

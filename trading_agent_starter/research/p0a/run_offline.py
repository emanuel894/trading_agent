"""Reproduce P0-A fixture measurements; never makes a source/model request.

Run from trading_agent_starter:
python research/p0a/run_offline.py --output runs/p0a-<unique-id>
"""
import argparse
from pathlib import Path
import sqlite3
import statistics
import sys
import time
import tracemalloc

sys.path.insert(0, str(Path(__file__).resolve().parents[2]))
from agent.audit_store import AuditFailure, EvidenceStore, canonical, digest, strict_json, utc_now
from agent.p0a_mda import process, prepare

HERE = Path(__file__).resolve().parent
STARTER = HERE.parents[1]


class ReadOnlyEvidence(EvidenceStore):
    """Use existing chain verification without initializing/modifying G4 storage."""
    def __init__(self, root):
        self.root = Path(root)
        self.objects = self.root / 'objects'
        self.db = sqlite3.connect((self.root / 'evidence.sqlite').resolve().as_uri() + '?mode=ro', uri=True)
        self.db.row_factory = sqlite3.Row


def inventory_g4(root):
    measurement = strict_json((HERE.parent / 'sec_g4_040/measurement.json').read_bytes())
    targets = [o for o in measurement['observations'] if o['role'] in ('primary', 'submission')]
    result = dict(inventory_at=utc_now(), root=str(root),
                  measurement_sha256=digest((HERE.parent / 'sec_g4_040/measurement.json').read_bytes()),
                  independent_authentic_filings=0, items=[], store_verification=None)
    store = None
    if root.is_dir():
        try:
            if digest((root / 'receipt.json').read_bytes()) != measurement['original_receipt_sha256']:
                raise AuditFailure('G4_RECEIPT_HASH_MISMATCH')
            store = ReadOnlyEvidence(root / 'evidence')
            verification = store.verify()
            if verification != measurement['latest_store']:
                raise AuditFailure('G4_CHAIN_BINDING_MISMATCH')
            result['store_verification'] = verification
        except (AuditFailure, OSError, sqlite3.Error):
            if store is not None:
                store.close()
            result['items'] = [dict(role=o['role'], sha256=o['sha256'], bytes=o['byte_count'],
                                    status='EXCLUDED', reason='G4_STORE_OR_RECEIPT_INTEGRITY_UNVERIFIED') for o in targets]
            return result
    try:
        for obs in targets:
            item = dict(role=obs['role'], sha256=obs['sha256'], bytes=obs['byte_count'],
                        accession='0000950170-25-067613', status='EXCLUDED')
            if store is None:
                item['reason'] = 'ORIGINAL_BYTES_AND_PROVENANCE_STORE_UNAVAILABLE'
            else:
                record = store.get(obs['id'])
                raw = store.raw(record)
                if record['blob_sha'] != obs['sha256'] or len(raw) != obs['byte_count']:
                    raise AuditFailure('G4_OBJECT_BINDING_MISMATCH')
                item.update(status='VERIFIED_LOCAL', path=str(store.objects / obs['sha256']),
                            source_ref=obs['uri'], provenance_ref=record['id'])
            result['items'].append(item)
        result['independent_authentic_filings'] = len({i['accession'] for i in result['items']
                                                       if i['status'] == 'VERIFIED_LOCAL'})
        return result
    except (AuditFailure, OSError, sqlite3.Error):
        result['items'] = [dict(role=o['role'], sha256=o['sha256'], bytes=o['byte_count'],
                                status='EXCLUDED', reason='G4_PROVENANCE_BINDING_UNVERIFIED') for o in targets]
        result['independent_authentic_filings'] = 0
        return result
    finally:
        if store is not None:
            store.close()


def footprint(root):
    files = [p for p in root.rglob('*') if p.is_file()]
    return dict(files=len(files), apparent_bytes=sum(p.stat().st_size for p in files),
                allocated_bytes=sum(getattr(p.stat(), 'st_blocks', 0) * 512 for p in files),
                scope='Output directory before final report; overlay allocation, not physical durability')


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--output', type=Path, required=True)
    args = parser.parse_args()
    # Refuse overwriting any earlier run; run UUID/path is an explicit operator choice.
    args.output.mkdir(parents=True, exist_ok=False)
    source_inventory = inventory_g4(STARTER / 'runs/issue40-g4/live-20261021')
    selection_raw = (HERE / 'fixture_selection.json').read_bytes()
    selection = strict_json(selection_raw)
    (args.output / 'source_inventory.json').write_bytes(canonical(source_inventory))
    (args.output / 'selection.json').write_bytes(selection_raw)
    # Selection and availability are persisted before any document processing.
    store = EvidenceStore(args.output / 'evidence')
    store.append('p0a_selection', 'p0a', dict(frozen_at=utc_now()),
                 canonical(dict(source_inventory=source_inventory, fixture_selection=selection)))
    results, mismatches = [], []
    source_evidence = (ReadOnlyEvidence(Path(source_inventory['root']) / 'evidence')
                       if source_inventory['independent_authentic_filings'] else None)
    tracemalloc.start()
    tick = time.perf_counter()
    try:
        inputs = []
        for item in source_inventory['items']:
            if item['status'] == 'VERIFIED_LOCAL':
                inputs.append((Path(item['path']).read_bytes(), dict(
                    accession=item['accession'], cik='0000700565', form='10-Q',
                    source_sha256=item['sha256'], byte_count=item['bytes'],
                    source_ref=item['source_ref'], provenance_ref=item['provenance_ref'],
                    synthetic=False, representation=item['role']), item['role'], None))
        for item in selection['items']:
            raw = (HERE / item['path']).read_bytes()
            if digest(raw) != item['sha256'] or len(raw) != item['bytes']:
                raise AuditFailure('FIXTURE_SELECTION_HASH_MISMATCH')
            inputs.append((raw, dict(accession='0000950170-25-067613', cik='0000700565', form='10-Q',
                                    source_sha256=item['sha256'], byte_count=len(raw),
                                    source_ref='fixture://p0a/' + item['path'],
                                    provenance_ref='fixture_selection.json:' + digest(selection_raw),
                                    synthetic=True, representation=item['representation']),
                           item['path'], item['expected_status']))
        for raw, meta, name, expected in inputs:
            result = process(store, raw, meta, source_evidence=source_evidence)
            result['sample'] = name
            if result['status'] == 'PREPARED_NO_INFERENCE':
                first = store.raw(store.get(result['prepared_id']))
                second = canonical(prepare(raw, meta, source_evidence=source_evidence))
                result['preparation_reproduced'] = first == second
                if first != second:
                    mismatches.append(name + ':NONDETERMINISTIC_PREPARATION')
            if expected is not None and result['status'] != expected:
                mismatches.append(name + ':UNEXPECTED_FIXTURE_OUTCOME')
            results.append(result)
        verification = store.verify()
    finally:
        store.close()
        if source_evidence is not None:
            source_evidence.close()
    _, peak = tracemalloc.get_traced_memory()
    tracemalloc.stop()
    elapsed = time.perf_counter() - tick
    success = [r for r in results if r['status'] == 'PREPARED_NO_INFERENCE' and r['synthetic']]
    seconds = sorted(r['offline_processing_seconds'] for r in success)
    # Nearest-rank descriptive p95 for a tiny sample; no inferential interpretation.
    report = dict(decision='P0A_INCOMPLETE', external_spend_usd=0,
                  source_inventory=source_inventory, selection_sha256=digest(selection_raw),
                  authentic_target=12, authentic_coverage='INCOMPLETE',
                  attempts=results, unexpected_outcomes=mismatches, store_verification=verification,
                  successful_fixture_preparations=len(success), fixture_attempts=sum(r['synthetic'] for r in results),
                  fixture_median_seconds=statistics.median(seconds) if seconds else None,
                  fixture_p95_nearest_rank_seconds=seconds[-1] if seconds else None,
                  statistics_scope='Small synthetic sample only; not authentic-source or LLM latency',
                  runner_seconds_including_reproduction=elapsed,
                  traced_python_peak_bytes=peak, rss='NOT_MEASURED',
                  footprint=footprint(args.output), real_inference='NOT_MEASURED',
                  input_output_tokens=None, real_schema_rate=None, real_assertion_support=None,
                  inference_latency_seconds=None, end_to_end_llm_seconds=None,
                  model_price=None, per_filing_inference_cost=None,
                  human_validation='NOT_PERFORMED', cross_provider_review='NOT_PERFORMED',
                  physical_clock_uncertainty='UNQUALIFIED; unchanged from G4',
                  projection_scope='Linear fixture-only arithmetic, excludes inference/concurrency/source acquisition',
                  projections=[dict(filings=n, fixture_offline_wall_seconds=statistics.mean(seconds)*n,
                                    prepared_plus_source_bytes=sum(r['derived_bytes']+r['source_bytes'] for r in success)/len(success)*n)
                               for n in (100,1000,10000)] if success else [])
    (args.output / 'report.json').write_bytes(canonical(report))
    print(canonical(dict(decision=report['decision'], attempts=len(results),
                         authentic_filings=source_inventory['independent_authentic_filings'],
                         unexpected_outcomes=mismatches, output=str(args.output))).decode())
    return 1 if mismatches else 0


if __name__ == '__main__':
    raise SystemExit(main())

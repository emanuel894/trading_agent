"""One offline replay using existing P0-A code and verified immutable G4 input.

Replays the bounded compatibility repair; no collection or inference.
"""
from pathlib import Path
import importlib.util
import json
import resource
import socket
import sqlite3
import sys
import time
import tracemalloc
from unittest.mock import patch
import urllib.request

HERE = Path(__file__).resolve().parent
STARTER = HERE.parents[2]
sys.path.insert(0, str(STARTER))
from agent.audit_store import EvidenceStore, canonical, digest, utc_now
from agent.p0a_mda import process, PROCESSING_CODE_SHA256

SOURCE = STARTER / 'runs/p0a-g4-import/g4-20261021'
MANIFEST = Path('/workspace/attachments/e5d2e07c-31a3-48af-8a05-0cd6d331c2b7/G4_TRANSFER_MANIFEST.json')
VERIFIER = Path('/workspace/attachments/acffa39c-a5d7-4ac7-8c36-d9e30826f955/VERIFY_G4_TRANSFER.py')
IMPORT_RECEIPT = STARTER / 'runs/p0a-g4-import-receipts/receipt.json'


class ImmutableEvidence(EvidenceStore):
    def __init__(self, root):
        self.root = Path(root)
        self.objects = self.root / 'objects'
        self.db = sqlite3.connect((self.root / 'evidence.sqlite').resolve().as_uri()
                                  + '?mode=ro&immutable=1', uri=True)
        self.db.row_factory = sqlite3.Row
        self.db.execute('PRAGMA query_only=ON')
        self.db.execute('PRAGMA trusted_schema=OFF')


def footprint(root):
    files = [p for p in root.rglob('*') if p.is_file()]
    return dict(files=len(files), apparent_bytes=sum(p.stat().st_size for p in files),
                allocated_bytes=sum(p.stat().st_blocks * 512 for p in files))


def main():
    receipt = json.loads(IMPORT_RECEIPT.read_bytes())
    assert receipt['status'] == 'DESTINATION_VERIFIED_READ_ONLY'
    assert digest(MANIFEST.read_bytes()) == '3dc0848e2abe75e7e0dde3a41cedd1c827a5f8056c52f6bcfc5dc0cb73c0d1dc'
    assert digest(VERIFIER.read_bytes()) == '2190c82c40ff06727f4874be44880a4c6634d4f12aa7f0167e889e2fac60cdc8'
    spec = importlib.util.spec_from_file_location('verified_g4_importer', VERIFIER)
    verifier = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(verifier)
    manifest = json.loads(MANIFEST.read_bytes())
    verifier.verify_extracted(SOURCE, manifest)
    assert all(not p.stat().st_mode & 0o222 for p in (SOURCE, *SOURCE.rglob('*')))
    input_hashes = {e['relative_path']: digest((SOURCE / e['relative_path']).read_bytes())
                    for e in manifest['files']}
    measurement = json.loads((STARTER / 'research/sec_g4_040/measurement.json').read_bytes())
    selected = sorted((o for o in measurement['observations'] if o['role'] in ('primary', 'submission')),
                      key=lambda o: o['role'])
    selection = dict(selected_at=utc_now(), rule='One recovered accession; both published representations; roles sorted',
                     accession='0000950170-25-067613', independent_filings=1,
                     processing_head='cfe4a1b99e7f7555b003d1126b1caf277a5656aa',
                     processing_code_sha256=PROCESSING_CODE_SHA256,
                     orchestration_sha256=digest(Path(__file__).read_bytes()),
                     source_import_receipt=receipt, source_file_hashes_before=input_hashes,
                     selected=[{k: o[k] for k in ('id', 'role', 'sha256', 'byte_count', 'uri')}
                               for o in selected])
    (HERE / 'selection.json').write_bytes(canonical(selection))
    source = ImmutableEvidence(SOURCE / 'evidence')
    output = EvidenceStore(HERE / 'evidence')
    attempts = []
    output.append('p0a_selection', 'recovered-g4', dict(untrusted=True), canonical(selection))
    tick = time.perf_counter()
    try:
        # Deny accidental network use; documents are only inert input bytes.
        with (patch.object(socket, 'socket', side_effect=AssertionError('NETWORK_FORBIDDEN')),
              patch.object(urllib.request, 'urlopen', side_effect=AssertionError('NETWORK_FORBIDDEN'))):
            for observation in selected:
                print('Starting original representation:', observation['role'], flush=True)
                tracemalloc.start()
                started = time.perf_counter()
                raw = source.raw(source.get(observation['id']))
                source_read_seconds = time.perf_counter() - started
                meta = dict(accession='0000950170-25-067613', cik='0000700565', form='10-Q',
                            source_sha256=observation['sha256'], byte_count=observation['byte_count'],
                            source_ref=observation['uri'], provenance_ref=observation['id'],
                            synthetic=False, representation=observation['role'])
                result = process(output, raw, meta, source_evidence=source)
                _, peak = tracemalloc.get_traced_memory()
                tracemalloc.stop()
                result.update(representation=observation['role'], source_bytes=len(raw),
                              source_read_seconds=source_read_seconds,
                              traced_python_peak_bytes=peak,
                              process_high_water_rss_bytes=resource.getrusage(resource.RUSAGE_SELF).ru_maxrss * 1024)
                attempts.append(result)
                (HERE / ('attempt-' + observation['role'] + '.json')).write_bytes(canonical(result))
                print('Completed:', observation['role'], result['status'], result.get('failure'), flush=True)
                del raw
        verification = output.verify()
    finally:
        source.close()
        output.close()
    original_verification = verifier.verify_extracted(SOURCE, manifest)
    input_hashes_after = {e['relative_path']: digest((SOURCE / e['relative_path']).read_bytes())
                          for e in manifest['files']}
    assert input_hashes_after == input_hashes
    assert all(not p.stat().st_mode & 0o222 for p in (SOURCE, *SOURCE.rglob('*')))
    report = dict(decision='P0A_INCOMPLETE', finished_utc=utc_now(),
                  authentic_filings_verified=1, authentic_target=12,
                  representations_attempted=len(attempts), attempts=attempts,
                  authentic_preparations_succeeded=sum(a['status'] == 'PREPARED_NO_INFERENCE' for a in attempts),
                  independent_complete_extractions='NOT_ESTABLISHED',
                  source_import_status='DESTINATION_VERIFIED_READ_ONLY',
                  original_evidence_unchanged=True, original_verification_after=original_verification,
                  source_file_hashes_after=input_hashes_after, output_verification=verification,
                  output_footprint_before_final_report=footprint(HERE),
                  verified_import_footprint=footprint(SOURCE),
                  replay_and_postverification_seconds=time.perf_counter() - tick,
                  process_high_water_rss_bytes=resource.getrusage(resource.RUSAGE_SELF).ru_maxrss * 1024,
                  resource_scope='Linux process high-water RSS cumulative; per-attempt traced Python peaks with instrumentation overhead',
                  real_inference='NOT_MEASURED', actual_tokens=None, actual_inference_cost_usd=None,
                  end_to_end_llm_seconds=None, physical_clock_qualification='UNCHANGED_UNQUALIFIED',
                  sec_source_conflicts='UNCHANGED_UNRESOLVED',
                  external_spend_usd=0, new_sec_requests=0, new_model_requests=0)
    (HERE / 'report.json').write_bytes(canonical(report))
    print(canonical(dict(decision=report['decision'], authentic_filings=1,
                         results=[dict(role=a['representation'], status=a['status'], failure=a.get('failure'),
                                       seconds=a['offline_processing_seconds']) for a in attempts],
                         original_evidence_unchanged=True)).decode(), flush=True)


if __name__ == '__main__':
    main()

"""Single operator invocation; reviewed alongside the adapter, never scheduled."""
import json
from pathlib import Path
import platform
import signal
import subprocess
import sys

from agent.audit_store import AuditFailure, canonical, digest
from agent.sec_g4_qualification import AUTHORITY, Qualification, native_metadata

def main():
    ROOT = Path('/workspace/trading_agent/trading_agent_starter/runs/issue40-g4/live-20261021')
    ROOT.mkdir(parents=True, exist_ok=True)
    with (ROOT / 'run-intent.json').open('xb') as f:
        f.write(canonical(dict(authority=AUTHORITY, external_spend_usd=0,
            code_head=subprocess.check_output(['git', 'rev-parse', 'HEAD'], text=True).strip(),
            python=sys.version, platform=platform.platform(), runner_sha256=digest(Path(__file__).read_bytes()))))


    def deadline(signum, frame):
        raise AuditFailure('G4_DEADLINE')


    prior = signal.signal(signal.SIGALRM, deadline)
    signal.setitimer(signal.ITIMER_REAL, 900)
    try:
        q = Qualification(ROOT / 'evidence', authorization_ref=AUTHORITY)
        stop = None
        try:
            for plan in q.plans:
                record = q.fetch(plan)
                if record['metadata']['failure']:
                    stop = record['metadata']['failure']
                    break
                parsed = native_metadata(plan, q.store.raw(record))
                q.store.append('g4.native', plan.url, dict(source_observation=record['id'],
                    body_sha256=record['blob_sha'], native=parsed, parse_completed=q._sample()))
                q.store.verify()
        except (AuditFailure, KeyError, ValueError, OSError) as exc:
            stop = str(exc) if isinstance(exc, AuditFailure) else type(exc).__name__

        observations = q.store.records('preservation.observation')
        summary = q.summary()
        status = 'INCOMPLETE' if stop or len(observations) != 6 else 'PASSED'
        # A qualified UTC/offset and source contract remain required for full G4 measurement.
        if any(r['metadata']['timing_flags'] for r in observations):
            status = 'INCOMPLETE'
        receipt = dict(status=status, stop=stop, external_spend_usd=0,
            exact_attempts=summary['control']['requests'], aggregate_body_bytes=sum(r['metadata']['byte_count'] for r in observations),
            largest_response=max((r['metadata']['byte_count'] for r in observations), default=0),
            jobs=q.jobs(), observations=observations, native=q.store.records('g4.native'),
            summary=summary, limitations=['Not scientific admission or prospective capture registration',
            'No historical first observation/receipt reconstructed', 'UTC offset/uncertainty unqualified',
            'Allocated samples are observations, not exhaustive filesystem peaks; host durability/backup unqualified',
            'HTTP/TLS/proxy network overhead not counted as response body bytes'])
        q.store.append('g4.terminal', 'issue40', dict(status=status, stop=stop,
            attempts=receipt['exact_attempts'], aggregate_body_bytes=receipt['aggregate_body_bytes'],
            elapsed_seconds=summary['elapsed_seconds'], external_spend_usd=0))
        receipt['store_verification'] = q.store.verify()
        receipt['storage_final_open'] = q._footprint()
        q.close()
        receipt['storage_final_closed'] = q._footprint()
        receipt['elapsed_seconds'] = q.timer() - q.started
        receipt['session_started_monotonic'] = q.started
        with (ROOT / 'receipt.json').open('xb') as f:
            f.write(canonical(receipt))
        print(json.dumps({k: receipt[k] for k in ('status', 'stop', 'exact_attempts', 'aggregate_body_bytes', 'largest_response')}))
        print(json.dumps(dict(elapsed_seconds=receipt['elapsed_seconds'], receipt=str(ROOT / 'receipt.json'))))
    finally:
        signal.setitimer(signal.ITIMER_REAL, 0)
        signal.signal(signal.SIGALRM, prior)


if __name__ == '__main__':
    main()

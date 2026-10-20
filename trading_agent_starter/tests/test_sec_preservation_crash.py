"""Real process termination at each offline object/transaction boundary."""
from pathlib import Path
import subprocess
import sys
import tempfile
import unittest

from agent.sec_preservation_offline import ClockSample, OfflinePreserver, Response

CHILD = r'''
import os
from pathlib import Path
import sys
from agent.sec_preservation_offline import ClockSample, OfflinePreserver, Response
root, boundary = sys.argv[1:]
def clock():
    return ClockSample('2026-10-20T12:00:00Z', 1, 'killed-session', .1, 'fixture-measurement')
def transport(uri, limit):
    return Response(200, {}, [b'complete'])
capture = OfflinePreserver(root, transport=transport, clock=clock)
capture.enqueue('fixture://sec/primary', 'primary', 'one')
if boundary == 'reserved':
    capture._receive = lambda *args: os._exit(17)
elif boundary == 'partial-spool':
    def partial(raw):
        path = capture.store.spool / 'interrupted'
        with path.open('xb') as handle:
            handle.write(b'part')
            handle.flush()
            os.fsync(handle.fileno())
        os._exit(17)
    capture.store._finalize_blob = partial
elif boundary == 'finalized':
    original = capture.store._finalize_blob
    def finalized(raw):
        original(raw)
        os._exit(17)
    capture.store._finalize_blob = finalized
elif boundary == 'uncommitted':
    original = capture.store.append_in_transaction
    def uncommitted(kind, *args, **kwargs):
        result = original(kind, *args, **kwargs)
        if kind == 'preservation.observation':
            os._exit(17)
        return result
    capture.store.append_in_transaction = uncommitted
capture.run_one()
os._exit(17)
'''


class ProcessCrashTests(unittest.TestCase):
    def test_kernel_exit_at_every_boundary_retains_job_and_releases_writer(self):
        for boundary in ('reserved', 'partial-spool', 'finalized', 'uncommitted', 'committed'):
            with self.subTest(boundary=boundary), tempfile.TemporaryDirectory() as temporary:
                root = Path(temporary) / 'store'
                child = subprocess.run([sys.executable, '-c', CHILD, str(root), boundary],
                                       capture_output=True, timeout=15)
                self.assertEqual(child.returncode, 17, child.stderr.decode())
                clock = lambda: ClockSample('2026-10-20T12:00:10Z', 1, 'recovery-session', .1, 'fixture')
                capture = OfflinePreserver(root, transport=lambda *a: Response(200, {}, [b'complete']), clock=clock)
                try:
                    job = capture.jobs()[0]
                    self.assertEqual(job['attempts'], 1)
                    self.assertEqual(job['state'], 'COMPLETE' if boundary == 'committed' else 'PENDING')
                    observations = capture.store.records('preservation.observation')
                    self.assertEqual(len(observations), int(boundary == 'committed'))
                    if boundary in {'partial-spool', 'finalized', 'uncommitted'}:
                        self.assertTrue(capture.store.records('preservation.orphan'))
                    if boundary == 'committed':
                        self.assertIsNone(capture.run_one())
                    else:
                        self.assertEqual(capture.store.raw(capture.run_one()), b'complete')
                    self.assertEqual(capture.store.verify()['status'], 'VERIFIED')
                finally:
                    capture.close()

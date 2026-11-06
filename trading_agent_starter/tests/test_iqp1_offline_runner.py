"""Offline runner contracts; no Docker or source connections in unit tests."""
import importlib.util
from pathlib import Path
import subprocess
import sys
import time
import unittest

ROOT = Path(__file__).resolve().parents[2]
SPEC = importlib.util.spec_from_file_location('offline_runner', ROOT / 'tools/iqp1_offline.py')


class OfflineRunnerTests(unittest.TestCase):
    def runner(self):
        module = importlib.util.module_from_spec(SPEC)
        SPEC.loader.exec_module(module)
        return module

    def test_launch_has_no_network_credentials_or_host_mounts(self):
        command = self.runner().command('sha256:' + 'a' * 64, 'qualification', 1800)
        for flag in ('--network=none', '--read-only', '--memory=2g', '--memory-swap=2g',
                     '--cap-drop=ALL', '--log-driver=none', '--ipc=none', '--user=65534:65534'):
            self.assertIn(flag, command)
        self.assertFalse(any(x in command for x in ('-v', '--volume', '--env-file', '--privileged')))

    def test_only_offline_modes_and_stricter_deadlines_are_accepted(self):
        runner = self.runner()
        for mode, seconds in [('online', 1800), ('qualification', 1801), ('qualification', 0)]:
            with self.assertRaises(ValueError):
                runner.command('sha256:' + 'a' * 64, mode, seconds)

    def test_disabled_tunnels_are_allowed_but_active_egress_is_rejected(self):
        runner = self.runner()
        self.assertTrue(runner.isolated_interfaces({"lo": 1, "tunl0": 0}))
        self.assertFalse(runner.isolated_interfaces({"lo": 1, "eth0": 1}))

    def test_watchdog_kills_a_stalled_child(self):
        started = time.monotonic()
        result = self.runner().supervise([sys.executable, '-c', 'import time; time.sleep(30)'], 0.2)
        self.assertEqual(result, 124)
        self.assertLess(time.monotonic() - started, 5)


class SourcePacketTests(unittest.TestCase):
    def test_build_packet_excludes_tracked_and_untracked_dotenv_and_runtime(self):
        import io
        import tarfile
        import tempfile
        spec = importlib.util.spec_from_file_location('source_build', ROOT / 'tools/iqp1_build.py')
        module = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(module)
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary)
            subprocess.run(['git', 'init', '-q', str(root)], check=True)
            for name in ('README.md', '.env', '.env.local', 'untracked.txt', '[.]env'):
                (root / name).write_text('SYNTHETIC ONLY')
            subprocess.run(['git', '--literal-pathspecs', '-C', str(root), 'add', 'README.md', '.env', '[.]env'], check=True)
            subprocess.run(['git', '-C', str(root), '-c', 'user.email=fixture@example.test',
                            '-c', 'user.name=fixture', 'commit', '-qm', 'fixture'], check=True)
            packet = module.source_packet(root)
        with tarfile.open(fileobj=io.BytesIO(packet)) as archive:
            self.assertEqual(archive.getnames(), ['README.md', '[.]env'])

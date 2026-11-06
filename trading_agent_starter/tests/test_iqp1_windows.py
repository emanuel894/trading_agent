"""Kernel tests on Windows CI only. Temporary fixtures, no source credentials."""
import ctypes
import importlib.util
import json
import os
from pathlib import Path
import subprocess
import sys
import tempfile
import time
import unittest
import uuid

TOOLS = Path(__file__).resolve().parents[2]/"tools"
sys.path.insert(0, str(TOOLS))
from iqp1_windows_job import run_job, sealed_environment
from iqp1_local import fixed_vhd, volume_command


class PortableWindowsContracts(unittest.TestCase):
    def test_child_environment_contains_no_acquisition_credentials(self):
        from unittest.mock import patch
        with patch.dict(os.environ, {"ALPACA_API_KEY":"do-not-forward", "AWS_SECRET_ACCESS_KEY":"do-not-forward"}):
            env = sealed_environment("Q:/tmp")
        self.assertNotIn("ALPACA_API_KEY", env)
        self.assertNotIn("AWS_SECRET_ACCESS_KEY", env)
        self.assertEqual(env["TRADING_ENABLED"], "false")


@unittest.skipUnless(os.name == "nt", "Actual Windows kernel/VHD tests run in mandatory Windows CI")
class WindowsKernelTests(unittest.TestCase):
    def test_job_success_and_hard_memory_enforcement(self):
        with tempfile.TemporaryDirectory() as temporary:
            marker = Path(temporary)/"memory.json"
            script = ("import json,pathlib; chunks=[];\ntry:\n"
                      " for i in range(256): chunks.append(bytearray(1024**2))\n"
                      "except MemoryError:\n pathlib.Path("+repr(str(marker))+").write_text('MEMORY_BLOCKED')\n")
            result = run_job([sys.executable,"-I","-B","-c",script], temporary=temporary,
                             seconds=20, memory=64*1024**2, mutex="Local\\IQP1-test-"+uuid.uuid4().hex)
            self.assertEqual(result["exit_code"], 0)
            self.assertEqual(marker.read_text(), "MEMORY_BLOCKED")
            self.assertLessEqual(result["peak_job_bytes"], 64*1024**2)
            self.assertGreater(result["peak_job_bytes"], 1024**2)

    def test_deadline_kills_hung_child_and_descendant(self):
        with tempfile.TemporaryDirectory() as temporary:
            marker = Path(temporary)/"descendant-survived"
            child = "import time,pathlib; time.sleep(4); pathlib.Path("+repr(str(marker))+").write_text('BAD')"
            parent = "import subprocess,sys,time; subprocess.Popen([sys.executable,'-I','-B','-c',"+repr(child)+"]); time.sleep(60)"
            result = run_job([sys.executable,"-I","-B","-c",parent], temporary=temporary,
                             seconds=2, mutex="Local\\IQP1-test-"+uuid.uuid4().hex)
            self.assertTrue(result["timed_out"])
            self.assertEqual(result["exit_code"],124)
            self.assertLess(result["wall_seconds"],4)
            time.sleep(3)
            self.assertFalse(marker.exists())

    def test_fixed_vhd_persists_and_fails_writes_at_physical_limit(self):
        self.assertTrue(ctypes.windll.shell32.IsUserAnAdmin(), "Windows qualification requires administrator VHD support")
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary)
            try:
                info = volume_command("Initialize", root, size=64)
                self.assertEqual(info["filesystem"], "NTFS")
                self.assertEqual(fixed_vhd(root/"pilot.vhd", size_mib=64),64*1024**2+512)
                volume = root/"volume"
                (volume/"retained.txt").write_text("persisted fixture")
                with self.assertRaises(OSError):
                    with (volume/"fill.bin").open("wb", buffering=0) as handle:
                        for _ in range(80):
                            handle.write(b"x"*1024**2)
                self.assertLess((root/"pilot.vhd").stat().st_size,65*1024**2)
                (volume/"fill.bin").unlink()
                volume_command("Detach",root,size=64)
                again = volume_command("Attach",root,size=64)
                self.assertEqual(info["volume_id"],again["volume_id"])
                self.assertEqual((volume/"retained.txt").read_text(),"persisted fixture")
            finally:
                volume_command("Detach",root,size=64)

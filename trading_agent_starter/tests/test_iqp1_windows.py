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
import iqp1_local as local
from iqp1_local import fixed_vhd, volume_command


class PortableWindowsContracts(unittest.TestCase):
    def test_failure_diagnostic_retains_only_codes_and_never_secret_exception_text(self):
        self.assertEqual(local.safe_failure(ValueError("fixture-secret-that-must-never-appear")),"LOCAL_RUNTIME_FAILURE")
        self.assertEqual(local.safe_failure(MemoryError()),"IQP1_MEMORY_LIMIT_REACHED")
        with tempfile.TemporaryDirectory() as temporary:
            local.retain_failure(temporary,"prepare-child",local.safe_failure(ValueError("fixture-secret")))
            local.retain_failure(temporary,"prepare-child","IQP1_STANDARD_OWNER_TOKEN_REQUIRED")
            raw = (Path(temporary)/"failure.jsonl").read_text()
            self.assertNotIn("fixture-secret",raw)
            self.assertEqual(len(raw.splitlines()),2)
            self.assertEqual(json.loads(raw.splitlines()[-1])["reason"],"IQP1_STANDARD_OWNER_TOKEN_REQUIRED")

    def test_diskpart_structured_failure_keeps_native_output_private(self):
        from unittest.mock import patch
        private = b"private-path-and-credentials-do-not-log"
        cmd_error = subprocess.CalledProcessError(
            1, ["powershell.exe"], stderr=(
                b"IQP1_SAFE_FAILURE_CODE=IQP1_DISKPART_CREATE_FAILED\r\n" + private))
        with patch.object(local, "powershell", return_value="powershell.exe"):
            with patch.object(local.subprocess, "check_output", side_effect=cmd_error):
                with self.assertRaisesRegex(RuntimeError, r"^IQP1_DISKPART_CREATE_FAILED$") as failure:
                    local.volume_command("Initialize", Path("C:/fixture"))
        self.assertNotIn(private.decode(), str(failure.exception))
        untrusted = subprocess.CalledProcessError(
            1, ["powershell.exe"],
            stderr=b"IQP1_SAFE_FAILURE_CODE=private-path-token\n" + private)
        with patch.object(local, "powershell", return_value="powershell.exe"):
            with patch.object(local.subprocess, "check_output", side_effect=untrusted):
                with self.assertRaisesRegex(RuntimeError, r"^IQP1_VOLUME_STAGE_FAILED$"):
                    local.volume_command("Initialize", Path("C:/fixture"))

    def test_native_diskpart_is_bounded_and_hides_error_transcript(self):
        from unittest.mock import patch
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary)
            private = b"private-host-path-and-secret-that-must-not-leak"
            native = subprocess.CompletedProcess(
                ["diskpart.exe"], 1, stdout=private, stderr=b"Virtual Disk Service error"
            )
            with patch.dict(os.environ, {"SystemRoot":"C:\\Windows"}):
                with patch.object(local.subprocess, "run", return_value=native):
                    with self.assertRaisesRegex(RuntimeError, r"^IQP1_DISKPART_CREATE_FAILED$") as caught:
                        local._native_diskpart(root, [
                            f'create vdisk file="{root / "pilot.vhd"}" maximum=64 type=fixed'
                        ], "Initialize")
            self.assertNotIn(private.decode(), str(caught.exception))
            self.assertFalse((root/"_diskpart.txt").exists())

    def test_timeout_and_new_invocation_never_report_a_stale_failure(self):
        with tempfile.TemporaryDirectory() as temporary:
            local.retain_failure(temporary,"prepare-child","IQP1_OLD_FAILURE",invocation="old")
            self.assertEqual(local.stop_reason(temporary,"new",timed_out=True),"IQP1_EXECUTION_DEADLINE_REACHED")
            self.assertEqual(local.stop_reason(temporary,"new",timed_out=False),"IQP1_CHILD_TERMINATED_WITHOUT_CURRENT_RECEIPT")
            local.retain_failure(temporary,"prepare-child","IQP1_CURRENT_FAILURE",invocation="new")
            self.assertEqual(local.stop_reason(temporary,"new",timed_out=False),"IQP1_CURRENT_FAILURE")
    def test_child_environment_contains_no_acquisition_credentials(self):
        from unittest.mock import patch
        with patch.dict(os.environ, {"ALPACA_API_KEY":"do-not-forward", "AWS_SECRET_ACCESS_KEY":"do-not-forward"}):
            env = sealed_environment("Q:/tmp")
        self.assertNotIn("ALPACA_API_KEY", env)
        self.assertNotIn("AWS_SECRET_ACCESS_KEY", env)
        self.assertEqual(env["TRADING_ENABLED"], "false")

    @unittest.skipUnless(os.name == "nt", "Native Windows system-drive paths")
    def test_sealed_environment_preserves_core_windows_paths_not_secrets(self):
        from unittest.mock import patch
        with patch.dict(os.environ, {"ALPACA_API_SECRET":"never-forward",
                                     "AWS_SECRET_ACCESS_KEY":"never-forward"}):
            env = sealed_environment("C:\\fixture-temp")
        expected_drive = Path(os.environ["SystemRoot"]).drive
        self.assertEqual(env["SystemDrive"].casefold(), expected_drive.casefold())
        self.assertEqual(env["ProgramData"].casefold(),
                         str(Path(expected_drive + "\\ProgramData")).casefold())
        self.assertEqual(env["ALLUSERSPROFILE"], env["ProgramData"])
        self.assertNotIn("%SystemDrive%", env["ProgramData"])
        self.assertNotIn("ALPACA_API_SECRET", env)
        self.assertNotIn("AWS_SECRET_ACCESS_KEY", env)

    def test_executed_tree_receipt_changes_on_code_or_dependency_tampering(self):
        with tempfile.TemporaryDirectory() as temporary:
            volume = Path(temporary)
            (volume/"source").mkdir()
            (volume/"python").mkdir()
            (volume/"source"/"gate.py").write_text("GET-only fixture")
            (volume/"python"/"python.exe").write_bytes(b"fixture interpreter")
            before = local.runtime_hash(volume)
            (volume/"source"/"gate.py").write_text("changed fixture")
            self.assertNotEqual(before,local.runtime_hash(volume))
            second = local.runtime_hash(volume)
            (volume/"python"/"extra.pth").write_text("fixture injection")
            self.assertNotEqual(second,local.runtime_hash(volume))


@unittest.skipUnless(os.name == "nt", "Actual Windows kernel/VHD tests run in mandatory Windows CI")
class WindowsKernelTests(unittest.TestCase):
    def test_named_admin_owned_job_authenticates_exact_membership(self):
        with tempfile.TemporaryDirectory() as temporary:
            name = "Local\\IQP1-authorized-test-"+uuid.uuid4().hex
            sid = local.owner_sid()
            marker = Path(temporary)/"authenticated"
            script = ("import sys,pathlib; sys.path.insert(0,"+repr(str(TOOLS))+"); "
                "from iqp1_windows_job import require_authorized_job; require_authorized_job("+repr(name)+"); "
                "pathlib.Path("+repr(str(marker))+").write_text('MEMBER')")
            result = run_job([sys.executable,"-I","-B","-c",script],temporary=temporary,
                seconds=20,job_name=name,protected_sid=sid,mutex="Local\\IQP1-test-"+uuid.uuid4().hex)
            self.assertEqual(result["exit_code"],0)
            self.assertEqual(marker.read_text(),"MEMBER")
            from iqp1_windows_job import require_authorized_job
            with self.assertRaises(RuntimeError):
                require_authorized_job(name)  # object is gone; matching caps are insufficient
    def test_private_acl_replaces_default_grants_and_checks_immutable_tree(self):
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary)
            for name in ("source","python","evidence","tmp"):
                (root/"volume"/name).mkdir(parents=True)
            (root/"volume"/"source"/"fixture.py").write_text("fixture")
            sid = local.owner_sid()
            with self.assertRaises(subprocess.CalledProcessError):
                local.storage_acl(root,sid,"Verify")
            for action in ("Harden","Verify"):
                proof = subprocess.run(["powershell.exe","-NoProfile","-NonInteractive","-ExecutionPolicy","Bypass",
                    "-File",str(TOOLS/"iqp1_storage_acl.ps1"),"-Action",action,"-Root",str(root),"-OwnerSid",sid],
                    capture_output=True,text=True)
                self.assertEqual(proof.returncode,0,proof.stderr)  # fixtures only, expose Windows diagnostics
            credential = root/"volume"/"evidence"/"fixture-not-a-secret.json"
            credential.write_text("not JSON: metadata check must not read credentials")
            self.assertEqual(local.private_credential_metadata(credential,sid),credential.resolve())
    def test_job_success_and_hard_memory_enforcement(self):
        with tempfile.TemporaryDirectory() as temporary:
            marker = Path(temporary)/"memory.json"
            script = ("import json,pathlib; chunks=[];\ntry:\n"
                      " bytearray(256*1024**2)\n"
                      "except MemoryError: pass\ntry:\n"
                      " for i in range(256): chunks.append(bytearray(1024**2))\n"
                      "except MemoryError:\n pathlib.Path("+repr(str(marker))+").write_text('MEMORY_BLOCKED')\n")
            result = run_job([sys.executable,"-I","-B","-c",script], temporary=temporary,
                             seconds=20, memory=64*1024**2, mutex="Local\\IQP1-test-"+uuid.uuid4().hex)
            self.assertEqual(result["exit_code"], 0)
            self.assertEqual(marker.read_text(), "MEMORY_BLOCKED")
            self.assertLessEqual(result["peak_job_bytes"], 64*1024**2)
            self.assertGreater(result["peak_job_bytes"], 1024**2)

    def test_machine_consumption_survives_mutable_ledger_removal(self):
        import winreg
        from types import SimpleNamespace
        from unittest.mock import patch
        keyname = r"SOFTWARE\TradingAgent\IQP1-test-"+uuid.uuid4().hex
        args = SimpleNamespace(root="C:\\fixture-only",commit="f"*40,approve="e"*64)
        try:
            with patch.object(local,"REGISTRY",keyname):
                local.binding(create=dict(root=args.root,commit=args.commit,manifest=args.approve))
                local.consume_once(args,"Global\\fixture-authorized-job")
                # The evidence directory is irrelevant to this independent cap.
                with self.assertRaisesRegex(RuntimeError,"ALREADY_CONSUMED"):
                    local.consume_once(args,"Global\\fixture-alternate-job")
        finally:
            winreg.DeleteKey(winreg.HKEY_LOCAL_MACHINE,keyname)

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

    def _cleanup_ci_vhd(self, root):
        """Dismount only the named disposable CI fixture, never any physical disk."""
        image = root/"pilot.vhd"
        if not image.is_file():
            return
        quoted = str(image).replace("'", "''")
        command = ("$d=Get-DiskImage -ImagePath '"+quoted+
                   "' -ErrorAction Stop; if ($d.Attached) { $d | Dismount-DiskImage -ErrorAction Stop }")
        result = subprocess.run(
            ["powershell.exe","-NoProfile","-NonInteractive","-ExecutionPolicy","Bypass",
             "-Command",command],
            capture_output=True, timeout=45
        )
        self.assertEqual(result.returncode, 0, "CI_VHD_FIXTURE_DISMOUNT_FAILED")

    def _initialize_vhd_in_kernel_job(self, size):
        self.assertTrue(ctypes.windll.shell32.IsUserAnAdmin())
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary)
            script = (
                "import pathlib,sys,re\n"
                "sys.path.insert(0," + repr(str(TOOLS)) + ")\n"
                "from iqp1_local import volume_command\n"
                "root=pathlib.Path(" + repr(str(root)) + ")\n"
                "try:\n"
                " info=volume_command('Initialize',root,size=" + str(size) + ")\n"
                " assert info['filesystem']=='NTFS'\n"
                "except BaseException as error:\n"
                " reason=str(error)\n"
                " if not re.fullmatch(r'IQP1_[A-Z0-9_]{1,120}',reason): reason='LOCAL_RUNTIME_FAILURE'\n"
                " (root/'fixture_failure_code.txt').write_text(reason,encoding='utf-8')\n"
                " raise\n"
            )
            try:
                receipt = run_job(
                    [sys.executable, "-I", "-B", "-c", script],
                    temporary=temporary, seconds=240, memory=2*1024**3,
                    mutex="Local\\IQP1-vhd-job-test-" + uuid.uuid4().hex
                )
                failure = root/"fixture_failure_code.txt"
                detail = failure.read_text() if failure.is_file() else receipt
                self.assertEqual(receipt["exit_code"], 0, detail)
                self.assertTrue((root/"pilot.vhd").is_file())
                self.assertEqual(fixed_vhd(root/"pilot.vhd",size_mib=size),size*1024**2+512)
            finally:
                self._cleanup_ci_vhd(root)

    def test_aa_small_fixed_vhd_initialize_under_kernel_job(self):
        self._initialize_vhd_in_kernel_job(64)

    def test_fixed_vhd_initialize_under_real_kernel_job_limits(self):
        self._initialize_vhd_in_kernel_job(4092)

    def test_fixed_vhd_persists_and_fails_writes_at_physical_limit(self):
        self.assertTrue(ctypes.windll.shell32.IsUserAnAdmin(), "Windows qualification requires administrator VHD support")
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary)
            try:
                local.retain_failure(root,"prepare-child","IQP1_FIXED_PREREQUISITE",invocation="old")
                diagnostic = (root/"failure.jsonl").read_bytes()
                info = volume_command("Initialize", root)
                self.assertEqual((root/"failure.jsonl").read_bytes(),diagnostic)
                self.assertEqual(info["filesystem"], "NTFS")
                self.assertEqual(fixed_vhd(root/"pilot.vhd"),4092*1024**2+512)
                volume = root/"volume"
                (volume/"retained.txt").write_text("persisted fixture")
                with (volume/"reserve.bin").open("wb",buffering=0) as reserve:
                    for _ in range(64):
                        reserve.write(b"r"*1024**2)
                proof = local.storage_gate(root,{"volume_id":info["volume_id"]},inspect=True)
                self.assertLessEqual(proof["physical_bound_bytes"],4*1024**3)
                with self.assertRaises(OSError):
                    with (volume/"fill.bin").open("wb", buffering=0) as handle:
                        for _ in range(4100):
                            handle.write(b"x"*1024**2)
                self.assertLess((root/"pilot.vhd").stat().st_size,4*1024**3)
                with self.assertRaisesRegex(RuntimeError,"FREE_SPACE_RESERVE"):
                    local.storage_gate(root,{"volume_id":info["volume_id"]})
                (volume/"fill.bin").unlink()
                volume_command("Detach",root)
                again = volume_command("Attach",root)
                self.assertEqual(info["volume_id"],again["volume_id"])
                self.assertEqual((volume/"retained.txt").read_text(),"persisted fixture")
            finally:
                volume_command("Detach",root)

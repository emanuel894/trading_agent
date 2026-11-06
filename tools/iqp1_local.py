"""One owner-local Windows pilot. Prepare never reads credentials or calls Alpaca.

All created pilot content lives in a fixed VHD plus <=4MiB control allowance.
Administrator-owned registry binding pins one root, manifest and evidence ID.
There is deliberately no reset, new-ledger, alternate schedule or resume switch.
"""
import argparse
import ctypes
import hashlib
import io
import json
import os
from pathlib import Path
import shutil
import struct
import subprocess
import sys
import tarfile
import time
import uuid

sys.path.insert(0, str(Path(__file__).resolve().parent))
from iqp1_windows_job import require_pilot_job, require_query_only_job, run_job

CAP = 4*1024**3
VHD_MIB = 4092
RESERVE = 64*1024**2
REGISTRY = r"SOFTWARE\TradingAgent\IQP1Boundary"
CONTROL = {"pilot.vhd", "volume", "manifest.json", "prepare.json", "_diskpart.txt"}


def powershell():
    return str(Path(os.environ["SystemRoot"])/"System32"/"WindowsPowerShell"/"v1.0"/"powershell.exe")


def fail(code):
    raise RuntimeError(code)


def encode(value):
    return json.dumps(value, sort_keys=True, separators=(",", ":"), ensure_ascii=True).encode()


def read_json(path):
    if path.stat().st_size > 65536:
        fail("IQP1_CONTROL_FILE_TOO_LARGE")
    return json.loads(path.read_bytes())


def write_json(path, value):
    raw = encode(value)
    if len(raw) > 65536:
        fail("IQP1_CONTROL_FILE_TOO_LARGE")
    with path.open("wb") as handle:
        handle.write(raw)
        handle.flush()
        os.fsync(handle.fileno())


def volume_command(action, root, *, size=VHD_MIB):
    script = Path(__file__).with_name("iqp1_volume.ps1")
    raw = subprocess.check_output([powershell(), "-NoProfile", "-NonInteractive", "-ExecutionPolicy", "Bypass",
            "-File", str(script), "-Action", action, "-Root", str(root), "-SizeMiB", str(size)],
            stderr=subprocess.DEVNULL)
    return json.loads(raw.decode("utf-8-sig")) if action != "Detach" else None


def fixed_vhd(path, *, size_mib=VHD_MIB):
    """Fixed footer, exact physical allocation and no sparse/compressed file."""
    expected = size_mib*1024**2
    stat = path.stat()
    if stat.st_size != expected+512 or getattr(stat, "st_file_attributes", 0) & (0x200|0x800|0x400):
        fail("IQP1_VHD_SIZE_OR_ALLOCATION_INVALID")
    with path.open("rb") as handle:
        handle.seek(-512, 2)
        footer = bytearray(handle.read(512))
    checksum = struct.unpack_from(">I", footer, 64)[0]
    footer[64:68] = b"\0"*4
    if (footer[:8] != b"conectix" or struct.unpack_from(">I", footer, 60)[0] != 2
            or struct.unpack_from(">Q", footer, 48)[0] != expected
            or checksum != (~sum(footer) & 0xFFFFFFFF)):
        fail("IQP1_FIXED_VHD_FOOTER_INVALID")
    if os.name == "nt":
        k = ctypes.WinDLL("kernel32", use_last_error=True)
        k.GetCompressedFileSizeW.argtypes = [ctypes.c_wchar_p, ctypes.POINTER(ctypes.c_ulong)]
        k.GetCompressedFileSizeW.restype = ctypes.c_ulong
        high = ctypes.c_ulong()
        low = k.GetCompressedFileSizeW(str(path), ctypes.byref(high))
        if low == 0xFFFFFFFF and ctypes.get_last_error():
            fail("IQP1_PHYSICAL_ALLOCATION_UNVERIFIED")
        allocated = (high.value << 32) | low
        if not expected <= allocated <= expected+65536:
            fail("IQP1_PHYSICAL_ALLOCATION_UNVERIFIED")
    return stat.st_size


def storage_gate(root, manifest, *, inspect=False):
    root = Path(root)
    if set(p.name for p in root.iterdir()) - CONTROL:
        fail("IQP1_UNACCOUNTED_CONTROL_FILE")
    total = fixed_vhd(root/"pilot.vhd")+65536  # conservative accepted host allocation-unit overhead
    for path in root.iterdir():
        if path.name in {"volume", "pilot.vhd"}:
            continue
        if not path.is_file() or path.stat().st_size > 65536:
            fail("IQP1_CONTROL_AREA_INVALID")
        total += max(65536, path.stat().st_size)
    if total > CAP:
        fail("IQP1_PHYSICAL_CAP_EXCEEDED")
    volume = root/"volume"
    if inspect:
        # Mount identity lookup is read-only and works for the unelevated worker;
        # no Storage/WMI administrative capability enters acquisition.
        k = ctypes.WinDLL("kernel32",use_last_error=True)
        k.GetVolumeNameForVolumeMountPointW.argtypes = [ctypes.c_wchar_p,ctypes.c_wchar_p,ctypes.c_ulong]
        k.GetVolumeNameForVolumeMountPointW.restype = ctypes.c_int
        actual = ctypes.create_unicode_buffer(1024)
        if (not k.GetVolumeNameForVolumeMountPointW(str(volume)+"\\",actual,len(actual))
                or actual.value.casefold() != manifest["volume_id"].casefold()):
            fail("IQP1_VOLUME_IDENTITY_CHANGED")
    # Check the mounted volume, not the unbounded directory underneath it.
    free = shutil.disk_usage(volume).free
    reserve = volume/"reserve.bin"
    if (reserve.stat().st_size != RESERVE or getattr(reserve.stat(),"st_file_attributes",0)&(0x200|0x800|0x400)
            or free < RESERVE+40_000_000):
        fail("IQP1_FREE_SPACE_RESERVE_UNAVAILABLE")
    return {"physical_bound_bytes":total, "free_bytes":free, "cap_bytes":CAP}


def owner_sid():
    # WindowsIdentity is metadata only; never enumerate environment/secrets.
    return subprocess.check_output([powershell(), "-NoProfile", "-NonInteractive", "-Command",
            "[Security.Principal.WindowsIdentity]::GetCurrent().User.Value"], stderr=subprocess.DEVNULL).decode().strip()


def binding(*, create=None):
    import winreg
    if create is not None:
        with winreg.CreateKeyEx(winreg.HKEY_LOCAL_MACHINE, REGISTRY, 0, winreg.KEY_READ|winreg.KEY_WRITE) as key:
            try:
                winreg.QueryValueEx(key, "Binding")
            except FileNotFoundError:
                winreg.SetValueEx(key, "Binding", 0, winreg.REG_SZ, encode(create).decode())
                return create
            fail("IQP1_MACHINE_ALREADY_BOUND_NO_RESET")
    with winreg.OpenKey(winreg.HKEY_LOCAL_MACHINE, REGISTRY, 0, winreg.KEY_READ) as key:
        return json.loads(winreg.QueryValueEx(key, "Binding")[0])


def storage_acl(root, sid, action):
    subprocess.run([powershell(), "-NoProfile", "-NonInteractive", "-ExecutionPolicy", "Bypass",
                   "-File", str(Path(__file__).with_name("iqp1_storage_acl.ps1")), "-Action", action,
                   "-Root", str(root), "-OwnerSid", sid], check=True,
                   stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)


def private_credential_metadata(path, sid):
    path = Path(path).resolve(strict=True)
    if not path.is_file() or path.stat().st_size > 65536:
        fail("IQP1_EXISTING_PRIVATE_CREDENTIAL_REFERENCE_REQUIRED")
    subprocess.run([powershell(), "-NoProfile", "-NonInteractive", "-ExecutionPolicy", "Bypass",
        "-File", str(Path(__file__).with_name("iqp1_private_acl.ps1")), "-File", str(path),
        "-OwnerSid", sid], check=True, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
    return path


def runtime_hash(volume):
    result = hashlib.sha256()
    for directory in (volume/"source", volume/"python"):
        for path in sorted(directory.rglob("*")):
            if path.is_symlink() or getattr(path.stat(), "st_file_attributes", 0) & 0x400:
                fail("IQP1_RUNTIME_LINK_REJECTED")
            if path.is_file():
                sha = hashlib.sha256()
                with path.open("rb") as handle:
                    for chunk in iter(lambda:handle.read(1024**2), b""):
                        sha.update(chunk)
                result.update(encode([path.relative_to(volume).as_posix(),path.stat().st_size,sha.hexdigest()]))
    return result.hexdigest()


def base_python_proof(base):
    """Trust only the owner's protected all-users Python; hash its code, not secrets."""
    base = Path(base).resolve(strict=True)
    program_files = Path(os.environ["ProgramFiles"]).resolve(strict=True)
    if not base.is_relative_to(program_files):
        fail("IQP1_SYSTEM_PYTHON_INSTALLATION_REQUIRED")
    subprocess.run([powershell(),"-NoProfile","-NonInteractive","-ExecutionPolicy","Bypass",
                   "-File",str(Path(__file__).with_name("iqp1_base_acl.ps1")),"-Base",str(base)],
                   check=True,stdout=subprocess.DEVNULL,stderr=subprocess.DEVNULL)
    result = hashlib.sha256()
    for path in sorted(base.rglob("*")):
        if "site-packages" in path.relative_to(base).parts:
            continue
        if path.is_symlink() or getattr(path.stat(),"st_file_attributes",0)&0x400:
            fail("IQP1_BASE_RUNTIME_LINK_REJECTED")
        if path.is_file() and path.suffix.lower() in {".exe",".dll",".pyd",".py",".pyc",".zip",".whl",".pth"}:
            result.update(encode([path.relative_to(base).as_posix(),hashlib.sha256(path.read_bytes()).hexdigest()]))
    return {"root":str(base),"sha256":result.hexdigest()}


def consume_once(args,job_name):
    """Elevated one-shot authorization, outside the owner-writable evidence VHD.

    Called with the global mutex held and child suspended. Failure after claim
    stays consumed; no supported command can erase or rearm it.
    """
    import winreg
    if not ctypes.windll.shell32.IsUserAnAdmin():
        fail("IQP1_ACQUIRE_REQUIRES_ELEVATED_OWNER_AUTHORIZATION")
    with winreg.OpenKey(winreg.HKEY_LOCAL_MACHINE, REGISTRY,0,winreg.KEY_READ|winreg.KEY_WRITE) as key:
        pinned = json.loads(winreg.QueryValueEx(key,"Binding")[0])
        if (pinned["root"] != args.root or pinned["commit"] != args.commit or pinned["manifest"] != args.approve):
            fail("IQP1_OWNER_AUTHORIZATION_BINDING_MISMATCH")
        try:
            winreg.QueryValueEx(key,"Consumed")
        except FileNotFoundError:
            winreg.SetValueEx(key,"AuthorizedJob",0,winreg.REG_SZ,job_name)
            winreg.SetValueEx(key,"Consumed",0,winreg.REG_DWORD,1)
            winreg.FlushKey(key)
        else:
            fail("IQP1_MACHINE_PILOT_ALREADY_CONSUMED_PRESERVE_LEDGER")


def authenticated_acquisition():
    import winreg
    with winreg.OpenKey(winreg.HKEY_LOCAL_MACHINE,REGISTRY,0,winreg.KEY_READ) as key:
        if winreg.QueryValueEx(key,"Consumed")[0] != 1:
            fail("IQP1_MACHINE_AUTHORIZATION_NOT_CONSUMED")
        name = winreg.QueryValueEx(key,"AuthorizedJob")[0]
    require_query_only_job(name)


def prepare(args):
    if not ctypes.windll.shell32.IsUserAnAdmin():
        fail("IQP1_PREPARE_REQUIRES_ONE_TIME_ADMINISTRATOR")
    try:
        binding()
    except FileNotFoundError:
        pass
    else:
        fail("IQP1_MACHINE_ALREADY_BOUND_NO_RESET")
    root = Path(args.root)
    base_proof = base_python_proof(sys.base_prefix)
    cache = Path(args.cache).resolve(strict=True)
    if not (cache/"evidence.sqlite").is_file():
        fail("IQP1_EXISTING_PRIVATE_CACHE_REQUIRED")
    sid = owner_sid()
    credential = private_credential_metadata(args.credential_file,sid)  # metadata only, no read
    info = volume_command("Initialize", root)
    volume = root/"volume"
    temp = volume/"tmp"
    temp.mkdir()
    os.environ.update(TEMP=str(temp), TMP=str(temp))
    os.chdir(temp)
    # Physically allocate reserve, do not merely extend/sparsify its length.
    with (volume/"reserve.bin").open("xb") as handle:
        for _ in range(64):
            handle.write(b"\0"*(1024**2))
        handle.flush()
        os.fsync(handle.fileno())
    from iqp1_build import source_packet
    repo = Path(__file__).resolve().parents[1]
    packet = source_packet(repo)
    source = volume/"source"
    source.mkdir()
    with tarfile.open(fileobj=io.BytesIO(packet)) as archive:
        if archive.pax_headers.get("comment") != args.commit:
            fail("IQP1_SOURCE_ARCHIVE_COMMIT_CHANGED")
        archive.extractall(source, filter="data")
    subprocess.run([sys.executable, "-I", "-B", "-m", "venv", str(volume/"python")], check=True,
                   stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
    python = volume/"python"/"Scripts"/"python.exe"
    subprocess.run([str(python), "-I", "-B", "-m", "pip", "--isolated", "install", "--disable-pip-version-check",
                   "--no-cache-dir", "--index-url", "https://pypi.org/simple", "-r",
                   str(source/"trading_agent_starter"/"requirements.txt")], check=True,
                   stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
    # Store creation/cache validation occurs in the isolated quota-bound venv.
    manifest = dict(commit=args.commit, root=str(root), volume_id=info["volume_id"], owner_sid=sid,
                    cache=str(cache), ledger_id=uuid.uuid4().hex, source_sha256=hashlib.sha256(packet).hexdigest(),
                    runtime_sha256=runtime_hash(volume),
                    base_python=base_python_proof(sys.base_prefix),
                    credential_reference=str(credential),
                    source_only=True, external_spend=0)
    write_json(root/"manifest.json", manifest)
    subprocess.run([str(python), "-I", "-B", str(source/"tools"/"iqp1_local.py"), "seed", "--root", str(root),
                    "--commit", args.commit], check=True, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
    manifest = read_json(root/"manifest.json")
    proof = storage_gate(root, manifest, inspect=True)
    approval = hashlib.sha256(encode(manifest)).hexdigest()
    # Bind only after complete setup. A failed/partial VHD is preserved, never reset.
    write_json(root/"prepare.json", dict(status="OFFLINE_PREPARED", **proof,
               approve_manifest=approval, alpaca_attempts=0, credentials_read=False))
    storage_acl(root,sid,"Harden")
    storage_acl(root,sid,"Verify")
    # Prove that this owner's UAC linked token is accessible and non-elevated,
    # through the exact suspended-child/job path used for later acquisition.
    marker = temp/"standard-user-probe.json"
    probe_name = "Local\\IQP1-private-preflight-"+uuid.uuid4().hex
    probe = run_job([str(python),"-I","-B",str(source/"tools"/"iqp1_local.py"),"verify-child",
                    "--root",str(root),"--commit",args.commit,"--verify-job",probe_name],temporary=temp,seconds=180,
                    linked_user=True,mutex="Local\\IQP1-standard-user-probe",job_name=probe_name,protected_sid=sid)
    if probe["exit_code"] != 0 or read_json(marker)["elevated"]:
        fail("IQP1_STANDARD_USER_RUNTIME_UNAVAILABLE")
    binding(create=dict(root=str(root), manifest=approval, commit=args.commit, owner_sid=sid))


def seed_or_acquire(args):
    if args.mode == "acquire-child":
        authenticated_acquisition()
    elif args.mode not in {"seed","verify-child"}:
        fail("IQP1_PRIVATE_WORKER_MODE_REJECTED")
    root = Path(args.root)
    manifest = read_json(root/"manifest.json")
    sys.path.insert(0, str(root/"volume"/"source"/"trading_agent_starter"))
    from agent.audit_store import EvidenceStore
    from agent.iqp1_pilot import cache_chain, open_cache, packet_plan, run_pilot
    with_cache = open_cache(manifest["cache"])
    try:
        # Verify mandatory Jan15 references before reading credentials.
        references = {}
        for packet in packet_plan()[1:3]:
            chain = cache_chain(with_cache, packet)
            references[packet["id"]] = [{key:r[key] for key in ("id","record_hash","blob_sha")} for r in chain]
        if args.mode == "seed":
            if not ctypes.windll.shell32.IsUserAnAdmin():
                fail("IQP1_SEED_REQUIRES_ADMINISTRATOR")
            try:
                binding()
            except FileNotFoundError:
                pass
            else:
                fail("IQP1_SEED_MACHINE_ALREADY_BOUND")
            if (root/"volume"/"evidence").exists():
                fail("IQP1_SEED_REQUIRES_ABSENT_LEDGER")
            manifest["cache_references"] = references
            write_json(root/"manifest.json",manifest)
            store = EvidenceStore(root/"volume"/"evidence")
            try:
                store.append("iqp1_private_binding", manifest["ledger_id"], manifest)
            finally:
                store.close()
            return
        if args.mode == "verify-child":
            require_query_only_job(args.verify_job)
            if ctypes.windll.shell32.IsUserAnAdmin() or manifest["owner_sid"] != owner_sid():
                fail("IQP1_STANDARD_OWNER_TOKEN_REQUIRED")
            storage_acl(root,manifest["owner_sid"],"Verify")
            storage_gate(root,manifest,inspect=True)
            private_credential_metadata(manifest["credential_reference"],manifest["owner_sid"])
            if runtime_hash(root/"volume") != manifest["runtime_sha256"] or references != manifest["cache_references"]:
                fail("IQP1_OFFLINE_BINDINGS_CHANGED")
            if base_python_proof(sys.base_prefix) != manifest["base_python"]:
                fail("IQP1_BASE_PYTHON_CHANGED")
            write_json(root/"volume"/"tmp"/"standard-user-probe.json",{"status":"OFFLINE_READY","elevated":False})
            return
        if references != manifest["cache_references"]:
            fail("IQP1_APPROVED_CACHE_REFERENCES_CHANGED")
        if ctypes.windll.shell32.IsUserAnAdmin():
            fail("IQP1_ACQUIRE_MUST_NOT_RUN_ELEVATED")
        pinned = binding()
        if (pinned["root"] != str(root) or pinned["commit"] != args.commit
                or pinned["owner_sid"] != owner_sid()
                or pinned["manifest"] != hashlib.sha256(encode(manifest)).hexdigest()
                or args.approve != pinned["manifest"]):
            fail("IQP1_OWNER_APPROVAL_OR_MACHINE_BINDING_MISMATCH")
        proof = storage_gate(root, manifest, inspect=True)
        ledger = root/"volume"/"evidence"
        if not (ledger/"evidence.sqlite").is_file():
            fail("IQP1_SOLE_LEDGER_MISSING_NO_REPLACEMENT")
        store = EvidenceStore(ledger)
        try:
            seed = store.records("iqp1_private_binding", manifest["ledger_id"])
            if len(seed) != 1 or seed[0]["metadata"] != manifest:
                fail("IQP1_SOLE_LEDGER_BINDING_MISMATCH")
            store.verify()
            if store.records("iqp1_started"):
                fail("IQP1_ALREADY_STARTED_PRESERVE_LEDGER")
            # Local runtime only; never Prepare/CI/agents. No .env discovery.
            credential = Path(args.credential_file).resolve(strict=True)
            if str(credential) != manifest["credential_reference"]:
                fail("IQP1_CREDENTIAL_REFERENCE_CHANGED")
            # Reject shared ACLs before reading. Inspect permissions, not values.
            private_credential_metadata(credential,manifest["owner_sid"])
            secret = read_json(credential)
            if set(secret) != {"key_id", "secret_key"} or not all(isinstance(x, str) and x for x in secret.values()):
                fail("IQP1_CREDENTIAL_FORMAT_INVALID")
            result = run_pilot(store, with_cache, (secret["key_id"], secret["secret_key"]),
                               lambda: storage_gate(root, manifest))
            proof = storage_gate(root,manifest)
            write_json(ledger/"usage.json", dict(result, **proof))
        finally:
            store.close()
    finally:
        with_cache.close()


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("mode", choices=["Prepare", "Acquire", "prepare-child", "acquire-bootstrap", "acquire-child", "seed", "verify-child"])
    parser.add_argument("--root", required=True)
    parser.add_argument("--commit", required=True)
    parser.add_argument("--cache", default="")
    parser.add_argument("--credential-file", default="")
    parser.add_argument("--approve", default="")
    parser.add_argument("--verify-job",default="")
    args = parser.parse_args()
    if os.name != "nt":
        fail("IQP1_WINDOWS_REQUIRED")
    if sys.version_info[:2] != (3,13) or struct.calcsize("P") != 8:
        fail("IQP1_PYTHON_313_X64_REQUIRED")
    root = Path(os.path.abspath(args.root))
    args.root = str(root)
    if args.mode in {"prepare-child", "acquire-bootstrap", "seed", "acquire-child", "verify-child"}:
        require_pilot_job()
        if args.mode in {"acquire-bootstrap","acquire-child"}:
            authenticated_acquisition()
        # All potentially blocking git/setup/storage/network operations belong to
        # the kernel-supervised child tree, never the watchdog process.
        repo = Path(__file__).resolve().parents[1]
        if args.mode in {"prepare-child", "acquire-bootstrap"}:
            actual = subprocess.check_output(["git", "-C", str(repo), "rev-parse", "HEAD"], stderr=subprocess.DEVNULL).decode().strip()
            if actual != args.commit or subprocess.check_output(["git", "-C", str(repo), "status", "--porcelain", "--untracked-files=no"]):
                fail("IQP1_REVIEWED_CLEAN_COMMIT_REQUIRED")
        if args.mode == "acquire-bootstrap":
            manifest = read_json(root/"manifest.json")
            if args.commit != manifest["commit"] or args.approve != hashlib.sha256(encode(manifest)).hexdigest():
                fail("IQP1_EXPLICIT_PREPARED_MANIFEST_APPROVAL_REQUIRED")
            storage_acl(root,manifest["owner_sid"],"Verify")
            storage_gate(root,manifest,inspect=True)
            if runtime_hash(root/"volume") != manifest["runtime_sha256"]:
                fail("IQP1_EXECUTABLE_RUNTIME_CHANGED")
            if base_python_proof(sys.base_prefix) != manifest["base_python"]:
                fail("IQP1_BASE_PYTHON_CHANGED")
            temporary = root/"volume"/"tmp"
            os.environ.update(TEMP=str(temporary), TMP=str(temporary))
            command = [root/"volume"/"python"/"Scripts"/"python.exe", "-I", "-B",
                       root/"volume"/"source"/"tools"/"iqp1_local.py", "acquire-child",
                       "--root", root, "--commit", args.commit, "--approve", args.approve,
                       "--credential-file", args.credential_file]
            return subprocess.call([str(x) for x in command], cwd=temporary)
        if args.mode == "prepare-child":
            prepare(args)
        else:
            seed_or_acquire(args)
        return 0
    # The parent only supervises. Slow checks are in the job, under the deadline.
    repo = Path(__file__).resolve().parents[1]
    if args.mode == "Prepare":
        root.mkdir(parents=True, exist_ok=True)
        temporary = root
        mode = "prepare-child"
    else:
        temporary = root
        mode = "acquire-bootstrap"
    python, script = Path(sys.executable), Path(__file__)
    command = [python, "-I", "-B", script, mode, "--root", root, "--commit", args.commit,
               "--cache", args.cache, "--credential-file", args.credential_file, "--approve", args.approve]
    job_name = "Global\\TradingAgent-IQP1-"+uuid.uuid4().hex if args.mode == "Acquire" else None
    protected_sid = binding()["owner_sid"] if args.mode == "Acquire" else None
    result = run_job(command, temporary=temporary, linked_user=args.mode == "Acquire",
                     before_start=(lambda:consume_once(args,job_name)) if args.mode == "Acquire" else None,
                     job_name=job_name,protected_sid=protected_sid)
    # No raw HTTP, exceptions, secret paths or child stdout in console/CI logs.
    result.update(alpaca_attempts=0 if args.mode == "Prepare" else "see sole ledger",
                  external_cost=0)
    print(json.dumps(result, sort_keys=True))
    if result["exit_code"] == 0 and args.mode == "Prepare":
        print("APPROVE_MANIFEST="+read_json(root/"prepare.json")["approve_manifest"])
    return result["exit_code"]


if __name__ == "__main__":
    try:
        raise SystemExit(main())
    except (Exception, KeyboardInterrupt) as error:
        # Preserve files/ledger on all failure paths; never print arbitrary errors.
        import re
        reason = str(error) if isinstance(error,RuntimeError) and re.fullmatch(r"[A-Z][A-Z0-9_]{0,120}",str(error)) else "LOCAL_RUNTIME_FAILURE"
        print("IQP1_STOPPED_PRESERVE_PRIVATE_ROOT: "+reason, file=sys.stderr)
        raise SystemExit(1)

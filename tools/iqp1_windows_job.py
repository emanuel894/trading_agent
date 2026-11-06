"""Windows kernel Job Object. Assign a suspended child before its first opcode.

The parent owns the only job handle. Closing it or the absolute wall deadline
kills the entire tree, including blocked native/network calls. No Docker daemon,
process-local RAM counter or cooperative timeout is used as enforcement.
"""
import ctypes
from ctypes import wintypes as W
import os
from pathlib import Path
import subprocess
import time

# Keep the agreed RAM envelope unchanged. Windows' peak commit statistic can
# include a denied allocation's transient charge (observed in hosted Windows).
# Reserve headroom inside the envelope; never relax the outer test/owner cap.
KERNEL_HEADROOM = 8*1024**2


def sealed_environment(temporary):
    result = {key:os.environ[key] for key in ("SystemRoot", "WINDIR", "PATH", "COMSPEC") if key in os.environ}
    result.update(TEMP=str(temporary), TMP=str(temporary), PYTHONNOUSERSITE="1",
                  TRADING_ENABLED="false", ALLOW_PAPER_ORDERS="false", ALPACA_LIVE_TRADE="false")
    return result


def require_pilot_job():
    """Reject a worker called directly outside our configured kernel job."""
    if os.name != "nt":
        raise RuntimeError("WINDOWS_KERNEL_REQUIRED")
    k = ctypes.WinDLL("kernel32", use_last_error=True)
    k.QueryInformationJobObject.argtypes = [W.HANDLE, ctypes.c_int, W.LPVOID, W.DWORD, W.LPVOID]
    k.QueryInformationJobObject.restype = W.BOOL
    # Read the same native struct layout without requiring a named/inheritable
    # job handle in a child. NULL queries the current process's innermost job.
    class Basic(ctypes.Structure):
        _fields_ = [("process_time",ctypes.c_int64),("job_time",ctypes.c_int64),("flags",W.DWORD),
                    ("min_ws",ctypes.c_size_t),("max_ws",ctypes.c_size_t),("active",W.DWORD),
                    ("affinity",ctypes.c_size_t),("priority",W.DWORD),("scheduling",W.DWORD)]
    class Extended(ctypes.Structure):
        _fields_ = [("basic",Basic),("io",ctypes.c_uint64*6),("process_memory",ctypes.c_size_t),
                    ("job_memory",ctypes.c_size_t),("peak_process",ctypes.c_size_t),("peak_job",ctypes.c_size_t)]
    info = Extended()
    if (not k.QueryInformationJobObject(None,9,ctypes.byref(info),ctypes.sizeof(info),None)
            or info.basic.flags & 0x2308 != 0x2308 or info.job_memory != 2*1024**3-KERNEL_HEADROOM
            or info.process_memory != 2*1024**3-KERNEL_HEADROOM or not 1 <= info.basic.active <= 8):
        raise RuntimeError("IQP1_REQUIRED_KERNEL_JOB_NOT_PRESENT")


def run_job(command, *, temporary, seconds=1800, memory=2*1024**3, mutex="Global\\TradingAgent-IQP1", active_processes=8,
            linked_user=False, before_start=None):
    if os.name != "nt":
        raise RuntimeError("WINDOWS_KERNEL_REQUIRED")
    if not 0 < seconds <= 1800 or not 32*1024**2 <= memory <= 2*1024**3 or not 1 <= active_processes <= 8:
        raise ValueError("INVALID_JOB_LIMITS")
    started = time.monotonic()
    wall_started = time.time()
    k = ctypes.WinDLL("kernel32", use_last_error=True)
    SIZE = ctypes.c_size_t
    class Basic(ctypes.Structure):
        _fields_ = [("process_time", ctypes.c_int64), ("job_time", ctypes.c_int64),
                    ("flags", W.DWORD), ("min_ws", SIZE), ("max_ws", SIZE),
                    ("active", W.DWORD), ("affinity", SIZE), ("priority", W.DWORD), ("scheduling", W.DWORD)]
    class IO(ctypes.Structure):
        _fields_ = [(name, ctypes.c_uint64) for name in ("read_ops", "write_ops", "other_ops", "read", "write", "other")]
    class Limits(ctypes.Structure):
        _fields_ = [("basic", Basic), ("io", IO), ("process_memory", SIZE), ("job_memory", SIZE),
                    ("peak_process", SIZE), ("peak_job", SIZE)]
    class Startup(ctypes.Structure):
        _fields_ = [("cb", W.DWORD), ("reserved", W.LPWSTR), ("desktop", W.LPWSTR), ("title", W.LPWSTR),
                    *[(name, W.DWORD) for name in ("x", "y", "xsize", "ysize", "xchars", "ychars", "fill", "flags")],
                    ("show", W.WORD), ("reserved_size", W.WORD), ("reserved_ptr", ctypes.POINTER(ctypes.c_byte)),
                    ("stdin", W.HANDLE), ("stdout", W.HANDLE), ("stderr", W.HANDLE)]
    class Process(ctypes.Structure):
        _fields_ = [("process", W.HANDLE), ("thread", W.HANDLE), ("pid", W.DWORD), ("tid", W.DWORD)]
    prototypes = {
        "CreateJobObjectW": ([W.LPVOID, W.LPCWSTR], W.HANDLE),
        "SetInformationJobObject": ([W.HANDLE, ctypes.c_int, W.LPVOID, W.DWORD], W.BOOL),
        "QueryInformationJobObject": ([W.HANDLE, ctypes.c_int, W.LPVOID, W.DWORD, W.LPVOID], W.BOOL),
        "CreateMutexW": ([W.LPVOID, W.BOOL, W.LPCWSTR], W.HANDLE),
        "ReleaseMutex": ([W.HANDLE], W.BOOL),
        "WaitForSingleObject": ([W.HANDLE, W.DWORD], W.DWORD),
        "CloseHandle": ([W.HANDLE], W.BOOL),
        "AssignProcessToJobObject": ([W.HANDLE, W.HANDLE], W.BOOL),
        "ResumeThread": ([W.HANDLE], W.DWORD),
        "TerminateJobObject": ([W.HANDLE, W.UINT], W.BOOL),
        "TerminateProcess": ([W.HANDLE, W.UINT], W.BOOL),
        "GetExitCodeProcess": ([W.HANDLE, ctypes.POINTER(W.DWORD)], W.BOOL),
        "CreateProcessW": ([W.LPCWSTR, W.LPWSTR, W.LPVOID, W.LPVOID, W.BOOL, W.DWORD,
                           W.LPVOID, W.LPCWSTR, ctypes.POINTER(Startup), ctypes.POINTER(Process)], W.BOOL),
    }
    for name, (args, result) in prototypes.items():
        function = getattr(k, name)
        function.argtypes, function.restype = args, result
    def check(value):
        if not value:
            raise OSError("WINDOWS_JOB_ENFORCEMENT_FAILED")
        return value
    lock = check(k.CreateMutexW(None, False, mutex))
    job, pi, acquired, token = None, Process(), False, None
    try:
        if k.WaitForSingleObject(lock, 0) != 0:
            raise RuntimeError("IQP1_OTHER_WORKER_OR_ABANDONED_LOCK")
        acquired = True
        job = check(k.CreateJobObjectW(None, None))
        limit = Limits()
        # KILL_ON_JOB_CLOSE | JOB_MEMORY | PROCESS_MEMORY | ACTIVE_PROCESS.
        # One acquisition Python; up to eight descendants for offline setup only.
        limit.basic.flags = 0x2000 | 0x200 | 0x100 | 0x8
        kernel_limit = memory-KERNEL_HEADROOM
        limit.basic.active, limit.process_memory, limit.job_memory = active_processes, kernel_limit, kernel_limit
        check(k.SetInformationJobObject(job, 9, ctypes.byref(limit), ctypes.sizeof(limit)))
        actual = Limits()
        check(k.QueryInformationJobObject(job, 9, ctypes.byref(actual), ctypes.sizeof(actual), None))
        if actual.basic.flags != limit.basic.flags or actual.job_memory != kernel_limit:
            raise RuntimeError("WINDOWS_JOB_LIMIT_READBACK_FAILED")
        env = sealed_environment(temporary)
        block = ctypes.create_unicode_buffer("\0".join(key+"="+value for key,value in sorted(env.items()))+"\0\0")
        si = Startup()
        si.cb = ctypes.sizeof(si)
        text = ctypes.create_unicode_buffer(subprocess.list2cmdline([str(value) for value in command]))
        # CREATE_SUSPENDED | CREATE_UNICODE_ENVIRONMENT | CREATE_NO_WINDOW.
        if linked_user:
            # Elevated owner authorizes/consumes one pilot; acquisition executes
            # as that owner's UAC-filtered standard token. No password is used.
            a = ctypes.WinDLL("advapi32", use_last_error=True)
            a.OpenProcessToken.argtypes = [W.HANDLE,W.DWORD,ctypes.POINTER(W.HANDLE)]
            a.OpenProcessToken.restype = W.BOOL
            a.GetTokenInformation.argtypes = [W.HANDLE,ctypes.c_int,W.LPVOID,W.DWORD,ctypes.POINTER(W.DWORD)]
            a.GetTokenInformation.restype = W.BOOL
            a.CreateProcessWithTokenW.argtypes = [W.HANDLE,W.DWORD,W.LPCWSTR,W.LPWSTR,W.DWORD,W.LPVOID,
                                                W.LPCWSTR,ctypes.POINTER(Startup),ctypes.POINTER(Process)]
            a.CreateProcessWithTokenW.restype = W.BOOL
            current, linked, needed = W.HANDLE(), W.HANDLE(), W.DWORD()
            check(a.OpenProcessToken(W.HANDLE(-1),0x8,ctypes.byref(current)))
            try:
                check(a.GetTokenInformation(current,19,ctypes.byref(linked),ctypes.sizeof(linked),ctypes.byref(needed)))
            finally:
                k.CloseHandle(current)
            token = linked
            check(a.CreateProcessWithTokenW(token,0,str(Path(command[0]).resolve()),text,0x4|0x400|0x08000000,
                                           block,str(temporary),ctypes.byref(si),ctypes.byref(pi)))
        else:
            check(k.CreateProcessW(str(Path(command[0]).resolve()), text, None, None, False,
                                  0x4|0x400|0x08000000, block, str(temporary), ctypes.byref(si), ctypes.byref(pi)))
        try:
            check(k.AssignProcessToJobObject(job, pi.process))
        except BaseException:
            k.TerminateProcess(pi.process, 126)
            raise
        if before_start is not None:
            before_start()  # machine-protected one-shot claim, under global mutex
        if k.ResumeThread(pi.thread) == 0xFFFFFFFF:
            raise OSError("WINDOWS_CHILD_RESUME_FAILED")
        # A single Windows relative wait can exclude time spent in suspend.
        # Recheck independent elapsed/wall clocks so sleep or a clock step cannot
        # grant another thirty minutes. No child cooperation is required.
        while True:
            remaining = seconds-max(time.monotonic()-started,time.time()-wall_started)
            if remaining <= 0:
                timed_out = True
                break
            status = k.WaitForSingleObject(pi.process, min(100,max(1,int(remaining*1000))))
            if status == 0:
                timed_out = False
                break
            if status != 0x102:
                raise OSError("WINDOWS_JOB_WAIT_FAILED")
        # Always kill any surviving descendant, even when the lead child exits.
        check(k.TerminateJobObject(job, 124 if timed_out else 125))
        code = W.DWORD()
        check(k.GetExitCodeProcess(pi.process, ctypes.byref(code)))
        check(k.QueryInformationJobObject(job, 9, ctypes.byref(actual), ctypes.sizeof(actual), None))
        return {"exit_code":124 if timed_out else code.value, "timed_out":timed_out,
                "wall_seconds":time.monotonic()-started, "peak_job_bytes":actual.peak_job,
                "memory_cap_bytes":memory, "kernel_commit_cap_bytes":kernel_limit,"deadline_seconds":seconds}
    finally:
        if job:
            k.CloseHandle(job)  # kernel termination on exceptions/parent exit too
        if token:
            k.CloseHandle(token)
        for handle in (pi.thread, pi.process):
            if handle:
                k.CloseHandle(handle)
        if acquired:
            k.ReleaseMutex(lock)
        k.CloseHandle(lock)

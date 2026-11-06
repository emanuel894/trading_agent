"""Credential-free Docker qualification only. There is deliberately no online mode."""
import argparse
import json
import os
from pathlib import Path
import re
import signal
import subprocess
import sys
import time
import uuid


def command(image, mode, seconds):
    if mode not in {'qualification', 'watchdog-test', 'storage-test', 'memory-test'} or type(seconds) is not int or not 1 <= seconds <= 1800:
        raise ValueError('Only bounded offline qualification is supported')
    if not re.fullmatch(r'sha256:[0-9a-f]{64}', image):
        raise ValueError('Use an immutable local image ID')
    return ['docker', 'run', '--read-only', '--network=none', '--memory=2g',
            '--memory-swap=2g', '--cpus=1', '--pids-limit=64', '--cap-drop=ALL',
            '--security-opt=no-new-privileges', '--user=65534:65534', '--ipc=none',
            '--log-driver=none', '--ulimit=core=0',
            '--tmpfs=/tmp:rw,noexec,nosuid,nodev,size=3g,mode=1777',
            '--env=HOME=/tmp', '--env=TMPDIR=/tmp', '--env=PYTHONDONTWRITEBYTECODE=1',
            '--env=TRADING_ENABLED=false', '--env=ALLOW_PAPER_ORDERS=false',
            '--env=ALPACA_LIVE_TRADE=false', image, '--inside', mode, '--seconds', str(seconds)]


def supervise(argv, seconds):
    child = subprocess.Popen(argv, start_new_session=True)
    try:
        return child.wait(timeout=seconds)
    except subprocess.TimeoutExpired:
        if os.name == "nt":
            subprocess.run(["taskkill", "/F", "/T", "/PID", str(child.pid)],
                           stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL, check=True, timeout=5)
        else:
            os.killpg(child.pid, signal.SIGKILL)
        child.wait()
        return 124


def isolated_interfaces(flags):
    return all(name == "lo" or not value & 1 for name, value in flags.items())


def preflight():
    if os.getuid() == 0:
        raise RuntimeError('Non-root user required')
    memory = int(Path('/sys/fs/cgroup/memory.max').read_text())
    swap = int(Path('/sys/fs/cgroup/memory.swap.max').read_text())
    if memory != 2 * 1024**3 or swap != 0:
        raise RuntimeError('Memory/swap ceilings not active')
    mounts = Path('/proc/mounts').read_text().splitlines()
    root = next(x.split() for x in mounts if x.split()[1] == '/')
    tmp = next(x.split() for x in mounts if x.split()[1] == '/tmp')
    if 'ro' not in root[3].split(',') or tmp[2] != 'tmpfs':
        raise RuntimeError('Read-only root and bounded tmpfs required')
    stat = os.statvfs('/tmp')
    capacity = stat.f_blocks * stat.f_frsize
    if capacity != 3 * 1024**3:
        raise RuntimeError('Unexpected scratch quota')
    import socket
    flags = {name: int(Path('/sys/class/net', name, 'flags').read_text(), 16)
             for _, name in socket.if_nameindex()}
    if not isolated_interfaces(flags) or len(Path('/proc/net/route').read_text().splitlines()) != 1:
        raise RuntimeError('Network isolation missing')
    for key in ('TRADING_ENABLED', 'ALLOW_PAPER_ORDERS', 'ALPACA_LIVE_TRADE'):
        if os.environ.get(key) != 'false':
            raise RuntimeError('Read-only flags required')
    # Physically allocated reserve, charged to the same RAM/storage ceilings.
    with open('/tmp/reserve', 'wb') as reserve:
        os.posix_fallocate(reserve.fileno(), 0, 64 * 1024**2)
    print(json.dumps({'memory_max': memory, 'swap_max': swap,
                      'scratch_bytes': capacity, 'allocated_reserve': 64 * 1024**2,
                      'network': 'none', 'root': 'read-only'}), flush=True)


def worker(mode):
    preflight()
    if mode == 'watchdog-test':
        time.sleep(1900)
        return 1
    if mode == 'storage-test':
        import errno
        try:
            with open('/tmp/oversize', 'wb') as target:
                os.posix_fallocate(target.fileno(), 0, 4 * 1024**3)
        except OSError as error:
            if error.errno == errno.ENOSPC:
                print('STORAGE_OVER_CAP_REJECTED', flush=True)
                return 0
            raise
        raise RuntimeError('Storage quota not enforced')
    if mode == 'memory-test':
        # Separate qualification container: expected OOMKilled/exit 137.
        blocks = []
        while True:
            blocks.append(bytearray(32 * 1024**2))
    code = subprocess.call([sys.executable, '-m', 'unittest', 'discover', '-s', 'tests', '-v'])
    if code:
        return code
    # Demo is fixture-only; do not print or inspect generated performance output.
    with open(os.devnull, 'wb') as sink:
        return subprocess.call([sys.executable, '-m', 'agent', 'demo', '--output', '/tmp/demo'], stdout=sink)


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--image', default='trading-agent-iqp1:offline')
    parser.add_argument('--inside', choices=['qualification', 'watchdog-test', 'storage-test', 'memory-test'])
    parser.add_argument('--worker', choices=['qualification', 'watchdog-test', 'storage-test', 'memory-test'])
    parser.add_argument('--mode', default='qualification', choices=['qualification', 'watchdog-test', 'storage-test', 'memory-test'])
    parser.add_argument('--seconds', type=int, default=1800)
    args = parser.parse_args()
    if not 1 <= args.seconds <= 1800:
        parser.error('Deadline must be 1..1800 seconds')
    if args.worker:
        return worker(args.worker)
    if args.inside:
        result = supervise([sys.executable, __file__, '--worker', args.inside], args.seconds)
        # PID 1 exit destroys the namespace, including any detached descendants.
        if result == 124:
            os._exit(124)
        return result
    info = json.loads(subprocess.check_output(['docker', 'image', 'inspect', args.image]))[0]
    if info['Size'] > 768 * 1024**2:
        raise RuntimeError('Image exceeds offline envelope')
    argv = command(info['Id'], args.mode, args.seconds)
    name = 'iqp1-offline-' + uuid.uuid4().hex
    argv[2:2] = ['--name', name]
    try:
        result = supervise(argv, args.seconds + 10)
        state = json.loads(subprocess.check_output(['docker', 'inspect', name]))[0]['State']
        print(json.dumps({'exit_code': state['ExitCode'], 'oom_killed': state['OOMKilled'],
                          'image_bytes': info['Size'], 'mode': args.mode}), flush=True)
        return result
    finally:
        subprocess.run(['docker', 'rm', '-f', name], stdout=subprocess.DEVNULL, check=True)


if __name__ == '__main__':
    sys.exit(main())

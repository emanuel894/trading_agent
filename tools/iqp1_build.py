"""Build an offline qualification image from committed source only; never build cwd."""
import io
from pathlib import Path
import subprocess
import tarfile
import tempfile


def safe_source_name(name):
    return bool(name) and not any(
        part.startswith('.env') or part in {'.git', '.venv', 'venv', 'runs', '__pycache__', '..'}
        or part.endswith('.local.json') for part in Path(name).parts) and not Path(name).is_absolute()


def source_packet(root):
    # Resolve once so an advancing branch cannot change the listing/archive binding.
    commit = subprocess.check_output(['git', '-C', str(root), 'rev-parse', '--verify', 'HEAD^{commit}']).decode().strip()
    paths = subprocess.check_output(['git', '-C', str(root), 'ls-tree', '-r', '--name-only', '-z', commit]).decode().split('\0')
    allowed = [name for name in paths if safe_source_name(name)]
    if not allowed:
        raise ValueError('No committed source')
    packet = subprocess.check_output(['git', '--literal-pathspecs', '-C', str(root), 'archive', commit, '--', *allowed])
    with tarfile.open(fileobj=io.BytesIO(packet)) as archive:
        if any(not (item.isfile() or item.isdir()) or not safe_source_name(item.name) for item in archive):
            raise ValueError('Unsafe path, link or special file in source context')
    return packet


def main():
    root = Path(__file__).resolve().parents[1]
    packet = source_packet(root)
    with tempfile.TemporaryDirectory(prefix='iqp1-source-') as temporary:
        with tarfile.open(fileobj=io.BytesIO(packet)) as archive:
            archive.extractall(temporary, filter='data')
        return subprocess.call(['docker', 'build', '-f', 'docker/iqp1-offline.Dockerfile',
                                '-t', 'trading-agent-iqp1:offline', temporary], cwd=temporary)


if __name__ == '__main__':
    raise SystemExit(main())

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
    # Resolve the reviewed commit once. Never pass the full tracked-file list
    # as Windows command-line arguments (CreateProcess has a ~32767-char cap).
    # Archive only committed Git objects; do not read the working tree.
    commit = subprocess.check_output(
        ['git', '-C', str(root), 'rev-parse', '--verify', 'HEAD^{commit}']
    ).decode().strip()
    original = subprocess.check_output(['git', '-C', str(root), 'archive', commit])
    output = io.BytesIO()
    count = 0
    with tarfile.open(fileobj=io.BytesIO(original), mode='r:') as archive:
        if archive.pax_headers.get('comment') != commit:
            raise ValueError('Reviewed source archive commit mismatch')
        # Filter before constructing the returned packet; excluded tracked
        # paths never enter the isolated runtime and special files fail closed.
        with tarfile.open(fileobj=output, mode='w', format=tarfile.PAX_FORMAT,
                          pax_headers={'comment': commit}) as filtered:
            for item in archive:
                if not safe_source_name(item.name):
                    continue
                if not item.isfile() and not item.isdir():
                    raise ValueError('Unsafe path, link or special file in source context')
                source = archive.extractfile(item) if item.isfile() else None
                try:
                    filtered.addfile(item, source)
                finally:
                    if source is not None:
                        source.close()
                if item.isfile():
                    count += 1
    if not count:
        raise ValueError('No committed source')
    return output.getvalue()


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

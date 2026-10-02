#!/usr/bin/env python3
"""Download, verify and extract a private data release in a cloud session (REST API only).

  python data_pulls/fetch_release.py --manifest ../options-data/manifests/research7-data-2026-10.json --output ..

Uses `gh api` REST endpoints (GraphQL is unavailable in Claude cloud sessions), checks every archive and
every extracted file against the manifest, rejects unsafe archive members and never overwrites a
different existing file. --offline extracts from already-downloaded archives without any network call.
"""
import argparse
import hashlib
import json
import os
import shutil
import subprocess
import tarfile
import tempfile
from pathlib import Path, PurePosixPath


def digest(path):
    h = hashlib.sha256()
    with open(path, 'rb') as stream:
        for chunk in iter(lambda: stream.read(1 << 20), b''):
            h.update(chunk)
    return h.hexdigest()


def download(repo, tag, name, path, assets):
    if name not in assets:
        raise ValueError('Release asset missing: ' + name)
    tmp = path.with_suffix(path.suffix + '.partial')
    try:
        with tmp.open('wb') as stream:
            subprocess.run(['gh', 'api', f'repos/{repo}/releases/assets/{assets[name]}',
                            '-H', 'Accept: application/octet-stream'], stdout=stream, check=True)
        tmp.replace(path)
    finally:
        tmp.unlink(missing_ok=True)


def extract(archive, output, records):
    output = output.resolve()
    expected = {r['path']: r for r in records}
    seen = set()
    with tarfile.open(archive, 'r:*') as tar:
        for member in tar:
            rel = PurePosixPath(member.name)
            if rel.is_absolute() or '..' in rel.parts or not member.isfile() or member.name not in expected or member.name in seen:
                raise ValueError('Unexpected or unsafe archive member: ' + member.name)
            target = output.joinpath(*rel.parts)
            if not target.resolve().is_relative_to(output):
                raise ValueError('Archive member escapes destination: ' + member.name)
            record = expected[member.name]
            if member.size != record['bytes']:
                raise ValueError('File size mismatch: ' + member.name)
            seen.add(member.name)
            if target.exists() and digest(target) == record['sha256']:
                continue
            if target.exists():
                raise FileExistsError('Different existing file: ' + str(target))
            target.parent.mkdir(parents=True, exist_ok=True)
            source = tar.extractfile(member)
            with tempfile.NamedTemporaryFile(dir=target.parent, prefix='.fetch-', delete=False) as stream:
                tmp = Path(stream.name)
                shutil.copyfileobj(source, stream)
            try:
                if digest(tmp) != record['sha256']:
                    raise ValueError('File checksum mismatch: ' + member.name)
                os.replace(tmp, target)
            finally:
                tmp.unlink(missing_ok=True)
    if seen != set(expected):
        raise ValueError('Archive is missing manifest entries: ' + str(archive))


def main(argv=None):
    p = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    p.add_argument('--manifest', required=True, type=Path)
    p.add_argument('--output', required=True, type=Path, help='workspace parent (e.g. /home/user)')
    p.add_argument('--repo', default='nicjia/options-data')
    p.add_argument('--cache-dir', type=Path, default=None)
    p.add_argument('--archive', action='append', help='only these archive names')
    p.add_argument('--offline', action='store_true')
    args = p.parse_args(argv)
    manifest = json.loads(args.manifest.read_text())
    tag = manifest['tag']
    cache = args.cache_dir or args.manifest.resolve().parent.parent / '.downloads' / tag
    cache.mkdir(parents=True, exist_ok=True)
    args.output.mkdir(parents=True, exist_ok=True)
    archives = [a for a in manifest['archives'] if not args.archive or a['name'] in args.archive]
    assets = None
    for a in archives:
        path = cache / a['name']
        if not path.exists() or digest(path) != a['sha256']:
            if args.offline:
                raise ValueError('Offline archive missing or corrupt: ' + a['name'])
            if assets is None:
                release = json.loads(subprocess.check_output(['gh', 'api', f"repos/{args.repo}/releases/tags/{tag}"]))
                assets = {x['name']: int(x['id']) for x in release['assets']}
            download(args.repo, tag, a['name'], path, assets)
        if path.stat().st_size != a['bytes'] or digest(path) != a['sha256']:
            raise ValueError('Archive checksum mismatch: ' + a['name'])
        extract(path, args.output, [r for r in manifest['files'] if r['archive'] == a['name']])
        print(f"Verified and restored {a['name']}: {a['files']} files", flush=True)


if __name__ == '__main__':
    main()

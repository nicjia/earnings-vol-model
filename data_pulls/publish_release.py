#!/usr/bin/env python3
"""Package a local data directory into verified archives and publish them as a private GitHub release.

Run locally (needs the GitHub CLI logged in with access to the private repository):

  python data_pulls/publish_release.py --data ~/stock/wrds_studies/research7_data --root ~/stock \
      --tag research7-data-2026-10 --options-data ~/stock/options-data

It writes archives to --staging, a manifest (same schema as options-data/cache-manifest.json) to
<options-data>/manifests/<tag>.json plus <options-data>/manifests/<tag>.SHA256SUMS, creates the release
<tag> in --repo and uploads every archive and the manifest. Re-running resumes: archives already uploaded
with the same size are skipped. Finally it prints the git commands that commit the manifest.
"""
import argparse
import hashlib
import json
import os
import subprocess
import sys
import tarfile

LIMIT = 1_800_000_000  # stay below GitHub's 2 GiB per-asset limit


def sha256(path):
    h = hashlib.sha256()
    with open(path, 'rb') as stream:
        for chunk in iter(lambda: stream.read(1 << 20), b''):
            h.update(chunk)
    return h.hexdigest()


def inventory(data, root):
    files = []
    for base, _, names in os.walk(data):
        for n in sorted(names):
            if n.endswith('.partial'):
                continue
            p = os.path.join(base, n)
            files.append({'abs': p, 'path': os.path.relpath(p, root).replace(os.sep, '/'), 'bytes': os.path.getsize(p)})
    return sorted(files, key=lambda f: f['path'])


def group_key(rel, data_rel):
    """Archive grouping: top-level files together; option quotes by year; other subfolders whole."""
    inner = rel[len(data_rel) + 1:]
    parts = inner.split('/')
    if len(parts) == 1:
        return 'meta'
    if parts[0] == 'options':
        year = [t for t in parts[1].replace('.csv.gz', '').split('_') if t.isdigit() and len(t) == 4]
        return f'options-{year[0] if year else "misc"}'
    return parts[0]


def plan_archives(files, data_rel, prefix):
    groups = {}
    for f in files:
        groups.setdefault(group_key(f['path'], data_rel), []).append(f)
    archives = []
    for key in sorted(groups):
        chunk, size, n = [], 0, 0
        for f in groups[key]:
            if chunk and size + f['bytes'] > LIMIT:
                archives.append((f'{prefix}-{key}-{n:02d}.tar.gz', chunk))
                chunk, size, n = [], 0, n + 1
            chunk.append(f)
            size += f['bytes']
        archives.append((f'{prefix}-{key}-{n:02d}.tar.gz', chunk))
    return archives


def build(data, root, staging, tag, prefix):
    data, root = os.path.abspath(os.path.expanduser(data)), os.path.abspath(os.path.expanduser(root))
    if not data.startswith(root + os.sep):
        sys.exit('--data must be inside --root so archive paths restore the workspace layout')
    os.makedirs(staging, exist_ok=True)
    files = inventory(data, root)
    data_rel = os.path.relpath(data, root).replace(os.sep, '/')
    manifest = {'tag': tag, 'root_layout': f'Extract into the parent workspace; files restore under {data_rel}/',
                'files': [], 'archives': []}
    for name, chunk in plan_archives(files, data_rel, prefix):
        path = os.path.join(staging, name)
        if not os.path.exists(path):
            tmp = path + '.partial'
            with tarfile.open(tmp, 'w:gz', compresslevel=1) as tar:
                for f in chunk:
                    info = tar.gettarinfo(f['abs'], arcname=f['path'])
                    info.uid = info.gid = 0
                    info.uname = info.gname = ''
                    with open(f['abs'], 'rb') as stream:
                        tar.addfile(info, stream)
            os.replace(tmp, path)
        for f in chunk:
            manifest['files'].append({'path': f['path'], 'bytes': f['bytes'], 'sha256': sha256(f['abs']), 'archive': name})
        manifest['archives'].append({'name': name, 'files': len(chunk), 'bytes': os.path.getsize(path), 'sha256': sha256(path)})
        print(f"{name}: {len(chunk)} files, {os.path.getsize(path) / 1e6:.1f} MB", flush=True)
    return manifest


def gh(*args, capture=False):
    return subprocess.run(['gh', *args], check=True, text=True, capture_output=capture).stdout


def publish(manifest, staging, repo, tag, manifest_path):
    try:
        gh('release', 'view', tag, '--repo', repo, capture=True)
    except subprocess.CalledProcessError:
        gh('release', 'create', tag, '--repo', repo, '--title', tag,
           '--notes', 'Licensed WRDS research data (OptionMetrics + I/B/E/S). Keep private. See manifests/' + tag + '.json')
    existing = json.loads(gh('api', f'repos/{repo}/releases/tags/{tag}', capture=True))
    uploaded = {a['name']: a['size'] for a in existing['assets']}
    for a in manifest['archives']:
        if uploaded.get(a['name']) == a['bytes']:
            continue
        print('uploading', a['name'], flush=True)
        gh('release', 'upload', tag, os.path.join(staging, a['name']), '--repo', repo, '--clobber')
    gh('release', 'upload', tag, manifest_path, '--repo', repo, '--clobber')


def main(argv=None):
    p = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    p.add_argument('--data', required=True, help='directory to publish, e.g. ~/stock/wrds_studies/research7_data')
    p.add_argument('--root', required=True, help='workspace root that archive paths are relative to, e.g. ~/stock')
    p.add_argument('--tag', required=True)
    p.add_argument('--options-data', required=True, help='local checkout of the private options-data repository')
    p.add_argument('--repo', default='nicjia/options-data')
    p.add_argument('--staging', default=None, help='where archives are written (default: <data>/../.release-<tag>)')
    p.add_argument('--no-upload', action='store_true', help='build archives and manifest only')
    args = p.parse_args(argv)
    staging = args.staging or os.path.join(os.path.dirname(os.path.abspath(os.path.expanduser(args.data))), f'.release-{args.tag}')
    manifest = build(args.data, args.root, staging, args.tag, prefix=args.tag)
    mdir = os.path.join(os.path.expanduser(args.options_data), 'manifests')
    os.makedirs(mdir, exist_ok=True)
    manifest_path = os.path.join(mdir, f'{args.tag}.json')
    with open(manifest_path, 'w') as stream:
        json.dump(manifest, stream, indent=1)
    with open(os.path.join(mdir, f'{args.tag}.SHA256SUMS'), 'w') as stream:
        for a in manifest['archives']:
            stream.write(f"{a['sha256']}  {a['name']}\n")
    total = sum(a['bytes'] for a in manifest['archives'])
    print(f"manifest: {len(manifest['files'])} files in {len(manifest['archives'])} archives, {total / 1e9:.2f} GB")
    if not args.no_upload:
        publish(manifest, staging, args.repo, args.tag, manifest_path)
    print('\nCommit the manifest so cloud sessions can verify downloads:')
    print(f'  cd {args.options_data} && git add manifests/{args.tag}.json manifests/{args.tag}.SHA256SUMS '
          f'&& git commit -m "Add {args.tag} data manifest" && git push')


if __name__ == '__main__':
    main()

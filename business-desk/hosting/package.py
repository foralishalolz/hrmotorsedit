#!/usr/bin/env python3
"""Build clean, reproducible operator kits from one application source tree.

No workspace sweep: runtime editions use explicit paths; the GitHub edition
uses Git's tracked files, filtered by the same sensitive/generated-file rules.
"""
import argparse
import hashlib
import json
from pathlib import Path, PurePosixPath
import subprocess
import zipfile

ROOT = Path(__file__).resolve().parents[1]
PROFILES = ('local', 'private-server', 'vercel', 'github')
CORE = ['domain.py', 'business.py', 'regional.py', 'operations.py',
        'branding.py', 'server.py']
COMMON = ['README.md', 'SECURITY.md', 'VERIFICATION.md', 'hosting/README.md',
          'hosting/preflight.py', 'hosting/package.py']
STATIC = ['app.css', 'app.js', 'bundle.css', 'experience.css', 'experience.js',
          'fonts.css', 'icon.svg', 'index.html', 'manifest.webmanifest',
          'print.css', 'print.js', 'studio.css', 'studio.js', 'sw.js',
          'sync.js', 'workspace.css', 'workspace.js']
ROOT_SOURCE = set(CORE + COMMON + ['admin.py', 'hosted.py', 'cloud.py', 'Dockerfile',
                  '.dockerignore', '.gitignore', '.vercelignore', '.python-version',
                  'requirements.txt', 'requirements-vercel.txt', 'vercel.json',
                  'Start-Windows.bat', 'Start-Mac.command', 'package.json', 'package-lock.json'])
SPECIFIC = {
    'local': ['admin.py', 'Start-Windows.bat', 'Start-Mac.command'],
    'private-server': ['admin.py', 'hosted.py', 'Dockerfile', '.dockerignore',
                       'requirements.txt', 'requirements-vercel.txt',
                       'deploy/compose.yaml', 'deploy/Caddyfile', 'deploy/configure.py'],
    'vercel': ['hosted.py', 'cloud.py', 'api/index.py', 'api/requirements.txt',
               'requirements-vercel.txt', 'requirements.txt', '.python-version',
               'vercel.json', '.vercelignore', 'deploy/build_vercel.py',
               'deploy/migrate_postgres.py'],
}
ROOT_SOURCE.update(name for names in SPECIFIC.values() for name in names)
BLOCKED_PARTS = {'data', 'backups', 'verification', 'node_modules', '__pycache__',
                 '.git', '.vercel', '.venv', 'venv', 'public', 'dist', 'packages'}
PUBLIC_CONFIG_JSON = {'hosting/vercel/project-settings.json',
                      'hosting/operations/launch-record.example.json'}


def document_source(name):
    path = PurePosixPath(name)
    return path.suffix in ('.py', '.md', '.mjs', '.sh') or path.name == '.env.example' or name in PUBLIC_CONFIG_JSON


def safe_path(name):
    path = PurePosixPath(name)
    if path.is_absolute() or '..' in path.parts:
        return False
    if any(part.lower() in BLOCKED_PARTS or part.lower().startswith('tmp') for part in path.parts):
        return False
    leaf = path.name.lower()
    if leaf.startswith('.env') and leaf != '.env.example':
        return False
    return not ('.sqlite' in leaf or leaf.endswith(('.db', '.pyc', '.zip', '.pem', '.key', '.p12')))


def files_for(profile, root=ROOT):
    if profile not in PROFILES:
        raise ValueError('Choose a supported deployment profile.')
    if profile == 'github':
        # New files must be staged first. Untracked local secrets are never swept in.
        listing = subprocess.run(['git', 'ls-files', '-z', '--', 'business-desk',
                                  '.github/workflows/business-desk*.yml'],
                                 cwd=root.parent, check=True, capture_output=True).stdout
        if 'business-desk/domain.py' not in listing.decode().split('\0'):
            raise ValueError('The GitHub kit requires a root Git checkout with tracked/staged business-desk source.')
        result = []
        for raw in listing.decode().split('\0'):
            if not raw:
                continue
            relative = raw.removeprefix('business-desk/')
            parts = PurePosixPath(relative).parts
            area = parts[0]
            source_area = area in ('docs', 'research', 'hosting', 'deploy', 'api', 'tests')
            text_source = document_source(relative) or relative in ('api/requirements.txt',)
            allowed = (relative in ROOT_SOURCE or (len(parts) == 1 and relative.startswith('test_') and relative.endswith('.py'))
                       or (area == 'static' and relative.removeprefix('static/') in STATIC)
                       or (source_area and text_source)
                       or raw in ('.github/workflows/business-desk.yml', '.github/workflows/business-desk-packages.yml'))
            if safe_path(relative) and allowed:
                result.append((raw, root.parent / raw))
        result.append(('README.md', root.parent / 'README.md'))
        return sorted(result)
    required = CORE + COMMON + SPECIFIC[profile]
    required += ['static/' + name for name in STATIC]
    for directory in ('hosting', 'research', 'docs'):
        required += [p.relative_to(root).as_posix() for p in (root / directory).rglob('*')
                     if p.is_file() and document_source(p.relative_to(root).as_posix())]
    result = []
    for name in sorted(set(required)):
        if not safe_path(name):
            continue
        source = root / name
        if source.is_symlink() or not source.is_file():
            raise ValueError('A required package path is missing or is a symlink: ' + name)
        result.append(('business-desk/' + name, source))
    return result


def build(profile, output, root=ROOT):
    entries = files_for(profile, root)
    contents = []
    for name, source in entries:
        if source.is_symlink() or not source.is_file():
            raise ValueError('Only regular source files may enter an operator kit.')
        contents.append((name, source.read_bytes()))
    manifest = {'profile': profile, 'format': 1, 'includes_runtime_data': False,
                'files': [{'path': name, 'bytes': len(data),
                           'sha256': hashlib.sha256(data).hexdigest()} for name, data in contents]}
    output.mkdir(parents=True, exist_ok=True)
    target = output / ('business-desk-' + profile + '.zip')
    # Refuse clobbering an operator's existing release archive or following links.
    with zipfile.ZipFile(target, 'x', compression=zipfile.ZIP_DEFLATED, compresslevel=9) as archive:
        for name, data in contents + [('PACKAGE-MANIFEST.json',
                                       (json.dumps(manifest, indent=2) + '\n').encode())]:
            info = zipfile.ZipInfo(name, date_time=(2026, 1, 1, 0, 0, 0))
            info.compress_type = zipfile.ZIP_DEFLATED
            info.external_attr = 0o100644 << 16
            archive.writestr(info, data)
    digest = hashlib.sha256(target.read_bytes()).hexdigest()
    checksum = target.with_suffix('.zip.sha256')
    with checksum.open('x') as stream:
        stream.write(digest + '  ' + target.name + '\n')
    return target, len(contents)


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--profile', choices=PROFILES + ('all',), default='all')
    parser.add_argument('--output', type=Path, default=ROOT / 'packages')
    args = parser.parse_args()
    try:
        for profile in PROFILES if args.profile == 'all' else (args.profile,):
            target, count = build(profile, args.output.resolve())
            print(f'Created {target.name}: {count} source files, no runtime data.')
    except (ValueError, FileExistsError, subprocess.CalledProcessError) as error:
        parser.exit(1, f'Package creation stopped: {error}\nUse a new output folder for each release.\n')


if __name__ == '__main__':
    main()

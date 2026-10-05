"""Deployment boundaries: private-file exclusion, reproducibility and safe checks."""
import hashlib
import json
import os
from pathlib import Path
import shutil
import subprocess
import sys
import tempfile
import unittest
import zipfile

from hosting import package, preflight

ROOT = Path(__file__).resolve().parent


class HostingKitTests(unittest.TestCase):
    def test_private_paths_are_excluded(self):
        for name in ('data/client.json', 'BACKUPS/day.db', '.env', 'hosting/vercel/.env.local',
                     '.vercel/project.json', 'static/patient.sqlite3', 'tmp-copy/key.json',
                     'node_modules/file.js', '../outside.py', '/etc/secret', 'private.key'):
            with self.subTest(name=name):
                self.assertFalse(package.safe_path(name))
        self.assertTrue(package.safe_path('hosting/vercel/.env.example'))

    def test_runtime_profiles_contain_the_correct_entry_points(self):
        local = {name for name, source in package.files_for('local')}
        cloud = {name for name, source in package.files_for('vercel')}
        private = {name for name, source in package.files_for('private-server')}
        self.assertIn('business-desk/server.py', local)
        self.assertNotIn('business-desk/api/index.py', local)
        self.assertIn('business-desk/api/index.py', cloud)
        self.assertIn('business-desk/deploy/migrate_postgres.py', cloud)
        self.assertIn('business-desk/.python-version', cloud)
        self.assertIn('business-desk/Dockerfile', private)
        self.assertIn('business-desk/deploy/compose.yaml', private)

    def test_github_source_retains_runtime_and_browser_check_sources(self):
        names = {name for name, source in package.files_for('github')}
        for name in ('deploy/Caddyfile', 'deploy/compose.yaml', 'api/index.py',
                     'tests/browser.mjs', 'tests/run_browser.py', 'package-lock.json'):
            self.assertIn('business-desk/' + name, names)

    def test_archive_hashes_reproduce_and_do_not_include_live_files(self):
        with tempfile.TemporaryDirectory() as folder:
            base = Path(folder)
            clone = base / 'app'
            clone.mkdir()
            for archived, source in package.files_for('local'):
                target = clone / archived.removeprefix('business-desk/')
                target.parent.mkdir(parents=True, exist_ok=True)
                shutil.copyfile(source, target)
            for name in ('data/clients.json', 'static/customer-photo.png', 'static/.env',
                         'hosting/vercel/.env.local', 'research/client-export.json'):
                target = clone / name
                target.parent.mkdir(parents=True, exist_ok=True)
                target.write_text('FICTIONAL-SENSITIVE-SENTINEL')
            first, count = package.build('local', base / 'first', clone)
            second, _ = package.build('local', base / 'second', clone)
            self.assertEqual(first.read_bytes(), second.read_bytes())
            with zipfile.ZipFile(first) as archive:
                manifest = json.loads(archive.read('PACKAGE-MANIFEST.json'))
                self.assertEqual(count, len(manifest['files']))
                for row in manifest['files']:
                    content = archive.read(row['path'])
                    self.assertNotIn(b'FICTIONAL-SENSITIVE-SENTINEL', content)
                    self.assertEqual(row['sha256'], hashlib.sha256(content).hexdigest())
            checksum = first.with_suffix('.zip.sha256').read_text().split()[0]
            self.assertEqual(checksum, hashlib.sha256(first.read_bytes()).hexdigest())

    def test_existing_archive_is_never_overwritten(self):
        with tempfile.TemporaryDirectory() as folder:
            output = Path(folder)
            target = output / 'business-desk-local.zip'
            target.write_bytes(b'previous-reviewed-release')
            with self.assertRaises(FileExistsError):
                package.build('local', output)
            self.assertEqual(target.read_bytes(), b'previous-reviewed-release')

    @unittest.skipUnless(hasattr(os, 'symlink'), 'symlink support required')
    def test_required_source_symlink_cannot_exfiltrate(self):
        with tempfile.TemporaryDirectory() as folder:
            root = Path(folder) / 'app'
            root.mkdir()
            secret = Path(folder) / 'outside'
            secret.write_text('FICTIONAL-SECRET')
            (root / 'domain.py').symlink_to(secret)
            with self.assertRaises(ValueError):
                package.files_for('local', root)

    def test_github_kit_uses_tracked_source_and_filters_even_staged_secrets(self):
        with tempfile.TemporaryDirectory() as folder:
            repo = Path(folder)
            subprocess.run(['git', 'init', '-q', str(repo)], check=True)
            for name in ('README.md', 'business-desk/domain.py', 'business-desk/.env',
                         'business-desk/data/customer.json', 'business-desk/untracked-secret.py',
                         'business-desk/hosting/vercel/.env.example', 'business-desk/research/client-export.json'):
                target = repo / name
                target.parent.mkdir(parents=True, exist_ok=True)
                target.write_text('fictional fixture')
            subprocess.run(['git', 'add', '.', ':!business-desk/untracked-secret.py'], cwd=repo, check=True)
            names = {name for name, source in package.files_for('github', repo / 'business-desk')}
            self.assertIn('business-desk/domain.py', names)
            self.assertIn('business-desk/hosting/vercel/.env.example', names)
            self.assertNotIn('business-desk/.env', names)
            self.assertNotIn('business-desk/data/customer.json', names)
            self.assertNotIn('business-desk/research/client-export.json', names)
            self.assertNotIn('business-desk/untracked-secret.py', names)


class PreflightTests(unittest.TestCase):
    def cloud_env(self):
        return {'DATABASE_URL': 'postgresql://user:fictional@db.example.test/desk?sslmode=require',
                'DESK_PUBLIC_ORIGIN': 'https://desk.example.test', 'DESK_SETUP_KEY': 'fictional-' * 5,
                'DESK_REGISTRATION_ENABLED': 'false', 'DESK_ALLOW_PREVIEW': 'false'}

    def test_missing_configuration_fails_without_secret_values(self):
        problems, notes = preflight.checks('vercel', {})
        self.assertGreaterEqual(len(problems), 3)
        env = self.cloud_env()
        env['DATABASE_URL'] = 'postgresql://user:SECRET-SENTINEL@host:bad/desk?sslmode=require'
        problems, notes = preflight.checks('vercel', env)
        self.assertTrue(problems)
        self.assertNotIn('SECRET-SENTINEL', '\n'.join(problems + notes))

    def test_production_rejects_insecure_database_and_preview_hosts(self):
        env = self.cloud_env()
        env['DATABASE_URL'] = env['DATABASE_URL'].replace('require', 'disable')
        env['DESK_ALLOW_PREVIEW'] = 'true'
        problems, notes = preflight.checks('vercel', env)
        self.assertTrue(any('TLS' in row for row in problems))
        self.assertTrue(any('DESK_ALLOW_PREVIEW' in row for row in problems))
        env['DATABASE_URL'] = self.cloud_env()['DATABASE_URL'] + '&sslmode=disable'
        self.assertTrue(preflight.checks('vercel', env)[0])

    def test_reviewed_configuration_passes_and_templates_do_not(self):
        self.assertEqual([], preflight.checks('vercel', self.cloud_env())[0])
        template = preflight.read_env(ROOT / 'hosting/vercel/.env.example')
        self.assertTrue(preflight.checks('vercel', template)[0])
        self.assertEqual([], preflight.checks('local', {})[0])
        self.assertEqual([], preflight.checks('private-server', {
            'SITE_HOST': 'desk.example.test', 'DESK_SETUP_KEY': 'fictional-' * 5})[0])

    def test_env_file_is_data_not_shell_code(self):
        with tempfile.TemporaryDirectory() as folder:
            path = Path(folder) / '.env'
            path.write_text("DESK_SETUP_KEY='$(touch NEVER_EXECUTE)'\nDESK_ALLOW_PREVIEW=false\n")
            values = preflight.read_env(path)
            self.assertEqual(values['DESK_SETUP_KEY'], '$(touch NEVER_EXECUTE)')
            path.write_text('DATABASE_URL=first\nDATABASE_URL=second\n')
            with self.assertRaises(ValueError):
                preflight.read_env(path)

    def test_cli_invalid_env_error_is_redacted(self):
        with tempfile.TemporaryDirectory() as folder:
            path = Path(folder) / '.env'
            path.write_text('not a key=SECRET-SENTINEL\n')
            result = subprocess.run([sys.executable, str(ROOT / 'hosting/preflight.py'),
                                     '--profile', 'vercel', '--env-file', str(path)], capture_output=True, text=True)
            self.assertEqual(1, result.returncode)
            self.assertNotIn('SECRET-SENTINEL', result.stdout + result.stderr)


if __name__ == '__main__':
    unittest.main()

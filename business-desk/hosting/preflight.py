#!/usr/bin/env python3
"""Read-only configuration checks. No deployment, migration or secret output."""
import argparse
import json
import os
from pathlib import Path
import re
import sys
from urllib.parse import parse_qs, urlsplit

ROOT = Path(__file__).resolve().parents[1]


def read_env(path):
    values = {}
    for line_number, line in enumerate(path.read_text().splitlines(), 1):
        line = line.strip()
        if not line or line.startswith('#'):
            continue
        key, separator, value = line.partition('=')
        if not separator or not re.fullmatch(r'[A-Z][A-Z0-9_]*', key):
            raise ValueError(f'Invalid environment assignment on line {line_number}; use KEY=value.')
        if key in values:
            raise ValueError(f'Duplicate environment key on line {line_number}.')
        if value.startswith(('"', "'")):
            if len(value) < 2 or value[-1] != value[0]:
                raise ValueError(f'Unclosed quoted value on line {line_number}.')
            value = value[1:-1]
        values[key] = value
    return values


def checks(profile, env, environment='production', root=ROOT):
    problems, notes = [], []
    version = (3, 12) if profile == 'vercel' else (3, 10)
    if sys.version_info[:2] < version:
        problems.append(f'Python {version[0]}.{version[1]}+ is required for this profile.')
    required = ['domain.py', 'business.py', 'regional.py', 'operations.py',
                'branding.py', 'analytics.py', 'cloud_auth.py', 'server.py', 'static/index.html', 'static/analytics.js', 'static/cloud-auth.js']
    if profile == 'private-server':
        required += ['Dockerfile', 'deploy/compose.yaml', 'deploy/Caddyfile', 'hosted.py']
    if profile == 'vercel':
        required += ['vercel.json', 'cloud.py', 'api/index.py', 'api/requirements.txt',
                     'deploy/build_vercel.py', 'deploy/migrate_postgres.py', '.python-version']
    for name in required:
        if not (root / name).is_file():
            problems.append('Missing application file: ' + name)
    for source in (root / 'public').rglob('*'):
        if source.is_file() and ('.sqlite' in source.name.lower() or source.name.startswith('.env')):
            problems.append('Private runtime material found in public assets; remove it before packaging.')
            break
    if profile in ('private-server', 'vercel'):
        if len(env.get('DESK_SETUP_KEY', '')) < 32 or 'REPLACE' in env.get('DESK_SETUP_KEY', '').upper():
            problems.append('DESK_SETUP_KEY needs a private generated value of at least 32 characters.')
        origin = env.get('DESK_PUBLIC_ORIGIN', '')
        if profile == 'private-server':
            host = env.get('SITE_HOST', '')
            if not re.fullmatch(r'(?=.{1,253}$)(?:[a-zA-Z0-9](?:[a-zA-Z0-9-]{0,61}[a-zA-Z0-9])?\.)+[a-zA-Z]{2,63}', host):
                problems.append('SITE_HOST must be a DNS hostname without a scheme, port or path.')
            origin = 'https://' + host
        try:
            parsed = urlsplit(origin)
            valid = (parsed.scheme == 'https' and parsed.hostname and not parsed.username
                     and not parsed.password and parsed.path in ('', '/')
                     and not parsed.query and not parsed.fragment and parsed.port in (None, 443))
            if (not valid or parsed.hostname in ('localhost', '127.0.0.1')
                    or 'YOUR_' in origin.upper()
                    or not re.fullmatch(r'[A-Za-z0-9.-]+', parsed.hostname or '')):
                problems.append('Use a canonical HTTPS DESK_PUBLIC_ORIGIN without a path or credentials.')
        except ValueError:
            problems.append('DESK_PUBLIC_ORIGIN is invalid.')
    if profile == 'vercel':
        try:
            database_value = env.get('DATABASE_URL', '')
            url = urlsplit(database_value)
            if url.scheme not in ('postgres', 'postgresql') or not url.hostname or not url.path.strip('/'):
                problems.append('DATABASE_URL must identify the intended durable PostgreSQL database.')
            if 'REPLACE' in database_value.upper() or 'YOUR_' in database_value.upper():
                problems.append('Replace DATABASE_URL placeholders privately with the intended provider configuration.')
            modes = parse_qs(url.query).get('sslmode', [])
            if len(modes) != 1 or modes[0] not in ('require', 'verify-ca', 'verify-full'):
                problems.append('Require TLS in DATABASE_URL (sslmode=require or certificate verification).')
            # Accessing port also checks malformed port syntax without revealing the URL.
            url.port
        except ValueError:
            problems.append('DATABASE_URL syntax is invalid; its value has not been printed.')
        for key in ('DESK_REGISTRATION_ENABLED', 'DESK_ALLOW_PREVIEW','DESK_EMAIL_AUTH'):
            if env.get(key, 'false') not in ('true', 'false'):
                problems.append(key + ' must be exactly true or false.')
        if environment == 'production' and env.get('DESK_ALLOW_PREVIEW') == 'true':
            problems.append('Disable DESK_ALLOW_PREVIEW in production.')
        try:
            if not 1 <= int(env.get('DESK_DB_POOL_SIZE', '1')) <= 16:
                raise ValueError()
        except ValueError:
            problems.append('DESK_DB_POOL_SIZE must be an integer from 1 to 16; measure provider limits.')
        schema=env.get('DESK_DB_SCHEMA','public')
        if not re.fullmatch(r'[a-z][a-z0-9_]{0,62}',schema) or schema in ('auth','storage','realtime','pg_catalog','information_schema') or schema.startswith('pg_'):
            problems.append('DESK_DB_SCHEMA must be a dedicated application schema identifier.')
        if env.get('DESK_EMAIL_AUTH')=='true':
            from cloud_auth import SupabaseEmailAuth
            try:SupabaseEmailAuth(env.get('SUPABASE_URL',''),env.get('SUPABASE_PUBLISHABLE_KEY',''))
            except (ValueError,TypeError):problems.append('Set the intended Supabase HTTPS project URL and publishable/anon key. Secret keys are rejected.')
            if schema=='public':problems.append('Use a private application schema for the Supabase edition.')
            notes.append('Configure and test custom Auth SMTP and numeric-code templates; no email is sent by preflight.')
        if env.get('DATABASE_DIRECT_URL'):
            notes.append('Migration credentials are present in this operator environment; omit them from runtime deployment.')
        notes.append('Schema migration, runtime grants, preview isolation and provider restore still need operator verification.')
        try:
            configuration = json.loads((root / 'vercel.json').read_text())
            if configuration.get('buildCommand') != 'python3 deploy/build_vercel.py' or configuration.get('outputDirectory') != 'public':
                problems.append('Restore the reviewed Vercel build command and public output directory.')
        except (OSError, ValueError):
            problems.append('Cannot read the reviewed Vercel configuration.')
    if profile == 'local':
        notes.append('Localhost is this computer only. Phones require the same hosted HTTPS server.')
    if profile == 'private-server':
        notes.append('Use one process/stack per customer organisation and persistent /data; do not publish port 8080.')
    notes.append('Configuration checks do not establish production readiness, tax approval or successful recovery.')
    return problems, notes


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--profile', choices=('local', 'private-server', 'vercel'), required=True)
    parser.add_argument('--environment', choices=('production', 'preview'), default='production')
    parser.add_argument('--env-file', type=Path)
    args = parser.parse_args()
    env = dict(os.environ)
    try:
        if args.env_file:
            # The explicit file takes precedence; parsing does not execute shell expressions.
            env.update(read_env(args.env_file))
    except (OSError, ValueError):
        parser.exit(1, 'Cannot parse the environment file. Use unique KEY=value assignments and matching quotes. No values were printed.\n')
    problems, notes = checks(args.profile, env, args.environment)
    for item in problems:
        print('NEEDS CONFIGURATION: ' + item)
    for item in notes:
        print('NOTE: ' + item)
    print('Configuration checks failed.' if problems else 'Configuration checks passed.')
    return 1 if problems else 0


if __name__ == '__main__':
    raise SystemExit(main())

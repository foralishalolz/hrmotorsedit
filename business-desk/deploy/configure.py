"""Create a private deployment configuration without a shared default secret."""
import argparse
import os
from pathlib import Path
import re
import secrets

parser = argparse.ArgumentParser()
parser.add_argument('hostname', help='DNS hostname, e.g. desk.yourbusiness.com')
args = parser.parse_args()
if not re.fullmatch(r'(?=.{1,253}$)(?:[a-zA-Z0-9](?:[a-zA-Z0-9-]{0,61}[a-zA-Z0-9])?\.)+[a-zA-Z]{2,63}', args.hostname):
    parser.error('Enter a DNS hostname without https://, a port, or a path.')
target = Path(__file__).resolve().parent / '.env'
fd = os.open(target, os.O_CREAT | os.O_EXCL | os.O_WRONLY, 0o600)
with os.fdopen(fd, 'w') as file:
    file.write('SITE_HOST=' + args.hostname.lower() + '\nDESK_SETUP_KEY=' + secrets.token_urlsafe(48) + '\n')
print('Created deploy/.env with a new private setup key. Read it locally when creating the first owner account. Keep this file outside Git.')

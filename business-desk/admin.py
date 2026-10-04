"""Server-console recovery; requires filesystem access to the private database."""
import argparse
from getpass import getpass
from pathlib import Path
from domain import Desk, password_hash

parser = argparse.ArgumentParser()
parser.add_argument('--data-dir', type=Path, default=Path(__file__).resolve().parent / 'data')
parser.add_argument('command', choices=['backup', 'reset-password'])
parser.add_argument('--username')
args = parser.parse_args()
desk = Desk(args.data_dir)
if args.command == 'backup':
    print(desk.backup())
else:
    if not args.username:
        parser.error('--username is required')
    first = getpass('New password (at least 12 characters): ')
    if len(first) < 12 or first != getpass('Repeat password: '):
        parser.error('Passwords must match and contain at least 12 characters.')
    with desk.transaction() as conn:
        row = conn.execute('SELECT * FROM users WHERE username=?', (args.username.strip().lower(),)).fetchone()
        if not row:
            parser.error('Account not found')
        conn.execute('UPDATE users SET password=?,active=1 WHERE id=?', (password_hash(first), row['id']))
        desk.audit(conn, {'name':'Server administrator'}, '', 'Password recovered from server console', 'users', row['id'])
    print('Password changed. Existing sessions for this account will be rejected on their next request.')

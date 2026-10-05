#!/usr/bin/env python3
"""Explicit operator setup for a NEW private Supabase application schema.

No network actions occur until this command is run with the intended direct
URL. It never edits auth/storage/public or sends email. Back up existing data.
"""
import os
from pathlib import Path
import re
import sys
sys.path.insert(0,str(Path(__file__).resolve().parents[1]))

TABLES=('meta','users','businesses','records','counters','attachments','audit',
        'commands','desk_sessions','desk_rate_limits','desk_identities','desk_email_invites')


def secure_schema(desk,runtime_role=''):
    if desk.schema=='public':raise ValueError('Supabase setup requires a dedicated private schema.')
    if runtime_role and (not re.fullmatch(r'[a-z][a-z0-9_]{0,62}',runtime_role)
                         or runtime_role in ('anon','authenticated','service_role','postgres') or runtime_role.startswith('pg_')):
        raise ValueError('Choose a dedicated server-only runtime role.')
    schema=desk.schema
    with desk.transaction(scope='schema-security') as conn:
        if runtime_role:
            role=conn.execute('SELECT rolsuper,rolbypassrls,rolcanlogin FROM pg_roles WHERE rolname=?',(runtime_role,)).fetchone()
            if not role or role['rolsuper'] or role['rolbypassrls'] or not role['rolcanlogin']:
                raise ValueError('Create a login runtime role without superuser or BYPASSRLS privileges first.')
        targets=['PUBLIC']+[role for role in ('anon','authenticated') if conn.execute('SELECT 1 FROM pg_roles WHERE rolname=?',(role,)).fetchone()]
        for target in targets:
            conn.execute('REVOKE ALL ON SCHEMA '+schema+' FROM '+target)
        if runtime_role:conn.execute('GRANT USAGE ON SCHEMA '+schema+' TO '+runtime_role)
        for table in TABLES:
            name=schema+'.'+table
            conn.execute('ALTER TABLE '+name+' ENABLE ROW LEVEL SECURITY')
            for target in targets:conn.execute('REVOKE ALL ON TABLE '+name+' FROM '+target)
            if runtime_role:
                conn.execute('GRANT SELECT,INSERT,UPDATE,DELETE ON TABLE '+name+' TO '+runtime_role)
                conn.execute('DROP POLICY IF EXISTS business_desk_server ON '+name)
                conn.execute('CREATE POLICY business_desk_server ON '+name+' TO '+runtime_role+' USING (true) WITH CHECK (true)')
        sequence=schema+'.audit_id_seq'
        for target in targets:conn.execute('REVOKE ALL ON SEQUENCE '+sequence+' FROM '+target)
        if runtime_role:conn.execute('GRANT USAGE,SELECT ON SEQUENCE '+sequence+' TO '+runtime_role)
        # Defaults apply only to this migration owner's future objects in this schema.
        for target in targets:
            conn.execute('ALTER DEFAULT PRIVILEGES IN SCHEMA '+schema+' REVOKE ALL ON TABLES FROM '+target)
            conn.execute('ALTER DEFAULT PRIVILEGES IN SCHEMA '+schema+' REVOKE ALL ON SEQUENCES FROM '+target)


def main():
    from cloud import CloudDesk
    url=os.environ.get('DATABASE_DIRECT_URL','')
    schema=os.environ.get('DESK_DB_SCHEMA','business_desk')
    if not url:raise SystemExit('Set the intended DATABASE_DIRECT_URL privately before running setup.')
    if schema=='public':raise SystemExit('Use DESK_DB_SCHEMA=business_desk or another dedicated application schema.')
    desk=None
    try:
        desk=CloudDesk(url,bootstrap=True,schema=schema)
        secure_schema(desk,os.environ.get('DESK_RUNTIME_ROLE',''))
    except Exception as error:
        raise SystemExit('Setup stopped ('+type(error).__name__+'). Review configuration and database grants. No credentials were printed.') from None
    finally:
        if desk:desk.close()
    print('Private Business Desk schema and email identity tables are ready. Verify runtime grants and Auth email delivery before deployment.')


if __name__=='__main__':main()

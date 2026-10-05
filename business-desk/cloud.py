"""Durable PostgreSQL edition. Local edition never imports this optional adapter.
All public domain entrypoints keep the same business/role checks. Cross-worker
writes take an organisation transaction lock; command receipts commit with data.
"""
from contextlib import contextmanager
from datetime import datetime, timedelta, timezone
from pathlib import Path
import base64
import hashlib
import json
import secrets
import re
import tempfile
import threading
import time
from psycopg.rows import dict_row
from psycopg_pool import ConnectionPool
from domain import Desk, Problem, identifier, now, password_hash, password_ok
from urllib.parse import urlsplit, parse_qs


class Row(dict):
    def __getitem__(self, key):
        return list(self.values())[key] if isinstance(key, int) else super().__getitem__(key)


class Cursor:
    def __init__(self, cursor): self.cursor = cursor
    @property
    def rowcount(self): return self.cursor.rowcount
    def fetchone(self):
        row = self.cursor.fetchone()
        return Row(row) if row is not None else None
    def fetchall(self): return [Row(x) for x in self.cursor.fetchall()]
    def __iter__(self): return (Row(x) for x in self.cursor)


class Connection:
    def __init__(self, raw): self.raw = raw
    def execute(self, sql, params=()):
        # These are static domain SQL strings, never supplied by app users.
        ignore = 'INSERT OR IGNORE INTO' in sql
        sql = sql.replace('INSERT OR IGNORE INTO', 'INSERT INTO')
        sql = sql.replace('INTEGER PRIMARY KEY AUTOINCREMENT', 'BIGSERIAL PRIMARY KEY').replace(' BLOB ', ' BYTEA ')
        sql = sql.replace('?', '%s')
        if ignore: sql = sql.rstrip(';') + ' ON CONFLICT DO NOTHING'
        return Cursor(self.raw.execute(sql, params))
    def executescript(self, sql):
        for statement in sql.split(';'):
            if statement.strip(): self.execute(statement)


class SessionStore:
    def __init__(self, desk): self.desk = desk
    def pop(self, token, default=None):
        with self.desk.connect() as conn:
            conn.execute('DELETE FROM desk_sessions WHERE token_hash=?', (self.desk.token_hash(token),))
        return default


class CloudDesk(Desk):
    cloud = True
    def __init__(self, database_url, *, bootstrap=False, pool_size=1, schema='public'):
        if not database_url.startswith(('postgres://', 'postgresql://')):
            raise ValueError('A PostgreSQL DATABASE_URL is required; cloud mode cannot use SQLite.')
        parsed=urlsplit(database_url)
        if parsed.hostname not in ('localhost','127.0.0.1','::1') and parse_qs(parsed.query).get('sslmode') not in (['require'],['verify-ca'],['verify-full']):
            raise ValueError('Remote PostgreSQL connections must require TLS.')
        if not re.fullmatch(r'[a-z][a-z0-9_]{0,62}',schema) or schema in ('auth','storage','realtime','pg_catalog','information_schema') or schema.startswith('pg_'):
            raise ValueError('Use a dedicated application database schema.')
        if not 1 <= pool_size <= 16: raise ValueError('Database pool size must be between 1 and 16.')
        self.schema = schema
        self.local = threading.local()
        self.folder = Path(tempfile.gettempdir()) / 'desk-exports'
        self.folder.mkdir(exist_ok=True)
        self.pool = ConnectionPool(database_url, min_size=0, max_size=pool_size,
            timeout=8, max_idle=60, max_lifetime=300, kwargs={'row_factory':dict_row,
            'prepare_threshold':None, 'connect_timeout':8}, open=True)
        self.sessions = SessionStore(self)
        try:
            if bootstrap:
                with self.transaction(scope='schema') as conn:
                    if schema != 'public': conn.execute('CREATE SCHEMA IF NOT EXISTS '+schema)
                    self.initialize_schema()
                    self.initialize_cloud_schema()
            with self.connect() as conn:
                row=conn.execute("SELECT value FROM meta WHERE key='cloud_schema'").fetchone()
                if not row or row[0]!='1': raise RuntimeError('Run the reviewed PostgreSQL migration before deploying this version.')
                self.email_ready = bool(conn.execute("SELECT value FROM meta WHERE key='email_schema' AND value='1'").fetchone())
        except Exception:
            self.pool.close()
            raise

    @contextmanager
    def connect(self):
        nested=getattr(self.local,'connection',None)
        if nested is not None:
            yield nested
            return
        with self.pool.connection() as raw:
            raw.execute("SET LOCAL statement_timeout='15s'")
            raw.execute('SET LOCAL search_path TO '+self.schema+',pg_catalog')
            yield Connection(raw)

    @contextmanager
    def transaction(self, scope=None):
        nested=getattr(self.local,'connection',None)
        if nested is not None:
            yield nested
            return
        with self.connect() as conn:
            conn.execute("SET LOCAL lock_timeout='5s'")
            conn.execute('SELECT pg_advisory_xact_lock(hashtextextended(?,0))',
                ('desk:'+str(scope or getattr(self.local,'organization_id','registration')),))
            self.local.connection=conn
            try: yield conn
            finally: self.local.connection=None

    def initialize_cloud_schema(self):
        with self.connect() as conn:
            conn.executescript('''
              CREATE TABLE IF NOT EXISTS desk_sessions (
                token_hash TEXT PRIMARY KEY, user_id TEXT NOT NULL REFERENCES users(id),
                csrf TEXT NOT NULL, password_stamp TEXT NOT NULL, expires TIMESTAMPTZ NOT NULL);
              CREATE INDEX IF NOT EXISTS desk_sessions_user ON desk_sessions(user_id);
              CREATE INDEX IF NOT EXISTS desk_sessions_expiry ON desk_sessions(expires);
              CREATE TABLE IF NOT EXISTS desk_rate_limits (
                key_hash TEXT PRIMARY KEY, bucket BIGINT NOT NULL, attempts INTEGER NOT NULL);
              CREATE TABLE IF NOT EXISTS desk_identities (
                provider_id TEXT PRIMARY KEY, user_id TEXT UNIQUE NOT NULL REFERENCES users(id),
                email TEXT UNIQUE NOT NULL);
              CREATE TABLE IF NOT EXISTS desk_email_invites (
                email TEXT PRIMARY KEY, user_id TEXT UNIQUE NOT NULL REFERENCES users(id),
                expires TIMESTAMPTZ NOT NULL);
            ''')
            conn.execute("INSERT OR IGNORE INTO meta VALUES ('cloud_schema','1')")
            conn.execute("INSERT OR IGNORE INTO meta VALUES ('email_schema','1')")

    def column_exists(self,conn,table,column):
        return bool(conn.execute('SELECT 1 FROM information_schema.columns WHERE table_schema=? AND table_name=? AND column_name=?',(self.schema,table,column)).fetchone())

    def bind_user(self,user): self.local.organization_id=user.get('organization_id','local')
    def business_allowed(self,user,bid):
        self.bind_user(user)
        return super().business_allowed(user,bid)
    def save_business(self,user,payload):
        self.bind_user(user)
        return super().save_business(user,payload)

    def add_user(self,user,data):
        from psycopg.errors import UniqueViolation
        self.bind_user(user)
        try:
            if data.get('auth_email'):
                from cloud_auth import normal_email
                if not self.email_ready: raise Problem('Apply the email identity migration first.',503)
                email=normal_email(data['auth_email']); username='email-'+identifier()
                with self.transaction() as conn:
                    if conn.execute('SELECT 1 FROM desk_identities WHERE email=? UNION ALL SELECT 1 FROM desk_email_invites WHERE email=?',(email,email)).fetchone():
                        raise Problem('This email already has an account or invitation. Use its existing organisation or ask the administrator.',409)
                    result=super().add_user(user,{**data,'username':username,'password':secrets.token_urlsafe(48)})
                    uid=conn.execute('SELECT id FROM users WHERE username=?',(username,)).fetchone()[0]
                    conn.execute('INSERT INTO desk_email_invites VALUES (?,?,?)',(email,uid,datetime.now(timezone.utc)+timedelta(days=7)))
                    return {**result,'email':email,'invite_days':7}
            return super().add_user(user,data)
        except UniqueViolation: raise Problem('That username is unavailable.',409)

    def email_eligible(self,email):
        with self.connect() as conn:
            return bool(conn.execute('''SELECT 1 FROM users u JOIN desk_identities i ON u.id=i.user_id WHERE i.email=? AND u.active=1
                UNION ALL SELECT 1 FROM users u JOIN desk_email_invites i ON u.id=i.user_id WHERE i.email=? AND u.active=1 AND i.expires>now()''',(email,email)).fetchone())

    def email_identity(self,identity,name='',registration=False):
        """A verified provider identity can only accept a saved invite or create its own org."""
        from cloud_auth import normal_email
        from uuid import UUID
        if not self.email_ready: raise Problem('Apply the email identity migration first.',503)
        pid=str(UUID(identity['id']));email=normal_email(identity['email'])
        with self.transaction(scope='email-registration') as conn:
            linked=conn.execute('SELECT * FROM desk_identities WHERE provider_id=?',(pid,)).fetchone()
            if linked:
                if linked['email']!=email: raise Problem('Ask the administrator to review the changed email address.',403)
                user=conn.execute('SELECT * FROM users WHERE id=? AND active=1',(linked['user_id'],)).fetchone()
                if not user: raise Problem('This business account is disabled. Contact its owner.',403)
            else:
                if conn.execute('SELECT 1 FROM desk_identities WHERE email=?',(email,)).fetchone():
                    raise Problem('This email is linked to another identity. Ask the administrator to review it.',409)
                invite=conn.execute('SELECT * FROM desk_email_invites WHERE email=?',(email,)).fetchone()
                if invite:
                    if invite['expires'] <= datetime.now(timezone.utc): raise Problem('This invitation has expired. Ask the owner for a new one.',403)
                    user=conn.execute('SELECT * FROM users WHERE id=? AND active=1',(invite['user_id'],)).fetchone()
                    if not user: raise Problem('This invitation is disabled. Contact the owner.',403)
                    conn.execute('DELETE FROM desk_email_invites WHERE email=?',(email,))
                else:
                    if not registration: raise Problem('Ask the owner for an invitation or register a new business if registration is open.',403)
                    name=str(name).strip()
                    if not name or len(name)>200: raise Problem('Enter your name to create your business account.')
                    uid,organization=identifier(),identifier()
                    conn.execute('INSERT INTO users(id,username,name,password,role,business_ids,employee_id,active,organization_id) VALUES (?,?,?,?,?,?,?,1,?)',
                        (uid,'email-'+identifier(),name,password_hash(secrets.token_urlsafe(48)),'owner','[]','',organization))
                    user=conn.execute('SELECT * FROM users WHERE id=?',(uid,)).fetchone()
                conn.execute('INSERT INTO desk_identities VALUES (?,?,?)',(pid,user['id'],email))
        self.bind_user(user)
        return self.make_session(dict(user),ttl=min(3600,int(identity.get('ttl',3600))))

    def email_account(self,user_id):
        if not self.email_ready:return False
        with self.connect() as conn:
            return bool(conn.execute('SELECT 1 FROM desk_identities WHERE user_id=? UNION ALL SELECT 1 FROM desk_email_invites WHERE user_id=?',(user_id,user_id)).fetchone())

    def user_view(self,user):
        view=super().user_view(user)
        if self.email_ready:
            with self.connect() as conn: linked=conn.execute('SELECT email FROM desk_identities WHERE user_id=?',(user['id'],)).fetchone()
            if linked:view.update(auth_method='email',auth_email=linked['email'])
        return view

    def users(self,user):
        if user['role']!='owner':raise Problem('Only the owner can manage accounts.',403)
        with self.connect() as conn:
            accounts=conn.execute('SELECT * FROM users WHERE organization_id=?',(user.get('organization_id','local'),)).fetchall()
        rows=[super(CloudDesk,self).user_view(dict(x))|{'business_ids':json.loads(x['business_ids']),'active':bool(x['active'])} for x in accounts]
        if self.email_ready:
            with self.connect() as conn:
                addresses={r['user_id']:dict(r) for r in conn.execute('''SELECT i.user_id,i.email,false AS pending FROM desk_identities i JOIN users u ON u.id=i.user_id WHERE u.organization_id=?
                    UNION ALL SELECT i.user_id,i.email,true AS pending FROM desk_email_invites i JOIN users u ON u.id=i.user_id WHERE u.organization_id=?''',(user.get('organization_id','local'),)*2)}
            for row in rows:
                if row['id'] in addresses:row.update(auth_method='email',auth_email=addresses[row['id']]['email'],invite_pending=addresses[row['id']]['pending'])
        return rows

    def setup(self,data):
        username=str(data.get('username','')).strip().lower();name=str(data.get('name','')).strip();password=str(data.get('password',''))
        if not username or not name or len(username)>100 or len(name)>200 or not 12<=len(password)<=256:
            raise Problem('Enter your name, unique username and a password of 12 to 256 characters.')
        # The HTTP boundary additionally requires the private pilot invite key.
        with self.transaction(scope='registration') as conn:
            if conn.execute('SELECT 1 FROM users WHERE username=?',(username,)).fetchone(): raise Problem('That username is unavailable.',409)
            uid,organization=identifier(),identifier()
            conn.execute('INSERT INTO users(id,username,name,password,role,business_ids,employee_id,active,organization_id) VALUES (?,?,?,?,?,?,?,1,?)',
                (uid,username,name,password_hash(password),'owner','[]','',organization))
            user=dict(conn.execute('SELECT * FROM users WHERE id=?',(uid,)).fetchone())
        self.bind_user(user)
        return self.make_session(user)

    @staticmethod
    def token_hash(token): return hashlib.sha256(str(token).encode()).hexdigest()
    def make_session(self,user,ttl=43200):
        token=secrets.token_urlsafe(32);csrf=secrets.token_urlsafe(24)
        with self.connect() as conn:
            conn.execute('DELETE FROM desk_sessions WHERE expires<now()')
            conn.execute('INSERT INTO desk_sessions VALUES (?,?,?,?,?)',
                (self.token_hash(token),user['id'],csrf,hashlib.sha256(user['password'].encode()).hexdigest(),datetime.now(timezone.utc)+timedelta(seconds=max(1,min(43200,ttl)))))
        return token,{'user':self.user_view(user),'csrf':csrf}

    def session(self,token):
        with self.connect() as conn:
            session=conn.execute('SELECT * FROM desk_sessions WHERE token_hash=? AND expires>now()',(self.token_hash(token),)).fetchone()
            if not session: raise Problem('Please sign in.',401)
            user=conn.execute('SELECT * FROM users WHERE id=? AND active=1',(session['user_id'],)).fetchone()
        if not user or session['password_stamp']!=hashlib.sha256(user['password'].encode()).hexdigest(): raise Problem('Please sign in.',401)
        self.bind_user(user)
        return dict(user),session['csrf']

    def invalidate_sessions(self,user_id,keep_token=''):
        with self.connect() as conn:
            conn.execute('DELETE FROM desk_sessions WHERE user_id=? AND token_hash<>?',(user_id,self.token_hash(keep_token)))

    def auth_limit(self,key,limit=20,seconds=300):
        key_hash=self.token_hash(key);bucket=int(time.time())//seconds
        with self.connect() as conn:
            result=conn.execute('''INSERT INTO desk_rate_limits VALUES (?,?,1)
              ON CONFLICT(key_hash) DO UPDATE SET bucket=excluded.bucket,
              attempts=CASE WHEN desk_rate_limits.bucket=excluded.bucket THEN desk_rate_limits.attempts+1 ELSE 1 END RETURNING attempts''',(key_hash,bucket)).fetchone()
            conn.execute('DELETE FROM desk_rate_limits WHERE bucket<?',(bucket-2,))
        if result[0]>limit: raise Problem('Too many attempts. Try again in five minutes.',429)

    def login(self,data):
        username=str(data.get('username','')).strip().lower();password=str(data.get('password',''))
        if len(username)>100 or len(password)>256: raise Problem('Username or password is incorrect.',401)
        self.auth_limit('username:'+username,10)
        with self.connect() as conn: row=conn.execute('SELECT * FROM users WHERE username=? AND active=1',(username,)).fetchone()
        if row and self.email_account(row['id']):raise Problem('Use verified email sign-in for this account.',401)
        if not row or not password_ok(password,row['password']): raise Problem('Username or password is incorrect.',401)
        self.bind_user(row)
        return self.make_session(dict(row))

    def backup(self,automatic=False,user=None):
        if automatic: return None  # Managed provider backups/PITR are required independently.
        if not user or user['role']!='owner': raise Problem('Only the owner can export their organisation.',403)
        businesses=self.businesses(user);ids=[x['id'] for x in businesses]
        exported={'format':'business-desk-organisation-export-v1','version':'2.4.0-rc.1','exported_at':now(),'businesses':businesses,'data':{}}
        # A repeatable snapshot avoids mixing receipts and invoices from different instants.
        with self.connect() as conn:
            conn.execute('SET TRANSACTION ISOLATION LEVEL REPEATABLE READ')
            for table in ('records','attachments','audit','counters'):
                exported['data'][table]=[]
                for bid in ids:
                    for row in conn.execute('SELECT * FROM '+table+' WHERE business_id=?',(bid,)):
                        item=dict(row)
                        if table=='attachments': item['content']=base64.b64encode(item['content']).decode()
                        exported['data'][table].append(item)
        file=self.folder/(identifier()+'.json');file.write_text(json.dumps(exported,ensure_ascii=False),encoding='utf-8')
        return file

    def restore(self,user,content):
        raise Problem('Hosted recovery uses the database provider’s reviewed restore process. A local SQLite backup cannot replace a hosted organisation.',409)
    def close(self): self.pool.close()

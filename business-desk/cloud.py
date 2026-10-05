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
import tempfile
import threading
import time
from psycopg.rows import dict_row
from psycopg_pool import ConnectionPool
from domain import Desk, Problem, identifier, now, password_hash, password_ok


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
    def __init__(self, database_url, *, bootstrap=False, pool_size=4):
        if not database_url.startswith(('postgres://', 'postgresql://')):
            raise ValueError('A PostgreSQL DATABASE_URL is required; cloud mode cannot use SQLite.')
        self.local = threading.local()
        self.folder = Path(tempfile.gettempdir()) / 'desk-exports'
        self.folder.mkdir(exist_ok=True)
        self.pool = ConnectionPool(database_url, min_size=0, max_size=pool_size,
            timeout=8, max_idle=60, max_lifetime=300, kwargs={'row_factory':dict_row,
            'prepare_threshold':None, 'connect_timeout':8}, open=True)
        self.sessions = SessionStore(self)
        if bootstrap:
            with self.transaction(scope='schema'):
                self.initialize_schema()
                self.initialize_cloud_schema()
        with self.connect() as conn:
            row=conn.execute("SELECT value FROM meta WHERE key='cloud_schema'").fetchone()
            if not row or row[0]!='1': raise RuntimeError('Run the reviewed PostgreSQL migration before deploying this version.')

    @contextmanager
    def connect(self):
        nested=getattr(self.local,'connection',None)
        if nested is not None:
            yield nested
            return
        with self.pool.connection() as raw:
            raw.execute("SET LOCAL statement_timeout='15s'")
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
            ''')
            conn.execute("INSERT OR IGNORE INTO meta VALUES ('cloud_schema','1')")

    def column_exists(self,conn,table,column):
        return bool(conn.execute('SELECT 1 FROM information_schema.columns WHERE table_schema=current_schema() AND table_name=? AND column_name=?',(table,column)).fetchone())

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
        try: return super().add_user(user,data)
        except UniqueViolation: raise Problem('That username is unavailable.',409)

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
    def make_session(self,user):
        token=secrets.token_urlsafe(32);csrf=secrets.token_urlsafe(24)
        with self.connect() as conn:
            conn.execute('DELETE FROM desk_sessions WHERE expires<now()')
            conn.execute('INSERT INTO desk_sessions VALUES (?,?,?,?,?)',
                (self.token_hash(token),user['id'],csrf,hashlib.sha256(user['password'].encode()).hexdigest(),datetime.now(timezone.utc)+timedelta(hours=12)))
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
        if not row or not password_ok(password,row['password']): raise Problem('Username or password is incorrect.',401)
        self.bind_user(row)
        return self.make_session(dict(row))

    def backup(self,automatic=False,user=None):
        if automatic: return None  # Managed provider backups/PITR are required independently.
        if not user or user['role']!='owner': raise Problem('Only the owner can export their organisation.',403)
        businesses=self.businesses(user);ids=[x['id'] for x in businesses]
        exported={'format':'business-desk-organisation-export-v1','version':'2.2.0-rc.1','exported_at':now(),'businesses':businesses,'data':{}}
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

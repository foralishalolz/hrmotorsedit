"""Local Business Desk. Standard-library SQLite storage and business rules."""
from __future__ import annotations

import base64
import calendar
import hashlib
import hmac
import json
import secrets
import sqlite3
import threading
import uuid
from contextlib import closing, contextmanager
from datetime import date, datetime, timedelta, timezone
from decimal import Decimal, InvalidOperation, ROUND_HALF_UP
from pathlib import Path
from business import BusinessFeatures, PROFILES
from regional import RegionalFeatures, INDIA_STATES, UTGST_STATES, business_today, financial_year
from operations import OperationsFeatures, validate_identity

NEPAL = timezone(timedelta(hours=5, minutes=45))
KINDS = {
    'customers', 'assets', 'services', 'quotes', 'jobs', 'claims', 'external_quotes',
    'invoices', 'payments', 'credits', 'expenses', 'suppliers', 'stock', 'movements',
    'purchases', 'employees', 'attendance', 'time_entries', 'commissions', 'payroll',
    'followups', 'appointments', 'contracts', 'allocations',
    'leads', 'vehicles', 'supplier_bills', 'supplier_payments', 'opening_balances', 'cash_closures',
}
ROLE_READ = {
    'owner': KINDS,
    'manager': KINDS - {'payroll', 'commissions'},
    'frontdesk': {'customers', 'assets', 'services', 'quotes', 'jobs', 'claims',
                  'external_quotes', 'invoices', 'payments', 'allocations', 'appointments', 'followups', 'contracts', 'leads', 'vehicles', 'employees', 'opening_balances'},
    'technician': {'jobs', 'time_entries', 'attendance', 'employees'},
    'cashier': {'customers', 'invoices', 'payments', 'allocations', 'credits', 'expenses', 'followups', 'stock', 'supplier_bills', 'supplier_payments', 'suppliers', 'opening_balances','cash_closures'},
    'stock_clerk': {'stock','movements','suppliers','purchases','supplier_bills','services'},
}
ROLE_WRITE = {
    'owner': KINDS,
    'manager': ROLE_READ['manager'] - {'credits','opening_balances','cash_closures'},
    'frontdesk': ROLE_READ['frontdesk'] - {'invoices', 'payments', 'allocations', 'vehicles', 'employees', 'opening_balances'},
    'technician': {'jobs', 'time_entries', 'attendance'},
    'cashier': {'invoices', 'payments', 'allocations', 'expenses', 'followups', 'supplier_payments','cash_closures'},
    'stock_clerk': {'stock','movements','suppliers','purchases','supplier_bills'},
}
STAGES = ['Intake', 'Awaiting approval', 'Awaiting parts', 'Body repair', 'Preparation',
          'Painting', 'Curing', 'Reassembly', 'Quality check', 'Ready', 'Delivered']


class Problem(Exception):
    def __init__(self, message, status=400):
        super().__init__(message)
        self.status = status


class ClosingConnection(sqlite3.Connection):
    def __exit__(self, *args):
        try: return super().__exit__(*args)
        finally: self.close()


def now():
    return datetime.now(timezone.utc).isoformat(timespec='seconds')


def today():
    return datetime.now(NEPAL).date().isoformat()


def identifier():
    return uuid.uuid4().hex


def decimal(value, label='Number', minimum=None, maximum=None):
    try:
        result = Decimal(str(value if value not in ('', None) else 0))
        if not result.is_finite():
            raise InvalidOperation
    except (InvalidOperation, ValueError, TypeError):
        raise Problem(f'{label} must be a valid number.')
    if abs(result) > Decimal('1000000000000'):
        raise Problem(f'{label} is too large.')
    if minimum is not None and result < Decimal(str(minimum)):
        raise Problem(f'{label} must be at least {minimum}.')
    if maximum is not None and result > Decimal(str(maximum)):
        raise Problem(f'{label} must be at most {maximum}.')
    return result


def money(value):
    return decimal(value).quantize(Decimal('.01'), rounding=ROUND_HALF_UP)


def number(value):
    return float(value)


def checked_date(value, label='Date', optional=True):
    if not value and optional:
        return ''
    try:
        return date.fromisoformat(str(value)).isoformat()
    except (ValueError, TypeError):
        raise Problem(f'{label} must be an AD date in YYYY-MM-DD format.')


def calculate(data):
    """One calculation for editing, approvals, documents, reporting and export."""
    mode = data.get('vat_mode', 'added')
    if mode not in ('added', 'included', 'none'):
        raise Problem('Choose VAT added, VAT included or no VAT.')
    tax_rate = decimal(data.get('vat_rate', 13), 'Tax rate', 0, 100)
    indian = data.get('country') == 'IN'
    components = {}
    global_discount = decimal(data.get('discount_percent', 0), 'Overall discount', 0, 100)
    lines = []
    net = tax = total = cost = discount = Decimal(0)
    items = data.get('items', [])
    if not isinstance(items, list) or len(items) > 250:
        raise Problem('A document can contain at most 250 lines.')
    for item in items:
        description = str(item.get('description', '')).strip()
        rate = decimal(item.get('rate', 0), 'Rate', 0)
        if not description and not rate:
            continue
        if not description:
            raise Problem('Every priced line needs a description.')
        qty = decimal(item.get('qty', 1), 'Quantity', Decimal('.0001'))
        unit_cost = decimal(item.get('unit_cost', 0), 'Unit cost', 0)
        pct = decimal(item.get('discount', 0), 'Line discount', 0, 100)
        raw = money(qty * rate)
        amount = money(raw * (1 - pct / 100) * (1 - global_discount / 100))
        configured_percent=decimal(item.get('tax_rate', tax_rate), 'Line tax rate', 0, 100)
        percent = configured_percent if mode != 'none' else Decimal(0)
        configured_cess = decimal(item.get('cess_rate', 0), 'Cess rate', 0, 100) if indian else Decimal(0)
        cess_rate = configured_cess if mode != 'none' else Decimal(0)
        combined_percent = percent + cess_rate
        if mode == 'included':
            line_net = money(amount / (1 + combined_percent / 100))
            line_tax = amount - line_net
            line_total = amount
        else:
            line_net = amount
            line_tax = money(line_net * combined_percent / 100)
            line_total = line_net + line_tax
        split = {}
        if indian and mode != 'none':
            seller, supply = data.get('seller_state'), data.get('place_of_supply')
            if seller not in INDIA_STATES or supply not in INDIA_STATES:
                raise Problem('Choose the seller state and domestic place of supply to calculate GST.')
            cess = money(line_tax * cess_rate / combined_percent) if combined_percent else money(0)
            gst = line_tax - cess
            if seller == supply:
                central = money(gst / 2)
                split = {'CGST': number(central), 'UTGST' if seller in UTGST_STATES else 'SGST': number(gst - central)}
            else: split = {'IGST': number(gst)}
            if cess_rate: split['Cess'] = number(cess)
            for key, value in split.items(): components[key] = number(money(components.get(key, 0)) + money(value))
        line_cost = money(qty * unit_cost)
        lines.append({
            **item, 'description': description, 'qty': number(qty), 'rate': number(rate),
            'unit_cost': number(unit_cost), 'discount': number(pct), 'tax_rate': number(percent),
            'configured_tax_rate': number(configured_percent),
            'net': number(line_net), 'tax': number(line_tax), 'total': number(line_total),
            'cost': number(line_cost), 'discount_amount': number(raw - amount),
            **({'tax_components': split, 'cess_rate': number(cess_rate), 'configured_cess_rate': number(configured_cess)} if indian else {}),
        })
        net += line_net
        tax += line_tax
        total += line_total
        cost += line_cost
        discount += raw - amount
    return {'lines': lines, 'net': number(net), 'tax': number(tax), 'total': number(total),
            'estimated_cost': number(cost), 'estimated_contribution': number(net - cost),
            'discount': number(discount), 'words': words(total), 'tax_components': components}


def words(value):
    small = ['Zero', 'One', 'Two', 'Three', 'Four', 'Five', 'Six', 'Seven', 'Eight', 'Nine',
             'Ten', 'Eleven', 'Twelve', 'Thirteen', 'Fourteen', 'Fifteen', 'Sixteen',
             'Seventeen', 'Eighteen', 'Nineteen']
    tens = ['', '', 'Twenty', 'Thirty', 'Forty', 'Fifty', 'Sixty', 'Seventy', 'Eighty', 'Ninety']
    def spell(n):
        if n < 20:
            return small[n]
        if n < 100:
            return tens[n // 10] + (' ' + spell(n % 10) if n % 10 else '')
        for unit, name in [(10000000, 'Crore'), (100000, 'Lakh'), (1000, 'Thousand'), (100, 'Hundred')]:
            if n >= unit:
                return spell(n // unit) + ' ' + name + (' ' + spell(n % unit) if n % unit else '')
    amount = money(value)
    whole = int(amount)
    paisa = int((amount - whole) * 100)
    return spell(whole) + ' Rupees' + (' and ' + spell(paisa) + ' Paisa' if paisa else '') + ' Only'


def password_hash(password, salt=None):
    salt = salt or secrets.token_hex(16)
    digest = hashlib.pbkdf2_hmac('sha256', password.encode(), bytes.fromhex(salt), 600000).hex()
    return 'pbkdf2_sha256$600000$' + salt + '$' + digest


def password_ok(password, stored):
    try:
        if len(password) > 256: return False
        if stored.startswith('pbkdf2_sha256$'):
            _, iterations, salt, digest = stored.split('$')
            candidate = hashlib.pbkdf2_hmac('sha256', password.encode(), bytes.fromhex(salt), int(iterations)).hex()
            return hmac.compare_digest(candidate, digest)
        # Read existing v1 passwords; a password change upgrades the format.
        salt, digest = stored.split(':')
        candidate = hashlib.pbkdf2_hmac('sha256', password.encode(), bytes.fromhex(salt), 260000).hex()
        return hmac.compare_digest(candidate, digest)
    except Exception:
        return False


class Desk(OperationsFeatures, RegionalFeatures, BusinessFeatures):
    def __init__(self, folder):
        self.folder = Path(folder)
        self.folder.mkdir(parents=True, exist_ok=True)
        self.path = self.folder / 'business-desk.sqlite3'
        self.lock = threading.RLock()
        self.local = threading.local()
        self.sessions = {}
        self.login_attempts = {}
        self.initialize_schema()
        if self.has_users():
            self.backup(automatic=True)

    def initialize_schema(self):
        with self.connect() as conn:
            conn.executescript('''
                CREATE TABLE IF NOT EXISTS meta (key TEXT PRIMARY KEY, value TEXT NOT NULL);
                CREATE TABLE IF NOT EXISTS users (
                    id TEXT PRIMARY KEY, username TEXT UNIQUE NOT NULL, name TEXT NOT NULL,
                    password TEXT NOT NULL, role TEXT NOT NULL, business_ids TEXT NOT NULL,
                    employee_id TEXT NOT NULL DEFAULT '', active INTEGER NOT NULL DEFAULT 1);
                CREATE TABLE IF NOT EXISTS businesses (
                    id TEXT PRIMARY KEY, data TEXT NOT NULL, version INTEGER NOT NULL DEFAULT 1);
                CREATE TABLE IF NOT EXISTS records (
                    id TEXT PRIMARY KEY, business_id TEXT NOT NULL REFERENCES businesses(id),
                    kind TEXT NOT NULL, data TEXT NOT NULL, version INTEGER NOT NULL DEFAULT 1,
                    created_at TEXT NOT NULL, updated_at TEXT NOT NULL, archived INTEGER NOT NULL DEFAULT 0);
                CREATE INDEX IF NOT EXISTS records_business_kind ON records(business_id,kind,archived);
                CREATE TABLE IF NOT EXISTS counters (
                    business_id TEXT NOT NULL, kind TEXT NOT NULL, year TEXT NOT NULL,
                    value INTEGER NOT NULL, PRIMARY KEY(business_id,kind,year));
                CREATE TABLE IF NOT EXISTS attachments (
                    id TEXT PRIMARY KEY, business_id TEXT NOT NULL, record_id TEXT NOT NULL,
                    filename TEXT NOT NULL, mime TEXT NOT NULL, content BLOB NOT NULL,
                    hash TEXT NOT NULL, created_at TEXT NOT NULL);
                CREATE TABLE IF NOT EXISTS audit (
                    id INTEGER PRIMARY KEY AUTOINCREMENT, business_id TEXT NOT NULL,
                    user_name TEXT NOT NULL, action TEXT NOT NULL, kind TEXT NOT NULL,
                    record_id TEXT NOT NULL, detail TEXT NOT NULL, created_at TEXT NOT NULL);
            ''')
            conn.execute("INSERT OR IGNORE INTO meta VALUES ('schema','1')")
            self.migrate(conn)

    def connect(self):
        conn = sqlite3.connect(self.path, timeout=15, factory=ClosingConnection)
        conn.row_factory = sqlite3.Row
        conn.execute('PRAGMA foreign_keys=ON')
        conn.execute('PRAGMA journal_mode=WAL')
        return conn

    @contextmanager
    def transaction(self):
        # One command may call several domain methods. All writes and its retry
        # receipt commit atomically, or roll back together, on one connection.
        nested = getattr(self.local, 'connection', None)
        if nested is not None:
            yield nested
            return
        with self.lock, self.connect() as conn:
            conn.execute('BEGIN IMMEDIATE')
            self.local.connection = conn
            try:
                yield conn
            finally:
                self.local.connection = None

    def migrate(self, conn):
        version = conn.execute("SELECT value FROM meta WHERE key='schema'").fetchone()[0]
        if version not in ('1', '2', '3'):
            raise Problem('This database needs a newer version of Business Desk.')
        conn.execute('''CREATE TABLE IF NOT EXISTS commands (
            user_id TEXT NOT NULL, operation_id TEXT NOT NULL, business_id TEXT NOT NULL,
            fingerprint TEXT NOT NULL, response TEXT NOT NULL, created_at TEXT NOT NULL,
            PRIMARY KEY(user_id,operation_id))''')
        conn.execute("INSERT OR IGNORE INTO meta VALUES ('data_epoch',?)", (identifier(),))
        for table in ('users','businesses'):
            if not self.column_exists(conn,table,'organization_id'):
                conn.execute('ALTER TABLE '+table+" ADD COLUMN organization_id TEXT NOT NULL DEFAULT 'local'")
        conn.execute('CREATE INDEX IF NOT EXISTS businesses_org ON businesses(organization_id)')
        conn.execute('CREATE INDEX IF NOT EXISTS users_org ON users(organization_id)')
        conn.execute("UPDATE meta SET value='3' WHERE key='schema'")

    def column_exists(self,conn,table,column):
        return any(x['name']==column for x in conn.execute('PRAGMA table_info('+table+')'))

    def command(self, user, envelope):
        operation_id = str(envelope.get('operation_id', ''))
        if not 16 <= len(operation_id) <= 100 or not all(c.isalnum() or c in '-_' for c in operation_id):
            raise Problem('A unique operation ID is required.')
        path, data = envelope.get('endpoint'), envelope.get('payload')
        if not isinstance(data, dict):
            raise Problem('The operation payload must be an object.')
        bid = data.get('business_id')
        self.business_allowed(user, bid)
        handlers = {
            'record': lambda: self.save(user, bid, data.get('kind'), data),
            'action': lambda: self.action(user, bid, data.get('kind'), data.get('id'), data),
            'archive': lambda: self.archive(user, bid, data.get('kind'), data.get('id'), data.get('version')) or {'ok': True},
            'time': lambda: self.time_action(user, bid, data),
            'payroll': lambda: self.prepare_payroll(user, bid, data),
            'stock_count': lambda: self.stock_count(user,bid,data),
            'import_batch': lambda: self.import_batch(user,bid,data),
        }
        if path not in handlers:
            raise Problem('This operation cannot be synchronised.')
        self.permitted(user, data.get('kind') if path in ('record','action','archive','import_batch') else 'time_entries' if path == 'time' else 'movements' if path=='stock_count' else 'payroll', True)
        fingerprint = hashlib.sha256(json.dumps({'endpoint': path, 'payload': data}, sort_keys=True, ensure_ascii=False).encode()).hexdigest()
        with self.transaction() as conn:
            self.business(conn, bid)
            epoch = conn.execute("SELECT value FROM meta WHERE key='data_epoch'").fetchone()[0]
            if envelope.get('data_epoch') != epoch:
                raise Problem('The server database was restored or replaced. Review this saved operation against the current records before resubmitting.', 409)
            old = conn.execute('SELECT * FROM commands WHERE user_id=? AND operation_id=?', (user['id'], operation_id)).fetchone()
            if old:
                if old['fingerprint'] != fingerprint:
                    raise Problem('This operation ID was already used for different data.', 409)
                return json.loads(old['response'])
            result = handlers[path]()
            conn.execute('INSERT INTO commands VALUES (?,?,?,?,?,?)',
                         (user['id'], operation_id, bid, fingerprint, json.dumps(result), now()))
            return result

    def has_users(self):
        with self.connect() as conn:
            return bool(conn.execute('SELECT 1 FROM users LIMIT 1').fetchone())

    def user_view(self, user):
        return {k: user[k] for k in ('id', 'username', 'name', 'role', 'employee_id')} | {'organization_id':user.get('organization_id','local')}

    def setup(self, data):
        with self.transaction() as conn:
            if conn.execute('SELECT 1 FROM users LIMIT 1').fetchone():
                raise Problem('An owner account already exists.', 409)
            username = str(data.get('username', '')).strip().lower()
            name = str(data.get('name', '')).strip()
            password = str(data.get('password', ''))
            if not username or not name or not 12 <= len(password) <= 256 or len(username) > 100 or len(name) > 200:
                raise Problem('Enter your name, username and a password of 12 to 256 characters.')
            uid = identifier()
            conn.execute('INSERT INTO users(id,username,name,password,role,business_ids,employee_id,active) VALUES (?,?,?,?,?,?,?,1)',
                         (uid, username, name, password_hash(password), 'owner', '[]', ''))
            user = dict(conn.execute('SELECT * FROM users WHERE id=?', (uid,)).fetchone())
        return self.make_session(user)

    def make_session(self, user):
        token = secrets.token_urlsafe(32)
        csrf = secrets.token_urlsafe(24)
        self.sessions = {k: v for k, v in self.sessions.items() if v['expires'] > datetime.now(timezone.utc)}
        if len(self.sessions) > 10000: raise Problem('Too many active sessions. Try again later.', 429)
        self.sessions[token] = {'user_id': user['id'], 'csrf': csrf, 'password_stamp': hashlib.sha256(user['password'].encode()).hexdigest(), 'expires': datetime.now(timezone.utc) + timedelta(hours=12)}
        return token, {'user': self.user_view(user), 'csrf': csrf}

    def invalidate_sessions(self, user_id, keep_token=''):
        for token, session in list(self.sessions.items()):
            if session['user_id']==user_id and token!=keep_token: self.sessions.pop(token,None)

    def login(self, data):
        username = str(data.get('username', '')).strip().lower()
        if len(username) > 100 or len(str(data.get('password', ''))) > 256:
            raise Problem('Username or password is incorrect.', 401)
        attempts = self.login_attempts.get(username, [])
        cutoff = datetime.now(timezone.utc) - timedelta(minutes=5)
        attempts = [x for x in attempts if x > cutoff]
        if len(attempts) >= 10:
            raise Problem('Too many attempts. Try again in five minutes.', 429)
        with self.connect() as conn:
            row = conn.execute('SELECT * FROM users WHERE username=? AND active=1', (username,)).fetchone()
            if not row or not password_ok(str(data.get('password', '')), row['password']):
                self.login_attempts[username] = attempts + [datetime.now(timezone.utc)]
                raise Problem('Username or password is incorrect.', 401)
            self.login_attempts.pop(username, None)
            return self.make_session(dict(row))

    def session(self, token):
        session = self.sessions.get(token)
        if not session or session['expires'] < datetime.now(timezone.utc):
            self.sessions.pop(token, None)
            raise Problem('Please sign in.', 401)
        with self.connect() as conn:
            row = conn.execute('SELECT * FROM users WHERE id=? AND active=1', (session['user_id'],)).fetchone()
        if not row or session.get('password_stamp') != hashlib.sha256(row['password'].encode()).hexdigest():
            raise Problem('Please sign in.', 401)
        return dict(row), session['csrf']

    def business_allowed(self, user, bid):
        if not bid: raise Problem('Choose a business.',400)
        with self.connect() as conn:
            row=conn.execute('SELECT organization_id FROM businesses WHERE id=?',(bid,)).fetchone()
        if not row or row['organization_id']!=user.get('organization_id','local'):
            raise Problem('Business not found in your organisation.',404)
        if user['role'] != 'owner' and bid not in json.loads(user['business_ids']):
            raise Problem('You do not have access to this business.', 403)

    def permitted(self, user, kind, write=False):
        if kind not in (ROLE_WRITE if write else ROLE_READ).get(user['role'], set()):
            raise Problem('Your role does not have access to this area.', 403)

    def business(self, conn, bid):
        row = conn.execute('SELECT * FROM businesses WHERE id=?', (bid,)).fetchone()
        if not row:
            raise Problem('Business not found.', 404)
        return {**json.loads(row['data']), 'id': row['id'], 'version': row['version']}

    def businesses(self, user):
        with self.connect() as conn:
            rows = conn.execute('SELECT * FROM businesses WHERE organization_id=? ORDER BY id',(user.get('organization_id','local'),)).fetchall()
        ids = json.loads(user['business_ids'])
        return [{**json.loads(r['data']), 'id': r['id'], 'version': r['version']} for r in rows
                if user['role'] == 'owner' or r['id'] in ids]

    def save_business(self, user, payload):
        if user['role'] != 'owner':
            raise Problem('Only the owner can change business settings.', 403)
        data = dict(payload.get('data', {}))
        previous = None
        if payload.get('id'):
            self.business_allowed(user,payload['id'])
            with self.connect() as conn:
                previous = self.business(conn, payload['id'])
                data = {**previous, **data}
                if data.get('country', 'NP') != previous.get('country', 'NP') and any(self.records(conn, previous['id'])[k] for k in ('quotes', 'invoices', 'payments', 'stock', 'purchases', 'expenses', 'payroll')):
                    raise Problem('Country and currency are fixed once monetary records exist. Create a separate business for another country.')
        self.configure_profile(data, bool(payload.get('id')))
        if not str(data.get('name', '')).strip():
            raise Problem('Business name is required.')
        self.configure_region(data)
        validate_identity(data)
        data['vat_rate']=number(decimal(data.get('vat_rate',13),'VAT rate',0,100))
        data['print_font_size']=number(decimal(data.get('print_font_size',11),'Print font size',8,16))
        data['daily_capacity']=number(decimal(data.get('daily_capacity',8),'Daily capacity',1,10000))
        if 'stages' in data:
            if not isinstance(data['stages'],list) or not data['stages'] or len(data['stages'])>30: raise Problem('Enter between 1 and 30 job stages.')
            data['stages']=list(dict.fromkeys(str(x).strip()[:80] for x in data['stages'] if str(x).strip()))
        for key in ('quote_followup_days', 'payment_terms_days', 'low_stock_days'):
            data[key] = number(decimal(data.get(key, 3 if key != 'payment_terms_days' else 7), key.replace('_',' '), 0, 365))
        bid = payload.get('id') or identifier()
        with self.transaction() as conn:
            old = conn.execute('SELECT version FROM businesses WHERE id=?', (bid,)).fetchone()
            if old:
                if payload.get('version') != old['version']:
                    raise Problem('Settings changed in another window. Refresh and try again.', 409)
                current = self.business(conn, bid)
                if data['country'] != current.get('country', 'NP') and any(self.records(conn, bid)[k] for k in ('quotes', 'invoices', 'payments', 'stock', 'purchases', 'expenses', 'payroll')):
                    raise Problem('Country and currency are fixed once monetary records exist. Create a separate business for another country.')
                conn.execute('UPDATE businesses SET data=?,version=version+1 WHERE id=?', (json.dumps(data), bid))
            else:
                conn.execute('INSERT INTO businesses(id,data,organization_id) VALUES (?,?,?)', (bid, json.dumps(data),user.get('organization_id','local')))
            self.audit(conn, user, bid, 'Business settings saved', 'businesses', bid, data['name'])
            if payload.get('demo') and not old:
                self.seed(conn, bid)
            return self.business(conn, bid)

    def record(self, conn, bid, rid, kind=None):
        row = conn.execute('SELECT * FROM records WHERE id=? AND business_id=? AND archived=0', (rid, bid)).fetchone()
        if not row or (kind and row['kind'] != kind):
            raise Problem('Record not found in this business.', 404)
        return self.unpack(row)

    def unpack(self, row):
        return {**json.loads(row['data']), 'id': row['id'], 'type': row['kind'],
                'version': row['version'], 'created_at': row['created_at'], 'updated_at': row['updated_at']}

    def records(self, conn, bid):
        result = {kind: [] for kind in KINDS}
        for row in conn.execute('SELECT * FROM records WHERE business_id=? AND archived=0 ORDER BY created_at DESC', (bid,)):
            result[row['kind']].append(self.unpack(row))
        return result

    def audit(self, conn, user, bid, action, kind, rid, detail=''):
        conn.execute('INSERT INTO audit(business_id,user_name,action,kind,record_id,detail,created_at) VALUES(?,?,?,?,?,?,?)',
                     (bid, user.get('name', 'Owner'), action, kind, rid, str(detail)[:500], now()))

    def put(self, conn, bid, kind, data, rid=None):
        rid = rid or identifier()
        clean = {k: v for k, v in data.items() if k not in ('id', 'type', 'version', 'created_at', 'updated_at') and not k.startswith('_')}
        existing = conn.execute('SELECT business_id,kind FROM records WHERE id=?', (rid,)).fetchone()
        if existing and (existing['business_id'] != bid or existing['kind'] != kind):
            raise Problem('Record identifier belongs to another area.', 409)
        stamp = now()
        conn.execute('''INSERT INTO records(id,business_id,kind,data,created_at,updated_at) VALUES(?,?,?,?,?,?)
                        ON CONFLICT(id) DO UPDATE SET data=excluded.data,version=records.version+1,updated_at=excluded.updated_at''',
                     (rid, bid, kind, json.dumps(clean, ensure_ascii=False), stamp, stamp))
        return self.record(conn, bid, rid)

    def next_number(self, conn, bid, kind, day=None):
        business = self.business(conn, bid)
        day = day or business_today(business)
        year = financial_year(day) if business.get('country') == 'IN' else day[:4]
        conn.execute('INSERT OR IGNORE INTO counters VALUES (?,?,?,0)', (bid, kind, year))
        conn.execute('UPDATE counters SET value=value+1 WHERE business_id=? AND kind=? AND year=?', (bid, kind, year))
        n = conn.execute('SELECT value FROM counters WHERE business_id=? AND kind=? AND year=?', (bid, kind, year)).fetchone()[0]
        result = f'{kind}-{year}-{n:04}'
        if business.get('country') == 'IN' and len(result) > 16: raise Problem('Invoice series is full; configure a reviewed new series before continuing.')
        return result

    def save(self, user, bid, kind, payload):
        self.business_allowed(user, bid)
        self.permitted(user, kind, True)
        if kind not in KINDS:
            raise Problem('Unknown record type.')
        with self.transaction() as conn:
            self.business(conn, bid)
            rid = payload.get('id') or identifier()
            row = conn.execute('SELECT * FROM records WHERE id=?', (rid,)).fetchone()
            old = None
            if row:
                old = self.record(conn, bid, rid, kind)
                if payload.get('version') != old['version']:
                    raise Problem('This record changed in another window. Refresh before saving.', 409)
            data = dict(payload.get('data', {}))
            if old:
                data = {**old, **data}
            if user['role'] != 'owner':
                private = ('base_salary','salary_type','hourly_cost','overtime_rate','employee_percent','employer_percent') if kind == 'employees' else ('labor_cost','additional_material_cost','subcontract_cost','costs_final') if kind == 'jobs' else ('purchase_cost',) if kind == 'vehicles' else ()
                for key in private:
                    if old and key in old: data[key] = old[key]
                    else: data.pop(key, None)
            self.validate(conn, user, bid, kind, data, old)
            record = self.put(conn, bid, kind, data, rid)
            self.audit(conn, user, bid, 'Updated' if old else 'Created', kind, rid,
                       data.get('name') or data.get('subject') or data.get('number') or '')
        return record

    def validate(self, conn, user, bid, kind, data, old=None):
        for key, expected in [('customer_id','customers'), ('asset_id','assets'), ('job_id','jobs'),
                              ('employee_id','employees'), ('supplier_id','suppliers'), ('claim_id','claims'),
                              ('quote_id','quotes'), ('invoice_id','invoices'), ('vehicle_id','vehicles'),
                              ('lead_id','leads'), ('supplier_bill_id','supplier_bills'), ('opening_balance_id','opening_balances')]:
            if data.get(key):
                self.record(conn, bid, data[key], expected)
        self.validate_business_record(conn, user, bid, kind, data, old)
        self.validate_personalisation(conn, bid, kind, data, old)
        self.validate_operations(conn,user,bid,kind,data,old)
        for key in ('date', 'due_date', 'expected_date', 'start_date', 'end_date', 'expiry_date'):
            if data.get(key):
                checked_date(data[key], key.replace('_', ' '))
        if kind in {'customers','assets','services','employees','suppliers','stock','contracts','jobs','appointments','followups'} and not str(data.get('name', '')).strip():
            raise Problem('Name is required.')
        if kind in {'quotes', 'invoices'}:
            if old and old.get('status', 'draft') != 'draft':
                raise Problem('Sent quotes and issued invoices are retained. Create a revision or credit instead.', 409)
            if data.get('status', 'draft') != 'draft':
                raise Problem('Use the document action to send or issue this record.')
            if not data.get('customer_id'):
                raise Problem('Choose a customer.')
            calculated = calculate(data)
            data['items'] = [{**{k: v for k, v in x.items() if k not in ('net','tax','total','cost','discount_amount','configured_tax_rate','configured_cess_rate')},'tax_rate':x['configured_tax_rate'],**({'cess_rate':x['configured_cess_rate']} if 'configured_cess_rate' in x else {})} for x in calculated['lines']]
            data['status'] = 'draft'
            for line in data['items']:
                if line.get('item_id'):
                    self.record(conn, bid, line['item_id'], 'stock')
            data.setdefault('revision', 1)
            data['date']=checked_date(data.get('date') or today())
        if kind=='jobs' and not data.get('customer_id'): raise Problem('Choose the job customer.')
        if kind=='assets' and not data.get('customer_id'): raise Problem('Choose the asset owner.')
        if kind in {'payments','movements','credits','allocations'} and old:
            raise Problem('Ledger entries are retained. Record a correcting entry instead.', 409)
        if kind == 'payments':
            self.validate_payment(conn, bid, data)
        if kind == 'credits':
            self.validate_credit(conn, bid, data)
        if kind == 'allocations':
            raise Problem('Use Allocate advance to create a retained allocation entry.')
        if kind == 'movements':
            self.validate_movement(conn, bid, data)
        if kind == 'stock':
            for key in ('opening_qty', 'cost', 'rate', 'reorder_at'):
                data[key] = number(decimal(data.get(key, 0), key.replace('_',' '), 0))
            if old and decimal(data.get('opening_qty', 0)) != decimal(old.get('opening_qty', 0)):
                raise Problem('Opening quantity is retained. Use a stock adjustment.')
        if kind in {'services', 'expenses', 'employees', 'commissions'}:
            for key in ('rate','cost','amount','base_salary','hourly_cost','overtime_rate','shift_hours','employee_percent','employer_percent','percent','basis_amount','fixed_amount'):
                if key in data:
                    data[key] = number(decimal(data[key], key.replace('_',' '), 0, 100 if 'percent' in key else None))
        if kind == 'expenses' and decimal(data.get('amount', 0)) <= 0:
            raise Problem('Expense amount must be greater than zero.')
        if kind=='expenses' and data.get('category')=='Staff advance' and not data.get('employee_id'): raise Problem('Choose the employee receiving the advance.')
        if kind == 'jobs':
            if user['role'] == 'technician':
                if not old or user.get('employee_id') not in old.get('employee_ids', []):
                    raise Problem('You can update only your assigned jobs.', 403)
                allowed = {'stage', 'tasks', 'notes', 'blocker', 'custom_fields','inspection'}
                if any(data.get(k) != old.get(k) for k in set(data) - allowed if k not in ('id','version','type','created_at','updated_at') and not k.startswith('_')):
                    raise Problem('Technicians can update tasks, stages and work notes.', 403)
            for emp in data.get('employee_ids', []):
                self.record(conn, bid, emp, 'employees')
            for key in ('labor_cost', 'additional_material_cost', 'subcontract_cost'):
                data[key] = number(decimal(data.get(key, 0), key.replace('_',' '), 0))
            data.setdefault('tasks', [])
            if not isinstance(data['tasks'],list) or len(data['tasks'])>250: raise Problem('A job can have up to 250 checklist items.')
            if not old: data['number']=self.next_number(conn,bid,'JOB')
        if kind == 'claims':
            for key in ('requested', 'approved', 'customer_share', 'insurer_share'):
                data[key] = number(decimal(data.get(key, 0), key.replace('_',' '), 0))
            if data['customer_share'] + data['insurer_share'] > data['requested'] + .01:
                raise Problem('Expected payer shares cannot exceed the requested total.')
        if kind == 'external_quotes':
            if not data.get('issuer'):
                raise Problem('Enter the actual issuer or label the record as a hypothetical scenario.')
            data['_totals'] = calculate(data)
            if not data.get('quote_id'): raise Problem('Choose the own quotation being compared.')
            if not isinstance(data.get('simulation',False),bool): raise Problem('Choose whether this is hypothetical.')
        if kind == 'attendance':
            self.validate_attendance(conn, user, bid, data, old)
        if kind == 'time_entries':
            if not old:
                raise Problem('Use Start task to create a time entry.')
            raise Problem('Use Stop task to close a time entry.')
        if kind == 'commissions':
            if old and old.get('status') in ('approved','paid'):
                raise Problem('Approved earnings are retained. Record a separate adjustment.')
            data['amount'] = number(money(decimal(data.get('basis_amount', 0)) * decimal(data.get('percent', 0)) / 100
                                          + decimal(data.get('fixed_amount', 0))))
            data['status'] = 'earned'
            data['collection_required'] = bool(data.get('collection_required', True))
            if not data.get('employee_id'):
                raise Problem('Choose the beneficiary employee.')
            if data['collection_required'] and not (data.get('job_id') or data.get('lead_id')):
                raise Problem('A collection-based commission needs a linked job or sales enquiry.')
            if data.get('job_id') and data.get('lead_id'):
                raise Problem('Link an earning to either a job or a sales enquiry, not both.')
        if kind == 'payroll':
            if old:
                raise Problem('Payroll runs are retained. Create a separate adjustment run.')
            raise Problem('Use Prepare payroll to generate the reviewed calculation.')
        if kind == 'purchases':
            total = Decimal(0)
            seen = set()
            for line in data.get('items', []):
                if line.get('item_id') in seen: raise Problem('Combine duplicate stock items into one purchase line.')
                seen.add(line.get('item_id'))
                self.record(conn, bid, line.get('item_id'), 'stock')
                line['qty'] = number(decimal(line.get('qty', 0), 'Ordered quantity', Decimal('.0001')))
                line['cost'] = number(decimal(line.get('cost', 0), 'Unit cost', 0))
                total += money(decimal(line['qty']) * decimal(line['cost']))
            if not data.get('items'):
                raise Problem('Add at least one purchase line.')
            if old:
                records = self.records(conn, bid)
                if any(x.get('purchase_id') == old['id'] for x in records['movements']):
                    raise Problem('A received purchase order is retained. Create a new order.')
            data['total'] = number(total)
            data['status'] = 'ordered'
            data['number'] = (old or {}).get('number') or self.next_number(conn,bid,'PO')
        if kind=='appointments':
            if not data.get('date') or not data.get('time') or not data.get('customer_id'): raise Problem('Customer, visit date and arrival time are required.')
            duration=decimal(data.get('duration_minutes',60),'Reserved duration',1,1440)
            data['duration_minutes']=number(duration)
            try: start=datetime.fromisoformat(data['date']+'T'+data['time']); end=start+timedelta(minutes=float(duration))
            except ValueError: raise Problem('Enter a valid appointment time.')
            if data.get('status')!='cancelled':
                for other in self.records(conn,bid)['appointments']:
                    if other['id']==(old or {}).get('id') or other.get('status') in ('cancelled','completed') or not other.get('time'): continue
                    shared=(data.get('bay') and data.get('bay')==other.get('bay')) or (data.get('employee_id') and data.get('employee_id')==other.get('employee_id'))
                    if not shared: continue
                    other_start=datetime.fromisoformat(other['date']+'T'+other['time']); other_end=other_start+timedelta(minutes=float(other.get('duration_minutes',60)))
                    if start<other_end and end>other_start: raise Problem('This bay or employee already has an overlapping appointment.',409)

    def validate_attendance(self, conn, user, bid, data, old):
        if not data.get('employee_id') or not data.get('date'):
            raise Problem('Employee and attendance date are required.')
        if user['role'] == 'technician' and data.get('employee_id') != user.get('employee_id'):
            raise Problem('You can record only your attendance.', 403)
        for row in self.records(conn, bid)['attendance']:
            if row['id'] != (old or {}).get('id') and row.get('employee_id') == data['employee_id'] and row.get('date') == data['date']:
                raise Problem('Attendance already exists for this employee and date.', 409)
        hours = Decimal(0)
        if data.get('in_time') and data.get('out_time'):
            try:
                start = datetime.fromisoformat(data['date']+'T'+data['in_time'])
                end = datetime.fromisoformat(data['date']+'T'+data['out_time'])
            except ValueError:
                raise Problem('Use valid clock-in and clock-out times.')
            if end < start:
                if not data.get('overnight'):
                    raise Problem('Clock-out precedes clock-in. Select overnight shift if appropriate.')
                end += timedelta(days=1)
            hours = decimal((end-start).total_seconds()) / 3600 - decimal(data.get('break_minutes', 0), 'Break minutes', 0) / 60
            if hours < 0 or hours > 24:
                raise Problem('The attendance duration must be between zero and 24 hours.')
        data['hours'] = number(hours.quantize(Decimal('.01'), rounding=ROUND_HALF_UP))
        if user['role'] == 'technician':
            data['status'] = 'pending'
        elif data.get('status') not in ('pending','approved','leave','absent'):
            data['status'] = 'pending'

    def invoice_values(self, records, invoice):
        totals = invoice.get('totals_snapshot') or calculate(invoice)
        credit = sum((money(x.get('amount', 0)) for x in records['credits'] if x.get('invoice_id') == invoice['id']), Decimal(0))
        paid = sum((money(x.get('amount', 0)) * (-1 if x.get('direction') == 'refund' else 1)
                    for x in records['payments'] if x.get('invoice_id') == invoice['id']), Decimal(0))
        paid += sum((money(x.get('amount',0)) for x in records['allocations'] if x.get('invoice_id') == invoice['id']), Decimal(0))
        return totals, money(credit), money(paid), money(decimal(totals['total']) - credit - paid)

    def validate_payment(self, conn, bid, data):
        amount = money(decimal(data.get('amount', 0), 'Amount', Decimal('.01')))
        data['amount'] = number(amount)
        data['date'] = checked_date(data.get('date'), optional=False)
        if data.get('direction', 'receipt') not in ('receipt','refund'):
            raise Problem('Choose receipt or refund.')
        records = self.records(conn, bid)
        reference = str(data.get('reference', '')).strip()
        if reference and any(x.get('reference') == reference and x.get('method') == data.get('method') and x.get('direction','receipt') == data.get('direction','receipt') for x in records['payments']):
            raise Problem('That payment reference is already recorded.', 409)
        if data.get('opening_balance_id'):
            self.validate_opening_payment(conn,bid,data)
            return
        data['number'] = self.next_number(conn, bid, 'RCT' if data.get('direction') != 'refund' else 'RFD')
        if not data.get('invoice_id'):
            if data.get('direction') == 'refund' or not data.get('customer_id'):
                raise Problem('Choose an invoice for a refund or customer for an unapplied advance.')
            return
        invoice = self.record(conn, bid, data['invoice_id'], 'invoices')
        if invoice.get('status') != 'issued':
            raise Problem('Issue the invoice before recording a payment.')
        records = self.records(conn, bid)
        _, _, paid, balance = self.invoice_values(records, invoice)
        if data.get('direction') == 'refund':
            if amount > paid:
                raise Problem('Refund cannot exceed net receipts for this invoice.')
        elif amount > balance:
            raise Problem('Payment exceeds the outstanding balance. Record an unapplied customer advance separately.')
        data['customer_id'] = invoice['customer_id']
        reference = str(data.get('reference', '')).strip()
        if reference and any(x.get('reference') == reference and x.get('method') == data.get('method') and x.get('direction','receipt') == data.get('direction','receipt') for x in records['payments']):
            raise Problem('That payment reference is already recorded.', 409)
    def validate_credit(self, conn, bid, data):
        invoice = self.record(conn, bid, data.get('invoice_id'), 'invoices')
        if invoice.get('status') != 'issued':
            raise Problem('Credit notes require an issued invoice.')
        if invoice.get('country') == 'IN': raise Problem('Use Return / credit items on the invoice for a line-level GST credit.')
        totals, credited, _, _ = self.invoice_values(self.records(conn, bid), invoice)
        amount = money(decimal(data.get('amount', 0), 'Credit amount', Decimal('.01')))
        if amount + credited > money(totals['total']):
            raise Problem('Credits exceed the original invoice amount.')
        if not str(data.get('reason', '')).strip():
            raise Problem('A credit note needs a reason.')
        data['amount'] = number(amount)
        existing_net=sum((money(x.get('net',0)) for x in self.records(conn,bid)['credits'] if x.get('invoice_id')==invoice['id']),Decimal(0))
        data['net'] = number(money((credited+amount) * decimal(totals['net']) / decimal(totals['total']))-existing_net) if totals['total'] else 0
        data['tax'] = number(amount - money(data['net']))
        data['number'] = self.next_number(conn, bid, 'CRN')
        data['date'] = checked_date(data.get('date') or today())
        data['customer_id'] = invoice['customer_id']

    def stock_quantity(self, records, item_id):
        item = next((x for x in records['stock'] if x['id'] == item_id), None)
        if not item:
            raise Problem('Stock item not found.')
        return decimal(item.get('opening_qty', 0)) + sum((decimal(x.get('qty', 0)) * (-1 if x.get('kind') == 'issue' else 1)
                                                         for x in records['movements'] if x.get('item_id') == item_id), Decimal(0))

    def validate_movement(self, conn, bid, data):
        item = self.record(conn, bid, data.get('item_id'), 'stock')
        kind = data.get('kind', 'receipt')
        if kind not in ('receipt','issue','return','adjustment'):
            raise Problem('Choose a stock movement type.')
        qty = decimal(data.get('qty', 0), 'Quantity')
        if not qty or (kind != 'adjustment' and qty < 0):
            raise Problem('Enter a positive movement quantity; adjustments can be negative.')
        available = self.stock_quantity(self.records(conn, bid), item['id'])
        if available + (-qty if kind == 'issue' else qty) < 0:
            raise Problem('Not enough stock. Record a receipt or correction first.')
        if kind == 'adjustment' and not data.get('notes'):
            raise Problem('A stock adjustment needs a reason.')
        data['qty'] = number(qty)
        data['unit_cost'] = number(decimal(data.get('unit_cost', item.get('cost', 0)), 'Unit cost', 0))
        data['date'] = checked_date(data.get('date') or today())

    def action(self, user, bid, kind, rid, payload):
        self.business_allowed(user, bid)
        self.permitted(user, kind, True)
        action = payload.get('action')
        with self.transaction() as conn:
            business = self.business(conn, bid)
            record = self.record(conn, bid, rid, kind)
            if payload.get('version') != record['version']:
                raise Problem('This record changed. Refresh and try again.', 409)
            result = None
            if kind == 'quotes' and action in ('send', 'accept', 'decline', 'revise', 'job'):
                result = self.quote_action(conn, user, bid, record, action, payload, business)
            elif kind == 'invoices' and action == 'issue':
                if record.get('status','draft') != 'draft':
                    raise Problem('Invoice is already issued.', 409)
                self.prepare_regional_document(conn, bid, record, issuing=True)
                totals = calculate(record)
                self.enforce_credit_limit(conn,user,bid,record,totals,payload)
                if not totals['lines']:
                    raise Problem('Add at least one invoice line.')
                record.update(status='issued', number=self.next_number(conn, bid, 'INV', record.get('date')), issued_at=now(),
                              seller_snapshot=business, customer_snapshot=self.record(conn,bid,record['customer_id'],'customers'),
                              asset_snapshot=self.record(conn,bid,record['asset_id'],'assets') if record.get('asset_id') else {},
                              totals_snapshot=totals)
                self.issue_inventory(conn, bid, record)
                result = self.put(conn, bid, kind, record, rid)
            elif kind == 'invoices' and action == 'return':
                result = self.line_return(conn, user, bid, record, payload)
            elif kind == 'leads':
                result = self.sales_action(conn, user, bid, record, action, payload, business)
            elif kind == 'jobs' and action == 'invoice':
                self.permitted(user, 'invoices', True)
                existing = next((x for x in self.records(conn,bid)['invoices'] if x.get('job_id') == rid and x.get('status') != 'cancelled'), None)
                if existing:
                    result = existing
                else:
                    quote = self.record(conn,bid,record['quote_id'],'quotes') if record.get('quote_id') else None
                    result = self.put(conn,bid,'invoices',{
                        'job_id':rid,'customer_id':record['customer_id'],'asset_id':record.get('asset_id',''),
                        'subject':record.get('name','Service work'),'date':today(),
                        'due_date':(date.fromisoformat(today())+timedelta(days=int(business.get('payment_terms_days',7)))).isoformat(),
                        'status':'draft','items':(quote or {}).get('items',[]),'vat_mode':(quote or {}).get('vat_mode','added'),
                        'vat_rate':(quote or {}).get('vat_rate',business.get('vat_rate',13)),
                        'discount_percent':(quote or {}).get('discount_percent',0),'terms':(quote or {}).get('terms',business.get('terms','')),
                    })
            elif kind == 'commissions' and action in ('approve','pay'):
                if action == 'approve':
                    if record.get('status') != 'earned':
                        raise Problem('Only an earned commission can be approved.')
                    record.update(status='approved',approved_at=now(),approved_by=user['name'])
                else:
                    if record.get('reserved_payroll_id'): raise Problem('This earning is reserved in payroll. Pay that payroll run.',409)
                    if record.get('status') != 'approved':
                        raise Problem('Approve the commission before paying it.')
                    if record.get('collection_required') and self.commission_eligible(self.records(conn,bid),record) < money(record['amount']):
                        raise Problem('The linked job is not fully collected. Record an eligible portion as a separate earning.')
                    record.update(status='paid',paid_at=now(),paid_by=user['name'])
                result = self.put(conn,bid,kind,record,rid)
            elif kind == 'attendance' and action == 'approve':
                if user['role'] == 'technician':
                    raise Problem('A manager must approve attendance.',403)
                record.update(status='approved',approved_at=now(),approved_by=user['name'])
                result = self.put(conn,bid,kind,record,rid)
            elif kind == 'payroll' and action in ('approve','pay'):
                if action == 'approve' and record.get('status') != 'draft':
                    raise Problem('Payroll run is not awaiting approval.')
                if action == 'pay' and record.get('status') != 'approved':
                    raise Problem('Approve the payroll before marking it paid.')
                if action == 'approve':
                    for other in self.records(conn,bid)['payroll']:
                        if other['id']!=rid and other.get('status') in ('approved','paid') and other['start_date']<=record['end_date'] and other['end_date']>=record['start_date'] and {x['employee_id'] for x in other['lines']} & {x['employee_id'] for x in record['lines']}:
                            raise Problem('An approved payroll already covers this employee and period.',409)
                for cid in record.get('commission_ids',[]):
                    earning=self.record(conn,bid,cid,'commissions')
                    if earning.get('status') == 'paid' or (earning.get('reserved_payroll_id') not in ('',None,rid)):
                        raise Problem('A payroll commission is already paid or reserved by another run.',409)
                    if self.commission_eligible(self.records(conn,bid),earning)<money(earning['amount']):
                        raise Problem('A payroll commission is no longer fully eligible after a refund or credit.')
                    earning['reserved_payroll_id']=rid
                    if action == 'pay':
                        earning.update(status='paid',paid_at=now(),payroll_id=rid)
                    self.put(conn,bid,'commissions',earning,cid)
                record.update(status='approved' if action=='approve' else 'paid',**{action+'_at':now(),action+'_by':user['name']})
                result=self.put(conn,bid,kind,record,rid)
            elif kind == 'purchases' and action == 'receive':
                result=self.receive(conn,bid,record,payload)
            elif kind == 'payments' and action == 'allocate':
                if record.get('invoice_id') or record.get('opening_balance_id') or record.get('direction','receipt') != 'receipt': raise Problem('Only an unapplied advance can be allocated.')
                invoice = self.record(conn,bid,payload.get('invoice_id'),'invoices')
                if invoice.get('status')!='issued' or invoice.get('customer_id')!=record.get('customer_id'): raise Problem('Choose an issued invoice for the same customer.')
                records=self.records(conn,bid)
                available=money(record['amount'])-sum((money(x['amount']) for x in records['allocations'] if x.get('payment_id')==rid),Decimal(0))
                amount=money(decimal(payload.get('amount',0),'Allocation amount',Decimal('.01')))
                if amount>available or amount>self.invoice_values(records,invoice)[3]: raise Problem('Allocation exceeds the available advance or invoice balance.')
                result=self.put(conn,bid,'allocations',{'payment_id':rid,'invoice_id':invoice['id'],'customer_id':record['customer_id'],'amount':number(amount),'date':today(),'number':self.next_number(conn,bid,'ALC')})
            else:
                raise Problem('That action is not available.')
            self.audit(conn,user,bid,action.replace('_',' ').title(),kind,rid,record.get('number') or record.get('name',''))
            return result

    def quote_action(self,conn,user,bid,record,action,payload,business):
        status=record.get('status','draft')
        if action=='send':
            if status!='draft': raise Problem('Only a draft can be sent.')
            self.prepare_regional_document(conn, bid, record)
            totals=calculate(record)
            if not totals['lines']: raise Problem('Add at least one quotation line.')
            record.update(status='sent',sent_at=now(),number=record.get('number') or self.next_number(conn,bid,'Q'),
                          seller_snapshot=business,customer_snapshot=self.record(conn,bid,record['customer_id'],'customers'),
                          asset_snapshot=self.record(conn,bid,record['asset_id'],'assets') if record.get('asset_id') else {},totals_snapshot=totals)
        elif action in ('accept','decline'):
            if status!='sent': raise Problem('Only a sent quote can be accepted or declined.')
            if action=='accept' and not str(payload.get('approved_by','')).strip():
                raise Problem('Record who approved this exact quotation revision.')
            record.update(status='accepted' if action=='accept' else 'declined',decision_at=now(),
                          approved_by=payload.get('approved_by',''),approval_channel=payload.get('channel','Recorded by staff'),
                          approval_note=payload.get('notes',''))
        elif action=='revise':
            fresh={k:v for k,v in record.items() if k not in ('number','seller_snapshot','customer_snapshot','asset_snapshot','totals_snapshot','sent_at','approved_by','decision_at','approval_channel','approval_note')}
            fresh.update(status='draft',revision=int(record.get('revision',1))+1,previous_id=record['id'],group_id=record.get('group_id',record['id']))
            return self.put(conn,bid,'quotes',fresh)
        elif action=='job':
            if status!='accepted': raise Problem('Record approval before creating the work order.')
            existing=next((x for x in self.records(conn,bid)['jobs'] if x.get('quote_id')==record['id']),None)
            if existing: return existing
            checked_date(payload.get('due_date',''))
            return self.put(conn,bid,'jobs',{
                'name':record.get('subject') or 'Service job','number':self.next_number(conn,bid,'JOB'),
                'customer_id':record['customer_id'],'asset_id':record.get('asset_id',''),'quote_id':record['id'],
                'date':business_today(business),'due_date':payload.get('due_date',''),'stage':business.get('stages', ['Intake'])[0],'employee_ids':[],
                'tasks':[{'id':identifier(),'name':x,'done':False} for x in list(dict.fromkeys([i['description'] for i in record['items']] + business.get('job_checklist', [])))],
                'labor_cost':0,'additional_material_cost':0,'subcontract_cost':0,'notes':'','blocker':'',
            })
        return self.put(conn,bid,'quotes',record,record['id'])

    def receive(self,conn,bid,order,payload):
        records=self.records(conn,bid)
        received=0
        for line in payload.get('items',[]):
            item_id=line.get('item_id')
            source=next((x for x in order['items'] if x['item_id']==item_id),None)
            if not source: raise Problem('Item is not on this purchase order.')
            already=sum((decimal(x.get('qty',0)) for x in records['movements'] if x.get('purchase_id')==order['id'] and x.get('item_id')==item_id),Decimal(0))
            qty=decimal(line.get('qty',0),'Received quantity',0)
            if not qty: continue
            if qty+already>decimal(source['qty']): raise Problem('Receipt exceeds the remaining ordered quantity.')
            data={'item_id':item_id,'qty':number(qty),'kind':'receipt','unit_cost':source['cost'],
                  'date':today(),'purchase_id':order['id'],'supplier_id':order.get('supplier_id',''),'notes':order.get('number','')}
            self.validate_movement(conn,bid,data)
            self.put(conn,bid,'movements',data)
            records=self.records(conn,bid)
            received+=1
        if not received: raise Problem('Enter at least one quantity received.')
        full=all(sum((decimal(m.get('qty',0)) for m in records['movements'] if m.get('purchase_id')==order['id'] and m.get('item_id')==x['item_id']),Decimal(0))>=decimal(x['qty']) for x in order['items'])
        order['status']='received' if full else 'partial'
        return self.put(conn,bid,'purchases',order,order['id'])

    def time_action(self,user,bid,data):
        self.business_allowed(user,bid)
        self.permitted(user,'time_entries',True)
        with self.transaction() as conn:
            records=self.records(conn,bid)
            eid=data.get('employee_id') or user.get('employee_id')
            self.record(conn,bid,eid,'employees')
            if user['role']=='technician' and eid!=user.get('employee_id'):
                raise Problem('You can track only your own time.',403)
            active=next((x for x in records['time_entries'] if x.get('employee_id')==eid and not x.get('end_at')),None)
            if data.get('action')=='start':
                if active: raise Problem('Stop the current task before starting another.',409)
                job=self.record(conn,bid,data.get('job_id'),'jobs')
                if user['role']=='technician' and eid not in job.get('employee_ids',[]):
                    raise Problem('You can track time on your assigned jobs.',403)
                employee=self.record(conn,bid,eid,'employees')
                rec=self.put(conn,bid,'time_entries',{'employee_id':eid,'job_id':job['id'],'task':data.get('task','Work'),'hourly_cost_snapshot':employee.get('hourly_cost',0),
                            'start_at':now(),'end_at':'','hours':0,'date':today()})
            else:
                if not active: raise Problem('There is no running task for this employee.')
                active['end_at']=now()
                active['hours']=number((decimal((datetime.fromisoformat(active['end_at'])-datetime.fromisoformat(active['start_at'])).total_seconds())/3600).quantize(Decimal('.0001')))
                active['notes']=data.get('notes','')
                rec=self.put(conn,bid,'time_entries',active,active['id'])
            self.audit(conn,user,bid,'Task timer '+data.get('action',''),'time_entries',rec['id'])
            return rec

    def commission_eligible(self,records,earning):
        amount=money(earning.get('amount',0))
        if not earning.get('collection_required'): return amount
        reference = 'lead_id' if earning.get('lead_id') else 'job_id'
        linked=[x for x in records['invoices'] if earning.get(reference) and x.get(reference)==earning.get(reference) and x.get('status')=='issued']
        if not linked: return Decimal(0)
        due=paid=Decimal(0)
        for invoice in linked:
            totals,credit,receipts,_=self.invoice_values(records,invoice)
            due+=max(Decimal(0),money(totals['total'])-credit)
            paid+=receipts
        fraction=min(Decimal(1),max(Decimal(0),paid/due)) if due else Decimal(0)
        return money(amount*fraction)

    def prepare_payroll(self,user,bid,payload):
        self.business_allowed(user,bid)
        self.permitted(user,'payroll',True)
        start=checked_date(payload.get('start_date'),optional=False)
        end=checked_date(payload.get('end_date'),optional=False)
        if start>end: raise Problem('The end of the pay period precedes its start.')
        with self.transaction() as conn:
            records=self.records(conn,bid)
            lines=[]; commissions=[]
            for settings in payload.get('lines',[]):
                emp=self.record(conn,bid,settings.get('employee_id'),'employees')
                if not emp.get('active',True): continue
                units=decimal(settings.get('units',1),'Pay units',0)
                base=money(decimal(emp.get('base_salary',0))*units)
                overtime=money(decimal(settings.get('overtime_hours',0),'Overtime hours',0)*decimal(emp.get('overtime_rate',0)))
                bonus=money(decimal(settings.get('bonus',0),'Bonus',0))
                withholding=money(decimal(settings.get('withholding',0),'Withholding',0))
                deduction=money(decimal(settings.get('deductions',0),'Authorised deductions',0))
                if deduction and not settings.get('deduction_note'):
                    raise Problem('Authorised deductions need a recorded reason.')
                selected=[x for x in records['commissions'] if x['id'] in settings.get('commission_ids',[])]
                if len(selected)!=len(set(settings.get('commission_ids',[]))):
                    raise Problem('An included commission was not found.')
                for earning in selected:
                    if earning.get('employee_id')!=emp['id'] or earning.get('status')!='approved' or earning.get('reserved_payroll_id'):
                        raise Problem('Only approved, unreserved earnings for this employee can enter payroll.')
                    if self.commission_eligible(records,earning)<money(earning['amount']):
                        raise Problem('A selected commission is awaiting collection.')
                commission=sum((money(x['amount']) for x in selected),Decimal(0))
                contribution_base=money(decimal(settings.get('contribution_base',base),'Contribution base',0))
                employee_contribution=money(contribution_base*decimal(emp.get('employee_percent',0))/100)
                employer_contribution=money(contribution_base*decimal(emp.get('employer_percent',0))/100)
                gross=base+overtime+bonus+commission
                net=gross-withholding-deduction-employee_contribution
                if net<0: raise Problem('Net pay cannot be negative.')
                lines.append({'employee_id':emp['id'],'name':emp['name'],'basis':emp.get('salary_type','monthly'),
                    'units':number(units),'base':number(base),'overtime':number(overtime),'bonus':number(bonus),
                    'commission':number(commission),'gross':number(gross),'employee_contribution':number(employee_contribution),
                    'employer_contribution':number(employer_contribution),'withholding':number(withholding),
                    'deductions':number(deduction),'deduction_note':settings.get('deduction_note',''),'net':number(net),
                    'employer_cost':number(gross+employer_contribution),'employee_snapshot':emp})
                commissions.extend(x['id'] for x in selected)
            if not lines: raise Problem('Include at least one active employee.')
            if len({x['employee_id'] for x in lines})!=len(lines): raise Problem('Employee appears more than once.')
            for existing in records['payroll']:
                if existing.get('status') not in ('draft','cancelled') and existing.get('start_date')<=end and existing.get('end_date')>=start:
                    if set(x['employee_id'] for x in lines)&set(x['employee_id'] for x in existing['lines']):
                        raise Problem('An approved payroll already covers an included employee in this period. Use an explicit adjustment run.')
            rec=self.put(conn,bid,'payroll',{'number':self.next_number(conn,bid,'PAY'),'start_date':start,'end_date':end,
                'date':today(),'status':'draft','lines':lines,'commission_ids':commissions,
                'total_net':number(sum((money(x['net']) for x in lines),Decimal(0))),
                'total_cost':number(sum((money(x['employer_cost']) for x in lines),Decimal(0))),
                'notes':payload.get('notes',''),'seller_snapshot':self.business(conn,bid)})
            self.audit(conn,user,bid,'Prepared payroll','payroll',rec['id'],rec['number'])
            return rec

    def archive(self,user,bid,kind,rid,version):
        self.business_allowed(user,bid); self.permitted(user,kind,True)
        with self.transaction() as conn:
            rec=self.record(conn,bid,rid,kind)
            if rec['version']!=version: raise Problem('Record changed. Refresh first.',409)
            if kind in {'payments','credits','movements','time_entries','allocations','supplier_bills','supplier_payments','opening_balances','cash_closures'} or (kind in {'quotes','invoices','payroll','commissions'} and rec.get('status','draft') not in ('draft','earned')):
                raise Problem('This posted record is retained. Use a correction.')
            for collection in self.records(conn,bid).values():
                for other in collection:
                    if other['id']!=rid and (rid in [other.get(k) for k in ('customer_id','asset_id','job_id','quote_id','invoice_id','employee_id','item_id','supplier_id','claim_id','previous_id','group_id','payment_id','vehicle_id','lead_id','reserved_lead_id','supplier_bill_id','purchase_id','opening_balance_id')]
                        or rid in other.get('employee_ids',[]) or rid in other.get('commission_ids',[]) or any(x.get('item_id')==rid or x.get('employee_id')==rid for x in other.get('items',[])+other.get('lines',[]))):
                        raise Problem('This record is linked to other work. Keep it and mark it inactive instead.')
            conn.execute('UPDATE records SET archived=1,version=version+1 WHERE id=?',(rid,))
            self.audit(conn,user,bid,'Archived',kind,rid)

    def enrich(self,records):
        self.enrich_business_records(records)
        self.enrich_operations(records)
        for kind in ('quotes','invoices','external_quotes'):
            for rec in records[kind]:
                rec['_totals']=rec.get('totals_snapshot') or calculate(rec)
        for invoice in records['invoices']:
            _,credit,paid,balance=self.invoice_values(records,invoice)
            invoice.update(_credited=number(credit),_paid=number(paid),_balance=number(balance))
        for payment in records['payments']:
            payment['_unallocated']=number(money(payment['amount'])-sum((money(x['amount']) for x in records['allocations'] if x.get('payment_id')==payment['id']),Decimal(0))) if not payment.get('invoice_id') and not payment.get('opening_balance_id') else 0
        for item in records['stock']:
            item['_quantity']=number(self.stock_quantity(records,item['id']))
        employees={x['id']:x for x in records['employees']}
        for job in records['jobs']:
            revenue=sum((decimal(x['_totals']['net']) for x in records['invoices'] if x.get('job_id')==job['id'] and x.get('status')=='issued'),Decimal(0))
            invoice_ids={x['id'] for x in records['invoices'] if x.get('job_id')==job['id']}
            revenue-=sum((decimal(x.get('net',0)) for x in records['credits'] if x.get('invoice_id') in invoice_ids),Decimal(0))
            material=sum((decimal(x.get('qty',0))*decimal(x.get('unit_cost',0))*(1 if x.get('kind')=='issue' else -1)
                          for x in records['movements'] if x.get('job_id')==job['id'] and x.get('kind') in ('issue','return')),Decimal(0))
            labor=decimal(job.get('labor_cost',0))
            if not labor:
                labor=sum((decimal(x.get('hours',0))*decimal(x.get('hourly_cost_snapshot',employees.get(x.get('employee_id'),{}).get('hourly_cost',0)))
                           for x in records['time_entries'] if x.get('job_id')==job['id'] and x.get('end_at')),Decimal(0))
            direct=sum((decimal(x.get('amount',0)) for x in records['expenses'] if x.get('job_id')==job['id'] and x.get('category')!='Staff advance'),Decimal(0))
            incentive=sum((decimal(x.get('amount',0)) for x in records['commissions'] if x.get('job_id')==job['id']),Decimal(0))
            cost=material+labor+decimal(job.get('additional_material_cost',0))+decimal(job.get('subcontract_cost',0))+direct+incentive
            job.update(_revenue=number(money(revenue)),_cost=number(money(cost)),_contribution=number(money(revenue-cost)),
                       _cost_provisional=not bool(job.get('costs_final',False)))
        for earning in records['commissions']:
            earning['_eligible']=number(self.commission_eligible(records,earning))
        return records

    def alerts(self,business,records):
        alerts=self.business_alerts(records, business)
        day=date.fromisoformat(business_today(business))
        def add(key,priority,title,detail,kind,rid,next_action):
            alerts.append({'key':key,'priority':priority,'title':title,'detail':detail,'type':kind,'record_id':rid,'next_action':next_action})
        for q in records['quotes']:
            if q.get('status')=='sent' and q.get('sent_at') and (day-datetime.fromisoformat(q['sent_at']).astimezone(NEPAL).date()).days>=int(business.get('quote_followup_days',3)):
                add('quote:'+q['id'],2,'Quotation awaiting a reply',q.get('number') or q.get('subject','Quotation'),'quotes',q['id'],'Ask whether the customer is ready to approve the quoted work.')
        for invoice in records['invoices']:
            if invoice.get('status')=='issued' and invoice.get('_balance',0)>.009 and invoice.get('due_date') and invoice['due_date']<business_today(business):
                add('invoice:'+invoice['id'],1,'Payment overdue',f"{invoice.get('number','Invoice')} · {business.get('currency', 'NPR')} {invoice['_balance']:,.2f} outstanding",'invoices',invoice['id'],'Confirm the outstanding amount and agree a payment date.')
            if invoice.get('_balance',0)<-.009:
                add('refund:'+invoice['id'],1,'Customer credit to resolve',invoice.get('number','Invoice'),'invoices',invoice['id'],'Review the credit and arrange an authorised refund or allocation.')
        for job in records['jobs']:
            if job.get('stage')==(business.get('stages') or STAGES)[-1]: continue
            if job.get('blocker'):
                add('blocked:'+job['id'],1,'Job needs attention',job['name']+' · '+job['blocker'],'jobs',job['id'],'Resolve the blocker or agree an updated delivery promise.')
            elif job.get('due_date') and job['due_date']<=business_today(business):
                add('due:'+job['id'],1,'Delivery due',job['name'],'jobs',job['id'],'Check progress, complete quality checks and confirm delivery.')
            elif not job.get('employee_ids'):
                add('unassigned:'+job['id'],2,'Assign this job',job['name'],'jobs',job['id'],'Choose a technician or service team.')
        for item in records['stock']:
            if item.get('_quantity',0)<=float(item.get('reorder_at',0)):
                add('stock:'+item['id'],2,'Stock needs replenishing',f"{item['name']} · {item['_quantity']:g} {item.get('unit','pc')} left",'stock',item['id'],'Check upcoming jobs and prepare a supplier order.')
        for claim in records['claims']:
            if claim.get('status') not in ('settled','closed') and claim.get('due_date') and claim['due_date']<=business_today(business):
                add('claim:'+claim['id'],1,'Insurance follow-up due',claim.get('reference') or claim.get('insurer','Claim'),'claims',claim['id'],claim.get('next_action') or 'Confirm the next approval or settlement step with the insurer.')
        for order in records['purchases']:
            if order.get('status')!='received' and order.get('expected_date') and order['expected_date']<=business_today(business):
                add('purchase:'+order['id'],2,'Supplier delivery due',order.get('number','Purchase order'),'purchases',order['id'],'Confirm delivery and receive the actual quantity supplied.')
        for a in records['attendance']:
            if a.get('status')=='pending' and a.get('date','')<=business_today(business):
                add('attendance:'+a['id'],3,'Attendance needs review',a.get('date',''),'attendance',a['id'],'Check missing punches and approve the correct attendance.')
        for c in records['contracts']:
            if c.get('expiry_date') and business_today(business)<=c['expiry_date']<=(day+timedelta(days=30)).isoformat() and c.get('status')!='closed':
                add('contract:'+c['id'],2,'Contract renewal approaching',c['name'],'contracts',c['id'],'Review the agreement and prepare a renewal quotation.')
        for appointment in records['appointments']:
            if appointment.get('date')==business_today(business) and appointment.get('status') not in ('completed','cancelled'):
                add('appointment:'+appointment['id'],2,'Appointment today',appointment.get('name','Appointment')+' · '+appointment.get('time',''),'appointments',appointment['id'],'Confirm arrival and prepare the service job.')
        dismiss={x.get('alert_key'):x for x in records['followups'] if x.get('alert_key')}
        filtered=[]
        for alert in alerts:
            note=dismiss.get(alert['key'])
            if note and note.get('due_date','')>business_today(business): continue
            if note and note.get('status')=='completed' and note.get('date')==business_today(business): continue
            if note: alert['last_note']=note.get('notes','')
            filtered.append(alert)
        for task in records['followups']:
            if not task.get('alert_key') and task.get('status','open')!='completed' and task.get('due_date','')<=business_today(business):
                add_task={'key':'manual:'+task['id'],'priority':2,'title':task.get('name','Follow-up'),
                    'detail':task.get('notes',''),'type':'followups','record_id':task['id'],'next_action':task.get('next_action','Complete the planned follow-up.')}
                filtered.append(add_task)
        for opening in records['opening_balances']:
            if opening.get('_balance',0)>.009:
                filtered.append({'key':'opening:'+opening['id'],'priority':2,'title':'Opening balance to collect','detail':opening['source_reference'],'type':'opening_balances','record_id':opening['id'],'next_action':'Confirm the reconciled balance and record the actual receipt.'})
        for closure in records['cash_closures']:
            if closure.get('_source_changed'):
                filtered.append({'key':'cash:'+closure['id'],'priority':1,'title':'Cash count needs review','detail':closure['date'],'type':'cash_closures','record_id':closure['id'],'next_action':'Cash entries changed after this count. Reconcile and post an owner-reviewed replacement.'})
        return sorted(filtered,key=lambda x:(x['priority'],x['title']))

    def state(self,user,bid):
        self.business_allowed(user,bid)
        with self.connect() as conn:
            business=self.business(conn,bid)
            records=self.enrich(self.records(conn,bid))
            allowed=ROLE_READ[user['role']]
            if user['role']=='technician':
                eid=user.get('employee_id')
                records['jobs']=[x for x in records['jobs'] if eid in x.get('employee_ids',[])]
                for kind in ('time_entries','attendance'):
                    records[kind]=[x for x in records[kind] if x.get('employee_id')==eid]
            for kind in list(records):
                if kind not in allowed: records[kind]=[]
            if user['role']!='owner':
                records['employees']=[{k:v for k,v in x.items() if k in ('id','name','role','active','version','type')} for x in records['employees']]
                for job in records['jobs']:
                    for k in ('labor_cost','additional_material_cost','subcontract_cost','_revenue','_cost','_contribution'):
                        job.pop(k,None)
                for vehicle in records['vehicles']:
                    vehicle.pop('purchase_cost', None)
            attachments=[]
            visible={x['id'] for rows in records.values() for x in rows}
            for x in conn.execute('SELECT id,record_id,filename,mime,hash,created_at FROM attachments WHERE business_id=?',(bid,)):
                if x['record_id'] in visible: attachments.append(dict(x))
            audit=[dict(x) for x in conn.execute('SELECT * FROM audit WHERE business_id=? ORDER BY id DESC LIMIT 60',(bid,))] if user['role']=='owner' else []
            epoch = conn.execute("SELECT value FROM meta WHERE key='data_epoch'").fetchone()[0]
        return {'business':business,'records':records,'alerts':self.alerts(business,records),'attachments':attachments, 'data_epoch':epoch,
                'profiles':PROFILES, 'india_states':INDIA_STATES,
                'audit':audit,'today':business_today(business),'stages':business.get('stages') or STAGES,'permissions':{'read':sorted(allowed),'write':sorted(ROLE_WRITE[user['role']])}}

    def assistant(self,user,bid,question):
        state=self.state(user,bid); records=state['records']; business=state['business']
        query=question.lower()
        opening_due=[x for x in records['opening_balances'] if x.get('_balance',0)>0]
        balance=sum(x.get('_balance',0) for x in records['invoices'] if x.get('status')=='issued' and x.get('_balance',0)>0)+sum(x['_balance'] for x in opening_due)
        if any(x in query for x in ('owe','overdue','payment','collect','receivable')):
            due=[x for x in records['invoices'] if x.get('status')=='issued' and x.get('_balance',0)>0]
            answer=f"{len(due)} issued invoices and {len(opening_due)} opening balances have {business.get('currency', 'NPR')} {balance:,.2f} outstanding. "
            answer+='Prioritise '+', '.join(x.get('number','Invoice') for x in sorted(due,key=lambda x:x.get('due_date','9999'))[:4])+'.' if due else 'Review the reconciled opening balances.' if opening_due else 'There are no outstanding issued invoices or opening balances.'
        elif any(x in query for x in ('profit','margin','earning','cost')):
            if user['role']!='owner': raise Problem('Job profitability is available to the owner.',403)
            jobs=[x for x in records['jobs'] if x.get('_revenue',0)]
            answer=f"Recorded billed jobs show {business.get('currency', 'NPR')} {sum(x['_revenue'] for x in jobs):,.2f} net revenue and {business.get('currency', 'NPR')} {sum(x['_cost'] for x in jobs):,.2f} direct costs/incentives. "
            answer+=f"Their contribution is {business.get('currency', 'NPR')} {sum(x['_contribution'] for x in jobs):,.2f}, before business overhead. {sum(x['_cost_provisional'] for x in jobs)} jobs still have provisional costs."
        elif any(x in query for x in ('stock','part','material','supplier')):
            low=[x for x in records['stock'] if x.get('_quantity',0)<=x.get('reorder_at',0)]
            answer=f"{len(low)} stock items are at or below their reorder level. "+(', '.join(x['name'] for x in low[:6])+'.' if low else 'Stock levels are above the recorded reorder points.')
        elif any(x in query for x in ('payroll','salary','staff','attendance')):
            pending=sum(x.get('status')=='pending' for x in records['attendance'])
            answer=f"There are {pending} attendance records awaiting review. "
            if 'payroll' in ROLE_READ[user['role']]: answer+=f"{sum(x.get('status')=='draft' for x in records['payroll'])} payroll runs await approval and {sum(x.get('status')=='approved' for x in records['payroll'])} approved runs await payment."
        elif any(x in query for x in ('quote','estimate','approval')):
            sent=[x for x in records['quotes'] if x.get('status')=='sent']
            answer=f"{len(sent)} quotations await a decision. Your follow-up interval is {int(business.get('quote_followup_days',3))} days. "+', '.join(x.get('number','Quote') for x in sent[:5])
        else:
            alerts=state['alerts'][:4]
            answer=f"For {business['name']}, your recorded focus is {business.get('goal') or 'keeping work moving and collecting on time'}. "
            answer+=('Next: '+'; '.join(x['title']+' - '+x['next_action'] for x in alerts)+'.') if alerts else 'There are no due actions in the current records. Review upcoming jobs, stock and unpaid invoices before taking new work.'
        return {'answer':answer,'basis':'Calculated from this business\'s local records and saved settings.','actions':state['alerts'][:5]}

    def attachment(self,user,bid,data):
        self.business_allowed(user,bid)
        with self.transaction() as conn:
            rec=self.record(conn,bid,data.get('record_id'))
            self.permitted(user,rec['type'],True)
            if user['role']=='technician' and rec['type']=='jobs' and user.get('employee_id') not in rec.get('employee_ids',[]): raise Problem('This job is not assigned to you.',403)
            try: content=base64.b64decode(data.get('content',''),validate=True)
            except Exception: raise Problem('Invalid file content.')
            if not content or len(content)>12*1024*1024: raise Problem('Choose a file smaller than 12 MB.')
            filename=Path(str(data.get('filename','attachment'))).name[:180]
            aid=identifier()
            conn.execute('INSERT INTO attachments VALUES (?,?,?,?,?,?,?,?)',(aid,bid,rec['id'],filename,
                         data.get('mime','application/octet-stream'),content,hashlib.sha256(content).hexdigest(),now()))
            self.audit(conn,user,bid,'Attached original document',rec['type'],rec['id'],filename)
        return {'id':aid,'filename':filename}

    def get_attachment(self,user,bid,aid):
        self.business_allowed(user,bid)
        with self.connect() as conn:
            row=conn.execute('SELECT * FROM attachments WHERE id=? AND business_id=?',(aid,bid)).fetchone()
            if not row: raise Problem('Attachment not found.',404)
            rec=self.record(conn,bid,row['record_id']); self.permitted(user,rec['type'])
            if user['role']=='technician' and rec['type']=='jobs' and user.get('employee_id') not in rec.get('employee_ids',[]):
                raise Problem('This job is not assigned to you.',403)
            return dict(row)

    def users(self,user):
        if user['role']!='owner': raise Problem('Only the owner can manage accounts.',403)
        with self.connect() as conn:
            return [self.user_view(dict(x))|{'business_ids':json.loads(x['business_ids']),'active':bool(x['active'])} for x in conn.execute('SELECT * FROM users WHERE organization_id=?',(user.get('organization_id','local'),))]

    def add_user(self,user,data):
        if user['role']!='owner': raise Problem('Only the owner can create accounts.',403)
        name=str(data.get('name','')).strip(); username=str(data.get('username','')).strip().lower()
        password=str(data.get('password','')); role=data.get('role','frontdesk')
        if not name or not username or not 12<=len(password)<=256 or role not in ROLE_READ or len(username)>100:
            raise Problem('Enter name, username, role and a password of 12 to 256 characters.')
        ids=data.get('business_ids',[])
        with self.transaction() as conn:
            for bid in ids: self.business_allowed(user,bid);self.business(conn,bid)
            if not ids and role!='owner': raise Problem('Choose at least one business for this account.')
            eid=data.get('employee_id','')
            if role=='technician' and (len(ids)!=1 or not eid):
                raise Problem('A technician account needs one business and a linked employee.')
            if eid: self.record(conn,ids[0],eid,'employees')
            try:
                conn.execute('INSERT INTO users(id,username,name,password,role,business_ids,employee_id,active,organization_id) VALUES (?,?,?,?,?,?,?,1,?)',(identifier(),username,name,password_hash(password),role,json.dumps(ids),eid,user.get('organization_id','local')))
            except sqlite3.IntegrityError: raise Problem('That username is already used.',409)
        return {'ok':True}

    def backup(self,automatic=False,user=None):
        folder=self.folder/'backups'; folder.mkdir(exist_ok=True)
        path=folder/('daily-'+today()+'.sqlite3' if automatic else 'backup-'+datetime.now().strftime('%Y%m%d-%H%M%S')+'-'+secrets.token_hex(3)+'.sqlite3')
        with self.lock,self.connect() as source,closing(sqlite3.connect(path)) as target:
            source.backup(target)
        if automatic:
            for old in sorted(folder.glob('daily-*.sqlite3'))[:-14]: old.unlink()
        return path

    def restore(self,user,content):
        if user['role']!='owner': raise Problem('Only the owner can restore a backup.',403)
        if not content.startswith(b'SQLite format 3\x00') or len(content)>100*1024*1024:
            raise Problem('Choose a Business Desk SQLite backup smaller than 100 MB.')
        temp=self.folder/('restore-'+identifier()+'.sqlite3')
        temp.write_bytes(content)
        try:
            with closing(sqlite3.connect(temp)) as source:
                source.execute('PRAGMA query_only=ON')
                if source.execute('PRAGMA integrity_check').fetchone()[0]!='ok': raise Problem('Backup integrity check failed.')
                if source.execute("SELECT value FROM meta WHERE key='schema'").fetchone()[0] not in ('1','2','3'): raise Problem('This backup uses an unsupported schema.')
                for name in ('records','businesses','users','audit','attachments','counters'):
                    source.execute('SELECT * FROM '+name+' LIMIT 1')
                with self.lock:
                    self.backup()
                    with self.connect() as target:
                        source.backup(target)
                        self.migrate(target)
                        target.execute("UPDATE meta SET value=? WHERE key='data_epoch'", (identifier(),))
            self.sessions.clear()
            return {'ok':True,'message':'Backup restored. Sign in with the account stored in that backup.'}
        except sqlite3.Error:
            raise Problem('This is not a valid Business Desk backup.')
        finally: temp.unlink(missing_ok=True)

    def import_legacy(self,user,bid,payload):
        self.business_allowed(user,bid); self.permitted(user,'quotes',True)
        quotes=payload if isinstance(payload,list) else payload.get('quotes',[]) if isinstance(payload,dict) else None
        if not isinstance(quotes,list) or len(quotes)>2000: raise Problem('Import a list of up to 2,000 legacy quotations.')
        imported=skipped=0
        with self.transaction() as conn:
            records=self.records(conn,bid)
            fingerprints={x.get('legacy_key') for x in records['quotes']}
            business=self.business(conn,bid)
            for q in quotes:
                if not isinstance(q,dict): raise Problem('Every imported quotation must be a JSON object.')
                fingerprint=hashlib.sha256(json.dumps(q,sort_keys=True).encode()).hexdigest()
                if fingerprint in fingerprints: skipped+=1; continue
                name=q.get('clientName') or q.get('vehicleRegNo') or 'Legacy customer'
                cust=next((x for x in records['customers'] if x.get('name')==name and x.get('address','')==q.get('clientAddress','')),None)
                if not cust:
                    cust=self.put(conn,bid,'customers',{'name':name,'address':q.get('clientAddress',''),'phone':'','notes':'Imported from the previous quotation app.'})
                    records['customers'].append(cust)
                asset=None
                if q.get('vehicleRegNo') or q.get('vehicleModel'):
                    asset=next((x for x in records['assets'] if x.get('registration')==q.get('vehicleRegNo') and x.get('customer_id')==cust['id']),None)
                    if not asset:
                        asset=self.put(conn,bid,'assets',{'name':q.get('vehicleModel') or q.get('vehicleRegNo'),'registration':q.get('vehicleRegNo',''),
                            'customer_id':cust['id'],'chassis':q.get('chassisNumber',''),'asset_type':'Vehicle'})
                        records['assets'].append(asset)
                quote={'customer_id':cust['id'],'asset_id':asset['id'] if asset else '', 'subject':q.get('subject') or q.get('name','Imported quotation'),
                    'date':today(),'bs_date':q.get('quotationDate',''),'legacy_number':q.get('quotationNumber',''),'status':'draft','revision':1,
                    'items':q.get('items',[]),'vat_mode':q.get('vatMode','added'),'vat_rate':13,'discount_percent':0,
                    'terms':'\n'.join(q.get('zainTerms',[])),'legacy_key':fingerprint,'font_size':q.get('fontSizes',{}).get('zain',10),'show_chassis':q.get('showChassis',True),
                    'notes':'Legacy import. Verify dates, parties and prices before sending.'}
                calculate(quote)
                quote_record=self.put(conn,bid,'quotes',quote)
                for key,label in [('rageeItems','Legacy scenario A'),('moonstarItems','Legacy scenario B')]:
                    if q.get(key): self.put(conn,bid,'external_quotes',{'quote_id':quote_record['id'],'issuer':label,'date':today(),
                        'items':q[key],'vat_mode':q.get('vatMode','added'),'vat_rate':13,'simulation':True,
                        'notes':'Imported generated comparison. Hypothetical; not independent third-party evidence.'})
                imported+=1; fingerprints.add(fingerprint)
            self.audit(conn,user,bid,'Imported legacy quotations','quotes','',f'{imported} imported; {skipped} duplicates skipped')
        return {'imported':imported,'skipped':skipped}

    def seed(self,conn,bid):
        """Optional fictional demo records, isolated in the new business."""
        d=date.fromisoformat(today()); business=self.business(conn,bid)
        customer=self.put(conn,bid,'customers',{'name':'Demo Fleet Services','phone':'','address':'Hetauda','customer_type':'Fleet','notes':'Fictional demo customer.'})
        second=self.put(conn,bid,'customers',{'name':'Demo Walk-in Customer','phone':'','address':'Hetauda','customer_type':'Individual'})
        vehicle=self.put(conn,bid,'assets',{'name':'Demo pickup','customer_id':customer['id'],'registration':'DEMO-001','asset_type':'Vehicle','odometer':42000,'chassis':''})
        emp=self.put(conn,bid,'employees',{'name':'Demo Technician','role':'Body technician','salary_type':'monthly','base_salary':30000,
            'hourly_cost':250,'overtime_rate':300,'shift_hours':8,'employee_percent':0,'employer_percent':0,'active':True})
        for name,rate,category,cost,unit in [('Bumper repair',4500,'Labour',1500,'job'),('Panel painting',7500,'Labour',2500,'panel'),('Polish and finish',2500,'Labour',800,'job')]:
            self.put(conn,bid,'services',{'name':name,'rate':rate,'category':category,'cost':cost,'unit':unit})
        primer=self.put(conn,bid,'stock',{'name':'Primer','sku':'DEMO-PR','unit':'ltr','opening_qty':1,'cost':900,'rate':1300,'reorder_at':2,'location':'Paint store'})
        self.put(conn,bid,'stock',{'name':'Sanding discs','sku':'DEMO-SD','unit':'pc','opening_qty':20,'cost':45,'rate':70,'reorder_at':5,'location':'Shelf A'})
        items=[{'description':'Bumper repair','qty':1,'unit':'job','rate':4500,'unit_cost':1500,'category':'Labour'},
               {'description':'Panel painting','qty':1,'unit':'panel','rate':7500,'unit_cost':2500,'category':'Labour'}]
        quote_data={'customer_id':customer['id'],'asset_id':vehicle['id'],'subject':'Front bumper and panel repair','date':(d-timedelta(days=5)).isoformat(),
            'bs_date':'','vat_mode':'added','vat_rate':business.get('vat_rate',13),'discount_percent':0,'items':items,'terms':business.get('terms',''),
            'number':self.next_number(conn,bid,'Q'),'revision':1,'status':'sent','sent_at':(datetime.now(timezone.utc)-timedelta(days=5)).isoformat(),
            'seller_snapshot':business,'customer_snapshot':customer,'asset_snapshot':vehicle}
        quote_data['totals_snapshot']=calculate(quote_data)
        self.put(conn,bid,'quotes',quote_data)
        accepted=self.put(conn,bid,'quotes',{**quote_data,'subject':'Approved demo service','status':'accepted','number':self.next_number(conn,bid,'Q'),'approved_by':'Demo customer'})
        job=self.put(conn,bid,'jobs',{'name':'Pickup bumper repair','number':self.next_number(conn,bid,'JOB'),'customer_id':customer['id'],'asset_id':vehicle['id'],
            'quote_id':accepted['id'],'stage':'Preparation','date':today(),'due_date':today(),'employee_ids':[emp['id']],
            'tasks':[{'id':identifier(),'name':'Repair bumper','done':True},{'id':identifier(),'name':'Prepare and paint panel','done':False}],
            'labor_cost':2800,'additional_material_cost':1200,'subcontract_cost':0,'blocker':'Waiting for primer delivery','costs_final':False,'notes':'Fictional demo work.'})
        invoice_data={**quote_data,'job_id':job['id'],'status':'issued','number':self.next_number(conn,bid,'INV'),'due_date':(d-timedelta(days=2)).isoformat(),'date':(d-timedelta(days=8)).isoformat()}
        invoice=self.put(conn,bid,'invoices',invoice_data)
        self.put(conn,bid,'payments',{'invoice_id':invoice['id'],'customer_id':customer['id'],'amount':5000,'direction':'receipt','method':'Bank transfer','payer':'Customer',
            'date':(d-timedelta(days=4)).isoformat(),'number':self.next_number(conn,bid,'RCT'),'reference':'DEMO-PAY-001'})
        self.put(conn,bid,'claims',{'name':'Demo collision claim','reference':'DEMO-CLAIM-001','insurer':'Demo Insurer','job_id':job['id'],'customer_id':customer['id'],
            'requested':13560,'approved':10000,'customer_share':3560,'insurer_share':10000,'status':'Awaiting settlement','due_date':today(),
            'next_action':'Confirm the settlement date and outstanding documents.'})
        self.put(conn,bid,'commissions',{'employee_id':emp['id'],'job_id':job['id'],'name':'Demo service incentive','basis_amount':12000,'percent':5,
            'fixed_amount':0,'amount':600,'status':'earned','collection_required':True,'date':today(),'notes':'5% of eligible labour revenue, excluding VAT.'})
        self.put(conn,bid,'appointments',{'name':'Inspection appointment','customer_id':second['id'],'date':today(),'time':'14:30','status':'booked','notes':'Demo appointment.'})
        self.put(conn,bid,'followups',{'name':'Check tomorrow\'s workshop capacity','date':today(),'due_date':today(),'status':'open','next_action':'Review booth and technician availability.','notes':'Demo owner task.'})

#!/usr/bin/env python3
"""Run: python3 server.py --open. No third-party packages or cloud account required."""
from __future__ import annotations

import argparse
import base64
import csv
import html
import io
import json
import mimetypes
import os
import hmac
import threading
import time
import sys
import traceback
import webbrowser
from http.cookies import SimpleCookie
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path
from urllib.parse import parse_qs, quote, urlparse

if sys.version_info < (3,10):
    raise SystemExit('Business Desk requires Python 3.10 or newer. Install it from https://www.python.org/downloads/')

from domain import Desk, Problem, calculate, today, words, password_hash, password_ok
from regional import INDIA_STATES, business_today

ROOT = Path(__file__).resolve().parent
STATIC = ROOT / 'static'
APP_VERSION = '2.3.0-rc.1'


def escaped(value):
    return html.escape(str(value if value is not None else ''), quote=True)


def cash(value):
    return f'{float(value or 0):,.2f}'


def print_document(desk, user, bid, kind, rid, style='classic', font='11'):
    desk.business_allowed(user, bid)
    desk.permitted(user, kind)
    with desk.connect() as conn:
        record = desk.record(conn, bid, rid, kind)
        if user['role']=='technician' and kind=='jobs' and user.get('employee_id') not in record.get('employee_ids',[]): raise Problem('This job is not assigned to you.',403)
        business = record.get('seller_snapshot') or desk.business(conn, bid)
        records = desk.enrich(desk.records(conn, bid))
        record = next(x for x in records[kind] if x['id'] == rid)
        customer = record.get('customer_snapshot') or next((x for x in records['customers'] if x['id'] == record.get('customer_id')), {})
        asset = record.get('asset_snapshot') or next((x for x in records['assets'] if x['id'] == record.get('asset_id')), {})
    currency = business.get('currency', 'NPR')
    indian = business.get('country') == 'IN'
    tax_label = 'GST' if indian else 'VAT'
    title = {'quotes':'QUOTATION','invoices':record.get('document_title') or ('VAT INVOICE' if record.get('vat_mode')!='none' else 'INVOICE'),
             'external_quotes':'EXTERNAL QUOTATION RECORD','payments':'REFUND VOUCHER' if record.get('direction')=='refund' else 'PAYMENT RECEIPT',
             'credits':'CREDIT NOTE','jobs':'JOB CARD','purchases':'PURCHASE ORDER','payroll':'PAYROLL REGISTER'}.get(kind)
    if not title: raise Problem('A print layout is not available for this record.')
    if style not in ('classic','compact','modern'): style='classic'
    try: size=max(8,min(16,float(font)))
    except ValueError: size=11
    warning = ''
    if record.get('status')=='draft': warning='<div class="stamp">DRAFT · Review before issuing</div>'
    if kind=='external_quotes':
        warning = '<div class="stamp">HYPOTHETICAL COMPARISON · NOT A THIRD-PARTY QUOTATION</div>' if record.get('simulation') else '<div class="stamp">TRANSCRIBED COMPARISON · See the original issuer document</div>'
    from branding import display_name
    company = ('<img class="business-logo" alt="" src="'+escaped(business['logo_data'])+'">' if business.get('logo_data') else '')+'<h1>'+escaped(display_name(business))+'</h1><p>'+escaped(business.get('address',''))+'</p><p>'+escaped(business.get('phone',''))+' '+escaped(business.get('email',''))+'</p><p>'+('GSTIN: '+escaped(business.get('gstin','—')) if indian else 'PAN / VAT: '+escaped(business.get('pan','—')))+'</p>'
    if business.get('trading_name') and business['trading_name']!=business.get('name'): company+='<p>Legal name: '+escaped(business['name'])+'</p>'
    if kind=='external_quotes': company='<h1>'+escaped(record.get('issuer','Comparison scenario'))+'</h1><p>Reference recorded by '+escaped(business.get('name'))+'</p>'
    heading = '<header><div>'+company+'</div><div class="document"><h2>'+title+'</h2><p>'+escaped(record.get('number') or record.get('reference') or 'Unnumbered draft')+'</p><p>AD: '+escaped(record.get('date') or business_today(business))+'</p>'
    if record.get('bs_date'): heading+='<p>BS: '+escaped(record['bs_date'])+' (entered)</p>'
    if record.get('financial_year'): heading+='<p>Financial year: '+escaped(record['financial_year'][:2]+'–'+record['financial_year'][2:])+'</p>'
    if business.get('fiscal_label'): heading+='<p>Fiscal year: '+escaped(business['fiscal_label'])+'</p>'
    if record.get('revision'): heading+='<p>Revision '+escaped(record['revision'])+'</p>'
    heading+='</div></header>'
    context='<section class="context"><div><b>'+('Supplier' if kind=='purchases' else 'Customer')+'</b><p>'+escaped(customer.get('name',''))+'</p><p>'+escaped(customer.get('address',''))+'</p><p>'+escaped(customer.get('phone',''))+'</p><p>'+('PAN: '+escaped(customer['pan']) if customer.get('pan') else '')+'</p></div><div>'
    if kind=='purchases':
        supplier=next((x for x in records['suppliers'] if x['id']==record.get('supplier_id')), {})
        context='<section class="context"><div><b>Supplier</b><p>'+escaped(supplier.get('name',''))+'</p><p>'+escaped(supplier.get('address',''))+'</p><p>'+escaped(supplier.get('phone',''))+'</p></div><div>'
    context+='<b>'+escaped(record.get('subject') or record.get('name') or '')+'</b><p>'+escaped(asset.get('name',''))+'</p>'
    if asset.get('registration'): context+='<p>Registration / ID: '+escaped(asset['registration'])+'</p>'
    if asset.get('chassis') and record.get('show_chassis',True): context+='<p>Chassis / Serial: '+escaped(asset['chassis'])+'</p>'
    if record.get('due_date'): context+='<p>Due: '+escaped(record['due_date'])+'</p>'
    if indian:
        context+='<p>GSTIN: '+escaped(customer.get('gstin') or 'Unregistered')+'</p><p>Place of supply: '+escaped(record.get('place_of_supply', business.get('state_code','')))+' · '+escaped(INDIA_STATES.get(record.get('place_of_supply', business.get('state_code','')), ''))+'</p><p>Reverse charge: No · Domestic forward charge</p>'
        if business.get('gst_registration') == 'composition': context+='<p>Composition taxable person, not eligible to collect tax on supplies.</p>'
    context+='</div></section>'
    rows=''; totals=''; extra=''
    if kind in ('quotes','invoices','external_quotes'):
        computed=record['_totals']
        for i,x in enumerate(computed['lines'],1):
            rows+='<tr><td>'+str(i)+'</td><td class="description">'+escaped(x['description'])+('<br><small>HSN / SAC: '+escaped(x.get('hsn_sac',''))+'</small>' if indian else '')+'</td><td>'+escaped(x['qty'])+'</td><td>'+escaped(x.get('unit','pc'))+'</td><td class="num">'+cash(x['rate'])+'</td><td class="num">'+cash(x['discount_amount'])+'</td><td class="num">'+cash(x['net'])+'</td><td class="num">'+(escaped(x.get('tax_rate',0))+'% / ' if indian else '')+cash(x['tax'])+'</td><td class="num">'+cash(x['total'])+'</td></tr>'
        table='<table><thead><tr><th>#</th><th>Description</th><th>Qty</th><th>Unit</th><th>Rate</th><th>Discount</th><th>Net</th><th>'+tax_label+' rate / amount</th><th>Total</th></tr></thead><tbody>'+rows+'</tbody></table>'
        totals='<div class="totals"><p><span>Net amount</span><b>'+currency+' '+cash(computed['net'])+'</b></p><p><span>'+tax_label+' ('+escaped(record.get('vat_mode','added'))+')</span><b>'+currency+' '+cash(computed['tax'])+'</b></p><p class="grand"><span>Total</span><b>'+currency+' '+cash(computed['total'])+'</b></p>'
        for component, value in computed.get('tax_components', {}).items():
            totals+='<p><span>'+escaped(component)+'</span><b>'+currency+' '+cash(value)+'</b></p>'
        if kind=='invoices' and record.get('status')=='issued':
            totals+='<p><span>Credits</span><b>'+cash(record['_credited'])+'</b></p><p><span>Net receipts / allocations</span><b>'+cash(record['_paid'])+'</b></p><p><span>Outstanding / (credit)</span><b>'+currency+' '+cash(record['_balance'])+'</b></p>'
        totals+='</div><p class="words">'+escaped(computed['words'])+'</p>'
        if kind=='quotes' and record.get('status')=='accepted': extra='<p>Approval recorded: '+escaped(record.get('approved_by',''))+' · '+escaped(record.get('approval_channel',''))+' · '+escaped(record.get('decision_at',''))+'</p>'
    elif kind=='payroll':
        context='<section class="context"><p>Pay period: '+escaped(record['start_date'])+' to '+escaped(record['end_date'])+' · '+escaped(record['status'])+'</p></section>'
        for x in record['lines']:
            rows+='<tr><td>'+escaped(x['name'])+'</td><td class="num">'+cash(x['base'])+'</td><td class="num">'+cash(x['overtime']+x['bonus']+x['commission'])+'</td><td class="num">'+cash(x['gross'])+'</td><td class="num">'+cash(x['withholding']+x['deductions']+x['employee_contribution'])+'</td><td class="num">'+cash(x['net'])+'</td><td class="num">'+cash(x['employer_cost'])+'</td></tr>'
        table='<table><thead><tr><th>Employee</th><th>Base</th><th>OT / bonus / incentives</th><th>Gross</th><th>Deductions</th><th>Net pay</th><th>Employer cost</th></tr></thead><tbody>'+rows+'</tbody></table>'
        totals='<div class="totals"><p class="grand"><span>Net payroll</span><b>'+currency+' '+cash(record['total_net'])+'</b></p><p><span>Employer cost</span><b>'+currency+' '+cash(record['total_cost'])+'</b></p></div>'
        extra='<p>Rates, pay units and withholding are configured and reviewed by the owner. This register does not calculate statutory payroll tax automatically.</p>'
    elif kind=='jobs':
        for x in record.get('tasks',[]): rows+='<tr><td>'+('✓' if x.get('done') else '☐')+'</td><td>'+escaped(x.get('name',''))+'</td></tr>'
        table='<p><b>Stage:</b> '+escaped(record.get('stage',''))+' <b>Blocker:</b> '+escaped(record.get('blocker',''))+'</p><table><thead><tr><th>Done</th><th>Work / quality checklist</th></tr></thead><tbody>'+rows+'</tbody></table>'
        names=[x['name'] for x in records['employees'] if x['id'] in record.get('employee_ids',[])]
        extra='<p>Assigned: '+escaped(', '.join(names))+'</p>'
    elif kind=='purchases':
        for x in record['items']:
            item=next((y for y in records['stock'] if y['id']==x['item_id']),{})
            rows+='<tr><td>'+escaped(item.get('name','Item'))+'</td><td>'+escaped(x['qty'])+'</td><td class="num">'+cash(x['cost'])+'</td><td class="num">'+cash(float(x['qty'])*float(x['cost']))+'</td></tr>'
        table='<table><thead><tr><th>Stock item</th><th>Quantity</th><th>Unit cost</th><th>Amount</th></tr></thead><tbody>'+rows+'</tbody></table>'
        totals='<div class="totals"><p class="grand"><span>Order total (before supplier tax)</span><b>'+currency+' '+cash(record['total'])+'</b></p></div>'
    else:
        invoice=next((x for x in records['invoices'] if x['id']==record.get('invoice_id')), {})
        table='<table><tbody><tr><th>Linked invoice</th><td>'+escaped(invoice.get('number') or 'Unapplied customer advance')+'</td></tr>'
        if kind=='payments': table+='<tr><th>Method / reference</th><td>'+escaped(record.get('method',''))+' · '+escaped(record.get('reference',''))+'</td></tr>'
        else: table+='<tr><th>Reason</th><td>'+escaped(record.get('reason',''))+'</td></tr><tr><th>Net / tax credit</th><td>'+currency+' '+cash(record.get('net'))+' / '+cash(record.get('tax'))+'</td></tr>'
        table+='</tbody></table>'
        if kind == 'credits' and record.get('return_lines'):
            table+='<table><thead><tr><th>Credited item / HSN</th><th>Quantity</th><th>Net</th><th>Tax</th></tr></thead><tbody>'+''.join('<tr><td>'+escaped(x['description'])+' · '+escaped(x.get('hsn_sac',''))+'</td><td>'+escaped(x['qty'])+'</td><td>'+cash(x['net'])+'</td><td>'+cash(x['tax'])+'</td></tr>' for x in record['return_lines'])+'</tbody></table>'
            table+='<p>'+escaped(' · '.join(k+': '+cash(v) for k,v in record.get('tax_components',{}).items()))+'</p>'
        totals='<div class="totals"><p class="grand"><span>Amount</span><b>'+currency+' '+cash(record['amount'])+'</b></p></div><p class="words">'+escaped(words(record['amount']))+'</p>'
    terms=record.get('terms','')
    tail='<section class="notes">'+('<h3>Terms</h3><p>'+escaped(terms).replace('\n','<br>')+'</p>' if terms else '')+('<h3>Notes</h3><p>'+escaped(record['notes']).replace('\n','<br>')+'</p>' if record.get('notes') else '')+extra+'</section>'
    if kind in ('quotes','invoices','payments','credits'):
        tail+='<section class="notes">'+('<p>'+escaped(business.get('payment_instructions')).replace('\n','<br>')+'</p>' if business.get('payment_instructions') else '')+('<p>'+escaped(business.get('invoice_footer')).replace('\n','<br>')+'</p>' if business.get('invoice_footer') else '')+'</section>'
    return ('<!doctype html><html><head><meta charset="utf-8"><meta name="viewport" content="width=device-width, initial-scale=1"><title>'+escaped(title+' '+record.get('number',''))+'</title><link rel="stylesheet" href="/print.css"><style>:root{--print-size:'+str(size)+'pt}</style></head><body class="'+style+'"><nav class="printbar"><button id="print-button">Print / Save PDF</button><span>A4 · Review printer margins and preview before saving.</span></nav><main>'+warning+heading+context+table+totals+tail+'<footer><div>Prepared / authorised by<br><br>________________________</div><div>Customer / recipient<br><br>________________________</div></footer></main><script src="/print.js"></script></body></html>').encode()


class Handler(BaseHTTPRequestHandler):
    server_version = 'BusinessDesk'

    @property
    def desk(self): return self.server.desk

    def log_message(self, fmt, *args):
        if args and str(args[0]).startswith('GET /api/health'): return
        sys.stderr.write('[local] '+(fmt % args)+'\n')

    def headers_out(self, status, mime, length, extra=None):
        self.send_response(status)
        self.send_header('Content-Type', mime)
        self.send_header('Content-Length', str(length))
        self.send_header('Cache-Control', 'no-store')
        self.send_header('X-Content-Type-Options', 'nosniff')
        self.send_header('Referrer-Policy', 'same-origin')
        self.send_header('Permissions-Policy', 'camera=(), microphone=(), geolocation=()')
        if getattr(self.server, 'public_origin', '').startswith('https://'):
            self.send_header('Strict-Transport-Security', 'max-age=31536000')
        self.send_header('Content-Security-Policy', "default-src 'self'; script-src 'self'; style-src 'self' 'unsafe-inline'; img-src 'self' data:; connect-src 'self'; frame-ancestors 'none'; object-src 'none'; base-uri 'none'; form-action 'self'")
        for key, value in (extra or {}).items(): self.send_header(key,value)
        self.end_headers()

    def respond(self, value, status=200, extra=None):
        body=json.dumps(value,ensure_ascii=False,allow_nan=False).encode()
        self.headers_out(status,'application/json; charset=utf-8',len(body),extra)
        self.wfile.write(body)

    def binary(self, body, mime, filename=None):
        extra={'Content-Disposition':"attachment; filename*=UTF-8''"+quote(filename)} if filename else None
        self.headers_out(200,mime,len(body),extra)
        self.wfile.write(body)

    def check_origin(self):
        host=self.headers.get('Host','')
        allowed={f'127.0.0.1:{self.server.server_port}',f'localhost:{self.server.server_port}'}
        public_origin = getattr(self.server, 'public_origin', '')
        if public_origin:
            allowed = {urlparse(public_origin).netloc}
        if host not in allowed: raise Problem('Use the configured Business Desk address.',403)
        origin=self.headers.get('Origin')
        origins = {public_origin} if public_origin else {'http://'+x for x in allowed}
        if origin and origin not in origins: raise Problem('This request did not come from this app.',403)
        if self.headers.get('Sec-Fetch-Site') == 'cross-site': raise Problem('Cross-site requests are not allowed.',403)

    def session_cookie(self, token, age=43200):
        secure = '; Secure' if getattr(self.server, 'public_origin', '').startswith('https://') else ''
        return 'desk_session=' + token + '; HttpOnly; SameSite=Strict; Path=/; Max-Age=' + str(age) + secure

    def token(self):
        cookie=SimpleCookie()
        try: cookie.load(self.headers.get('Cookie',''))
        except Exception: return ''
        return cookie['desk_session'].value if 'desk_session' in cookie else ''

    def user(self, write=False):
        user,csrf=self.desk.session(self.token())
        if write and self.headers.get('X-CSRF-Token')!=csrf: raise Problem('Session verification failed. Refresh the page.',403)
        return user

    def body(self):
        if not self.headers.get('Content-Type','').startswith('application/json'): raise Problem('JSON content is required.',415)
        try: length=int(self.headers.get('Content-Length','0'))
        except ValueError: raise Problem('Invalid request length.')
        limit=getattr(self.server,'max_request_bytes',145*1024*1024 if self.path=='/api/restore' else 18*1024*1024)
        if length<0 or length>limit: raise Problem('The uploaded data is too large.',413)
        try:
            data=json.loads(self.rfile.read(length))
            if not isinstance(data,dict): raise ValueError()
            return data
        except (ValueError,UnicodeDecodeError): raise Problem('Invalid JSON request.')

    def do_GET(self): self.dispatch(False)
    def do_POST(self): self.dispatch(True)

    def dispatch(self, write):
        try:
            self.check_origin()
            parsed=urlparse(self.path); path=parsed.path; query=parse_qs(parsed.query)
            get=lambda key,default='':query.get(key,[default])[0]
            if path=='/api/health' and not write:
                result={'version':APP_VERSION,'setup_required':not self.desk.has_users(),'today':today(),'india_states':INDIA_STATES}
                result.update(hosted=bool(getattr(self.server, 'public_origin', '')), setup_key_required=bool(getattr(self.server, 'setup_key', '')))
                result.update(cloud=bool(getattr(self.desk,'cloud',False)), registration_enabled=bool(getattr(self.server,'registration_enabled',False)))
                try:
                    user,csrf=self.desk.session(self.token()); result.update(user=self.desk.user_view(user),csrf=csrf)
                except Problem: pass
                return self.respond(result)
            if path in ('/api/setup','/api/login') and write:
                limiter = getattr(self.server, 'auth_limiter', None)
                if limiter: limiter(self.client_address[0])
                data=self.body()
                if path.endswith('setup') and getattr(self.server, 'setup_key', ''):
                    if not hmac.compare_digest(str(data.get('setup_key', '')), self.server.setup_key):
                        raise Problem('Enter the server setup key provided by the administrator.',403)
                token,result=(self.desk.setup if path.endswith('setup') else self.desk.login)(data)
                return self.respond(result,extra={'Set-Cookie':self.session_cookie(token)})
            if path.startswith('/api/') or path=='/print':
                user=self.user(write)
                data=self.body() if write else {}
                bid=data.get('business_id') if write else get('business')
                if path=='/api/logout' and write:
                    self.desk.sessions.pop(self.token(),None)
                    return self.respond({'ok':True},extra={'Set-Cookie':self.session_cookie('', 0)})
                if path=='/api/businesses': return self.respond(self.desk.save_business(user,data) if write else self.desk.businesses(user))
                if path=='/api/portfolio' and not write: return self.respond(self.desk.portfolio(user,get('offset') or 0))
                if path=='/api/state' and not write: return self.respond(self.desk.state(user,bid))
                if path=='/api/calculate' and write: return self.respond(calculate(data.get('data',{})))
                if path=='/api/command' and write: return self.respond(self.desk.command(user,data))
                if write and getattr(self.server, 'public_origin', '') and path in ('/api/record','/api/action','/api/archive','/api/time','/api/payroll'):
                    raise Problem('Refresh the app to use retry-safe commands.', 400)
                if path=='/api/record' and write: return self.respond(self.desk.save(user,bid,data.get('kind'),data))
                if path=='/api/action' and write: return self.respond(self.desk.action(user,bid,data.get('kind'),data.get('id'),data))
                if path=='/api/archive' and write:
                    self.desk.archive(user,bid,data.get('kind'),data.get('id'),data.get('version'))
                    return self.respond({'ok':True})
                if path=='/api/time' and write: return self.respond(self.desk.time_action(user,bid,data))
                if path=='/api/payroll' and write: return self.respond(self.desk.prepare_payroll(user,bid,data))
                if path=='/api/assistant' and write: return self.respond(self.desk.assistant(user,bid,str(data.get('question',''))[:2000]))
                if path=='/api/import-preview' and write: return self.respond(self.desk.import_batch(user,bid,data,preview=True))
                if path=='/api/customer-statement' and not write: return self.respond(self.desk.customer_statement(user,bid,get('customer')))
                if path=='/api/attachment' and write: return self.respond(self.desk.attachment(user,bid,data))
                if path=='/api/attachment' and not write:
                    item=self.desk.get_attachment(user,bid,get('id'))
                    return self.binary(item['content'],'application/octet-stream',item['filename'])
                if path=='/api/users': return self.respond(self.desk.add_user(user,data) if write else self.desk.users(user))
                if path=='/api/account' and write: return self.respond(self.update_account(user,data))
                if path=='/api/backup' and write:
                    if user['role']!='owner': raise Problem('Only the owner can download the complete backup.',403)
                    file=self.desk.backup(user=user)
                    try: return self.binary(file.read_bytes(),'application/json' if file.suffix=='.json' else 'application/vnd.sqlite3',file.name)
                    finally:
                        if getattr(self.desk,'cloud',False): file.unlink(missing_ok=True)
                if path=='/api/restore' and write:
                    try: content=base64.b64decode(data.get('content',''),validate=True)
                    except Exception: raise Problem('Invalid backup content.')
                    return self.respond(self.desk.restore(user,content))
                if path=='/api/import' and write:
                    if user['role']!='owner': raise Problem('Only the owner can import legacy data.',403)
                    return self.respond(self.desk.import_legacy(user,bid,data.get('quotes',[])))
                if path=='/api/export' and not write: return self.export(user,bid,get('format','json'),get('kind','invoices'))
                if path=='/print' and not write:
                    body=print_document(self.desk,user,bid,get('kind'),get('id'),get('style','classic'),get('font','11'))
                    if get('bundle')=='1' and get('kind')=='quotes':
                        state=self.desk.state(user,bid)
                        extras=[x for x in state['records']['external_quotes'] if x.get('quote_id')==get('id')]
                        additional=''.join('<main>'+print_document(self.desk,user,bid,'external_quotes',x['id'],get('style','classic'),get('font','11')).decode().split('<main>',1)[1].split('</main>',1)[0]+'</main>' for x in extras)
                        if additional: body=body.decode().replace('</main>','</main>'+additional,1).replace('<body class="','<body class="bundle ',1).replace('</head>','<link rel="stylesheet" href="/bundle.css"></head>',1).encode()
                    return self.binary(body,'text/html; charset=utf-8')
                raise Problem('This endpoint does not exist.',404)
            if write: raise Problem('This endpoint does not exist.',404)
            if path=='/manifest.webmanifest' and get('business'):
                from branding import manifest
                user=self.user();bid=get('business');self.desk.business_allowed(user,bid)
                with self.desk.connect() as conn: business=self.desk.business(conn,bid)
                return self.binary(json.dumps(manifest(business),ensure_ascii=False).encode(),'application/manifest+json')
            requested='index.html' if path=='/' else path.lstrip('/')
            file=(STATIC/requested).resolve()
            if not file.is_relative_to(STATIC.resolve()) or not file.is_file(): raise Problem('File not found.',404)
            body=file.read_bytes(); self.binary(body,(mimetypes.guess_type(file.name)[0] or 'application/octet-stream')+'; charset=utf-8')
        except Problem as error: self.respond({'error':str(error)},error.status)
        except (BrokenPipeError,ConnectionResetError): pass
        except Exception:
            traceback.print_exc()
            self.respond({'error':'The operation could not be confirmed. Retry the same operation in Sync before entering it again.' if getattr(self.desk,'cloud',False) else 'The operation could not be completed. Your saved records were retained. See the local server window for details.'},503 if getattr(self.desk,'cloud',False) else 500)

    def update_account(self,user,data):
        target=data.get('id') or user['id']
        if target!=user['id'] and user['role']!='owner': raise Problem('Only the owner can manage another account.',403)
        with self.desk.transaction() as conn:
            row=conn.execute('SELECT * FROM users WHERE id=?',(target,)).fetchone()
            if not row or row['organization_id']!=user.get('organization_id','local'): raise Problem('Account not found in your organisation.',404)
            if data.get('password'):
                if target==user['id'] and not password_ok(str(data.get('current_password','')),row['password']): raise Problem('Current password is incorrect.')
                if not 12<=len(str(data['password']))<=256: raise Problem('Use a password of 12 to 256 characters.')
                conn.execute('UPDATE users SET password=? WHERE id=?',(password_hash(str(data['password'])),target))
            if 'active' in data:
                if user['role']!='owner' or target==user['id']: raise Problem('You cannot disable your own account.')
                conn.execute('UPDATE users SET active=? WHERE id=?',(int(bool(data['active'])),target))
        self.desk.invalidate_sessions(target,self.token())
        return {'ok':True}

    def export(self,user,bid,fmt,kind):
        state=self.desk.state(user,bid)
        if fmt=='json':
            output={'format':'business-desk-record-export-v1','exported_on':today(),'business':state['business'],'records':state['records']}
            return self.binary(json.dumps(output,ensure_ascii=False,indent=2).encode(),'application/json',f'business-desk-export-{today()}.json')
        self.desk.permitted(user,kind)
        rows=state['records'].get(kind,[])
        keys=list(dict.fromkeys(k for row in rows for k in row if not isinstance(row[k],(dict,list))))
        stream=io.StringIO(newline=''); writer=csv.DictWriter(stream,fieldnames=keys)
        writer.writeheader()
        for row in rows:
            clean={}
            for key in keys:
                value=row.get(key,'')
                if isinstance(value,str) and value.startswith(('=','+','-','@','\t','\r')): value="'"+value
                clean[key]=value
            writer.writerow(clean)
        self.binary(('\ufeff'+stream.getvalue()).encode(),'text/csv; charset=utf-8',f'{kind}-{today()}.csv')


def main():
    parser=argparse.ArgumentParser(description='Business Desk local app. Open the printed localhost URL in your browser.')
    parser.add_argument('--port',type=int,default=8765)
    parser.add_argument('--data-dir',type=Path,default=ROOT/'data')
    parser.add_argument('--open',action='store_true',help='Open the app in the default browser')
    args=parser.parse_args()
    try: server=ThreadingHTTPServer(('127.0.0.1',args.port),Handler)
    except OSError as error:
        print(f'Cannot start on port {args.port}: {error}. Try --port 8766.',file=sys.stderr); return 1
    server.desk=Desk(args.data_dir)
    stop_backups = start_backup_worker(server.desk)
    url=f'http://127.0.0.1:{server.server_port}'
    print(f'Business Desk {APP_VERSION}\nOpen {url}\nData: {server.desk.path}\nKeep this window open. Press Ctrl+C to stop.',flush=True)
    if args.open: webbrowser.open(url)
    try: server.serve_forever()
    except KeyboardInterrupt: print('\nBusiness Desk stopped. Records are saved locally.')
    finally:
        stop_backups.set()
        server.server_close()
    return 0


def start_backup_worker(desk):
    stop = threading.Event()
    def run():
        while not stop.wait(60):
            if desk.has_users() and not (desk.folder / 'backups' / ('daily-' + today() + '.sqlite3')).exists():
                try: desk.backup(automatic=True)
                except Exception: traceback.print_exc()
    threading.Thread(target=run, name='daily-backup', daemon=True).start()
    return stop


class AuthLimiter:
    def __init__(self):
        self.lock = threading.Lock()
        self.attempts = {}

    def __call__(self, ip):
        current = time.monotonic()
        with self.lock:
            self.attempts = {key: stamps for key, stamps in self.attempts.items() if stamps[-1] > current - 300}
            stamps = [stamp for stamp in self.attempts.get(ip, []) if stamp > current - 300]
            if len(stamps) >= 30 or len(self.attempts) >= 10000:
                raise Problem('Too many sign-in attempts. Try again in five minutes.',429)
            self.attempts[ip] = stamps + [current]


if __name__=='__main__': sys.exit(main())

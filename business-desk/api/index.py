"""Vercel WSGI boundary. DATABASE_URL missing/unreachable => 503, never local SQLite."""
import gzip
import io
import json
import logging
import os
from email.message import Message
from pathlib import Path
from threading import Lock
from types import SimpleNamespace
from urllib.parse import parse_qs, urlparse
import re
import sys
sys.path.insert(0,str(Path(__file__).resolve().parents[1]))
from server import Handler

_desk=None
_init_lock=Lock()


class WSGIHandler(Handler):
    def send_response(self,status,message=None): self.status=status
    def send_header(self,key,value): self.output_headers.append((key,value))
    def end_headers(self): pass
    def log_message(self,*args): pass


def allowed_origin(environ):
    configured=os.environ.get('DESK_PUBLIC_ORIGIN','').rstrip('/')
    parsed=urlparse(configured)
    if (parsed.scheme!='https' or not parsed.hostname or not re.fullmatch(r'[a-zA-Z0-9.-]+',parsed.hostname)
        or parsed.path or parsed.query or parsed.fragment or parsed.username or parsed.port not in (None,443)):
        raise RuntimeError('Set the canonical HTTPS DESK_PUBLIC_ORIGIN.')
    known={configured}
    # Preview must explicitly opt in; a random Host header is never trusted.
    if os.environ.get('DESK_ALLOW_PREVIEW')=='true' and os.environ.get('VERCEL_ENV')!='production':
        for key in ('VERCEL_URL','VERCEL_BRANCH_URL'):
            value=os.environ.get(key,'')
            if value and value.endswith('.vercel.app'): known.add('https://'+value)
    host=environ.get('HTTP_HOST','')
    return next((origin for origin in known if urlparse(origin).netloc==host),configured)


def application(environ,start_response):
    global _desk
    try:
        origin=allowed_origin(environ)
        setup_key=os.environ.get('DESK_SETUP_KEY','')
        if len(setup_key)<32: raise RuntimeError('Set a private pilot setup key of at least 32 characters.')
        email_auth=None
        if os.environ.get('DESK_EMAIL_AUTH','false')=='true':
            from cloud_auth import SupabaseEmailAuth
            email_auth=SupabaseEmailAuth(os.environ.get('SUPABASE_URL',''),os.environ.get('SUPABASE_PUBLISHABLE_KEY',''))
        with _init_lock:
            if _desk is None:
                from cloud import CloudDesk
                _desk=CloudDesk(os.environ.get('DATABASE_URL',''),pool_size=int(os.environ.get('DESK_DB_POOL_SIZE','1')),
                    schema=os.environ.get('DESK_DB_SCHEMA','public'))
        if email_auth and not _desk.email_ready:raise RuntimeError('Apply the reviewed email identity migration first.')
        _desk.local.organization_id='anonymous'
        raw_query=environ.get('QUERY_STRING','');query=parse_qs(raw_query)
        path=query.pop('desk_path',[environ.get('PATH_INFO','/')])[0]
        if not (path.startswith('/api/') or path in ('/print','/manifest.webmanifest')): path='/__unknown__'
        # Preserve all original query parameters except the internal rewrite.
        from urllib.parse import urlencode
        full_path=path+('?' + urlencode(query,doseq=True) if query else '')
        handler=WSGIHandler.__new__(WSGIHandler)
        handler.server=SimpleNamespace(desk=_desk,public_origin=origin,server_port=443,
            setup_key=setup_key,registration_enabled=os.environ.get('DESK_REGISTRATION_ENABLED','false')=='true',
            email_auth=email_auth,
            auth_limiter=lambda ip:_desk.auth_limit('ip:'+ip),max_request_bytes=3_900_000)
        handler.headers=Message()
        for key,value in environ.items():
            if key.startswith('HTTP_'): handler.headers[key[5:].replace('_','-')]=str(value)
        for key in ('CONTENT_TYPE','CONTENT_LENGTH'):
            if key in environ: handler.headers[key.replace('_','-')]=str(environ[key])
        handler.path=full_path;handler.command=environ.get('REQUEST_METHOD','GET');handler.client_address=(environ.get('REMOTE_ADDR','unknown'),0)
        handler.rfile=environ.get('wsgi.input',io.BytesIO());handler.wfile=io.BytesIO();handler.output_headers=[];handler.status=500
        if path=='/api/setup' and not handler.server.registration_enabled:
            handler.respond({'error':'New business registration is closed. Ask the administrator for access.'},403)
        elif handler.command not in ('GET','POST'):
            handler.respond({'error':'Method not allowed.'},405,{'Allow':'GET, POST'})
        else: handler.dispatch(handler.command=='POST')
        body=handler.wfile.getvalue();headers=handler.output_headers
        if len(body)>2048 and 'gzip' in environ.get('HTTP_ACCEPT_ENCODING',''):
            body=gzip.compress(body,compresslevel=5)
            headers=[(k,v) for k,v in headers if k.lower()!='content-length']+[('Content-Encoding','gzip'),('Vary','Accept-Encoding'),('Content-Length',str(len(body)))]
        from http import HTTPStatus
        start_response(f'{handler.status} {HTTPStatus(handler.status).phrase}',headers)
        return [body]
    except Exception as error:
        logging.error('Business Desk hosted request failed (%s)',type(error).__name__)
        body=json.dumps({'error':'The hosted service is temporarily unavailable. Please retry. No local database is used as a fallback.'}).encode()
        start_response('503 Service Unavailable',[('Content-Type','application/json'),('Cache-Control','no-store'),('Retry-After','10'),('Content-Length',str(len(body)))])
        return [body]
    finally:
        if _desk is not None: _desk.local.organization_id='anonymous'

app=application

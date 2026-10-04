"""Private-server WSGI entry point. Run behind an HTTPS reverse proxy.

One process per customer organisation: SQLite, session state, and the backup
worker stay together. Waitress bounds concurrent requests; never expose the
standard-library development server to the internet.
"""
import io
import os
from email.message import Message
from http import HTTPStatus
from pathlib import Path
from types import SimpleNamespace
from urllib.parse import urlsplit

from domain import Desk
from server import Handler, AuthLimiter, start_backup_worker


class WSGIHandler(Handler):
    def __init__(self, environ, configuration):
        self.server = configuration
        self.command = environ['REQUEST_METHOD']
        self.path = environ.get('PATH_INFO', '/')
        if environ.get('QUERY_STRING'):
            self.path += '?' + environ['QUERY_STRING']
        self.client_address = (environ.get('REMOTE_ADDR', ''), 0)
        self.headers = Message()
        for name, value in environ.items():
            if name.startswith('HTTP_'):
                self.headers[name[5:].replace('_', '-')] = value
        for name in ('CONTENT_TYPE', 'CONTENT_LENGTH'):
            if environ.get(name):
                self.headers[name.replace('_', '-')] = environ[name]
        self.rfile = environ['wsgi.input']
        self.wfile = io.BytesIO()
        self.response_headers = []
        self.response_status = 200

    def send_response(self, code, message=None):
        self.response_status = code

    def send_header(self, keyword, value):
        self.response_headers.append((keyword, value))

    def end_headers(self):
        pass


def create_app(data_dir, origin, setup_key):
    parsed = urlsplit(origin)
    if parsed.scheme != 'https' or not parsed.netloc or parsed.path or parsed.query or parsed.fragment or parsed.username or any(c.isspace() for c in origin):
        raise ValueError('DESK_PUBLIC_ORIGIN must be an HTTPS origin without a path, e.g. https://desk.example.com')
    if len(setup_key) < 32:
        raise ValueError('DESK_SETUP_KEY must contain at least 32 characters. Generate it with deploy/configure.py.')
    configuration = SimpleNamespace(desk=Desk(data_dir), public_origin=origin, setup_key=setup_key,
                                    server_port=8080, auth_limiter=AuthLimiter())
    def application(environ, start_response):
        handler = WSGIHandler(environ, configuration)
        if handler.command not in ('GET', 'POST', 'HEAD'):
            handler.respond({'error':'Method not allowed.'}, 405, {'Allow':'GET, POST, HEAD'})
        else:
            handler.dispatch(handler.command == 'POST')
        status = f'{handler.response_status} {HTTPStatus(handler.response_status).phrase}'
        start_response(status, handler.response_headers)
        return [] if handler.command == 'HEAD' else [handler.wfile.getvalue()]
    application.configuration = configuration
    return application


def main():
    from waitress import serve
    os.umask(0o077)
    app = create_app(Path(os.environ.get('DESK_DATA_DIR', './data')),
                     os.environ.get('DESK_PUBLIC_ORIGIN', ''), os.environ.get('DESK_SETUP_KEY', ''))
    stop = start_backup_worker(app.configuration.desk)
    proxy = os.environ.get('DESK_TRUSTED_PROXY')
    options = dict(host=os.environ.get('DESK_BIND', '127.0.0.1'), port=int(os.environ.get('PORT', '8080')),
                   threads=8, channel_timeout=30, connection_limit=100, max_request_body_size=145*1024*1024,
                   clear_untrusted_proxy_headers=True, expose_tracebacks=False)
    if proxy:
        options.update(trusted_proxy=proxy, trusted_proxy_count=1, trusted_proxy_headers={'x-forwarded-for'})
    try:
        serve(app, **options)
    finally:
        stop.set()


if __name__ == '__main__':
    main()

"""Optional Supabase verified-email bridge; no provider tokens reach the browser.

Identity comes only from Supabase's authenticated /user response. Application
roles and organisation membership come from the private Business Desk database.
"""
import base64
import json
import re
from urllib.error import HTTPError, URLError
from urllib.parse import urlsplit
from urllib.request import Request, urlopen, build_opener, HTTPRedirectHandler
from uuid import UUID

from domain import Problem


def normal_email(value):
    email = str(value or '').strip().lower()
    if len(email) > 254 or not re.fullmatch(r"[^\s@\x00-\x1f]+@[^\s@\x00-\x1f]+\.[^\s@\x00-\x1f]+", email):
        raise Problem('Enter a valid email address.')
    return email


class NoRedirect(HTTPRedirectHandler):
    def redirect_request(self, req, fp, code, msg, headers, newurl): return None


class SupabaseEmailAuth:
    def __init__(self, url, key):
        parsed = urlsplit(url)
        if (parsed.scheme != 'https' or not re.fullmatch(r'[a-z0-9-]+\.supabase\.co', parsed.hostname or '')
            or parsed.path not in ('', '/') or parsed.query or parsed.fragment or parsed.username
            or parsed.port not in (None, 443)):
            raise ValueError('SUPABASE_URL must be the intended project HTTPS URL.')
        if not key.startswith('sb_publishable_'):
            try:
                payload = key.split('.')[1]
                claims = json.loads(base64.urlsafe_b64decode(payload + '=' * (-len(payload) % 4)))
                if not isinstance(claims,dict) or claims.get('role') != 'anon': raise ValueError()
            except (ValueError, IndexError, TypeError):
                raise ValueError('Use a Supabase publishable key or legacy anon key; never a secret/service-role key.') from None
        if len(key) < 20 or any(c.isspace() for c in key): raise ValueError('Set a valid Supabase publishable key.')
        self.url, self.key = url.rstrip('/') + '/auth/v1', key
        self.opener = build_opener(NoRedirect())

    def request(self, endpoint, data=None, token=''):
        headers = {'apikey': self.key, 'Accept': 'application/json', 'Content-Type': 'application/json'}
        if token: headers['Authorization'] = 'Bearer ' + token
        req = Request(self.url + endpoint, data=json.dumps(data).encode() if data is not None else None,
                      headers=headers, method='POST' if data is not None else 'GET')
        try:
            with self.opener.open(req, timeout=8) as response:
                raw = response.read(1_048_577)
            if len(raw) > 1_048_576: raise ValueError()
            result = json.loads(raw)
            if not isinstance(result, dict): raise ValueError()
            return result
        except HTTPError as error:
            status = error.code; error.close()
            if status == 429: raise Problem('Too many email attempts. Wait before requesting another code.', 429) from None
            if status in (400, 401, 403, 404, 422):
                raise Problem('Email verification was unsuccessful. Check the address and request a fresh code.', 401) from None
            raise Problem('Email verification is temporarily unavailable. Please retry.', 503) from None
        except (URLError, TimeoutError, OSError, ValueError):
            raise Problem('Email verification is temporarily unavailable. Please retry.', 503) from None

    def send_code(self, email, create_user=False):
        self.request('/otp', {'email': normal_email(email), 'create_user': bool(create_user)})

    def verify(self, email, code):
        email = normal_email(email); code = str(code or '').strip()
        if not re.fullmatch(r'[0-9]{6,10}', code): raise Problem('Enter the numeric code from your email.', 401)
        verified = self.request('/verify', {'email': email, 'token': code, 'type': 'email'})
        token = verified.get('access_token')
        if not isinstance(token, str) or not token or len(token) > 8192:
            raise Problem('Email verification was unsuccessful. Request a fresh code.', 401)
        # Do not trust /verify metadata, browser IDs, decoded JWT claims or submitted roles.
        user = self.request('/user', token=token)
        try:
            provider_id = str(UUID(user['id']))
            if normal_email(user.get('email')) != email or not user.get('email_confirmed_at'): raise ValueError()
            ttl = max(1, min(3600, int(verified.get('expires_in', 3600))))
        except (KeyError, TypeError, ValueError, Problem):
            raise Problem('A confirmed email identity is required. Request a fresh code.', 401) from None
        return {'id': provider_id, 'email': email, 'ttl': ttl}

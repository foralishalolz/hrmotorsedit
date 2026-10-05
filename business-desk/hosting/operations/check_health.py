#!/usr/bin/env python3
"""Check a configured app URL without logging credentials or customer records."""
import argparse
import json
import sys
from urllib.parse import urlsplit
from urllib.request import urlopen, Request


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('origin', help='HTTPS app origin, or http://127.0.0.1:8765 for local use')
    parser.add_argument('--expect-cloud', action='store_true')
    parser.add_argument('--expect-version')
    args = parser.parse_args()
    try:
        url = urlsplit(args.origin)
        if (url.username or url.password or url.query or url.fragment or url.path not in ('', '/')
                or not url.hostname or url.scheme not in ('https', 'http')
                or (url.scheme == 'http' and url.hostname not in ('127.0.0.1', 'localhost', '::1'))):
            raise ValueError()
        request = Request(args.origin.rstrip('/') + '/api/health', headers={'Accept': 'application/json'})
        with urlopen(request, timeout=10) as response:
            # Redirects must not turn this into a check of a different deployment.
            final = urlsplit(response.geturl())
            if final.netloc != url.netloc or final.scheme != url.scheme:
                raise ValueError()
            result = json.loads(response.read(65537))
        if not isinstance(result.get('version'), str) or (args.expect_cloud and not result.get('cloud')):
            raise ValueError()
        if args.expect_version and args.expect_version != result['version']:
            raise ValueError()
        print('Health responded: version ' + result['version'])
        print('Storage edition: ' + ('PostgreSQL cloud' if result.get('cloud') else 'local / private SQLite'))
        print('First-owner setup: ' + ('required' if result.get('setup_required') else 'completed'))
        print('This does not verify staff access, collections, tax documents or restore.')
        return 0
    except Exception:
        print('Health check failed: review the URL, version/storage expectation and server logs. No credentials were printed.', file=sys.stderr)
        return 1


if __name__ == '__main__':
    raise SystemExit(main())

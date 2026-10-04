"""Run the browser checks against an isolated, disposable local database."""
import os
from pathlib import Path
import subprocess
import sys
import tempfile
import threading
from http.server import ThreadingHTTPServer

ROOT=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT))
from domain import Desk
from server import Handler

class QuietHandler(Handler):
    def log_message(self,*args):pass

with tempfile.TemporaryDirectory() as folder:
    server=ThreadingHTTPServer(('127.0.0.1',0),QuietHandler)
    server.desk=Desk(folder)
    thread=threading.Thread(target=server.serve_forever,daemon=True);thread.start()
    try:
        env={**os.environ,'DESK_TEST_URL':f'http://127.0.0.1:{server.server_port}'}
        result=subprocess.run(['node',str(ROOT/'tests/browser.mjs')],env=env)
    finally:
        server.shutdown();server.server_close()
    raise SystemExit(result.returncode)

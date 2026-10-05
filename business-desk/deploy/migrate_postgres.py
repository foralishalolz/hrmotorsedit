#!/usr/bin/env python3
"""Operator-only migration. Use a backed-up, linked database's DIRECT URL.
Run after Vercel link/env verification, never as a Vercel build command.
"""
import os
import sys
from pathlib import Path
sys.path.insert(0,str(Path(__file__).resolve().parents[1]))
from cloud import CloudDesk
if __name__=='__main__':
    url=os.environ.get('DATABASE_DIRECT_URL','')
    if not url: raise SystemExit('Set DATABASE_DIRECT_URL for the intended backed-up database.')
    desk=CloudDesk(url,bootstrap=True)
    desk.close()
    print('Business Desk PostgreSQL schema 3 / cloud schema 1 is ready.')

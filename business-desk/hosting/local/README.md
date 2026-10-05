# One-PC local edition

## What is needed

Python 3.10 or newer, a current browser, and a writable folder on the computer's own disk. No Node, PostgreSQL, Docker, cloud subscription or internet connection is needed to run the core local server. The app interface is English; Unicode client names/notes can be entered. This is a browser app served by Python, not an Android/iOS native binary.

From a GitHub checkout or an extracted local kit:

```sh
cd business-desk
python3 hosting/preflight.py --profile local
python3 server.py --open
```

Windows: open `Start-Windows.bat`. macOS: open `Start-Mac.command`, or use Terminal if downloaded-file execution policy blocks it. Linux/macOS can use the command above. Keep the server window open. To stop it, press Ctrl+C. If port 8765 is occupied, run `python3 server.py --port 8766 --open`.

The address is normally `http://127.0.0.1:8765`. Create the owner account, then the business and individual staff accounts. Never use fictional sample data as opening balances in a live business.

## Data and moving computers

Default records are in `business-desk/data/business-desk.sqlite3`, with original attachments and backups handled by the app. For an explicit durable location:

```sh
python3 server.py --data-dir /your/private/desk-data --open
```

Use a real writable path, quoted if it contains spaces. Do not run two app servers against one database, keep it on a network share, or use a synchronised cloud-drive live database. A phone cannot connect to this localhost-only server. Choose private-server or Vercel when several devices must share the same business.

Owner **Full backup**, or `python3 admin.py --data-dir ./data backup`, creates a consistent SQLite backup. Protect an encrypted copy outside the computer. Test restoration on a separate disposable app folder. Stop the old computer's writes before a reviewed switch to a restored authoritative copy. Do not copy just the live database while WAL writes are running, and do not merge two independently used copies.

Console recovery: `python3 admin.py --data-dir ./data reset-password --username your-user`. Password entry is hidden and requires filesystem access. This command is for the SQLite editions, not the PostgreSQL cloud edition.

Local → private-server can use a reviewed full SQLite restore. Local → Vercel is a separately scoped migration: cloud organisation exports are not SQLite restore files, and no automatic full-history importer is implemented. Use the switching worksheet to reconcile supported master CSVs/openings or arrange a tested adapter before moving financial history.

Check the running app: `python3 hosting/operations/check_health.py http://127.0.0.1:8765 --expect-version 2.2.0-rc.1`. Health does not replace the owner/staff acceptance flow.

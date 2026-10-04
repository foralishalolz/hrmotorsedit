# Verification

Release candidate: 2.0.0-rc.1.

## Completed locally

`python3 -m unittest -q`: **43 tests passed**. Covers quotation approvals and snapshots, decimal VAT and credit rounding, receipts and advance allocation, inventory, payroll and commissions, business and role isolation, attachment/backup recovery, CSRF and Host checks, and the new pilot workflows.

New failure cases include:

- Concurrent retry of one payment command produces one receipt and one number.
- A reused operation ID with changed data is rejected.
- A failed financial command rolls back its number and retry receipt together.
- Restoring a database changes its epoch and blocks stale queued operations.
- Two enquiries cannot reserve the same chassis concurrently.
- Vehicle delivery requires collection and the saved handover checklist.
- Invoice issuance consumes stock atomically; retries and previously issued job parts do not consume it twice.
- Supplier references, overpayments and outstanding balances are checked.
- Commissions can follow collections on a showroom enquiry.
- Hosted setup requires a private setup key; HTTPS cookies and origin boundaries are checked.
- Password changes invalidate existing sessions; v1 hashes remain readable.

## Browser and container checks

`tests/run_browser.py` starts an isolated disposable database. `tests/browser.mjs` exercises real forms, showroom booking → invoice → receipt, a lost payment response, encrypted offline reload, sync, and a conflicting edit from a second device. It captures desktop and phone screenshots, checks phone overflow and browser exceptions.

The current workspace could not launch Chromium (SIGTRAP); **no local visual acceptance is claimed**. GitHub Actions runs this browser test on Ubuntu and builds/health-checks the production container. Check the workflow on the exact commit being deployed; results are not implied by this document.

```sh
python3 -m unittest -v
npm ci
npx playwright install --with-deps chromium
python3 tests/run_browser.py
```

See `docs/RELEASE_GATES.md` for operational and business acceptance still required before a production rollout.

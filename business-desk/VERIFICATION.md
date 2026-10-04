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

GitHub Actions [run 37200204530](https://github.com/foralishalolz/hrmotorsedit/actions/runs/37200204530), for application commit `d6d3db0f4d390e466200aece69106589c724fd49`, passed all three jobs: business rules, browser and container. The real Chromium browser run completed **17 assertions with no uncaught exceptions**. It exercised lost payment responses, encrypted offline reload, reconnection and a competing edit; desktop and phone screenshots were inspected. The container built, served its health endpoint, and its Caddy configuration validated.

Local Chromium could not launch in the restricted workspace, so browser evidence came from that CI run. Screenshot review led to a final refinement: one dismissible notification and a stacked bill editor on phones. The browser suite now includes an additional phone-billing assertion; consult the latest PR check for subsequent commits. A CI pass does not replace live server recovery, staff-device and pilot acceptance.

```sh
python3 -m unittest -v
npm ci
npx playwright install --with-deps chromium
python3 tests/run_browser.py
```

See `docs/RELEASE_GATES.md` for operational and business acceptance still required before a production rollout.

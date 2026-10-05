# Operating a real business deployment

Give the business owner a usable daily app and give a named operator responsibility for hosting, recovery and updates. Do not leave a garage owner to debug database connections during collection time.

## Release handover

Copy `launch-record.example.json` to a **private operator location outside Git**. Record the actual commit/deployment, organisation scope, country/sector, owner acceptance, accountant decision, role checks, recovery evidence and support owner. Keep credentials in the provider/secret manager; the record contains references and results, not passwords or database URLs.

The template has `launchApproved=false`. Fill actual evidence before setting it true; the app does not treat this file as a permission or tax certificate. [Release gates](../../docs/RELEASE_GATES.md) remain the acceptance standard. No production launch is approved just because a folder/ZIP exists.

## Daily and weekly checks

| When | Operator checks | Business owner checks |
|---|---|---|
| Every working day | HTTPS health, error/restart signals, latest backup timestamp, available disk or provider storage/connection quota | Due jobs, blocked approvals, overdue collections, unresolved Sync items, cash discrepancy |
| After an error report | Exact action/record/operation ID and commit; sanitised logs; whether the same command already committed | Review original receipt/stock record before re-entering money or quantities |
| Weekly | Staff/device removals, failed backups, dependency advisories, capacity/cost, attachment growth | Unresolved returns, supplier differences, old promises, upcoming payroll/renewals |
| Before every upgrade | Backup, known image/deployment, schema compatibility, passing tests, short maintenance plan | Sync drafts, pause posting during cutover, accept representative work after update |
| At an agreed recovery interval | Restore a real-shaped protected backup into an isolated environment and time it | Compare an independently selected bill, receipt balance, stock quantity and attachment |

Use `python3 hosting/operations/check_health.py YOUR-HTTPS-ORIGIN`; add `--expect-cloud` for Vercel and `--expect-version 2.4.0-rc.1` for this candidate. The checker prints no accounts/CSRF material. A successful health response proves only the checked endpoint answered with the expected edition/version.

## Recovery is different in each edition

| Edition | Recoverable source | Do not mistake for recovery |
|---|---|---|
| Local/private SQLite | Owner full backup or consistent `admin.py backup`; encrypted offsite copy | A live `.sqlite3` copied without WAL consistency; a CSV export |
| Vercel/PostgreSQL | Provider database backup/PITR with protected access and tested isolated restore | Owner organisation JSON export; function temporary filesystem |

Before live work, choose backup retention, maximum acceptable data loss (RPO), maximum interruption (RTO), location, encryption/access, the restore operator and escalation contact. A possible small-business pilot starting proposal is one working day RPO/four-hour RTO; ask the owner and measure it. These are not guaranteed or achieved values for this candidate.

For SQLite: make a consistent backup, copy/encrypt offsite, restore in a separate disposable installation, sign in again and compare known records. Do not destroy the only authoritative copy or use `down -v`. Restoring changes the epoch; queued device operations require review.

For PostgreSQL: restore to an isolated provider database, use separate preview credentials, record record counts/financial balances/attachment hashes, verify sessions and uncertain commands under the recovery procedure, then arrange a controlled cutover. Provider-wide recovery can affect all hosted organisations. Do not assume replay safety after an old snapshot: a payment acknowledged after the restore point may no longer have its record/command receipt. Reconcile it from external evidence before replaying or re-entering it.

## Phone support and incident handling

Ask for the time, business, action, visible error and operation/record ID. Do not request a full database, password, setup key, customer photograph or browser storage dump in an ordinary support chat. For a cash/stock uncertainty, suspend the affected action, inspect authoritative records, retry the **same operation ID** through Sync if appropriate, and record the resolution. A timeout alone does not prove failure.

For suspected account/data exposure: disable the affected account, rotate necessary credentials, preserve restricted evidence and obtain a qualified incident assessment/notification decision. Do not continue expanding onboarding while unresolved isolation or financial integrity problems exist.

Lost PC/phone: revoke staff access on the server and remove local/offline data when the device is available. An already-offline device may retain its encrypted cache until its 24-hour access expiry; server revocation is checked at reconnect. Shared devices need distinct logins and logout, not a shared owner account. Cloud self-service account recovery/MFA is not yet implemented; agree an actual supported recovery path before broader launch.

## Billing and scope before switching

India: accountant checks registration, HSN/SAC, supply states, supported calculations, numbering and whether IRP/e-way bill or specialised tax treatment is required. The implemented e-invoice-required flag blocks issuance; it is not an IRP adapter.

Nepal: check IRD electronic-billing approval/procedure and CBMS applicability, not just VAT arithmetic. This app has no IRD enlistment/approval or CBMS submission. Use it for permitted operational/pilot workflows and keep required statutory billing in an approved arrangement until reviewed. Do not present printed output as automatically approved electronic VAT billing. See the [Nepal country dossier](../../research/nepal/README.md).

Retain an accountant-reviewed source of truth for full books and statutory payroll. The app's job contribution/cash counts are operational views with documented scope, not a complete profit-and-loss statement or reconciled bank balance.

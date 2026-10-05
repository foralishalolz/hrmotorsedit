# Vercel deployment and operator runbook

Candidate: 2.2.0-rc.1. This is a preparation/runbook, not evidence of a live deployment. The connected account's default team `webchatter` returned **403 Not authorized**. No project or database has been provisioned for this candidate. Restore the intended team connection before publishing there; do not deploy into another account as a workaround.

## Architecture

- GitHub repository: `foralishalolz/hrmotorsedit`; project root: `business-desk`.
- Vercel serves packaged `public/` static assets and `api/index.py` as a Python WSGI function.
- Region `bom1` is configured; choose a nearby database region and verify availability for the selected plan.
- PostgreSQL is the durable store. Function filesystem is used only for temporary scoped export files, deleted after download.
- `CloudDesk` shares business rules with the local edition. It never opens a SQLite database in cloud mode.
- Local use stays `python server.py --open`; the managed single-server SQLite deployment remains a separate deployment model.
- Tenancy is application-enforced organisation/business/role scoping. No DB row-level-security certification is claimed. Clients never receive a direct database connection.

## Required configuration

| Variable | Purpose | Scope |
|---|---|---|
| `DATABASE_URL` | TLS PostgreSQL pooled runtime URL, least-privileged role | Production and isolated preview DB separately |
| `DATABASE_DIRECT_URL` | Direct migration/operator URL | Operator environment only; do not expose to the browser |
| `DESK_PUBLIC_ORIGIN` | Canonical `https://` URL; no path | Production, and suitable canonical preview setting |
| `DESK_SETUP_KEY` | Private pilot registration invitation, at least 32 characters | Sensitive server environment; never in public assets |
| `DESK_REGISTRATION_ENABLED` | `true` opens invite-only owner registration; default closed | Enable during controlled onboarding only |
| `DESK_ALLOW_PREVIEW` | `true` allows Vercel-provided preview hosts outside production | Preview only; use isolated sample data |
| `DESK_DB_POOL_SIZE` | Maximum local connections per function instance; default 4 | Tune with provider pooling and actual concurrency |

Do not put runtime secrets in `VITE_`, `NEXT_PUBLIC_` or committed files. `VERCEL_URL` and `VERCEL_BRANCH_URL` can be considered for preview only when explicitly enabled; arbitrary Host headers are never trusted. Secure, HttpOnly, SameSite cookies and same-origin/CSRF checks protect write endpoints.

## Deploy the concrete candidate

1. Reconnect Vercel with access to the intended team. Confirm the team and project rather than creating a personal project to evade the 403.
2. Import the GitHub repository with root directory `business-desk`. Framework is `Other` / no framework. The checked-in `vercel.json` sets the build command and output directory. Keep production branch `main` after the verified candidate is merged.
3. Provision managed PostgreSQL, preferably via the available Vercel Marketplace integration. Choose a region close to Mumbai and enable provider backups with an agreed retention. Verify the actual plan's pooling and restore capabilities; “free app” does not eliminate infrastructure cost.
4. Create a separate empty preview database/branch. Preview deployments must not execute acceptance transactions against production customer records.
5. Link the local operator checkout to the intended Vercel project and verify its environment. Keep migration credentials separate from the runtime role. Review and back up any existing database before migration.
6. Install `requirements-vercel.txt` in the operator environment and run `DATABASE_DIRECT_URL`-configured `python deploy/migrate_postgres.py` once. This is an explicit schema operation, never part of a Vercel build. Runtime cold starts only check the schema; they do not migrate it.
7. Grant the runtime role only the required table/sequence operations, connect/schema usage and future grants appropriate to these tables. It must not have database owner/superuser power or migration privileges. Test a cold start with that role. The provider’s pooled endpoint should disable unsupported prepared statements; the adapter sets `prepare_threshold=None`.
8. Set the runtime environment variables in Vercel. No actual URL or secret has been invented in this repository.
9. Deploy a preview. Verify static assets, API rewrites, authenticated business manifests and Print/PDF. Then run the pilot flow and cross-organisation tests on the preview infrastructure.
10. Promote the known build and verify the canonical domain, HTTPS, cookie flags, closed/open registration policy, logs and backup recovery. Record the deployment ID, commit and migration version in the release record.

## Reliability design

Writes use bounded database transactions and an organisation-scoped PostgreSQL transaction advisory lock. This serialises money/stock operations across Vercel instances within an organisation, while unrelated organisations use separate locks. `lock_timeout` is 5 seconds, statement timeout 15 seconds and pool wait timeout 8 seconds. The function duration is 30 seconds. Tune after measuring actual request/connection patterns; do not add unlimited retries around a write.

Financial/stock actions use `/api/command`. The operation ID, payload fingerprint and stored response commit with the business changes. Replays return the original result; changed-payload replays are rejected. Uncertain client outcomes stay in Sync with the same ID. Stale versions and restored database epochs require review. PostgreSQL CI exercises two independent adapter instances against one database; it does not substitute for the actual Vercel acceptance check.

Sessions store only token hashes, user IDs, CSRF secrets, expiry and password stamps in PostgreSQL. They survive function restarts and are invalidated by password changes/account disabling. Login attempt limits are shared fixed windows for username and IP; they are not a complete bot-abuse system. Keep pilot registration private, rotate the invitation when necessary and verify account recovery before wider opening.

The app returns service errors without switching to local persistence. Such errors do not establish whether a command committed: the client must retry the same operation in Sync. Do not re-enter a receipt manually because a response timed out.

## Limits to communicate

- Request JSON is capped at 3.9 MB to remain below the platform request boundary. Cloud attachment UI caps files at 2.5 MB before base64 encoding; local edition remains 12 MB.
- Original attachments are stored in PostgreSQL for this pilot. Storage cost and large-file throughput should be measured; introduce a reviewed object-store adapter before accepting extensive photo archives.
- CSV files contain at most 5,000 rows and post in 250-row atomic batches. A later batch failure leaves earlier confirmed batches saved; retry with duplicate skips.
- Stock counts post at most 100 items per command. Large warehouse workflows require a dedicated pilot.
- State still loads a business snapshot. Paginated rendering improves the UI, but this is not server-side pagination for every record type. API response size and large-history enrichment must be tested before onboarding a high-volume organisation.
- WSGI behaviour, body/response limits and platform packaging need verification on a real deployment. CI tests the WSGI boundary and packaging, not the Vercel platform itself.
- HTTPS and passwords are present; MFA, SSO, independent security review and a public customer portal are not.
- Government e-invoice/CBMS, statutory payroll, payment settlement, automatic communications, full accounting and subscription billing remain separate.

## Organisation export and recovery

The owner downloads only their organisation’s businesses, records, original attachments, audit events and counters as a JSON export. Other organisations, accounts, passwords, sessions and command receipts are excluded. This supports data portability and source retention; it is not a drop-in PostgreSQL restore file. The file is produced as a database snapshot and deleted from temporary function storage after response.

Managed database recovery is an operator/provider task. Before launch, restore a provider backup into an isolated database, deploy an isolated candidate against it, compare business/record counts, financial balances and attachment hashes, and prove that old sessions/queued commands behave as expected. A provider-wide restore affects all organisations. Agree recovery procedures and communications before treating a shared hosted database as production.

Record target RPO/RTO from the business’s real tolerance and the selected provider's capabilities. No RPO/RTO has been measured for this candidate. Keep tested retention and recovery evidence; merely enabling a backup setting does not demonstrate restore success.

## Production acceptance

- Actual Vercel deployment and durable database configured under the authorised team.
- Provider backup retention and isolated restore successfully checked.
- Owner/staff and two different organisations verified on the live deployment.
- Quote → approval → work → bill → receipt → cash count completed with original source evidence.
- Customer opening balances and stock reconciled by the business and accountant.
- Lost receipt response and conflicting stock actions safely recovered.
- Mobile layouts, load time, response size and concurrent use measured with the intended data volume.
- Independent security review and appropriate privacy/retention/account recovery process.
- Accountant review of relevant tax, payroll and export outputs.
- Real pilot staff acceptance, support owner and incident/rollback procedure.

The release remains a tested candidate until these gates are evidenced.

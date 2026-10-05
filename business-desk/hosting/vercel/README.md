# Vercel and PostgreSQL edition

The application already has a Python WSGI entry point, durable PostgreSQL adapter and checked-in Vercel configuration. This folder contains operator files; **it is not the Vercel project root**. For the existing GitHub repository use Root Directory **`business-desk`**. For an extracted Vercel kit import/push its `business-desk/` contents using that directory as the project root. Keep one source of application code.

## Exact project settings

| Setting | Value |
|---|---|
| GitHub repository | `foralishalolz/hrmotorsedit` |
| Root Directory | `business-desk` |
| Production branch | `main`, after checks pass |
| Framework | Other / no framework |
| Build command | `python3 deploy/build_vercel.py` |
| Output directory | `public` |
| Python | 3.12, pinned by `.python-version` |
| Function | `api/index.py`, 30-second maximum in `vercel.json` |
| App region | `bom1`; verify selected plan/database region |
| Durable storage | Managed PostgreSQL with TLS and provider backups |

`project-settings.json` is an operator reference, not a second Vercel config. The canonical configuration remains `business-desk/vercel.json`. GitHub Pages, a static-only deployment and function-local SQLite cannot run this edition. See the [official Python runtime](https://vercel.com/docs/functions/runtimes/python) and [Vercel SQLite explanation](https://vercel.com/kb/guide/is-sqlite-supported-in-vercel).

## Deploy in order

1. Confirm the authorised Vercel team can access the GitHub repository. The previous connected default team `webchatter` returned 403; reconnect that scope or select the intended authorised team before creating resources. No project/database has been provisioned by this candidate.
2. Import the repository using the settings above. Keep the deployment private while configuring it. An initial deployment without database/env configuration is not ready for use.
3. Provision PostgreSQL near the app region. Choose pooling/backup/restore capabilities to fit measured usage. Create **separate preview and production databases/branches** and separate roles. A preview must never use production money or customer records.
4. Use an operator environment with Python 3.12 and `pip install -r requirements-vercel.txt`. Link/verify the exact Vercel project and environment. Copy `.env.example` to `.env.local` for private operator configuration if needed; never commit it. The preflight reads that file without executing it; the app does not automatically load it.
5. Put the **direct migration URL** in the operator's `DATABASE_DIRECT_URL` environment; back up any existing database; run `python3 deploy/migrate_postgres.py` once. This operation creates/updates schema 3/cloud schema 1. Do not add migrations to the build command or expose migration-owner credentials to Vercel runtime. Preflight deliberately does not run migrations.
6. Give the runtime role only required schema/table/sequence access and use its **pooled TLS URL** as `DATABASE_URL`. Verify schema/grants and cold starts with that role. Review provider-specific grants; do not paste guessed universal SQL against a live database.
7. Add the runtime variables in Vercel for the correct environment. `DESK_SETUP_KEY` must be generated privately with at least 32 characters. Use `DESK_REGISTRATION_ENABLED=true` only during controlled invited onboarding, then close it. Keep `DESK_ALLOW_PREVIEW=false` in production. Do not use `VITE_` or `NEXT_PUBLIC_` secret names.
8. Run `python3 hosting/preflight.py --profile vercel --env-file hosting/vercel/.env.local`. For isolated preview config add `--environment preview`. Passing checks validates configuration shape only, not provider connectivity, migration, backup or readiness.
9. Deploy a preview and verify static loading, `/api/health`, login, two organisations/staff roles, print, partial payment, same-ID retry, conflicting stock actions, attachments and logout. Use fictional data. Record the tested deployment ID and commit.
10. Complete a provider restore to an isolated database and the business/accountant acceptance. Promote the tested candidate, check the canonical domain and close registration. Use `python3 hosting/operations/check_health.py https://YOUR-ACTUAL-DOMAIN --expect-cloud --expect-version 2.2.0-rc.1` against the real domain.

For future Git updates, use Vercel's repository integration for previews/production. GitHub quality checks and Vercel deployments are separate systems: configure the platform's protection/promotion process so green checks and reviewed migrations precede live financial use. The package workflow publishes ZIP artifacts; it does not deploy or migrate anything.

## Boundaries

Request JSON is capped at 3.9 MB; cloud uploads are capped at 2.5 MB before base64 encoding. Original attachments currently live in PostgreSQL. Larger archives need a reviewed object-store adapter. Each request uses bounded transactions; do not increase the function pool without measuring provider-wide connections. The app still loads a business snapshot; large histories need API/load testing and later server pagination.

Owner cloud export is organisation-scoped JSON excluding passwords/accounts/sessions. It is **not** a PostgreSQL backup or automatic SQLite migration. Provider recovery affects shared organisations; record its scope and invalidate/reconcile old sessions/commands under the tested recovery procedure. Do not run `admin.py` against a cloud export.

Read the [full Vercel runbook](../../docs/VERCEL_DEPLOYMENT.md) and [launch record](../operations/launch-record.example.json). Testing is strong for a candidate; a deployed restore, independent review, customer acceptance and country billing approvals remain outstanding.

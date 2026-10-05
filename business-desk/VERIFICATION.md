# Verification · 2.4.0-rc.1

The owner analytics and optional Supabase email-auth update has **147 discovered tests**: **128 local** calculation/business/security/packaging checks and **19 disposable PostgreSQL** checks. [GitHub Actions run 37306474684](https://github.com/foralishalolz/hrmotorsedit/actions/runs/37306474684) passed all four jobs on application commit `2de0b823dbfb9b1ca8c111fc4e6c7937d45bad1c`: 128 local checks, 19 real PostgreSQL checks, 144 Chromium assertions with zero uncaught errors, container health/Caddy and Vercel asset packaging. Release notes may be updated in a later documentation commit; the app source stays identical. Live provider email delivery and deployment acceptance are separate checks.

The new regression cases cover profit versus cash, payroll/commission duplication, nonnegative cent allocations, credit cost reversals, credits to older bills, future receipts, opening balances, drafts, highest/lowest highlights beyond the 100-row table, missing wage/material costs, sample sizes, quality-review permissions and CSV formula escaping. Auth-boundary checks use fictional HTTP responses and never send a real email.

The real PostgreSQL job extends the two-worker/org-scope suite with verified identity creation, saved invitation roles, disabled/expired accounts, legacy-username separation, provider-to-cookie-to-shared-session WSGI flow and analytics snapshots. A separate private schema tests a dedicated runtime role without DDL permission, server RLS, and denied Data API role grants. Auth provider responses in these CI flows are mocked; the PostgreSQL connections, saved identities and sessions are real and disposable.

The Chromium suite extends the existing four-sector/offline/payment experience with live API-backed analytics, highest/lowest service/job results, profit/cash, CSV download, client search, saved quality ratings, team sample sizes, recommendations saved as follow-ups, period presets, failed-request recovery, keyboard tabs and 320/390/768/900/901 layouts. Verified-email UI fixtures check code submission, cooldown, invalid-code recovery, address changes and the legacy sign-in option. They do not verify SMTP or production Auth.

The same source is packaged into four clean runtime/source kits: local 69, private-server 75, Vercel 78 and GitHub 107 source files, excluding each manifest. No database, account credentials, provider keys, live email or customer files enter CI or these kits. The public build copies only the static asset directory. Cloud runtime never creates a SQLite fallback and migrations remain explicit operator actions.

Production blockers still require the intended accounts: the connected Vercel team returns 403, and a new Supabase project has not been selected/provisioned. See [Supabase setup](hosting/supabase/README.md) and [Business health calculation basis](docs/BUSINESS_HEALTH.md). The candidate does not claim a live deployment, statutory financial statements or real-device performance guarantees.

## Historical verification

# Verification

Historical release candidate: **2.3.0-rc.1**. This verifies a candidate, not a live Vercel deployment or completed business acceptance.

## Premium workspace verification

The current [PR #11 checks](https://github.com/foralishalolz/hrmotorsedit/pull/11/checks) run the 2.3 source. The suite discovers **115 tests**: **104 local business/security/packaging checks**, plus **11 real PostgreSQL checks** in the separate disposable PostgreSQL 16 job. Ordinary local discovery skips those 11 when their test URL is absent.

New coverage checks owner organisation/role isolation, page-scoped currency totals, credits/refunds/advances/allocations and reconciled opening balances, future-dated receipt exclusion from monthly collections, posted/draft distinctions, old business settings, bounded pagination, stock/work stages, task priority and stale settings versions.

The real Chromium flow covers saved dashboard goals/targets, Focus categories and future tasks, generated-issue next dates, display preference reload, trading names and separate INR/NPR owner summaries, failed and successful business switching, linked-record search, actual front-desk sign-in and the owner API's 403 response. Viewports include 320, 390, 768, 900 and 901 pixels; an isolated authenticated touch context checks 320/390 layouts, a 44-pixel billing action and drawer open/close. Reduced motion, floating navigation position, dialog overflow, the original billing/offline/stock flows and uncaught browser errors are checked. The exact assertion count, browser version and measured asset sizes are emitted into `verification/` artifacts, rather than assumed in this document.

The new UI uses local system fonts/SVG icons and inline SVG charts. Search caches linked record text per state and debounces input for 140 ms; results cap at 100. Existing lists still paginate 50 rows. The added UI assets have a conservative 110 KB raw-size regression budget. Synthetic rendering timing excludes network, database, paint and real-device latency; it is not a deployment SLO.

The same workflow builds the private container, checks health/Caddy, tests the real PostgreSQL adapter and packages Vercel static assets. Clean kits include the new backend and UI files, with no runtime data. The current kit counts are local **62**, private-server **68**, Vercel **70**, GitHub **96** source files, excluding the per-ZIP manifest. Browser artifacts expire after seven days; operator-kit artifacts after 14. Use the manual package workflow to regenerate them.

This is a tested release candidate when those checks are green. They do not certify an actual Vercel deployment, bank/government integrations, field-device performance, statutory payroll or customer recovery/acceptance. The intended connected Vercel team remains blocked by a 403 access response. Follow the existing release gates for the actual operator and business.

## Historical 2.2 India/Nepal operating-kit verification

The 5 October 2026 research/hosting update adds 12 package/configuration checks to the unchanged application baseline below. Local discovery: **104 tests, 94 run successfully and 10 PostgreSQL-only tests skipped without their disposable URL**. An extracted GitHub source kit, initialised/staged as documented, passes the same suite.

Clean ZIPs were built for local (58 source files), private-server (64), Vercel (66) and GitHub (90), excluding each ZIP's manifest. The extracted local edition starts with isolated data and returns the expected 2.2.0-rc.1 health; its health checker succeeds. The extracted Vercel edition packages `public/index.html`, omits the generic public manifest and includes no SQLite files. ZIP integrity, reproducible hashes, per-file manifests, private-file/untracked-data exclusion, required-source symlink rejection and non-overwriting release creation are checked. Placeholder/insecure configuration fails, and error output is redacted. New-guide local links and staged whitespace checks pass.

GitHub's quality workflow additionally publishes clean operator-kit artifacts for 14 days; a manual package workflow is provided. Neither workflow deploys or migrates a live business. Real provider/platform acceptance remains outstanding.

## Historical 2.2 application evidence

[GitHub Actions run 37272337114](https://github.com/foralishalolz/hrmotorsedit/actions/runs/37272337114), application commit `5a0745ed5220be8ae46970dbd0a77ea3d5320655`, passed all four jobs:

- **82 local business/security tests**. The ordinary suite discovers 92 tests and skips the 10 PostgreSQL-only tests when their disposable test URL is absent.
- **10 real PostgreSQL tests**, using PostgreSQL 16 and two independent server adapters: organisation/role scoping, cross-business references, hashed shared sessions, shared login limits, scoped exports, preview rollback, origin/CSRF/size checks, missing-configuration failure, one receipt under concurrent retry and one sale of the final stock item.
- **61 real Chromium assertions**, Chromium `145.0.7632.6`, **0 uncaught exceptions**. Configuration → API → records → UI flows cover all four profiles, Nepal/India billing, line returns, owned branding/manifest, CSV preview/import, agreed quantity pricing, stock counting, opening collections/statements, cash closing, inspections, offline reload/sync/conflicts and lost payment responses.
- **Container build/health and Caddy validation** pass. Static Vercel packaging also passes in the PostgreSQL job.

The 2,000-customer synthetic snapshot rendered 50 visible rows: synchronous DOM rendering p50 **3.1 ms**, p95 **5.9 ms** over 15 samples on the CI runner. This excludes paint, network and database work; it is not a production capacity, mobile hardware or end-to-end latency claim. The regression budget is deliberately conservative.

Evidence is in the workflow's `business-desk-browser-evidence` artifact; screenshots include the business-owned desktop/phone dashboard, desktop/phone configuration, customer statement, catalogue checkout, India dashboard and sector workspaces. The final desktop and phone configuration/dashboard screenshots were visually inspected. Artifacts use seven-day retention; rerun on the intended deployment and retain its release evidence before launch.

Vercel team access returned 403, so the actual deployment, canonical domain, provider restore, real function/database performance, independent security review and staff/accountant pilot acceptance are outstanding. WSGI and PostgreSQL CI tests do not assert those gates are complete. See [Vercel deployment](docs/VERCEL_DEPLOYMENT.md) and [release gates](docs/RELEASE_GATES.md).

## Historical 2.1 evidence

Historical baseline: 2.1.0-rc.1.

## Completed locally

`python3 -m unittest -q`: **65 tests passed**. Covers quotation approvals and snapshots, decimal VAT and credit rounding, receipts and advance allocation, inventory, payroll and commissions, business and role isolation, attachment/backup recovery, CSRF and Host checks, and the new pilot workflows.

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

GitHub Actions [run 37265352725](https://github.com/foralishalolz/hrmotorsedit/actions/runs/37265352725), for application commit `4b85ea06fa0b8184fbabaf54e0a64044603a3352`, passed all three jobs: **65 business/security tests**, **43 real-browser assertions with no uncaught exceptions**, and the container build/health plus Caddy configuration checks. The browser was Chromium `145.0.7632.6`.

The browser run covered all four sector workspaces; India onboarding and domestic GST billing; customer discount/payment terms; keyboard barcode selection; a partial line credit with restocking; custom business/customer fields; case-insensitive command search; showroom reservation and collection; lost payment responses; encrypted offline reload; reconnection; and a competing-device edit. It checked phone overflow, readable balance cards and the stacked bill editor.

Desktop screenshots for showroom inventory, garage work, service visits, quick billing and the client timeline were inspected, alongside phone dashboard, invoice editor and quick-billing screenshots. Evidence is retained in the run's `business-desk-browser-evidence` artifact for seven days. `tests/run_browser.py` reproduces it with disposable fictional records; do not commit live business data as evidence.

Local Chromium could not launch in the restricted workspace, so the real-browser evidence came from CI. That verification found and resolved a dialog-close timing defect in cart-to-invoice review. Static review also tightened no-tax GST/cess preservation, and screenshot review improved large monetary values on phones. The final tests pass after those application changes. Subsequent documentation-only commits preserve that application code; consult the latest [PR #8 checks](https://github.com/foralishalolz/hrmotorsedit/pull/8/checks) before deployment. A CI pass does not replace live server recovery, staff-device and pilot acceptance.

```sh
python3 -m unittest -v
npm ci
npx playwright install --with-deps chromium
python3 tests/run_browser.py
```

See `docs/RELEASE_GATES.md` for operational and business acceptance still required before a production rollout.

## 2.1 additions

Twenty-two additional backend tests cover India GST components, included tax and percentage cess, financial-year numbering, retained print snapshots, registration/HSN/address checks, e-invoice blocking, currency immutability, customer terms/custom fields, unique barcodes, partial line returns/stock rollback/permissions, and no-tax rate preservation/invalid-cess rejection. The full suite has 65 tests. Exact current-commit CI results are recorded in the release pull request.

# Business workspace · 2.3 candidate

The daily workspace is built for an owner opening a phone between jobs, a front desk using a PC and a technician checking assigned work. It uses local system fonts and SVG icons, with no chart service, remote asset dependency or new frontend framework.

## Make it belong to the business

Keep the legal/trading name, logo, document identity, sector stages, checks and billing preferences in **Settings → Guided configuration**. The dashboard's sliders button sets a shared business focus, a monthly collection target and useful panels. These settings belong to that business and persist on the server. The target repeats each calendar month; it is compared with recorded receipts less refunds, including customer advances, and excludes future-dated payments. It is neither profit nor bank-confirmed settlement.

The dashboard shows collections only to roles that can read the complete invoice, payment, credit, allocation and opening-balance set. Staff panels follow existing permissions. Technicians see their assigned work and own attendance. Changing the dashboard does not change record permissions or posting rules.

**Display preferences** belong to the signed-in account on the current device: liquid glass or solid surfaces, and comfortable or compact spacing. Compact spacing does not reduce touch targets. System reduced-motion preferences disable animation; reduced-transparency and forced-colour preferences have fallbacks.

## Turn attention into a dated action

**Focus inbox → Due & unresolved** brings together saved record conditions and planned tasks. Filter work, collections, clients, stock/suppliers or people; search the inbox. A manual task has a category, priority, responsible employee, next date and outcome. **Next 7 days** shows future follow-ups, appointments, promised work dates, enquiries, supplier deliveries and contract expiry dates that are not already visible as unresolved issues.

For a generated issue, **Plan next step** opens the existing reviewed follow-up workflow. Save the agreed next date and contact outcome. Messages are copied for review; the app does not contact the client automatically. Completing a reminder does not mark a bill paid, receive goods or deliver a job. The authoritative source record controls those states.

## Keep several businesses separate

Only the owner can open **All businesses** or its API. Every query uses the owner's organisation. The overview shows up to 24 businesses at a time; Previous/Next controls load the next page. Currency summaries cover the visible page only, with INR and NPR separate. Each business uses its local month. Collection figures include advances, net of refunds; allocations are not counted as another receipt. Outstanding totals use issued invoices and positive reconciled opening balances, with credits/refunds/allocations applied. Drafts and customer credit balances are excluded from receivables.

Cards show the business's own trading name, sector, shared focus, outstanding collections, recorded monthly collections, open work and generated actions. Open a business or a source action from the card. If loading fails, the original business selection and records are restored together. Cash-count source review requires the full business view and is not included in the portfolio action count. This overview is an operational view, not a consolidated statutory financial statement.

## Performance and recovery

Linked-record search builds one in-memory index per loaded state, debounces typing for 140 ms and displays at most 100 results. Existing lists keep 50-row pagination. Charts use inline SVG. Blur is limited to navigation and dialog backdrops; record surfaces stay nearly opaque. Search indexes and portfolio snapshots are memory-only, not an unencrypted device cache. The existing passphrase-protected offline draft vault remains separate.

API calls time out after 30 seconds. The command system still retains an uncertain write's operation ID for a safe retry. Older state responses cannot replace the current business or a different signed-in user's workspace. Local mode remains a single authoritative Python/SQLite server; private hosting and Vercel/Postgres use the same permission checks. Offline mode can save the already-supported draft kinds; it cannot post money or stock without the server.

Use `python3 -m unittest -v` for financial/scope boundaries and `python tests/run_browser.py` with installed Playwright Chromium for complete UI flows. CI tests the real Postgres adapter, packaging, container entry point and Vercel asset build. Pilot acceptance, real hosting configuration, recovery drills and country-specific statutory integrations remain the release gates described in `RELEASE_GATES.md`.

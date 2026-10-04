# Business Desk · 2.1.0-rc.1

A local or privately hosted business workspace for garages, vehicle showrooms, retailers and service businesses in Nepal and India. This is a controlled pilot candidate; finish the [release gates](docs/RELEASE_GATES.md) before operating it as a production service.

## Start locally

Install Python 3.10+ and open `Start-Windows.bat`, `Start-Mac.command`, or run:

```sh
python3 server.py --open
```

Open `http://127.0.0.1:8765`, create your owner account, and choose a business profile. Local mode binds to this computer only and does not need an internet connection. Your database is in `data/business-desk.sqlite3`. Keep the server window open.

## New in this candidate

- Country-aware Nepal/NPR and India/INR setup, domestic GST components, HSN/SAC, percentage cess and April–March Indian numbering. No government filing or IRP integration is claimed.
- Business name/colour, speciality, work checklists and up to 20 custom fields for customers, work orders, enquiries and assets.
- Customer relationship timeline, tags, language/contact preferences, agreed discounts and payment terms, and dynamic customer segments.
- Quick catalogue billing with SKU/barcode input, customer terms and an explicit invoice review.
- Retained line returns/credits with quantity limits, original tax allocation and optional direct-sale stock return. Cash refunds remain separate entries.
- A consistent SVG icon set, mobile navigation and Ctrl/Command K command search.
- **Free pilot — no charges, automatic conversion or payment-card collection.**

Read the [India/Nepal product research](docs/INDIA_NEPAL_PRODUCT_RESEARCH.md) and [client discovery worksheet](docs/CLIENT_DISCOVERY_QUESTIONNAIRE.md).

## Your daily workspace

The first screen puts unpaid bills, receipts today, work or enquiries, and due actions together. Setup steps guide a new owner to a customer, catalogue/vehicle stock, and a first bill. Use **Settings → Choose workspace modules** to keep navigation relevant without deleting records.

| Profile | Starting workflow |
|---|---|
| Garage & collision | Customer/vehicle → estimate → recorded approval → work card → parts and labour → quality check → bill → collection. Insurance comparisons and settlements are available. |
| Vehicle showroom | Customer → sales enquiry with next action → unique chassis inventory → reserve → invoice → collect → PDI/document/handover checklist → deliver. |
| Retail & trading | Customer → bill with stock catalogue lines → issue and deduct stock → receipt or customer credit → replenishment and supplier payment. |
| Service & repair | Customer/asset → booking → quotation → work stages → invoice → collection → repeat visit or agreement renewal. |

## Features included

- Quotations with revisions, approval records, line/document discounts, mixed tax rates, VAT added/included/no VAT, NPR words, print styles and spreadsheet paste.
- Retained invoice snapshots, receipts/refunds, credit notes, advances and allocations. Issued bills and posted financial entries cannot be silently edited.
- Insurance claims, expected payer shares, original document attachments, and clearly labelled hypothetical comparisons. Simulations are never presented as independent competitor quotations.
- Sales enquiries with source, staff owner, follow-up date, next action, finance status, lost reason, and board view.
- Showroom inventory with a unique chassis/VIN, condition, price, arrival date and location. Server transactions prevent double reservation. Issuing its invoice records the sale; delivery checks collection and the handover checklist.
- Stock ledger, no-negative-stock checks, reorder alerts, purchase orders and partial receipts. Stock catalogue lines deduct inventory when an invoice is issued. Previously consumed job parts are not deducted a second time.
- Supplier bills, duplicate reference checks, due balances and supplier payments. Recording a bill does not receive stock again: use the purchase receipt/movement for physical goods.
- Jobs, tasks, blockers, due dates, staff assignment, time tracking and direct contribution estimates.
- Attendance, overnight shifts, reviewed payroll, salary advances and commissions. Commission collection eligibility can follow either a job or a sales enquiry. Payroll rates and statutory deductions require owner/accountant review.
- Dated follow-ups generated from saved conditions. The records assistant answers supported questions from your data. It does not autonomously contact customers or use a cloud AI model.
- Owner, manager, front desk, cashier and technician roles, per-business access, audit events, attachments, CSV/JSON export and complete SQLite backups.

## Several staff devices and offline drafts

Use the [private HTTPS deployment](docs/DEPLOYMENT.md) for several phones/PCs. Each device connects to the same authoritative business server. Each paying organisation should have a separate instance during the pilot.

On a trusted device, choose **Settings → Offline drafts on this device**, and set a separate offline passphrase. An encrypted device copy permits customer, enquiry, quotation-draft, attendance and follow-up entry during a connection loss. Payroll and commissions are excluded. Offline access expires 24 hours after the last online refresh.

Use **Sync** to see every pending change. When connected, the same operation ID is retried, so a lost response does not duplicate a posted payment. Conflicting edits require review. Only one editing tab per account per browser is supported. An offline device does not provide a second independently writable server; this is browser draft sync, not two-way synchronisation of separate SQLite installations.

Bills are issued, receipts posted, inventory allocated and payroll approved **only when the server confirms them**. Do not give a customer an official receipt for a queued draft. The app cannot instantly revoke access on a device that is already offline; its cached access expires and server permissions are checked at sync.

## Backups and recovery

The server takes a daily database backup at startup and while running, retaining the latest 14 daily files. **Full backup** downloads accounts, businesses, records and original attachment files. Keep an encrypted copy outside the server: the built-in local backup cannot protect against loss of the whole server.

Restore takes a safety backup, validates database integrity, migrates supported v1/v2 data, expires sessions, and changes the database epoch. Old pending device operations must be reviewed after restore. JSON/CSV exports are for portability and review, not full recovery.

A server administrator can recover an account without a public password-reset endpoint:

```sh
python3 admin.py --data-dir ./data reset-password --username your-user
```

## Current limits that affect a live business

- Nepal tax software approval/CBMS integration is not implemented or claimed. AD dates drive reminders; BS dates and fiscal labels are entered manually. Validate invoice fields, numbering and retention for the actual business before live VAT billing.
- Payroll tax/SSF/contribution calculations are not a statutory payroll engine. Configure and review the applicable figures.
- This is an operational subledger, not a complete double-entry accounting package or a bank reconciliation system.
- Indian export/SEZ/reverse-charge, fixed-amount cess, used-vehicle margin schemes, GST return filing, IRN/e-way bills and statutory payroll are not implemented. GSTIN checks validate format and state, not active registration. Marking e-invoicing as required blocks invoice issuance until integration is available.
- Supplier credit notes/returns, vehicle resale after an issued sale, and progress invoicing against one job need additional workflows. Supplier bill/payment corrections currently require controlled administrator/accountant review; do not silently delete ledger records.
- SMS/WhatsApp/email sending, bank/wallet payment processing, finance-provider APIs, manufacturer dealer-system integration and automatic subscription charging are not implemented.
- Interface text is English. A client’s preferred contact language is stored but does not translate the entire application. Keyboard barcode input is supported; camera scanning and hardware printer integrations are not included.
- Multi-tenant SaaS billing, self-service customer provisioning, device conflict merging and independently operating local-server/cloud-server replication are not included.
- The available older quotation repository was used as a migration reference. Exact feature parity with the newer hosted preview has not been verified.

## Development and verification

```sh
python3 -m unittest -v
npm ci
npx playwright install --with-deps chromium
python3 tests/run_browser.py
```

The expanded checks exercise all four profiles, India billing/returns, customer terms and custom fields as well as the existing offline/retry flows.

Node/Playwright are development-only dependencies. Local operation uses the Python standard library; private hosting adds the pinned Waitress dependency. See [verification](VERIFICATION.md), [security](SECURITY.md), and the [market and pilot plan](docs/MARKET_AND_PILOT.md).

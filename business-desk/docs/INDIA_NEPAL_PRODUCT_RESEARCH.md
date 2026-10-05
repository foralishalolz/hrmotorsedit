# Business Desk: sector product strategy for India and Nepal

Historical 2.1 strategy. For the current 2.2 workflow/country/deployment analysis read the [research index](../research/README.md), [full client workflow](../research/workflows/FULL_CLIENT_WORKFLOW.md) and [hosting folders](../hosting/README.md). The later PostgreSQL edition supports application-scoped private organisations; the per-customer-stack statements below describe the older SQLite rollout, not that cloud adapter.

Research date: 5 October 2026 (India time). Release: 2.1.0-rc.1.

The owner confirmed: **all four business profiles, a free pilot with paid plans later, and offline drafts with server-confirmed financial posting**. This document distinguishes public evidence, product decisions, implemented behaviour and work that still needs customer validation. No customer interviews or willingness-to-pay results have been invented.

## The product to sell

A configured operating workspace for an owner and their staff: know what needs attention, complete work, collect the money and retain the customer history. It should feel like the business's own application because its vocabulary, daily queue, forms, checklists and client terms fit the work.

Keep one maintained product. Configure a business instead of creating a code fork per customer. Country rules, monetary calculations, permissions, posting, recovery and sync stay shared. A new bespoke rule must come with its owner, a real example, its exceptions and an acceptance check.

Support the four profiles throughout the pilot. Run the same core acceptance script in each profile, then the sector-specific script. Each paying customer organisation currently needs its own private instance; multiple businesses inside one installation belong to that organisation. The owner account can see them all. This is **not** a self-service, shared-database, multi-tenant SaaS launch.

## Research: patterns worth adopting

These are observed product capabilities, not independent proof of their vendors' marketing claims or evidence that our customers will pay.

| Primary evidence | What it establishes | Decision for Business Desk |
|---|---|---|
| [Shopify customer management](https://help.shopify.com/en/manual/sell-in-person/shopify-pos/customer-management) | Customer profiles connect contact information, purchase history, preferences and custom information. | A customer hub, relationship timeline, tags, contact language, agreed discounts and payment terms. |
| [Shopify customer segments](https://help.shopify.com/en/manual/customers/customer-segmentation/manage-customer-segments) | Segments update according to saved customer criteria; marketing has subscription checks. | Recomputed views for outstanding balances, repeat customers, inactivity and recorded marketing preference. No automatic campaign sending. |
| [Shopify draft orders](https://help.shopify.com/en/manual/fulfillment/managing-orders/create-orders/create-draft) | Staff can prepare orders with customer details, products, discounts and payment terms before completion. | A catalogue cart followed by review, saved draft and deliberate invoice issuance. Our draft does not reserve stock. |
| [Shopify POS](https://help.shopify.com/en/manual/sell-in-person/shopify-pos) | The staff workflow starts with a cart and links sales and inventory; retail hardware can extend it. | Item/SKU/barcode search, explicit quantities, server-confirmed stock deduction and touch-sized primary actions. Keyboard-wedge barcode entry is supported; camera scanning and printer drivers are not implemented. |
| [Shopify exchanges](https://help.shopify.com/en/manual/sell-in-person/shopify-pos/order-management/exchange) | Return decisions, restocking and replacement items are separate parts of an exchange. | Link line credits to the original invoice, cap quantities and make restocking explicit. Record a cash refund separately; bill a replacement as a new sale. |
| [Zoho Inventory item management](https://www.zoho.com/inventory/help/items/additional-features.html) | Reorder levels, preferred vendors and customer-specific pricing are established inventory workflows. | Reorder queues and agreed customer discount/terms. Full item-specific or volume price lists remain separate work. |
| [Zoho Books India](https://www.zoho.com/in/books/gst-accounting-software/) | GST, accounting and electronic invoicing are established expectations in the Indian category. | Add a distinct India configuration and retain tax components. Do not equate this operational ledger with GST filing, IRP integration or full accounting. |
| [Vyapar](https://vyaparapp.in/) | Promotes billing, stock, payment tracking, offline use and multiple devices for Indian small businesses. | Offline is a baseline expectation to validate, not a unique selling claim. Clearly show pending drafts and require confirmation for money entries. |
| [Tekmetric inspections](https://www.tekmetric.com/feature/digital-vehicle-inspection) | Garage-specific tools connect inspection findings, photos, work recommendations and approval. | Default work/quality checklists, assets, retained quotation approvals and original attachments. Dedicated condition grading, image markup and external customer approval links are future work. |
| [SIDBI MSME outlook, FY2024–25](https://www.sidbi.in/annualreport/AnnualReport202425/msme-outlook.php) | Describes a diverse MSME sector and challenges accessing timely, adequate credit. | Prioritise accurate receivables and daily cash visibility. This is an inference for product discovery, not evidence that this app solves access to finance. |
| [SIDBI Outlook Round 6, Jan–Mar 2026](https://www.sidbi.in/uploads/publicationreport/MSME_Report_R6_Final_march_2026.pdf) | Its published summary discusses cost pressures, supply-chain uncertainty and differing sector conditions. | Interview sectors separately. Do not infer one demand curve or a software market size from aggregate MSME confidence. |

The earlier [Nepal market plan](MARKET_AND_PILOT.md) covers GMS Nepal, MekanikMitra, Tigg, Sajilo Billing and local positioning. Public competitors already offer much of the basic billing feature set. The proposed advantage is the quality of setup, daily work completion, collections and support. That advantage must be demonstrated with real staff.

## Pain → behaviour → feature → evidence

| Pain hypothesis | What staff are trying to do | Included response | Pilot evidence to collect |
|---|---|---|---|
| Owner repeatedly calls staff for updates | Find blocked work, promises and due money | Sector daily queue and dated actions | Time to prepare the morning review; promises missed |
| Long forms slow down a busy counter | Find a known item/customer and bill correctly | Catalogue search, barcode input, customer terms and review screen | Median repeat-customer bill time; correction rate |
| Customer preferences live with one employee | Recognise the client and continue the conversation | Customer hub, timeline, tags, language and extra fields | Staff can answer the last-work/balance question without asking a colleague |
| Discounts and credit terms are inconsistent | Apply the agreement made with that customer | Saved default discount and payment term | Difference between agreement and issued bill; override reasons |
| Returns corrupt stock or cash balances | Reverse the right part of the original sale | Retained line credit, quantity limits and explicit restock | Reconcile invoice, credit, cash refund and physical item |
| Generic software does not match the business | Use familiar terminology and capture necessary details | Four profiles, workspace name/colour, custom fields and checklists | Unassisted completion and number of fields staff ignore |
| Team distrusts a connection failure | Know whether the entry reached the server | Pending queue, stable retry IDs, encrypted drafts and conflict review | Zero duplicate/lost financial entries in interruption tests |
| Forgotten follow-ups lose collections or repeat work | Agree a specific next action and date | Enquiry owners, customer reminder interval, follow-up tasks | Overdue promise coverage and action completion |
| Too many modules discourage adoption | Complete a small role-specific task | Module visibility and backend role permissions | Help requests, unused modules and shared-login incidents |
| Bills use the wrong tax or currency settings | Produce the document appropriate to this registration | Country configuration, reviewed item tax data and retained snapshots | Accountant review of representative bills and exceptions |

Customer tags and marketing preference are organisational tools. A checked marketing box is not by itself a complete consent system or proof of lawful outreach. Contact-language preference does not translate the entire interface. No customer messages are sent automatically.

## Sector operating models

### Garage, dent/paint and collision

**Owner:** promised delivery dates, blocked cars, approvals, outstanding insurer/customer balances, direct job contribution and staff workload.

**Service adviser:** find customer/vehicle, record complaint and existing damage, attach evidence, prepare estimate, record the exact approval, open work and agree a delivery date.

**Technician:** assigned job, work/quality checklist, parts request, task time and a specific blocker. Salary, unrelated businesses and owner reports remain restricted.

**Cashier:** retained bill, correct payer, partial receipt, advance allocation and unpaid balance. Insurance approval is not money received.

Configuration examples: body/paint/general service speciality; paint code and claim contact as extra fields; repair stages; bay names; default handover checks; fleet customer payment terms.

Exception discovery: additional damage after dismantling, supplements, customer-supplied parts, subcontract paint, warranty rework, excess/depreciation, insurer paying the customer, and disputes after delivery. The app must not manufacture independently issued competitor documents. Hypothetical comparisons remain clearly labelled.

Acceptance: record a repair estimate, retain its approval, assign the job, issue a part, bill it once, record partial payment, find the remaining balance and follow up. Existing parts consumption must not be deducted again on billing.

### Vehicle showroom

**Owner:** active enquiries, next sales action, ageing chassis inventory, booking commitments, collected cash and delivery readiness.

**Salesperson:** source, desired model/variant, customer conversation, next date, finance status and a distinct lost reason. Finance approval and disbursement are different from a recorded collection.

**Stock/delivery team:** one record per chassis, exclusive reservation, preparation, documents, PDI and signed handover.

Configuration examples: new/used/two-wheeler speciality; prospect budget and exchange interest as extra fields; staff owner; handover checklist; brand/model vocabulary.

Acceptance: two salespeople attempt to reserve one chassis; only one succeeds. Convert the reservation to an invoice, allocate any advance, complete collection and record handover checks before delivery.

Boundaries: used-vehicle margin schemes, trade-in accounting, consignment, registration fee treatment, manufacturer integrations, financing APIs, vehicle returns/re-sale and non-percentage cess require specific work and accountant acceptance. New country support is not approval to use every automotive tax treatment.

### Retail and trading

**Owner:** cash/credit sales, receivables, low stock, supplier bills, fast-moving items and margin checks.

**Cashier:** select customer, find or scan an item, choose quantity, review agreed discount/tax, issue bill and record receipt. An interruption must not duplicate the receipt.

**Stock clerk:** ordered vs received vs billed quantities, shelf location and stock adjustments with reasons. Supplier invoice entry must not receive goods twice.

Configuration examples: spare parts/electrical/wholesale speciality; catalogue collection and barcode; fleet/wholesale client tags; customer payment terms; reorder levels.

Acceptance: sell two items, record a partial receipt, credit one original line, restock only the sellable return, record the actual refund if one occurs, and reconcile all balances.

Boundaries: this is not full Shopify commerce. Online storefronts, shipping, marketplace sync, product option groups, gift cards, loyalty liabilities, volume pricing, batch/expiry, multi-warehouse allocation and general supplier returns need separate scoped work.

### Service and repair teams

**Owner:** visits due, work not completed, renewal promises, receivables and technician availability.

**Coordinator:** client/asset, complaint, appointment, agreed scope, technician, required parts and a next contact.

**Technician:** assigned work and completion checks, actual time and proof/notes. A part needing approval must not become an unapproved extra charge.

Configuration examples: AC/appliance/equipment speciality; appliance model, warranty expiry or site-access instructions as extra fields; service checklist; appointment capacity and return interval.

Acceptance: book a visit, complete the work order, issue a bill, collect payment and create the next service/renewal action.

Boundaries: geolocation, route planning, SMS dispatch, self-service bookings, automatic recurring billing, external signatures and warranty adjudication are not implemented.

## Personalisation without fragile forks

| Level | Included settings | Retained safeguards |
|---|---|---|
| Country | Nepal/NPR or India/INR, business timezone, country tax fields | Country/currency cannot relabel existing monetary records; each country business is separate |
| Sector | Navigation defaults, work labels, first stage, daily queue and checklist | Same transactional finance, stock and permission rules |
| Business | Workspace name, speciality, accent, modules, stages, terms, checklist, up to 20 extra fields | Owner-only business changes; field keys/types validated; changes are audited |
| Customer | Tags, preferred channel/language, discount, payment term, reminder interval and extra values | Explicit transaction review; issued document values and customer/seller snapshots retained |
| Staff role | Owner, manager, front desk, cashier, technician | Hiding a module is not the access control; the backend enforces permissions |

Do not expose technical terminology in daily staff flows. The setup operator may need a stable custom-field key, but a technician should see “Paint code” or “Site access instructions”, not internal storage configuration.

## India: what is included and what needs acceptance

The [CBIC Rule 46 source](https://taxinformation.cbic.gov.in/content-page/explore-rules/1000136/1000001) specifies invoice particulars including supplier/recipient details, document numbering, goods/services classification, value and tax details. The implementation adds GSTIN-format/state checks, HSN/SAC entry, domestic place of supply, April–March numbering and retained seller/customer details. Numbers are capped at 16 characters for Indian businesses.

Ordinary domestic forward-charge calculations support intra-state CGST + SGST/UTGST, inter-state IGST, tax-added/included pricing, discounts and percentage cess. Use the [official GST state-code list](https://docs.ewaybillgst.gov.in/apidocs/state-code.html) for configuration. Rates and classifications are entered and reviewed for each business; no universal Indian rate is inferred from the sector.

Amounts use decimal arithmetic. Each line rounds to paise and totals sum the lines. Components allocate the calculated tax; a remaining cent goes to the second intra-state component. Partial returns allocate original line amounts cumulatively so a complete return exactly reverses the original rounded amount. Have the accountant verify the rounding convention and sample documents before live use.

Unregistered and composition businesses cannot select a tax-collecting mode. Composition documents include the relevant no-tax-collection statement. A regular GST business using no-tax mode cannot retain positive configured tax/cess rates on an issued bill. Composition/exempt/zero-rated and mixed-supply treatment still needs review; the app does not classify transactions automatically.

[CBIC Rule 48](https://taxinformation.cbic.gov.in/content-page/explore-rules/1000139/1000001) imposes specific electronic-invoice requirements on notified persons. [GST IRP guidance](https://einvoice6.gst.gov.in/content/new-advisory-on-e-invoicing-enablement-status-update-for-taxpayers/) describes threshold enablement, and [the reporting-window advisory](https://einvoice6.gst.gov.in/content/revised-time-limit-for-e-invoice-reporting-for-businesses-with-aato-of-%E2%82%B910-crores-above/) describes a later time limit for covered taxpayers. Applicability depends on the actual business and transaction. The app deliberately does not infer eligibility from an unchecked turnover field. If the owner marks e-invoicing as required, invoice issuance is blocked until a real integration exists.

**Not implemented:** IRN/IRP submission, signed QR verification, e-way bills, GST return filing, GSTIN active-status verification, export/SEZ/RCM treatment, fixed-amount cess, statutory accounting or Indian payroll/TDS/EPF/ESI engines. A manually typed bank or UPI reference is not a verified payment-provider callback.

## Free pilot and future paid service

The interface says **Free pilot — No charges**. There is no payment-card collection, automatic trial conversion, subscription charging or hidden expiry. Agree pilot expectations outside the app. Introduce paid access only after prices, notice, consent and payment-provider handling are implemented and tested.

A sensible later package is a maintained business service: configured profile, agreed staff/branch scope, onboarding, hosting, monitored backup, updates and bounded support. Price exceptional migration, integrations and bespoke work separately after discovery. Do not count total MSME registrations as an addressable market or assume every small shop will subscribe.

Test prices only after measuring value. Possible interview anchors—not launch prices or validated demand—are INR 799–1,499/month for a simple connected workspace and INR 1,499–2,999/month for more involved sector operations. Retain the earlier Nepal hypotheses separately; do not convert prices at a fixed assumed exchange rate.

For every pilot record subscription willingness, setup time, import effort, support minutes, peak users, stored attachments and infrastructure cost. Contribution = revenue − hosting allocation − backup/storage − payment fees − support cost. Free pilots cost real money to operate. Confirm an operating budget before promising uptime or free hosting at scale.

Do not penalise staff accountability by making businesses share one login. Never withhold a customer's export to pressure payment. Define read-only access, data export and retention when a subscription ends before adding enforcement.

## The path to a production SaaS

### Ready in this candidate

A locally runnable app, private HTTPS deployment configuration, four profiles, country configuration, personalised client/work records, catalogue billing, retained line returns, audit, roles, backups and encrypted offline drafts. Automated verification is recorded in `VERIFICATION.md` and the exact GitHub commit checks.

### Required before each business uses live financial records

1. Confirm registration/country, required bill format, taxes, numbering, retention and permitted workflows with its accountant. Use another compliant invoicing system for unsupported cases.
2. Configure a private customer instance and domain, secure owner recovery, staff permissions and device access. Do not put unrelated paying organisations under one owner account.
3. Configure an encrypted offsite destination, monitor backup success and complete a restore to another instance. Local backups alone are insufficient.
4. Reconcile opening customers, credit balances and stock against signed-off source records. Start with a controlled subset if history is unreliable.
5. Observe real staff completing sector scripts on their actual phones, network and printers, including a lost response and recovery.
6. Define support hours, incident contact, recovery objectives, privacy terms, export/retention and upgrade procedure. Have the deployment independently reviewed.

### Required before selling a self-service multi-tenant SaaS

An organisation membership/tenant model, isolation enforcement for every query/job/file/export, owner invitation/recovery/MFA, platform-admin boundaries, durable distributed sessions and rate limits, billing entitlements and idempotent provider webhooks, provision/deprovision workflows, offsite restore monitoring, queues, operational alerts, measured capacity and migration/rollback controls. Add automated cross-tenant denial tests for all entry points. A business profile is not a security tenant boundary.

Build an app-wide privacy and data lifecycle process. The [official DPDP commencement notification](https://egazette.gov.in/WriteReadData/2025/267647.pdf) uses staged commencement; do not rely on a simplified “all rules are already active” claim. Review the applicable dates, role and obligations for your launch with qualified counsel. Define purposes, access, notices, retention, permitted deletion/anonymisation, contact requests and breach response. Financial retention may limit deletion; the app must not silently remove posted records. The marketing checkbox and JSON export are not a complete privacy programme.

## How to learn from all four sectors

Use 3–5 businesses initially, covering the profiles where possible. This is a design sample, not market validation. Observe the owner and the actual person doing the work; their problems differ.

- Baseline: ask for the latest unpaid invoice, delayed job, failed booking, stock correction and return. Record their current steps and time.
- Setup: let the operator choose sector, speciality, tax mode, work stages and five important fields. Record which terms are unclear.
- Daily use: watch the busiest 30–60 minutes; measure repeated typing, abandoned forms, printer problems and time to answer a client question.
- Exceptions: test partial receipts, revised estimates, returned goods, duplicate submissions, conflicting devices and a restore.
- Commercial decision: present a real scoped paid offer only after the owner has used the product. Record an accepted offer or refusal and its reason; compliments are not conversion.

Suggested pilot targets, not results achieved: repeat-customer bill in 60–90 seconds; first correct bill within five minutes after setup; at least 90% unassisted completion for selected routine tasks; no unexplained balance/stock variance; all sampled due promises visible; no lost or duplicate posted money in interruption tests. Track support minutes and retention alongside speed.

The next features should follow repeated evidence. For example, add a receipt-printer integration only after recording printer models and formats; add WhatsApp only after selecting the provider, opt-in rules, approval step, delivery logs and budget; add richer AI only after reliable structured records and permissions exist. Generated text must not be presented as a bank confirmation, customer approval or tax filing.

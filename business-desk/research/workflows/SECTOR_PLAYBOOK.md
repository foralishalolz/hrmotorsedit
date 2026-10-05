# Sector workflows, pain points and acceptance

These scenarios are operating hypotheses for client discovery. They are not claims of survey prevalence. Status refers to 2.2.0-rc.1; country billing/legal acceptance is required separately. Configure only modules that a business actually needs.

## Shared owner pain-point map

| Problem to verify | Business consequence | Desired workflow | Current app / remaining work |
|---|---|---|---|
| Work has no clear owner/next date | Repeated calls and missed promises | Every active request has an assignee, stage, blocker and next action | Jobs/leads/follow-ups exist; capacity optimisation and push dispatch are proposed |
| Approval is buried in chat or changed after work | Disputes and unbilled extras | Retained estimate version and explicit approval; new scope re-approved | Quotes/approval/evidence and supported work gate; customer portal/e-signature delivery proposed |
| Old credit and current sales mixed | Unreliable collection priorities | Reconciled opening plus dated retained bills/receipts/credits | Implemented; native accounting import/write-offs/bank reconciliation separate |
| Payment status trusted from a screenshot | False collection or duplication | Verify provider evidence; record once; reconcile exceptions | Manual receipts/unique commands; actual provider integration absent |
| Physical stock differs from the sheet | Delays, overselling and unexplained adjustments | Purchase receipt, consumption, return decision and reasoned count | Stock ledger/counts; batch/warehouse/supplier-return ledger absent |
| Discount/pricing depends on one person | Delay at counter and margin leakage | Reviewed catalogue/client/quantity rules; privileged exception | Implemented narrow rules; advanced contract pricing/versioning separate |
| Staff share the owner's account | No accountability and wage/data exposure | Separate role/business-scoped accounts | Implemented; MFA/device revocation/account recovery expansion needed |
| Attendance and job time confused | Disputed wages and distorted job cost | Presence, task time, approval and payroll period separate | Implemented basics; statutory payroll/leave/overtime policy engine absent |
| Repeat service and promises forgotten | Lost returning customers | Dated action with owner/outcome, then next date | Implemented records; automatic campaigns/dispatch absent |
| App setup is overwhelming | Abandonment before first useful transaction | Business-owned identity, four profiles, six-step setup, few relevant modules | Implemented; observational localisation/onboarding refinement needed |
| Internet or device fails during money entry | Staff re-enter and duplicate posting | Uncertain command retains ID; Sync reviews outcome | Implemented; independent offline final billing/local-cloud replication absent |
| Nobody has restored a backup | A small failure becomes business loss | Protected offsite/provider backup and timed isolated restore | Local backup/cloud export exist; operator disaster recovery must be configured/proved |

## Garage, maintenance and collision

### The normal work chain

1. Find/create the customer and vehicle. Record complaint, arrival, promised time, existing damage and authorised contact. Avoid asking for unrelated identity documents.
2. Inspect/diagnose. Mark what was checked, observations and recommendations; attach relevant evidence. “Urgent” is a finding, not customer approval.
3. Prepare a quote with labour/parts/subcontract descriptions, discounts, tax treatment, validity and exclusions. Retain the version the customer/insurer actually approved.
4. Record authorisation and open/assign work. Apply the configured approval gate. Identify the waiting reason and next responsible action if work cannot start.
5. Record parts consumption and task time against the job. Receiving a supplier bill is not physically receiving a part. Additional damage needs a supplement/new approval.
6. Perform quality/handover checks using the configured checklist. Review billability, consumed parts and appropriate bill details before issue.
7. Bill once, allocate advance/part-payment, preserve different payer obligations, and collect/reconcile the remainder. A completed job may still need a collection follow-up.
8. Record handover with completed checks and the business's collection rule/owner exception; create the agreed next service contact where needed.

### Roles and phone screens

| Role | Must see quickly | Must do | Must stay restricted |
|---|---|---|---|
| Owner | Late/blocked jobs, approvals waiting, payer dues, contribution inputs | Assign responsibility, review exceptions, accept cash/stock differences | Only owner-approved financial/permission changes |
| Adviser/front desk | Customer/vehicle, approved scope, promised date and contact | Quote, approval evidence, next action and status explanation | Wages, unrelated business/customer finance outside granted scope |
| Technician | Assigned card, complaint/findings, checklist, required part/blocker | Findings, task notes/time, complete permitted checks | Price/credit overrides, payroll/whole-company financial reports |
| Stock clerk | Required item, ordered/received/available quantity | Receive/issue permitted stock, record source/reason | Payroll and broad collection/owner finance |
| Cashier | Issued bill, approved credit/advance, payer and outstanding amount | Receipt/refund within permission, print and cash count | Altering issued scope or technician recommendations |

### Collision and insurance exceptions

Maintain customer authority, insurer authority, surveyor/contact, claim reference, original estimate/comparison sources, revisions, expected payer shares, settlement deductions and actual receipts. Original competitor documents must remain original; transcription must retain provenance; hypothetical comparisons must stay labelled. Never manufacture an independently issued competitor quotation for an insurance submission.

Discovery cases: unseen damage after dismantling; insurer rejection; authorised amount below repair estimate; depreciation/excess; insurer pays customer; customer pays first and later recovers; subcontract repair; total-loss decision; client changes delivery date; rework without another charge. Each changes approval, billability, payer or next action. Record the actual process instead of assuming all claims settle the same way.

Current limits: no live insurer/surveyor portal, automatic claims submission, binding digital customer signature or automated settlement allocation from external advice. The app's claim/receipt records do not replace the insurer's process. Progress invoices across one job and advanced warranty/rework accounting need scoped work.

Acceptance with fictional numbers: quote 10,000, retain approval, consume two parts, bill the approved scope, collect 3,000 and show the remaining 7,000. Credit a legitimate original line and separately record any actual refund. Verify stock was consumed once, and final-stage rules require the configured checks/collection or a recorded owner exception. Use accountant-reviewed country/tax figures; the numbers illustrate state transitions, not a rate recommendation.

## Vehicle showroom and sales team

Normal chain: enquiry → assigned salesperson/next action → model/budget/finance notes → distinct chassis inventory → exclusive reservation → booking/advance evidence → reviewed bill → collection → PDI/documents/handover → next relationship action.

Pain hypotheses: salespeople lose contact history, stale finance statuses, two staff promise one VIN, owner sees bookings as cash, and incomplete documents cause delivery delays. A prospect list should show the next action and ageing reason, not only expected revenue. “Approved finance”, “disbursed” and “receipt recorded” are separate events.

Configuration: new/used/two-wheeler scope, model/variant vocabulary, location, customer budget/trade-in interest fields, sales responsibility, lead stages, source/lost reasons, reservation policy and delivery checks. Explain which responsibilities belong to sales versus stock/delivery versus cashier.

Exception cases: cancelled reservation, expired booking, switch to another VIN, refunded advance, rejected finance, lender disbursement shortfall, customer exchange vehicle, manufacturer incentive, registration delayed, damaged demonstrator and sale return. Current VIN/reservation/invoice/handover path handles the ordinary case and double-reservation prevention; many dealer, trade-in, used-margin and issued-vehicle-return accounting cases are not supported.

Commission discovery: booking vs delivered vs collected basis, dealer discounts, finance referral fees, salesperson splits, returns and targets. Current fixed collection-linked commission is narrower than a complete dealership incentive engine. Do not pay a promised commission as if lender funds arrived.

Acceptance: two staff reserve one chassis concurrently; only one succeeds. Allocate a reviewed advance, bill/collect, complete required checks, and deliver. Confirm failed/cancelled steps do not create an unexplained duplicate sale or receipt. Test branch/role scope with another user's phone.

## Retail, spare parts, electrical and trading

Normal chain: supplier/catalogue setup → purchase/order → partial physical receipt → supplier bill/payable → counter or credit sale → issue/stock deduction → receipt/customer balance → return/credit/refund decision → count/reorder.

Pain hypotheses: wrong SKU/compatibility, pack vs unit confusion, forgotten credit, inconsistent customer prices, delayed invoice entry, receiving stock twice and turning every returned part into sellable stock. Shelf stock, reserved demand and on-order quantity should have distinct meanings; the present app does not implement every reservation/warehouse model.

Counter configuration: top catalogue, SKU/barcode, units, reviewed price/tax, client terms and quantity prices, receipt method, printer/document format and return permissions. Warehouse configuration: supplier, lead time/reorder level, count responsibility and evidence for adjustments. Input barcodes work as keyboard text; camera scanning/hardware drivers are proposed.

Exception cases: partial supplier delivery, invoice later, wrong quantity/price, damaged purchase, customer part-supplied repair, substituted compatible item, negative opening correction, returned sellable/non-sellable item, credit sale beyond agreed limit and unknown duplicate client. Supplier credits/returns, multi-warehouse transfers, batch/expiry, multi-unit conversions and full landed-cost valuation are gaps. A notes field is not a reliable substitute for an inventory algorithm.

Acceptance: receive five of ten ordered units; record the supplier bill without receiving again; sell two units; collect only part of the price; credit one original unit and explicitly restock only if sellable; record the actual refund separately. Compare stock movements and financial balances to an independently prepared worksheet. For a physical count, a conflicting item-version change must stop posting rather than silently overwriting the latest quantity.

## Appliance, AC, equipment and field service

Normal chain: client/site/asset → request → triage/booking → diagnosis → quoted scope/approval → technician/work/parts → test/completion → bill/collection → warranty or next service/contract action.

Pain hypotheses: staff do not know site access or asset history, customer calls repeatedly for status, required parts are discovered too late, repeat visits are forgotten, and technician completion is assumed to mean collection. Separate a work-completion check from an agreement entitlement or a future renewal promise.

Configuration: service area, appointment labels, site access/contact, asset model/serial/warranty fields, work stages, checklist, technician permissions, standard service catalogue and manual return/renewal dates. Keep the phone card short enough for a technician to use while at the site.

Exception cases: client not available, no access, diagnosis-only charge, repeated unresolved fault, part ordered, customer declines repair, warranty dispute, third-party installer, emergency visit, several assets on a contract and advance paid by head office. Current bookings/assets/jobs/agreements cover basic recording. Route optimisation, GPS, automatic dispatch, recurring entitlement consumption/billing, customer signatures and warranty adjudication are absent.

Acceptance: book a visit; retain diagnosis and approval; consume a part; complete checks; bill and partially collect; set a next action with a responsible staff member. A recommendation for an additional repair must not automatically become a billed item. An overdue visit should remain visible even if a technician marked another task complete.

## Adjacent sectors: assess fit before expanding

| Sector | Reusable core | Missing domain work | Pilot decision |
|---|---|---|---|
| Tyre/battery/accessory shop | Catalogue sales, customer/vehicle, fitting job and receipts | Serial/warranty tracking, tyre specifications/fitment and disposal workflow | Narrow pilot only where those gaps are handled explicitly |
| Salon/beauty/fitness service | Customer, appointment, attendance and collection | Resource booking capacity, packages/membership liability, commission splits, service-specific privacy | Discovery/design; not a claimed ready vertical |
| Small distributor | Customer pricing, suppliers, stock and dues | Sales routes, delivery proof, truck/warehouse stock, schemes and supplier returns | Standard single-stock trading only; distribution suite proposed |
| Installation/project contractor | Estimate, work stages, parts/time and collections | Milestones, retention, variations, subcontract payable and project accounting | Simple service jobs only; complex projects unsuitable today |
| Small manufacturer | Supplier/stock/catalogue/work recording | BOM, production order, yields/waste, WIP, quality lots and costing | Not a manufacturing ERP today |
| Restaurant/hotel | Some clients, purchases, attendance | KOT/table/room/reservation, recipe/expiry and domain settlement | Not a ready hospitality POS/PMS |
| Pharmacy/healthcare | Generic stock/appointments | Clinical/prescription controls, batch/expiry, sensitive data and regulated workflows | Do not onboard as a healthcare replacement |
| Jewellery/financial services | Basic contacts/receipts only | Purity/weight valuation, custody or regulated financial ledgers | Not a fit for the current general ledger |

Breadth should come from a stable shared core plus deliberately tested sector adapters. Renaming “job” does not implement manufacturing, hospitality or medical workflows. This decision prevents a broad onboarding promise from forcing a business into inaccurate records.

## Configuration contract for each client

Agree: organisation/legal business scope; country/currency/registration; identity; sector/speciality; work stages and final stage; authorisation and exception roles; essential fields; checklists; client prices/terms; stock identities/units; pay/commission basis; follow-up rules; source openings; device/backup expectations; and explicit unsupported cases.

For every custom request capture an example, trigger, normal result, permission, money/stock effect, correction path and acceptance. Use configuration when existing semantics fit. Add a maintained feature only when a genuine workflow requires it. Narrative notes guide discovery; they do not silently redefine ledger rules.

The [client worksheet](../discovery/CLIENT_WORKSHEET.md) turns these choices into a reviewed setup. The [feature plan](../FEATURE_PRIORITIES.md) separates immediate pilot blockers from later integrations.

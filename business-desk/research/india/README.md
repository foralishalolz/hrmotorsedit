# India: operating needs and product fit

Research checked 5 October 2026; app baseline 2.2.0-rc.1. Read with the [detailed India switching playbook](../../docs/INDIA_MARKET_AND_SWITCHING_PLAYBOOK.md). Public facts and vendor capabilities are cited; the customer scenarios and priorities are proposals requiring observation.

## What the market evidence means

The MSME dashboard reports **97,417,406 Udyam-plus-UAP registrations as of 3 October 2026**. Registrations span very different scales/activities; they are not active businesses willing to buy this app. A small number of qualified, supported sector pilots is more useful than a fictional national conversion-rate forecast. [I1](https://dashboard.msme.gov.in/)

SIDBI's Jan–Mar 2026 outlook reports broad margin pressure across covered manufacturing/trading/services firms, with many reporting unchanged margins and some declines. Our inference: owners need visibility into discounts, parts/labour cost, rework and collections; software cannot remove input-cost shocks or guarantee profitability. [I2](https://www.sidbi.in/uploads/publicationreport/MSME_Report_R6_Final_march_2026.pdf)

NPCI reports **24,508.96 million UPI transactions in August 2026**. This is national payment activity, not merchant count or demand for our product. Build a reviewed collection/reconciliation workflow, not just a decorative QR/payment button. [I3](https://www.npci.org.in/product/upi/product-statistics)

MSME Samadhaan is an official delayed-payment mechanism with eligibility/process requirements. Good source records may help a business organise a dispute; an overdue badge is not legal recovery or adjudication. [I4](https://ramp.msme.gov.in/ramp/RAMP-initiative/msme-samadhaan/msme-samadhaan)

## Segment by workflow, scale and decision-maker

| Client type | Main operating hypothesis | Fit today | Discovery that changes the design |
|---|---|---|---|
| Independent garage/two-wheeler workshop | Owner wants less repeated explanation and fewer missed repairs/collections | Work cards, approvals, inspections, parts/labour, client history | Walk-in volume, job vocabulary, phone literacy, who issues the bill |
| Body/paint/collision shop | Need estimate/supplement evidence, responsibility and split-payer collection | Claims/originals, revisions, jobs, receipts and follow-ups | Insurer process, excess/depreciation, outsourced work, approval authority |
| Parts/electrical/hardware trader | Fast checkout plus trusted quantities/prices and customer credit | Catalogue bill, agreed prices, stock/suppliers, statements | Unit conversions, barcode quality, B2B GST details, warehouse/return needs |
| Vehicle dealer/showroom | Every prospect/chassis/advance needs an accountable owner | Enquiries, exclusive VIN reservation, invoice/collection/handover | New vs used, finance/disbursement, manufacturer requirements, trade-in accounting |
| AC/appliance/equipment service team | Visits/jobs must survive hand-offs and parts delays | Appointments, assets, work stages, agreements/follow-ups | Dispatch geography, warranty, service contracts, billing milestones |
| Owner plus outside accountant | Owner needs daily operations; accountant needs complete reliable books | Auditable operations and reviewed exports | Existing Tally/Zoho process, chart of accounts, month close and tax filing |
| Several businesses/branches of one owner | Remote visibility plus business-specific terms/roles | Business switching and role scope | Legal entity/GST registrations, inter-branch transfers, consolidation |

Ask separately who owns the business, who enters records, who approves exceptions, who pays for software/hosting, and who can veto the switch. A cashier's preference for speed and an accountant's preference for correct exports are both adoption constraints.

## Daily work and the cost of fragmentation

The proposed core failure pattern is that a request is recorded in one place, approval in another, parts on a notebook, and payment in a banking app. The owner repeatedly asks staff for status and cannot trace the outstanding amount. Validate this with one actual recent transaction from first contact to final collection; do not assume every business still uses paper.

The workspace should keep a customer/asset reference, retained approved scope, current stage/blocker, responsible staff, bill/receipt links, next action/date and original evidence. The owner needs a useful exception queue, not another screen of unrelated totals. Repeated re-entry of client/item details should be replaced by catalogue/client search and deliberate review.

Current app fit: those records, stages, roles, assistant questions, client terms, quantity prices, business identity and manual follow-ups exist. Current limitation: no automated external messaging, bank settlement, universal accounting adapter or real-time event feed; a role view may require refresh to see another user's update.

## Counter speed without weakening the ledger

A trader's fast path should be customer/walk-in → catalogue item/barcode → quantity → visible price/discount/tax → review → issue → receipt. Keep commonly used items/search easy and the focused form short. A receipt amount must not silently mean the full bill was paid. The operator should see remaining balance and change/refund policy explicitly.

Personalisation should show the business name/logo and locally understood work labels. Customer rules should explain which agreed price/discount/credit term applied; staff can review a manual price, and privileged exceptions require the supported reason/audit. Do not expose payroll/whole-company margins to every counter user to make navigation faster.

Proposed tests: ordinary two-line bill, credit sale, advance allocation, mixed payment arrangement, partial return, damaged return without restocking, wrong price corrected before issue, interrupted posting and duplicate barcode. Current stock issuing/line credit/refund mechanics cover much of this; split-tender automation, printer drivers, product variants and sophisticated POS registers are not complete.

## Trade credit and UPI reconciliation

For each credit client identify the actual debtor, due terms, limit, collections contact, disputed items and historical source. Separate owner-approved opening balance from new issued sales. The app's owner override should be an intentional recorded business decision, not an everyday way around a bad configuration.

For UPI ask how many collecting accounts/QRs exist, whether a cashier can confirm credit, how references/fees/refunds appear and how month-end statements are checked. Current receipt methods/references and cash counts do not verify provider success. A customer showing a screenshot does not prove settlement. A paid flag can represent a reviewed manual record; it is not a payment-provider callback.

Proposed next scope: import one agreed bank/acquirer statement format, match each external transaction once to an app receipt, preserve provider reversals/fees, and queue unmatched differences. Only then add signed webhooks/automatic receipt confirmation with duplicate/reversal testing. Do not mark debt collected from a payment-request link or “initiated” status.

## Indian registration and documents

Rule 46 specifies tax-invoice particulars such as supplier/recipient identity, numbering, classification, quantities/value and tax/place-of-supply details. Current domestic calculations and printed documents must be accepted for the client's actual registration/items; selecting “India” is not a general GST approval. [I5](https://taxinformation.cbic.gov.in/content-page/explore-rules/1000136/1000001)

The app supports INR/Asia-Kolkata, registration state, GSTIN format/state checks, ordinary domestic CGST+SGST/UTGST or IGST, tax added/included, HSN/SAC entry, percentage cess, retained seller/client snapshots and April–March numbering. Unregistered/composition setups cannot collect tax under the supported configuration. A format check does not verify active GST registration.

Check supply type, classification/rate, recipient/state, rounding, series and returns with the accountant. IRP/e-way bill, RCM, export/SEZ, fixed-amount cess, used-vehicle margin treatment and other specialised cases are unsupported. The IRP advisory's 30-day reporting restriction for AATO ≥ ₹10 crore is separate from the rules deciding mandatory e-invoicing. Do not copy it into a universal eligibility switch. [I6](https://einvoice6.gst.gov.in/content/revised-time-limit-for-e-invoice-reporting-for-businesses-with-aato-of-%E2%82%B910-crores-above/)

If e-invoicing is required, the current flag blocks issue because no genuine IRP adapter exists. Keep unsupported statutory documents in an accepted system until integration is reviewed. Do not encourage an owner to leave the flag false to get past the gate.

## Staff, attendance and incentives

Discover the actual employment basis, shifts, overnight work, breaks, leave, salary advances, approval responsibilities and deductions. Attendance is not billable job time; a productive technician can spend time on diagnosis/rework that should not become an unauthorised charge. Collection-linked commission can discourage leaving unpaid deals unmanaged, but the rule needs exceptions and fairness checks.

Current support includes attendance, timers, reviewed payroll, advances and fixed earned/collection-linked commissions. Tiered targets, complex splits, refund clawbacks, statutory payroll filings and payroll bank transfer are separate work. Agree whether the base excludes tax, returns, discounts or parts cost; test the same policy on a refund/part-paid case before payout.

Statutory employment obligations can depend on location, establishment and employee circumstances. Do not use one generic deduction percentage for all Indian SMEs. Keep the actual accountant/payroll process, using [official EPFO resources](https://www.epfindia.gov.in/site_en/For_Employers.php) and the applicable official state/central sources. This application is not a statutory payroll engine.

## Switching and customisation

Common alternatives to investigate include paper/Excel, an accounting package, a credit-ledger app, POS, dealer software and service-specific tools. Ask to see the actual current export/templates. Tally's official import/mapping workflow illustrates why migration is more than copying column headings. Our current CSV importer is not native Tally/Zoho voucher synchronisation. [V2](https://help.tallysolutions.com/getting-started-with-importing-data-into-tallyprime/)

Use one reconciliation date and preserve history/source documents. Import supported masters in reviewed batches, match customers/SKUs, check balances, count stock and agree what history remains in the old read-only system. Do not re-create old taxed sales merely to seed a new balance. Retain the old system until the owner/accountant accepts the new authoritative workflow; formal invoice numbering must not accidentally overlap.

Customisation means explicit settings, not a separate code fork for every shop: sector/profile, business identity, stages/checklist, roles, fields, client terms/price rules and supported approval/credit/handover gates. If an unusual requirement needs a new algorithm or ledger type, give it a specified example, exceptions and acceptance tests. The guided discovery notes are retained context, not executable instructions.

## Privacy and trust

The official November 2025 commencement notification stages different DPDP Act provisions over immediate, one-year and eighteen-month dates. At this research date, do not claim the whole regime came into force at once or that the app is certified compliant. Obtain a current applicability/processing review. [I7](https://egazette.gov.in/WriteReadData/2025/267647.pdf)

The design proposal is purpose-based collection, clear contact preference, role-restricted records, secure devices, retention/export/deletion procedures and actual incident/account-recovery ownership. The current app provides parts of this through roles, sessions, audit and encrypted drafts; consent lifecycle, public data-subject workflows, MFA and independent review are incomplete. A marketing preference checkbox alone is not a complete legal consent system.

## Pilot economics and proof

Do not claim the app replaces full accounts, statutory payroll, manufacturer dealer integrations or all specialist POS features today. Lead with the supported operational value and verify it against the client's current process. The free pilot has no automatic charging/card collection; hosting, backup and support still incur costs.

For each proposed pilot measure a baseline week and an agreed comparison period: time to create a request/bill, owner interruptions, overdue next actions, unreconciled stock/cash, collection ageing, repeat re-entry, support minutes and peak users/attachment storage. Annotate business volume/seasonality; a before/after change is not necessarily caused by the app.

Price/support hypotheses come after demonstrated use and a costs worksheet; no registration statistic validates willingness to pay. A retained, successfully configured business is more valuable evidence than dozens of signups that never complete a real transaction.

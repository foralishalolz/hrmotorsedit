# Nepal: operating needs and product fit

Research checked 5 October 2026; app baseline 2.2.0-rc.1. Facts link to [primary sources](../SOURCES.md). The business scenarios below are **hypotheses to validate**, not invented Nepalese customer interviews.

## What the evidence can tell us

The NSO portal displays **923,356 establishments**, **462,605 registered establishments** and **3,228,457 persons engaged** for the **2018 economic census**. These are historical establishment figures; do not label them as today's business count or a software-buying market. [N1](https://ec.nsonepal.gov.np/)

In the World Bank's 2023 formal-firm profile, **75.8% experienced electrical outages**; political instability was the leading perceived obstacle, followed by finance/tax concerns. Its sample excludes firms with fewer than five employees. It is evidence of constraints among covered firms, not proof of today's outage rate or every micro garage's main problem. Software cannot remove political instability or replace credit. [N2, pp. 3, 11–13](https://www.enterprisesurveys.org/content/dam/enterprisesurveys/documents/country/Nepal-2023.pdf)

NRB records **72,438,302 QR-based transactions**, **53,006,769 wallet transactions** and **78,653,719 mobile-banking transactions** in Saun 2083, mid-July–mid-August 2026. These are transactions, not unique customers or shops. Their operational implication is to keep payment channel, reference, payer and reconciliation evidence distinct from an issued bill. [N3](https://www.nrb.org.np/psd/payment-systems-indicators-of-2083-saun/)

IFC's May 2025 study discusses digital/financial literacy barriers and differences across rural and urban settings. ESCAP's 2020 study describes a lending gap for micro/small enterprises whose needs may sit between microfinance and bank products. These support investigating training and record quality; they do not prove this app will improve loan access. [N4](https://www.ifc.org/content/dam/ifc/doc/2025/digital-financial-services-in-nepal.pdf), [N5](https://www.unescap.org/resources/micro-small-and-medium-sized-enterprises-access-finance-nepal)

## Do not make “Nepal” one persona

| Discovery group | Operating hypothesis to check | Good starting workspace | What could prevent adoption |
|---|---|---|---|
| Owner-operated neighbourhood garage | Owner does diagnosis, estimates and collection; work details live in memory/chat/notebooks | Small daily work queue, client/vehicle history, approval, collection | Extra typing, unsuitable language, unclear invoice authority |
| Collision/paint workshop | Several approval parties, supplements and promised deliveries | Jobs, inspections, claim evidence, payer balances, follow-ups | Treating insurer authorisation as received money; missing original evidence |
| Spare-parts/electrical trader | Credit customers, uncertain shelf stock and partial supplier receipts | Fast bill, customer statement, stock and supplier dues | Wrong part compatibility, poorly reconciled openings, excessive checkout steps |
| Vehicle showroom | Enquiries, bookings, chassis commitments and delivery documents | Enquiry owner/next action, VIN reservation, collection, handover | Finance status confused with disbursement; unsupported trade-in tax/accounting |
| Appliance/equipment repair team | Site visit, diagnosis, approval and parts wait | Booking, asset/job, technician, checklist, next service date | Needing dispatch/navigation or warranty adjudication beyond current app |
| Family business with an outside accountant | Daily operations managed by family, formal books maintained elsewhere | Restricted staff roles and reviewed month-end exports | Expecting this operational ledger to replace general accounts/filing |
| Multi-location owner | Wants remote visibility and clear responsibility | Explicit organisation/business scope and per-business staff access | Assuming existing records implement inter-branch transfers or a consolidated legal entity's books |

Record district/city, connectivity, language, staff, customer type and operating method for each actual client. Do not assume every Kathmandu shop is digitally fluent, every provincial shop is offline, or family staff should share the owner's login. Include women owners, older staff and people with different reading/access needs in testing; demographic assumptions are not product requirements.

## The owner's real decisions

An owner should be able to answer: Which jobs are blocked? Which promised delivery will slip? Who has agreed to what? What cash was actually counted? What is still owed by the customer, insurer or fleet? Which part prevents completion? What supplier payment falls due? Who is available? What must I call about today?

Build each answer from retained records with a visible timestamp/scope and a way to open the underlying items. A single sales total cannot answer these questions. For example, a completed repair with an unpaid insurer amount needs a collection action even if the customer's excess has been paid. A quote accepted verbally needs an approval record even if the car is already at the workshop.

The current app has work/approval, due-action, receivable, stock, attendance and cash-count records. It does not turn every narrative onboarding answer into a programmed rule. Translate the owner's answers into explicit stages, checklists, roles, customer terms and supported operating gates, then test them.

## Credit and collection: make the relationship clear

Discovery must identify who legally owes the money, who usually pays, the agreed date, how reminders happen, whether multiple branches/family members use one customer account, and how an old balance was established. Phone/name similarity is not sufficient to merge accounts.

For a trader, distinguish an opening balance from a new sale, a receipt from a discount/write-off, and a customer advance from invoice collection. Keep an original ledger/source reference and reconciliation date. For a garage, distinguish the customer, fleet and insurer shares; retain the settlement communication, deduction reason and actual receipt separately. An insurer's promise does not close a receivable.

Current support: owner-reviewed customer openings, partial receipts, advances/allocations, credits/refunds, terms, next actions and full customer statements for roles with complete financial access. Limits: no bank feed, automated debt collection, arbitrary ledger corrections or insurer portal settlement. Source-key duplicate checks are narrower than intelligent account matching.

Suggested pilot measure: days between due date and collection, unresolved balance differences, and whether the owner can find the original bill/receipt on a phone. Count cash recovered from old debt separately from current-period sales; improvement cannot be inferred just from a higher dashboard total.

## Payments: acceptance, recording and settlement

The counter may receive cash, a bank transfer or a payment through a bank/wallet QR. Ask which account belongs to the business, which staff can confirm its credit and how fees/refunds are handled. Record the channel and actual reference with the receipt. Reconcile to the merchant/bank statement using the business's reviewed process.

The app's manually entered receipt is an operational record. It does not query eSewa/Khalti/Fonepay/connectIPS or verify that a screenshot is genuine. A screenshot is evidence to review, not a server-confirmed provider settlement. Cross-border QR activity does not make this app a currency-conversion or international-payment service.

Proposed next work after a payment pilot: an immutable match record linking receipts to imported provider statement rows, duplicates/reversals, fees and unmatched exceptions. Begin with a reviewed statement format and one acquiring account; do not invent an integration across every Nepalese bank. Automated callbacks require verified signatures, unique external IDs, retry/reversal handling and provider credentials before they can close a receivable.

## Tax documents: an explicit adoption gate

VAT calculations and a professional-looking PDF do not establish electronic-billing approval. IRD's hosted VAT Act translation describes prior approval/procedure in section 14A; IRD separately publishes listed software and CBMS developer material. **This application has no claimed IRD enlistment or electronic-billing approval.** [N6](https://www.ird.gov.np/public/pdf/116345766.pdf), [N8](https://ird.gov.np/content/9368/notice-17599213073/), [N9](https://ird.gov.np/content/9052/cbmsapitechnicaldocumentfor/)

IRD's **4 Baisakh 2083** notice calls for electronic issuance and immediate CBMS linkage for taxpayers with **annual turnover exceeding NPR 20 crore**, with the notice's stated exceptions. This is not a universal safe harbour below the threshold: the accountant must check the current procedure, approvals and any other applicable notices. [N7](https://ird.gov.np/content/13488/cbms-notice-01-04/)

Before live statutory billing obtain the actual PAN/VAT registration, business branch/series, required bill format, tax/rate treatment, invoice date/fiscal year practice, cancellation/credit procedure, retention and approval/CBMS applicability. Do not publish a blanket “IRD compliant” label. Where approval/integration is required and unavailable, keep statutory billing in an approved arrangement and use this app only for permitted operations/pilot records with a reconciled external reference. An external-reference workflow needs its own acceptance; do not issue a second tax bill for the same sale.

Current limits: BS date conversion is not built in; AD dates drive actions and fiscal labels are entered manually. CBMS credentials/submission/acknowledgements and an enforceable Nepal applicability gate are not implemented. An owner-entered field cannot itself certify compliance. This is a launch dependency, not a cosmetic backlog item.

## Dates, language and the owner's identity

The app uses NPR and Asia/Kathmandu for a Nepal business. It stores the business's own name/legal details/logo/colour/payment instructions and retains issued seller snapshots. Clients can have tags, terms and contact-language preferences. UI text remains English; storing a preference does not translate screens or documents.

Ask whether the owner wants Nepali, English or both on documents, whether staff enter Romanised names, what they call bills/credit/work cards, and which calendar they use to promise delivery, close a month and process wages. The prototype should display one unambiguous authoritative date and a validated equivalent only after a reviewed calendar library is added. Do not silently convert manually entered BS text with a guessed fixed offset.

Proposed localisation acceptance: a Nepali-speaking cashier completes a sale/partial collection without help; a print sample fits actual stationery/Unicode fonts; a date spanning the chosen fiscal boundary has the correct label; export dates remain unambiguous for the accountant. Test document fonts and a phone's available printer/share flow, not just a desktop screenshot.

## Parts, work and supplier realities to investigate

A collision job can be waiting for a part, repair permission, subcontractor, paint booth or payment. These are different blockers with different owners/next dates. Keep diagnosis and recommendation separate from customer authorisation. Supplement estimates must retain the previously approved scope. A customer's own part, a supplier replacement and a warranty rework need explicit decisions about stock, cost and billability.

A trader may order one quantity, receive another, and receive the supplier bill later. Use purchase → physical receipt → supplier bill → supplier payment as separate events. The app supports that separation and no-double-consumption for previously issued job parts. It does not provide an import/customs landed-cost allocation, multi-warehouse transfer, batch/expiry control or complete supplier-return ledger.

Ask the actual supplier lead time, part identity/SKU, substitutes/compatibility, unit/pack conversion, landed expenses, quantity/count tolerance and who may adjust stock. Start with verified physical counts and agreed prices; importing an old spreadsheet without reconciliation only makes old errors easier to repeat.

## Staff, payroll and commissions

Discover salary/daily/hourly basis, actual shifts/breaks, overtime approval, leave, advances, incentives, collection conditions and employer/employee deductions. Separate time on a job from attendance; a technician can be present but blocked awaiting a part. Do not use an incentive to encourage unapproved repairs or unsafe throughput.

Current payroll/commission calculation and approval prevent some duplicate payment/reservation errors, but are not Nepal statutory payroll, SSF filing or bank transfers. Check applicable employment/payroll rules with a specialist using [Labour Act/SSF official sources](../SOURCES.md). Keep an independently reviewed statutory process. Payroll-paid markers are excluded from the app's scoped cash-count arithmetic unless supported cash movements are separately recorded; do not present that count as the total cash book.

For commission interviews define the base (sale, collected amount or contribution), exclusions (tax, refunds, parts cost), splits, returns/cancellations, payout date and who approves. Current fixed earned/collection-linked commissions do not implement every tier/split/clawback policy. Record the policy and test one ordinary and one return example before enabling it.

## Privacy, devices and continuity

Phone numbers, vehicle identifiers, repair photographs and wages can expose clients/staff. Nepal's Privacy Act is a relevant source for an applicability review; it does not certify this app. [N11](../SOURCES.md)

Keep technical staff restricted to assigned work, and wages/owner financials behind roles. Teach logout and recovery on shared devices. Encrypted offline drafts expire after 24 hours; money/stock actions still require the authoritative server. If the business requires independently offline final billing for several days, the present cloud workflow is not a fit. A local app on an accessible PC has a different recovery/connectivity model; it is not automatic local/cloud replication.

Before onboarding: measure actual connections/devices, record tolerable outage/data loss, prove an offsite/provider restore, nominate support, and confirm the owner can export. Include a low-cost Android phone and the owner's real PC/printer in acceptance. National infrastructure statistics do not replace a test at that premises.

## Positioning and an adoption experiment

Nepal-oriented products already document accounting/reconciliation (Tigg) and mobile bookkeeping/offline/language/calendar capabilities (Karobar). These are vendor capability observations, not an independent ranking. [V5](https://help.tiggapp.com/article/reconciling-bank-accounts-in-tigg), [V6](https://apps.apple.com/np/app/karobar/id1566107724)

Our proposed entry point is coordinated sector work plus collection: “know the status, approval, parts, payer and next action for each repair/sale.” Do not force an accountant to abandon a complete ledger or a business to abandon approved billing before a replacement is validated.

Recruit a proposed initial mix of two garages/collision shops, one parts trader, one service team and one showroom where the current boundaries fit. This is a pilot design, not completed recruitment. Observe work, configure one workspace, reconcile openings, run parallel comparisons without duplicate statutory documents, and ask staff to complete ordinary/exception cases. Measure entry time, follow-up completion, balance/stock differences, support minutes and demonstrated recovery. Define the free pilot's support/hosting budget; no national statistic establishes a sustainable subscription price.

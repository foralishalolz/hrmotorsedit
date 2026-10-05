# India business operations and switching playbook

Research reviewed 5 October 2026. Product baseline: Business Desk 2.2.0 release candidate. This extends `INDIA_NEPAL_PRODUCT_RESEARCH.md` and the detailed client discovery questionnaire. The recommendations below are product decisions and hypotheses to validate with real owners and staff. No interviews, willingness-to-pay study, nationwide adoption estimate or production certification have been conducted.

## 1. What the product should become

Build an operating desk that a garage, parts shop, showroom or service team can make its own: its name, logo, vocabulary, stages, clients, agreed prices, checks and staff responsibilities. The value is that a customer request becomes approved work, material use, a bill, a receipt and the next visit without being retyped into disconnected registers. A business should open the app and immediately understand what needs attention, who owns it and what action to take.

Treat “replace every software” as an ambition to earn workflow by workflow. Accounting, statutory submissions, bank settlement, insurance portals and communications providers have external obligations and interfaces. Retain them until their replacement or integration is independently verified. Removing an essential tool before matching its outputs makes switching harder and can damage the business. A trustworthy product tells the owner which workflow it can take over now.

For the first pilot, the working assumption is one city cluster, owners with roughly 2–10 staff, and Excel/paper migration. The optional questions about region, team size and current tools were unanswered. These are starting assumptions, not established market preferences. The current UI is English; client contact-language preferences are stored, but they do not translate screens or documents.

## 2. Market evidence and its limits

The official MSME dashboard dated 3 October 2026 reports 9,74,17,406 registrations across Udyam and UAP. The categories are overwhelmingly micro enterprises; trading and services account for large reported activity groups. Registration counts include informal enterprises recorded through UAP and are not a count of software buyers, active garages or businesses able to pay a subscription. Use this evidence to justify studying small operational teams, not to invent a SaaS total addressable market. [S1]

SIDBI’s FY2024–25 annual report identifies timely and adequate credit as a continuing challenge. Its MSME Outlook work examines a sample of businesses rather than a census of every local business. The July 2026 MSME Pulse provides lending context, with important distinctions between enterprise and individual-business borrowers. Financing aggregates do not identify the repair shops most likely to adopt this product. [S2, S3]

RBI material identifies delayed payments, financing access, documentation and digital adoption as business challenges. Our product inference is to prioritise collections, source records, reconciled balances and auditable financial actions before adding decorative analytics. This does not mean that software guarantees credit approval or debt recovery. [S4]

NPCI’s published August 2026 UPI statistics show approximately 24.5 billion transactions for that month across the system. Those totals include payment contexts beyond the target sectors. They support making UPI a normal receipt method and retaining a bank reference, but do not prove that every shop uses UPI or that a screenshot confirms settlement. [S5]

Indian tax and privacy requirements are operational constraints, not optional interface preferences. The government’s e-invoice advisory extends a 30-day reporting restriction to taxpayers with AATO of ₹10 crore or above from 1 April 2025; the threshold for mandatory e-invoicing is a separate applicability question. Businesses must have their accountant determine the relevant obligations. The app blocks issue when e-invoicing is configured as required because it currently has no IRP integration. [S6]

The government notified DPDP rules in November 2025 with a phased implementation timeline. The applicable provisions and commencement dates need legal review for the actual launch. Do not describe this release as DPDP-certified. A design based on collecting only useful business data, restricting staff access and documenting retention is a practical starting point, not a legal conclusion. [S7]

## 3. Segment the market by how work happens

| Segment | Typical transaction | Primary switching problem | Configuration to investigate |
|---|---|---|---|
| Independent repair garage | Intake → inspection → estimate → approval → repair → quality → collection | Job scope, parts and receipts are disconnected | Vehicle identity, work stages, bays, technicians, required handover checks |
| Collision and paint shop | Damage evidence → insurer/customer approval → supplements → repair → settlement | Several approval versions and two payers | Original evidence, quote revisions, insurer reference, surveyor, excess and payer tagging |
| Two-wheeler workshop | Fast intake → service/parts → bill → return visit | Counter speed and recognising repeat clients | Phone lookup, registration, service catalogue, quick bill and short checklists |
| Fleet service provider | Multiple vehicles → rate agreement → jobs → consolidated collection | Agreed prices and credit are mixed with walk-in sales | Fleet tags, asset history, quantity tiers, terms, credit limits and statements |
| Spare-parts retailer | Catalogue lookup → quantity → tax bill → return | Stock disagreement, barcode lookup and duplicate item identities | SKU/barcode, HSN, categories, units, return rules and physical counts |
| Distributor or wholesaler | Order → availability → dispatch → credit collection | Customer-specific prices and long receivables | Quantity price tiers, warehouse location, limits, opening balances and statements |
| Vehicle showroom | Enquiry → vehicle reservation → finance → bill → PDI → handover | One chassis promised twice or delivered before collection | VIN, reservation, finance state, collection and delivery gates |
| Home/appliance service | Booking → asset history → visit → work → bill → renewal | Lost visits and customer instructions | Time, duration, assigned staff, assets and agreement expiry |
| Installation/service contractor | Proposal → site work → materials → completion → payment | Scope changes, responsibility and cost visibility | Work stages, site/custom fields, approval evidence, expenses and task time |

These are operational archetypes. A rural motorcycle shop and an urban fleet body shop may both call themselves garages while needing different daily screens. Ask about transaction count, parts handling, payer types and approval habits before selecting modules. Do not equate “small business” with low workflow complexity.

## 4. The owner’s day

At opening, the owner needs promised deliveries, overdue collections, unanswered estimates, parts shortages, scheduled visits and attendance needing review. Each should open the relevant record, carry a next action and allow a dated follow-up. A generic chart without a drill-down creates another task: the owner must find the customer elsewhere.

During the day, the owner handles exceptions: a customer changes scope, a technician finds further damage, a supplier substitutes a part, a cashier takes a partial payment, or a fleet asks to exceed its normal credit. The software should retain the original version, record the change and restrict exceptional actions. A new bill above a configured customer limit needs an owner’s reason; front-desk staff must not silently remove the limit.

At closing, the owner needs physically counted cash compared with recorded cash receipts, refunds, expenses and supplier payments. The current cash closing deliberately uses that specified scope. Payroll paid markers and unrecorded drawings are excluded; record relevant cash expenditure before counting. A replacement count needs an owner explanation and leaves the original count in place. Later dated cash entries flag that the count needs review.

Weekly, owners need open work, collections ageing, repeat visits, supply problems and provisional job contribution. Contribution is not profit: it excludes general overhead, and direct costs may still be incomplete. Do not present an attractive green number as an audited margin. Existing reports expose their underlying records and allow CSV export.

## 5. Staff-specific experience

| Person | Their daily decision | Screen and action | What must be protected |
|---|---|---|---|
| Owner | What needs intervention? | Today, follow-ups, financial records, business configuration | Cross-business isolation and review of overrides |
| Manager | Who is doing what and what is blocked? | Work stages, assigned staff, visits and parts | Salary and commission restrictions |
| Front desk | What did the customer ask and approve? | Customer/asset history, estimates, bookings and contact outcomes | Posted money, stock reservation and owner policy |
| Technician | What should I inspect and repair? | Assigned jobs, findings, checklist, timers and own attendance | Other technicians’ work and private costing |
| Cashier | What is billed, collected or refunded? | Invoices, receipts, customer balances and cash counts | Immutable money entries and owner-only credit decisions |
| Stock clerk | What arrived, was used and is available? | Items, purchase orders, supplier bills and movements | Customer payments and payroll |
| Accountant | Can I reconcile and retain the source? | Owner-provided statements, CSV and document evidence | Actual ledger/statutory requirements; no automatic compliance claim |

Create separate staff accounts. An owner sharing a password with every employee defeats role restrictions. The stock-clerk role is now explicit so a parts employee does not need manager access. Technician updates are restricted to assigned jobs; inspection findings use the same boundary.

Training should use each person’s actual daily scenario. A technician should practise an assigned inspection, not navigate payroll to learn the app. A cashier should practise partial collection, a wrong reference and a refund. An owner should practise reviewing a conflict and finding a source record.

## 6. Garage intake and inspection

A useful intake captures the customer, vehicle/asset identity, requested work, symptoms, date, promised completion, responsible team and existing condition. For collision work, attach the original images and approval documents. Preserve the customer’s instructions exactly enough that another staff member can continue the job. Custom fields can capture a particular shop’s repair category, insurer contact, key count or pickup arrangement.

The new inspection workflow records an area, condition, observed notes and recommended action. Conditions are not checked, good, advisory and urgent. Findings do not authorise charges. Chargeable recommendations should become a quotation that the customer approves; the approved revision becomes the retained scope. This prevents “we inspected it” from becoming an accidental claim that the customer agreed to the repair.

The garage’s checklist should represent real release criteria: for example, a visual inspection, functional check and customer belongings check. These examples are configuration prompts, not universal safety procedures. When the handover-check rule is enabled, the required configured checks must be present and completed. Deleting the checklist is not an acceptable way to pass the gate.

Investigate who can photograph vehicles, where photos are stored, whether clients expect a before/after report and which signatures are required. The current release retains attachments and findings; it does not provide a secure customer inspection portal or cryptographic digital signature. Do not promise those before building and validating them.

## 7. Estimate, approval and change control

A quick estimate should reuse catalogue descriptions, units, costs and relevant tax classification. The person entering it should be able to add a special line without creating permanent catalogue clutter. The calculation must be the same in the editor, approval view, printed document and report. Mixed line rates, included tax and domestic state-dependent GST must reconcile to the total.

Once sent, a quotation is retained. A change creates a new revision, preserving the former scope and approval history. Approval records who approved that exact version and through which channel. It does not send a message or claim a legally validated signature. Staff can attach original evidence from the communication channel actually used.

If a configured business requires approval of a linked quotation before work, moving into work stages is gated by that record. The final configured job stage represents handover. The payment rule requires at least one issued job invoice and settlement of the linked invoice balances before reaching that stage. An owner may record a reasoned exception, which is audited.

Future approval portals should use short-lived, record-specific links, an explicit revision number, an expiry, authorisation limits and retained evidence. A client must not gain access to the whole workspace through a public link. Decline and partial approval need deliberate rules; a button that approves an unspecified current document would undermine the retained version.

## 8. Insurance and legitimate comparison evidence

The existing insurance workflow retains insurer details, claim reference, surveyor/contact, requested amount, approved amount, payer shares, stage and the next follow-up. A claim approval is not money received. Receipts must be explicitly tagged to the claim and payer to support insurer/customer collection tracking.

Real third-party comparisons must retain their original issuer and source document. A staff transcription is distinguishable from an original. Hypothetical price scenarios are clearly labelled as hypothetical in the interface and print output. They cannot be presented as quotations independently issued by a competing business. This is essential for any insurance submission that depends on genuine evidence.

Pain hypotheses to validate include delayed surveys, missing documents, supplements agreed verbally, unclear depreciation/excess and staff not knowing whether settlement is the customer’s or insurer’s responsibility. The practical response is a next-action owner and due date tied to retained evidence, not a fabricated insurer integration.

Next work should explore a claim document checklist, supplement-specific approval trail and settlement reconciliation. Each insurer may have a different portal, document format and authorisation process. Pilot with original customer-authorised claim documents and verify every exported bundle before sharing it.

## 9. Catalogue, prices and counter speed

A parts counter needs an identifiable item, not merely a name that several employees spell differently. Prefer a retained SKU or barcode, then a useful description, unit, shelf, default cost and rate. Opening quantity is reconciled at switching. Subsequent differences use movements so the history is visible.

Quick bill supports catalogue search, SKU/barcode lookup, customer terms and a review step before issue. Scan codes identify a catalogue entry; they are not evidence that the right physical part was selected. Staff should still review fitment, unit and quantity. Catalogue rendering is bounded so a very large set does not create thousands of buttons at once.

New customer price agreements contain the catalogue item, minimum quantity and rate. Quick bill selects the highest matching minimum quantity. The customer’s default percentage discount is then applied to the agreed rate; the UI says so explicitly. This is an important question during discovery because some businesses intend discount-after-price and others do not. If the agreed tier already includes the full discount, set the customer percentage to zero rather than silently double-discounting.

The current price agreement application is in Quick bill. Manual quotation lines and manual document editing remain under staff review; the system does not silently rewrite a price the user entered. A future pricing engine needs an effective date, allowed customer groups, tax treatment, margins and a retained explanation of the selected rule.

## 10. Inventory and supplier reliability

Common hypotheses include stock quantities drifting, purchases being recorded as fully received when delivered partially, parts used on a job without an issue entry, and cash supplier payments being detached from the supplier bill. The existing app connects purchases, partial receipts, stock movements, jobs, supplier bills and payments.

A physical count should compare a captured recorded quantity with the quantity actually counted. The new command requires the expected quantity and item version to still match at posting. If stock moved during the count, staff must refresh and review. Posting several adjustments is atomic: a bad later line must not leave earlier count lines saved.

The current first implementation limits each posted count to 100 items. Staff should count in practical batches. Further discovery should determine whether the shop counts by shelf, category, supplier or fast-moving stock; the selector needs to match that habit. A wholesale warehouse should not be accepted merely because this feature exists—location/lot/serial needs and much larger catalogues require specific validation.

Future work can add approved reorder suggestions based on confirmed demand, purchase returns, serial/lot traceability, reservations and multi-location transfers. Do not forecast ordering from sparse pilot history as if it were reliable demand. Supplier quotations, actual receipts and actual payments should remain separate events.

## 11. Collections, credit and statements

Collections are a relationship workflow: the correct customer, retained bill or opening source, responsible person, agreed date, contact outcome and actual receipt. The follow-up screen should make a next action easy to create without forcing another duplicate customer record. Preferred channel and language are useful context; communication consent and operational contact need separate treatment.

A credit limit is a business policy, not a calculated credit score. A limit of zero means no configured limit. When the rule is enabled, new issue checks positive outstanding invoices and opening balances plus the new bill total. Only the owner can override with a substantive reason. It does not automatically net every unrelated credit or reserve credit for future draft work.

Opening balances address the first-day switching problem. An owner records the customer, signed reconciled amount, as-of date and source reference. Positive means owed; negative means customer credit. They are retained and cannot be edited or archived. Corrections are separate reviewed entries. A receipt or refund against an opening balance is capped by the remaining balance and cannot also be linked to an invoice.

The new customer statement includes issued bills, signed opening balances, credits and actual receipts/refunds. Unapplied customer advances are included in the account view; allocation still matters for clearing a particular invoice. The statement explains that distinction. Access requires the relevant financial read permissions so a restricted view cannot generate an incomplete ledger silently.

Samadhaan is an official delayed-payment mechanism with defined eligibility and a council process. Product reminders are not a substitute for that legal process, and the app should not automatically threaten legal action or calculate statutory consequences without professional review. [S8]

## 12. Payroll, attendance and incentives

Owners may pay monthly, daily or hourly and may agree collection-dependent incentives. The existing attendance workflow allows missing-punch corrections and review; payroll preparation is a deliberate calculation, followed by approval and an actual paid marker. The user-configured contribution and withholding fields do not establish statutory applicability.

A commission should record its agreed basis: net labour revenue, net service revenue, direct job contribution, a fixed referral or another agreement. Keep tax outside revenue-based commission assumptions unless the actual agreement explicitly specifies otherwise. Collection-dependent earnings become eligible from linked collected work; approved unreserved earnings can enter payroll. Reserving them avoids paying the same earning through separate payroll runs.

Questions to validate include leave policy, paid versus unpaid breaks, overnight shifts, overtime approval, piece-rate work, contractor status, staff advances, clawbacks, cancelled work and who authorises corrections. Daily attendance totals are not automatically a lawful salary calculation. Avoid adding an automatic deduction simply because a timer is missing.

EPFO’s employer material distinguishes establishment and employee compliance work from basic wage calculation and provides dedicated submission/payment facilities. Preserve those providers and professional workflows until a supported integration is verified. The release does not file EPF/ESI/TDS or initiate salary payments. [S9]

## 13. Showroom and service-specific work

A vehicle showroom needs one chassis reservation at a time, a customer/enquiry owner, finance state, bill, actual collection, PDI and documented handover. The existing reservation-to-delivery workflow gates collection and checks. Inventory status alone is not a delivery authorisation. A lost enquiry can release a reservation with a reason, preserving the enquiry history.

Vehicle-specific discovery includes used versus new inventory, trade-ins, registration coordination, document sets, finance commissions and warranty obligations. The current domestic tax calculator is not a complete used-vehicle margin-scheme or dealer accounting system. Do not onboard those use cases without a verified workflow and accountant acceptance.

A service business needs booking date/time, duration, assigned employee, asset/site history, promised work and the next visit or agreement renewal. Service templates alter vocabulary and show upcoming visits. Extra fields can record equipment model, access instructions or service area. An appointment does not guarantee technician availability beyond the recorded schedule checks.

Future field-service work includes route planning, visit evidence, signatures, parts carried by staff and recurring invoice generation. Geolocation and staff tracking should be an explicit operational decision, with appropriate permissions and retention, rather than added by default because a phone has location capability.

## 14. Make configuration useful

The guided setup now covers identity, work, clients, money, team and switching. It retains detailed answers about sources of work, approval habits, parts handling, client types, repeat visits, collections, staffing, pay and existing tools. The owner reviews all settings before saving them together.

Some answers directly change behaviour: branding, stages, checklist, follow-up interval, terms and operating gates. Narrative discovery answers give the operator context; they do not automatically program the app or prove that an AI understands the entire business. The record assistant remains calculated from saved records and settings. It does not autonomously contact clients, transfer money or make managerial decisions.

The business’s trading name, logo and colour now appear in the workspace, browser identity and installed-app manifest. Financial documents retain the legal name and saved seller identity when issued. Updating today’s branding does not rewrite the identity on already-issued bills. This protects continuity when a business changes its logo or trading style.

The remaining practical configuration task is to remove irrelevant modules. A parts retailer should not see a collision claim workflow simply because the platform supports garages. Owners can select modules; staff still receive server-enforced permissions. Hiding a navigation entry is not the security boundary.

## 15. Switching from Excel, paper and accounting tools

Start with an inventory of source systems: customer register, item list, supplier contacts, current jobs, outstanding balances, vehicle stock and original documents. Identify which source is authoritative for each field. If two registers disagree, reconcile before importing. Do not hide a disagreement by accepting whichever spreadsheet is newest.

The new CSV workflow offers templates, column mapping, preview, validation, numeric parsing and existing-record skips. It handles quoted commas, embedded line breaks, escaped quotes and a UTF-8 BOM. Imports accept at most 5,000 rows per file and post at most 250 per atomic batch. Invalid posted batches roll back. If a later batch fails, earlier confirmed batches remain saved; re-importing skips matching identities rather than overwriting them.

Matching rules are deliberately visible: customers/suppliers use name and normalised phone, stock prefers SKU then barcode then name, services use name, vehicles use VIN, and openings use customer/source reference. These are not fuzzy identity resolution. A changed customer name can create a second record; a reused SKU can skip a row the user intended to change. Staff must review source identities and skipped rows. Import is creation, not bulk overwrite.

Opening balances match a customer phone to exactly one imported customer and require an owner reconciliation confirmation. Import customers first. Preserve the original ledger reference so the owner can prove what was carried forward. Old bills need not be reconstructed as new issued invoices merely to represent debt; doing so can confuse tax periods and duplicate revenue.

TallyPrime supports data import and mapping capabilities that vary by version and file format. Its native formats are not automatically this app’s CSV. The supported path here is a reviewed spreadsheet conversion, not two-way Tally synchronisation. Export this app’s records for the accountant and test their chosen workflow before cutting over. [S10]

## 16. Learn from other products without copying their claims

Shopify-style catalogue collections, a clear checkout/cart and customer relationship context are useful interaction patterns. Apply them to service/parts businesses with work approval and tax review; a repair estimate is not the same event as a completed product sale. The app now has a catalogue/cart review flow, tags and customer history, but no Shopify storefront or order integration.

Zoho documentation shows organised price-list and credit-limit features. Those are useful patterns for repeat-business terms; our implemented version is explicitly bounded to customer item quantity tiers and issue-time limit review. It does not reproduce every rule or integration of a mature finance suite. [S11, S12]

Repair-system documentation such as Tekmetric’s service-writer workflow makes inspection, repair-order work and authorisation explicit. Our product inference is to connect inspection evidence to a retained approved quote and work checklist. A competing product’s marketing list is not proof that Indian staff need every feature. [S13]

Vyapar’s published features include billing, stock and related business tools. A generic feature-count contest against established billing apps is unlikely to be a persuasive switching reason. The hypothesis to test is whether a garage or service business gains enough from connected approval, job, collection and follow-up workflows that it accepts migration and training. [S14]

## 17. Professional interaction and speed

Professional means predictable daily work: one clear primary action, visible active business, consistent icons, useful loading/error states, keyboard search, readable financial amounts and touch targets. Repeating the platform name everywhere would make a configured business feel generic; the business identity now leads the workspace.

The interface uses local SVG icons and system fonts, so it does not depend on external font/icon services. Reduced-motion preferences are respected. Desktop tables are paginated to 50 rows. Record ID lookups use an index, and customer relationship metrics are aggregated once per state instead of rescanning all invoices for every customer and segment.

The browser suite exercises a synthetic 2,000-customer snapshot and records render timings and visible row counts. This isolates client rendering; it is not a network benchmark or proof of nationwide server capacity. Actual performance depends on record mix, concurrent workers, database location, devices and connectivity. Do not promise “never crashes” or “instant for every business” from one test runner.

For pilot acceptance, measure the real steps to enter a repeat customer’s bill, collect a partial balance, inspect a job and find an overdue follow-up. Compare with their existing process. A suggested target is a substantial reduction in retyping and missed next actions, but establish a baseline before publishing a percentage improvement. Record failure recovery as carefully as speed.

## 18. Vercel architecture and persistence

The old local SQLite edition cannot simply be uploaded to Vercel. Vercel’s function filesystem is not durable application storage; the provider explicitly recommends an external database instead of SQLite for that use. The new hosted candidate uses PostgreSQL while retaining the local SQLite edition for a locally run installation. [S15]

The hosted candidate uses a WSGI Python function and static assets. PostgreSQL stores businesses, records, original attachment bytes, audit events, counters, command receipts, hashed sessions and login rate limits. Warm function memory is not authoritative for sessions or money. Missing/unreachable database configuration fails closed; there is no automatic SQLite fallback in `/tmp`.

An organisation is established when an invited owner registers. Business ownership is checked on server entrypoints, and staff scope and role checks remain in the domain rules. Cross-worker writes use a transaction advisory lock for the organisation so retries, stock movements, invoice numbering and record changes do not rely on a process-local lock. Transactions and command receipts commit together.

This is application-enforced tenancy, not a claim of independently reviewed database row-level security. There is no exposed direct database API for clients. Production needs a least-privileged runtime role, TLS, provider backups, a restore drill, monitoring and an independent security review. The deployed environment, provider permissions and real function/database behaviour still require acceptance.

## 19. Offline and unreliable connections

Many daily actions can be drafted while disconnected, but money, stock reservation and payroll require the server. The browser can retain encrypted offline drafts with a passphrase and a limited lifetime. A saved draft must visibly differ from a confirmed invoice, payment or reservation.

Commands carry an operation ID and payload fingerprint. Repeating the same accepted command returns its stored result. Reusing an ID with different data is rejected. If a connection is lost after a payment may have been saved, Sync retries the same command rather than posting a new receipt. A restored/replaced database epoch invalidates stale queued operations for review.

Independent offline installations do not automatically merge their separate databases. An owner should choose a shared hosted server or one local authoritative installation. Two unrelated servers acting as if each owns the same stock would undermine the conflict controls. Offline capability is a bounded drafting workflow, not multi-master financial replication.

The production pilot should include mobile network loss during a receipt, browser reload, conflicting customer edits, another staff sale during a count and a database outage. The right failure state preserves uncertainty and offers a safe retry; it must not claim success because an animation completed.

## 20. What is implemented and what remains

| Area | Release-candidate capability | Boundary / next work |
|---|---|---|
| Identity | Business trading/legal name, logo, colour, footer, browser and installed identity | Preview-domain branded landing/login needs domain routing |
| Configuration | Four profiles, modules, custom fields, stages, checklist, rules, discovery answers | Narrative answers require operator interpretation |
| Switching | CSV templates/mapping/preview, identity skips, opening balances, legacy quote JSON | No fuzzy merge or native two-way accounting sync |
| Work | Quote revisions, approval records, jobs, visits, inspection, assigned tasks | No client approval portal or verified signature service |
| Money | Bills, receipts, advances/allocations, credits, statements, limits and cash counts | No complete general ledger or automatic bank reconciliation |
| Inventory | Items, partial receiving, stock ledger, returns and count adjustments | No complete warehouse lot/serial/location engine |
| People | Roles, attendance, task time, incentives and reviewed payroll | No statutory submissions or salary transfer integration |
| Insurance | Claims, payer tracking, original/transcribed comparison evidence | No insurer portal automation; hypothetical scenarios remain labelled |
| Hosted data | PostgreSQL, organisation checks, shared sessions and retry-safe transactions | Intended Vercel team still inaccessible; live acceptance outstanding |
| Local use | Existing SQLite app and local backup/recovery workflow | Not automatically synchronised with hosted databases |

Prioritise the next feature by a demonstrated blocked workflow, not the number of requests a marketing page can list. Promising every sector and every accounting edge case immediately would make onboarding less predictable and dilute the connected operations advantage.

## 21. Validation plan with real businesses

Recruit a small set from one geographic cluster: one collision shop, one general/two-wheeler garage, one parts counter and one recurring service team. Include the staff doing the work, not only owners. Obtain permission to use examples, remove unnecessary personal data and retain the source copies securely.

Observe a complete day or representative workflow. Record what they enter, what they repeat, where approval lives, how payment is verified, what the accountant needs and what happens when someone is absent. Ask them to show the last difficult transaction rather than answer whether they “want automation.” A hypothetical preference is weaker evidence than an observed workaround.

Run a controlled parallel period. Reconcile customer balances, stock, receipts and cash every day. Confirm a printed bill with the accountant. Measure failed tasks and training time. Check each role with an account belonging to that person. Practise recovery with a copy of the data, not the only live database.

Acceptance examples: a repeat customer’s agreed tier is applied and reviewed; a second sale cannot oversell the final item; a failed import batch leaves no partial records; a technician cannot access another organisation; a cancelled visit remains visible; an opening receipt reduces the retained balance correctly; a late cash entry flags the count; a lost receipt response retries once; and an issued bill retains its original seller details after rebranding.

## 22. Free pilot, paid product and support economics

The app currently displays a free pilot with no charges. No subscription collection is wired. Free access still has database, deployment, backup, monitoring and support costs. Track those before promising unlimited free hosting or permanent unlimited storage. Pricing cannot be validated solely from competitor prices or a national registration count.

Measure acquisition source, assisted setup time, migration corrections, active staff, completed workflows, support incidents, retention and direct operating cost per business. Ask a pilot owner what they would lose if access ended and which workflow they would pay to keep. Avoid hypothetical “would you pay?” questions without actual use.

Potential packaging should follow operational complexity: one location/team, more branches or approved integrations, and assisted migration/support. These are hypotheses, not announced plans or prices. Do not put essential data export or correct invoices behind a surprise paywall. A free pilot should have clear duration, storage limits, support expectations and notice before paid terms change.

For India, subscription payments and merchant payments are separate decisions. The business may record UPI receipts from customers while your SaaS charges a recurring subscription through a supported provider. Neither is implemented by adding a UPI method label. Confirm the company’s jurisdiction, gateway availability, tax invoices and refund terms before integrating monetisation.

## 23. Launch decision

The next concrete launch step is a private, monitored pilot after the intended Vercel team connection is restored and a backed-up PostgreSQL database is provisioned. GitHub stores the implementation and CI evidence; it is not the live financial backend. Vercel hosting requires the project and environment to be linked to the correct account and team.

Production readiness remains a set of evidenced operational outcomes: deploy a known build, preserve records through restarts, restore a backup, restrict every role and organisation, recover from uncertain commands, reconcile money, verify tax outputs and support real staff. Passing automated tests helps establish the candidate; it does not complete those hosted and pilot gates.

## Source register

Sources describe public facts or the vendor’s own documented feature behaviour. Product recommendations and sector pain hypotheses above are our analysis.

- **S1:** Ministry of MSME, dashboard, dated 3 October 2026: https://dashboard.msme.gov.in/ ; registration classifications: https://www.udyamregistration.gov.in/default.aspx
- **S2:** SIDBI Annual Report FY2024–25, MSME Outlook: https://www.sidbi.in/annualreport/AnnualReport202425/msme-outlook.php
- **S3:** SIDBI MSME Pulse, July 2026 entry: https://www.sidbi.in/msme-pulse.php
- **S4:** RBI, speech on MSME financing and operating challenges: https://rbi.org.in/Scripts/BS_SpeechesView.aspx?Id=1455
- **S5:** NPCI UPI product statistics, August 2026: https://www.npci.org.in/product/upi/product-statistics
- **S6:** Government GST IRP, reporting restriction advisory: https://einvoice6.gst.gov.in/content/revised-time-limit-for-e-invoice-reporting-for-businesses-with-aato-of-%E2%82%B910-crores-above/ ; GST Council advisory: https://gstcouncil.gov.in/sites/default/files/2025-01/november_2024_newsletter_0.pdf
- **S7:** MeitY Annual Report 2025–26, DPDP rules/phased implementation: https://www.meity.gov.in/static/uploads/2026/04/46face7d48c8f6a97030f713ad5fdab4.pdf ; Government notification context: https://www.pib.gov.in/PressReleasePage.aspx?PRID=2198217&lang=1&reg=3
- **S8:** Ministry of MSME, Samadhaan: https://ramp.msme.gov.in/ramp/RAMP-initiative/msme-samadhaan/msme-samadhaan
- **S9:** EPFO employer services: https://www.epfindia.gov.in/site_en/For_Employers.php ; employer portal: https://unifiedportal-emp.epfindia.gov.in/epfo/
- **S10:** TallyPrime import guide: https://help.tallysolutions.com/getting-started-with-importing-data-into-tallyprime/ ; custom mapping: https://help.tallysolutions.com/import-data/import-data-using-any-excel-file/
- **S11:** Zoho item price lists: https://www.zoho.com/en-in/erp/help/items/price-lists/understanding-price-list.html
- **S12:** Zoho customer credit-limit feature: https://www.zoho.com/bh/books/help/contacts/credit-limit.html (feature reference; not Indian regulatory guidance)
- **S13:** Tekmetric service-writer workflow: https://support.tekmetric.com/hc/en-us/articles/360043239813-Repair-Order-Workflow-Overview-for-Service-Writers ; authorisation: https://support.tekmetric.com/hc/en-us/articles/4421125978391-Digital-Signature-Authorization-Process
- **S14:** Vyapar, published app features: https://vyaparapp.in/blog/vyapar-app-features/
- **S15:** Vercel SQLite guidance: https://vercel.com/kb/guide/is-sqlite-supported-in-vercel ; Python runtime: https://vercel.com/docs/functions/runtimes/python

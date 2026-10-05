# Client discovery, configuration and switching worksheet

Copy to a private client project outside the public repository. Use anonymised examples; do not put original client records/credentials in GitHub. This worksheet complements the [72-question questionnaire](../../docs/CLIENT_DISCOVERY_QUESTIONNAIRE.md) with concrete workflow evidence and decisions.

## A. Identify the actual business

Record country, location, sector/speciality, legal businesses/branches, registration, owner/contact, operating days, staff/roles, peak concurrent users, phone/PC/printer models, internet/power observations and who maintains accounts. Ask what the business calls an estimate, work card, bill, credit, receipt and delivery.

Decisions: organisation scope, separate country/currency businesses, registration/tax acceptance, branding/name/footer, language/date requirements and supported deployment. Do not copy an unrelated business's answers.

## B. Shadow three complete cases

Ask staff to show one ordinary completed request/sale, one delayed/disputed case and one partial-payment/return exception. Obtain consent for anonymised observation. For each hand-off fill:

| Evidence field | What to write |
|---|---|
| Trigger and current status | What started it, date/time and current outstanding work |
| Person/responsibility | Who entered, approved, executed, collected and reconciled |
| Information/source | Actual document/chat/ledger reference; where the authoritative amount/quantity came from |
| Action/hand-off | What they did, whom they asked, what they retyped and how the next person found it |
| Failure/workaround | What was missing, delayed or wrong; the exact correction and reason |
| Effort/frequency | Measured minutes in this case; count in a defined sample/window, not an invented estimate |
| Financial/stock effect | What posted or physically moved; what was only a promise/status |
| Desired result | How the person would know the problem was solved |
| App fit | Implemented setting/record, partial workaround accepted by reviewer, or feature gap |

Do not lead with “Would an AI assistant help?” Ask “Show me how you knew what was still owed” or “What happened when the part did not arrive?” Actual behaviour is more useful than praise for a hypothetical feature.

## C. Questions that change configuration

1. Who may agree a price/date/scope, give credit and override a check? Who must approve extras?
2. What stages are used, and what precisely makes work finished? Can finished work still be unpaid?
3. What evidence of customer/fleet/insurer approval is retained? How are supplements and declined recommendations handled?
4. Which inspection/checklist fields prevent a real error? Which fields would staff never use?
5. Who is the debtor and who actually pays? How are advances, split payer shares and disputes tracked?
6. What counts as verified QR/bank collection? Who has statement access? What do failed/reversed payments look like?
7. How are customer names/phones/SKUs duplicated? Can one phone represent several distinct accounts?
8. Which client prices/discounts/terms/limits are agreed? What does 0 credit limit mean in the proposed setup?
9. When are goods received versus billed? How are returns, unit/pack conversions and supplier credits handled?
10. What does stock quantity mean: shelf, branch, reserved or on-order? Which meanings are unsupported today?
11. Which bay/skill/part/dependency limits scheduling? Who changes the promise and informs the client?
12. How are attendance, task time, wages, advances and earned commissions independently reviewed?
13. What is the commission base, exclusion, collection threshold, split and refund/clawback policy?
14. What follow-up is transactional versus promotional? Which channel/language and contact authority are required?
15. What statutory billing/payroll/accounting systems must remain? What exact export does the accountant accept?
16. How long may connection/server recovery take? Which actions must work offline, and is draft-only offline acceptable?
17. Who owns upgrades/recovery/support? How does a lost phone or forgotten owner password get handled?
18. What would make the client refuse the switch, even if the interface looks better?

Translate answers into specific settings or a recorded gap. Do not promise support for an unsupported policy because a free-text field can store its description.

## D. Source and reconciliation pack

With permission gather reviewed/anonymised source shapes: customer and item masters; one quote/revision/approval; one ordinary bill/receipt; one partial return/refund; a customer opening ledger; a purchase/receipt/supplier bill/payment; a physical count; attendance/payroll/commission examples; and sector-specific claim or VIN/handover evidence.

Keep originals in the private client workspace. Choose a cutover date, numbering strategy, old-history access and responsible reviewers. Match source keys, review importer preview, reconcile each batch, and record skipped/failed rows. Supported imports are creation/duplicate-skip, not intelligent updates/merges or full voucher history.

Compare customer dues/advances, physical stock, outstanding supplier obligations and sample document totals independently. Do not fabricate transactions to force a match. Explain unsupported corrections and agree an accepted external process before live use.

## E. Staff acceptance and first week

For each actual role, run the [full workflow](../workflows/FULL_CLIENT_WORKFLOW.md) without developer prompting. Use their phone/PC and appropriate country-approved fictional examples first. Include lost response/retry, conflicting edit/stock action, partial receipt, original-line return, final-stage check and scope/privacy test.

Agree a baseline/comparison window and measure task time/help requests, missed promises, overdue actions, discrepancies, sync backlog, support effort and peak usage. Do not issue duplicate statutory documents while comparing old/new systems. Keep historical source access until owner/accountant acceptance.

At week's end record accepted behaviours, blockers, corrections, responsible person and due date. Failure in money/stock correctness, access or restore blocks expansion. Cosmetic preferences should not hide unresolved ledger problems.

## F. Sign-off

Owner accepts the supported operating scope, source openings, staff roles and exception policy. Accountant/qualified reviewer accepts actual applicable billing/payroll/export treatment or specifies what stays external. Operator accepts hosting, private credentials, backup retention, measured isolated restore, incident/account recovery and costs.

Use the [private launch record](../../hosting/operations/launch-record.example.json). No imagined client signature or automatically generated “production-ready” badge is sufficient. Retain evidence and do not widen onboarding until blockers are resolved.

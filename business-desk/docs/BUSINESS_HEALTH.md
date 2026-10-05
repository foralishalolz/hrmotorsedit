# Business health: owner analytics and next actions

Open **Business health** in the owner's workspace. The same interface adapts to a garage, showroom, retail business or service team and uses its trading name and NPR/INR currency. Financial records and rankings are scoped to the selected business. Staff roles cannot access this API, CSV export or navigation.

## What each view answers

| View | Owner question | Source records and action |
|---|---|---|
| Overview | Where are we doing well and where should I look first? | Sales/result trend, cash movement, overdue balances, highest/lowest contributions, source completeness and next steps. |
| Profit & loss | What did we earn after the costs we recorded? | Issued bill net after credits, retained non-Labour bill costs, classified operating expenses, approved payroll employer cost and commissions outside payroll. Cash is shown separately. |
| Work & services | Which packages earn more, which jobs overrun? | Product/service contribution; lifetime job revenue less material issues/returns, saved labour/time, extras, subcontract costs, operating job expenses and approved commissions. Open the source and review quality. |
| Clients | Who buys, returns, owes us or has stopped coming? | Period sales and gross contribution, outstanding and overdue at the selected end date, first/last bill, new/returning/inactive segments, search and sort. |
| Team | What does saved work tell me about delivery and quality? | Assignment load, completed/overdue work, task hours, actual completion versus promise, owner-recorded client ratings/rework, saved attendance statuses. |
| Patterns | When do bills occur, which sources bring enquiries? | Invoice weekday, returning client share, client concentration, current outcomes of period-dated quotes and enquiries, current job stages. |
| Next actions | What should I investigate and do next? | Rule-based evidence for missing costs, expense classification, overdue collections, loss jobs, loss periods, reliance on a client, inactive clients and overdue work. Review the source; save a task with owner/date/next action. |

Choose this month, last 30/90 days or an AD range up to 366 days ending today or earlier. The comparison period immediately precedes the selected range and has the same number of days. Date boundaries follow India/Nepal business time; currency is never converted or combined across businesses. Trends use daily values up to 45 days, then monthly totals. Export includes calculations and their basis, with spreadsheet formula escaping.

Highest/lowest highlights use **all qualifying records**, including entries beyond the tables' 100-row limit. Team delivery highlights require at least three reviewed deliveries per person. A small sample or no records is shown explicitly. Rankings are comparisons of recorded outcomes, not a label that an employee is a good or bad person.

## Follow the money correctly

**Recorded operating result = net sales − direct bill costs − operating expenses − approved payroll employer cost − approved commissions outside payroll.** VAT/GST is separated. Draft invoices and draft payroll are excluded. Approved payroll is allocated across its pay period using nonnegative cumulative cent boundaries, so the whole period totals exactly. A commission included in payroll counts once.

Labour estimates on bill lines are excluded from the period result because payroll supplies the wage cost. Billed Labour without an overlapping approved payroll is flagged for review. Non-Labour lines without a recorded cost, legacy Parts/Tools expenses without explicit treatment and unapproved overlapping payroll drafts are also flagged. These flags do not invent a cost or silently change posted documents.

Classify each expense as Operating expense, Inventory purchase, Payroll payout, Staff advance, Capital asset, Tax payment or Owner withdrawal. Non-operating categories stay in cash movement and do not reduce operating profit again. If the same cash payment is entered both as an expense and as supplier/payroll payment, cash will count both records: record each payment once. Staff advance category always uses advance treatment.

Receipts include customer advances and subtract refunds. Allocating an existing advance is not a second receipt. Paid net payroll, supplier payments, standalone paid commissions and saved expense cash entries are outflows. An invoice's output tax is not evidence that the tax was remitted. Balance ageing excludes future receipts/credits and groups only positive invoice/opening balances as of the selected end date. Customer credit and unused advance balances remain available in the client hub; this receivable total is not their net balance.

Line returns reverse direct cost only for physically restocked non-Labour quantities. Service credits/manual credits reduce sales without pretending materials returned. Manual credit net is apportioned across original lines exactly in cents; an older invoice credited this period reduces this period's sales. Fully credited jobs remain in the billed loss review.

## Quality and team reviews

An owner can open a job → Quality review, or use the Work & services table. Record the actual AD completion date only after the final configured work stage, client quality rating 1–5 (0 means unrecorded), count of actual rework events and evidence notes. Future dates, fractional ratings/rework and staff edits to these review fields are rejected. Saved versions prevent an older review overwriting a newer one.

Shared jobs appear for each saved assignee. Missing reviews do not mean poor performance; missing attendance days are not assumed absent. Delivery percentages use only recorded completion dates and promises. Team workload and stage/assignment history are current saved values; the app does not reconstruct historical reassignments. Reviews inform a conversation about blockers, training, scope and client promises; they do not automatically cut pay, fire staff or change commissions.

## Limits that matter to a business owner

This is an estimate from recorded operations before income tax/depreciation. It is not a statutory double-entry profit-and-loss statement. Depreciation, income tax, unrecorded adjustments and unpaid operating supplier bills are excluded. Client/service contribution excludes shared wages and overhead. Whole-job contribution uses lifetime saved job costs through the end date and is never added again to period profit. Showroom vehicle costs and retail inventory need correctly retained bill costs; partial/unrecorded labour and overhead still require review.

Suggestions cite measured records and save ordinary follow-ups for human review. They never send messages, post money, file tax, change staff access or execute a management decision. Bills, collections, payroll and tax country settings still need owner/accountant acceptance.

Analytics are read from a consistent database snapshot and calculated in linear passes, with bounded trend windows and result tables. The browser caches a result in memory for 60 seconds and clears it after saved-state reload; Refresh requests a new report. Offline use does not fabricate current financial analysis. Large histories still use the app's whole-business snapshot and require measured database/API load testing before wider onboarding.

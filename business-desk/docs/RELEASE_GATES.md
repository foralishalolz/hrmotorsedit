# Production acceptance gates

This release is a pilot candidate, not a blanket claim that every SME workflow or production obligation is complete.

| Gate | Required evidence | Current state |
|---|---|---|
| Financial and inventory rules | Rounding, credits, retries, stock, reservations, payroll, opening balances and operating gates | 82 local tests pass; [2.2 application CI](https://github.com/foralishalolz/hrmotorsedit/actions/runs/37272337114) is green |
| Real browser flows | UI → API → records → response, mobile layout and no uncaught exceptions | 61 Chromium assertions pass with 0 uncaught errors; desktop/phone evidence inspected; [verification](../VERIFICATION.md) |
| PostgreSQL boundary | Two workers, persistent sessions, scoped organisations and concurrent writes | 10 real PostgreSQL tests pass in CI; actual Vercel acceptance remains outstanding |
| Hosted runtime | Correct team/project, durable DB, HTTPS domain and known deployed commit | Container/proxy and WSGI/packaging checks pass; intended Vercel team returns 403 and no production database/project is provisioned |
| Recovery | Protected offsite/provider backup and timed isolated restore | Local backup/recovery exists; hosted scoped export exists; offsite/provider restore drill required |
| Organisation isolation | Owner, staff and different organisations tested on real infrastructure | Application-scoped PostgreSQL organisation tests pass; independent review and deployed staff-device verification required |
| Country billing acceptance | Accountant verifies registration, classifications, supply/tax treatment, retention and needed government integrations | Domestic India calculations and Nepal VAT arithmetic exist; Nepal electronic-billing approval/procedure and CBMS applicability are explicit launch dependencies; no IRD approval/integration or blanket statutory acceptance claimed |
| Payroll acceptance | Applicable pay basis, withholding, contribution and statutory provider review | Configurable reviewed calculation; no statutory filing or transfers |
| Pilot usability | Real businesses complete their observed work and switching reconciliation | Detailed playbook/configuration provided; actual interviews and staff acceptance not performed |
| Commercial operation | Hosting budget, support, data terms and evidenced packaging | Free pilot shown; no subscription integration; cost and pricing validation outstanding |
| Security review | Authentication/recovery, tenancy, privacy/retention, dependencies, logs and recovery | Hardening/failure checks included; independent review and production operations outstanding |

## Pilot acceptance script

Use fictional data first. For each business, ask the actual staff member to complete the work without an explanation of the UI:

1. Set up the business and add a real-shaped customer, service/stock item and employee.
2. Create an estimate or sale, record approval where needed, issue a bill and record a partial receipt.
3. Find the remaining balance, agree a next date and record the follow-up outcome.
4. Receive partial supplier stock and match a supplier bill without receiving the stock twice.
5. Have a second staff device update the same record; verify the first device cannot silently overwrite it.
6. Disconnect a device, save a customer and quotation draft, reload, unlock and reconnect. Verify each appears once.
7. For a showroom, attempt two reservations on one chassis, then complete finance/document notes, collection and handover.
8. For a garage, issue a part to a job, bill the part, and verify stock was consumed once.
9. Review attendance and one payroll/commission calculation using independently checked figures.
10. Export a backup and restore it elsewhere; compare selected records and an attachment.

A blocking defect is any duplicate/missing money entry, incorrect stock, silent overwrite, cross-business exposure, unusable primary phone flow, or failed restore. Fix these before expanding the pilot. Cosmetic preferences can be scheduled after core workflow acceptance.

## Additional 2.1 acceptance

Verify customer discounts and payment terms on actual catalogue items; review India intra/inter-state and composition samples; scan a known barcode; partially return a direct-sale item and reconcile credit, stock and any separate refund; customise a field and checklist in each profile. Confirm English UI suitability. Do not onboard live workflows requiring unsupported tax, vehicle returns, supplier returns or independent offline billing.

## Additional 2.2 acceptance

Configure the business identity, stages and real handover checks with the owner. Import a reviewed customer/catalogue source without writing during preview; reconcile opening balances and stock. Exercise a customer's quantity price and credit limit, collect an opening balance, check the statement, close cash and add a late cash expense to trigger review. Record an assigned technician inspection and verify a custom final stage ends work alerts. Verify both ordinary and exceptional owner-approved handover. On the actual Vercel deployment, use two organisations and two staff devices, then run the provider restore drill. English UI and supported tax/accounting boundaries must fit the chosen pilot.

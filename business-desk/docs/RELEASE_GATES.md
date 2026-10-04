# Production acceptance gates

This release is a pilot candidate, not a blanket claim that every SME workflow or production obligation is complete.

| Gate | Required evidence | Current state |
|---|---|---|
| Financial and inventory rules | Passing tests for rounding, credits, duplicate retries, reservations, stock and payroll | 63 local tests passed; CI must pass on the deployment commit |
| Real browser flows | Setup, billing, offline reload, conflicts, phone layout, no uncaught exceptions | Real Chromium checks passed in CI; desktop/phone screenshots inspected; see exact-commit checks in PR #1 |
| Hosted runtime | Container builds, health check passes, HTTPS proxy config validates | Container build/health and proxy validation passed in CI; no live server/domain provisioned |
| Recovery | Encrypted offsite backup and a timed restore to a separate instance | Local backups/restore implemented; offsite destination and drill required |
| Organisation isolation | Separate customer stacks, restricted owners, role checks on staff devices | Separate-instance model documented; deployment/operator checks required |
| Country billing acceptance | Accountant validates Nepal/India bill fields, registration, HSN/SAC, supply/tax treatment, fiscal numbering, retention and required IRD/CBMS/IRP integrations | Nepal VAT and ordinary domestic Indian GST configuration implemented; no tax-software approval or filing integration claimed |
| Payroll acceptance | Accountant reviews applicable pay basis, withholding and contribution rules | Configurable reviewed payroll; no statutory engine |
| Pilot usability | 3–5 real businesses complete their own observed daily workflows and reconciliations | Recruitment offered by owner; interviews and observation not yet performed |
| Commercial operation | Chosen hosting budget, support coverage, data terms and pricing evidence | Market hypotheses documented; subscriptions/payment integration not implemented |
| Security review | Review deployment, authentication, permissions, restores, offline storage and dependency updates | Hardening and tests included; independent security review outstanding |

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

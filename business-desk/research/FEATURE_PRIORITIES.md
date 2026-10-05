# Feature priorities and the honest product promise

Current baseline: 2.2.0-rc.1. Labels below describe current code, not completed production acceptance. Priorities are proposed and change after client observation. Do not promise that this app replaces every client's existing software today.

## What is already supported

| Need | Supported workflow | Scope to communicate |
|---|---|---|
| Business-owned app | Name/legal details, logo/accent, payment/footer text, PWA identity and retained seller snapshots | Responsive browser app, not native binaries; branding does not certify tax output |
| Configured sector workflow | Four profiles, stages, checklist, modules, 20 fields, roles, six-step setup and explicit gates | Narrative discovery is context, not automatic custom programming |
| Work/approval visibility | Quotes/revisions, recorded approval, jobs/findings/tasks/assignment/timers, claims/original evidence | No external approval portal, dispatch algorithm or insurer integration |
| Fast sale/collections | Catalogue, client/quantity prices, discount/terms/credit gate, bill/receipt/advance/credit/refund/statement | No bank verification, full accounts or every billing model |
| Stock/supplier control | Purchase/partial receipt, consumption, no-negative-stock, supplier bills/payments, count/reorder | Supplier-return credits, multi-warehouse, batch/expiry/unit-conversion/landed-cost gaps |
| Showroom | Enquiries, unique VIN, exclusive reservation, invoice/collection/handover | Dealer/manufacturer integration, used-margin/trade-in/issued-vehicle-return gaps |
| Service work | Client/assets, bookings, jobs, agreements/next actions | Route/GPS/automatic dispatch/recurring entitlements and billing gaps |
| Staff records | Attendance, reviewed payroll/advances and fixed earned/collection-linked commissions | No statutory engine/bank transfer, every tier/split/clawback or full leave scheduler |
| Follow-up/help | Dated actions, supported records assistant, client channel/language preference | No autonomous external messaging/cloud AI or full interface translation |
| Safe records/portability | Roles/audit, retries/versions, encrypted drafts, CSV preview/openings, local backups/cloud scoped export | Offsite/provider restore, public recovery/MFA, native migration and large-history capacity still need work |

## Prioritise by failure cost and observed frequency

Use actual pilot observations, not made-up importance scores. First fix wrong/missing/duplicate money or stock, access leaks, failed restore and unusable primary actions. Then remove frequent repetitive work and unclear hand-offs. Integrations and specialist features need evidence that their value exceeds their support/cost and correctness risk.

| Order | Proposed work | Concrete problem solved | Acceptance before claiming complete |
|---|---|---|---|
| Launch dependency | Actual authorised hosting/DB, account recovery, provider/offsite restore and independent review | A tested checkout is not a durable supported live business | Correct team/project, protected roles, staff-device/organisation checks, measured restore and named operator |
| Launch dependency | Country billing approval/applicability and required IRP/CBMS path | Professional PDFs can still be unusable statutory documents | Accountant/authority decision for actual business; real approved integration or supported external billing arrangement |
| High if language blocks use | Nepali/Hindi/needed regional labels, print/fonts and validated Nepal calendar | Staff cannot confidently read/form dates | Staff unaided task/print/date-boundary test; reviewed terminology, no guessed conversion |
| High if collections unreliable | Statement import/provider payment matching and reversal handling | Paid screenshot/status confused with cleared receipt | Unique external match, duplicates/fees/reversal/unmatched handling and reconciliation |
| High for traders/parts | Supplier-return/credit and controlled bill/payment correction | Purchase mistakes force ad-hoc ledger adjustment | Retained original, no excess return/refund, stock/payable reconciliation and audit |
| High for busy workshops | Capacity/skill/bay scheduling and clearer blocker/parts requests | Date/assignment exists but impossible promises persist | Collision prevention, dependencies, unavailable staff and realistic replan tested |
| High for larger histories | Server-side list/search/aggregation pagination and load verification | Snapshot grows despite 50-row rendering | Response sizes, p95 actions, concurrent writes and realistic attachment/history load |
| Next after observed demand | Client portal/authorisation and consent-based transactional messaging | Repeated status calls and approval buried in chat | Identity, exact scope/version, secure links, consent/template/provider policy, delivery/duplicate handling |
| Next after policy review | Commission tiers/splits/clawbacks and payroll/leave adapters | Fixed entries do not represent real staff agreements | Independent ordinary/partial/returned-sale calculations; no duplicate inclusion/payout |
| Next after accountant agreement | Maintained accounting export/import adapter | Owner repeats data entry into accepted books | Named package/version, mappings, opening/delta rules, round-trip reconciliation and error queue |
| Later vertical expansion | Warehouse/batch/serial/entitlements/loyalty/commerce/dealer-specific modules | New vertical semantics exceed custom fields | Separate domain model, returns/liability/cost rules and sector pilot |

A phone-friendly dashboard, Shopify-inspired cart or better icons does not implement those algorithms. Features should appear in the customer's workspace only when their underlying process is reliable and relevant.

## Why one shared product can still feel custom

Keep country money/ledger/permissions/retry/recovery rules in one core. Configure identity, sector language, stages/checks, relevant fields, client prices/terms and supported approval rules. A customer's exceptional need can become a maintained feature when it has a clear trigger, examples, corrections and tests. Avoid unsupported business logic hidden in arbitrary free-text settings.

Do not create a fork for every garage: its bugs/security fixes would diverge. Keep deployment profiles as adapters to the same source. Each customer owns their data/context; unrelated organisations must remain isolated in the cloud or separate private stacks.

## Release sequence as evidence gates

1. **Observe:** shadow ordinary/blocked/return or collection cases; identify workflow language and supported scope.
2. **Configure:** identity, roles, country/accountant decision, stages/checks, terms and source masters/openings.
3. **Reconcile:** stock/client dues/advances/supplier references; preserve old history and compare independent samples.
4. **Prove:** staff complete phone/PC work and exceptions unaided; lost responses/conflicts/recovery tested.
5. **Operate:** measured hosting/cost/capacity, support/recovery owner and reviewed upgrade/incident procedure.
6. **Expand:** repeat observed feature needs, validate a maintained adapter, then onboard the next matching sector/scale.

No calendar launch date is invented. Actual team access, provider setup, approval decisions and pilot evidence determine progress. The current Vercel team's 403 must be resolved through the intended authorised connection; do not deploy to another account to bypass it.

## Commercial design

The app currently displays a free pilot and does not charge automatically. Free software does not imply free hosting/support for unlimited organisations. Record cost per customer: database/compute, backup/storage, attachments, support time, onboarding/migration and integrations. Price hypotheses should follow demonstrated use, not national enterprise counts.

If paid plans are later introduced, agree notice, consent, billing provider, entitlement/limits, downgrade/read-only policy, export and retention. Keep staff accounts affordable enough to avoid shared logins. Do not withhold the client's data to force payment, or turn the pilot into a subscription without their agreement.

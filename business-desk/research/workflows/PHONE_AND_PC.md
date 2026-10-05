# Phone and PC: usable daily journeys

Design proposal and acceptance criteria, not measured pilot results. Current app is responsive browser/PWA-style software with local SVG icons and locally served typography. A native-looking interface is useful only if staff can complete work reliably. It is not an installed native iOS/Android binary.

## Owner on a phone

First show the business's own name and the currently selected business. Then show unresolved posting/sync issues, today's/late work, approvals, money due, important stock shortages and next actions. Each tile/list needs scope, date, count, readable label and an action to see records. Do not put the owner's wage report or broad margin summary on a shared technician device.

The owner should be able to open a blocked job, understand why/whose action is needed, contact the relevant person through the agreed manual process, assign/update a next action and see the retained result. A contact shortcut must not imply a message was sent. Owner financial/exception approval should explain the effect and reason.

Proposed unaided test: find today's most urgent blocked job, a customer's remaining balance and tomorrow's obligation in 60 seconds each. These are pilot targets, not performance guarantees. Test using real-shaped dates/record volume and the owner's actual phone.

## Technician on a phone

Show assigned work first: client/asset reference, complaint, authorised tasks, useful findings, checklist, needed part and blocker. Large touch actions should save a note/finding, start/stop task time, record a permitted check and report a blocker. Avoid requiring a technician to select tax, price or payroll data they do not own.

Required forms should have concrete labels, appropriate keyboard/input types, retained validation errors, visible save/uncertain state and a return to the card. Keep at least 44px primary touch targets and keyboard focus visibility. Do not use icon-only unexplained actions for irreversible financial decisions.

Test dirty/noisy/workshop conditions without inventing biometric or surveillance features. Consider whether staff can use the device safely at that moment; a screen redesign cannot make phone use appropriate during hazardous work.

## Adviser/salesperson on phone and PC

Phone: quickly find client/history, record enquiry, promised callback, appointment/blocker and agreed next date. PC: compare scope/revisions, build a multi-line quote, review claim originals and prepare a document. One authoritative record should follow across devices; independent app installations do not automatically synchronise local databases.

A sales board should display responsibility and next action, not only stages. A “won” enquiry should not imply fully collected money. Chassis availability/reservation must come from the server, not an old cached tile.

## Cashier: fastest supported financial path

Keep customer/item search, quantities, price/discount/tax, issued amount, prior advance/receipts and balance close to the action. Confirm the actual receipt method/reference. Hide optional secondary fields until needed without hiding the result's meaning. A clear error should preserve entered data.

Normal sequence: prepare → review → issue → post receipt → display retained result/balance. Show “pending/uncertain” when a response is lost. Disable casual repeated submission, retain the operation ID and resolve through Sync. Do not show a success receipt before server confirmation.

PC test: keyboard item/barcode entry and tab order, receipt print with actual printer/browser settings. Phone test: two-line sale, partial collection, opening-balance collection and original-line return. Current keyboard barcode input works; camera scanner and printer drivers are separate integrations. Browser Print/PDF must be tested on the business's real devices.

## Stock clerk and accountant on a PC

The stock clerk needs a practical receiving/counting worksheet with order, item identity, expected/actual quantity, source and discrepancy. The current count command handles 100 items and the UI first 100; a large warehouse requires another pilot/design. Stale item changes must stop adjustment posting.

The accountant needs source exports/opening reconciliation, issued-document references, balances, inventory movement, supplier obligations and reviewed payroll inputs. Do not offer an “accounting export” badge that suggests the existing CSV is a complete Tally/Zoho voucher adapter. Complex setup/mapping and reconciliation belong on a PC, while owners can inspect the agreed results from a phone.

## Connection loss, refresh and shared devices

| Event | Staff must understand | Current behaviour / limit |
|---|---|---|
| Device disconnected | Which actions are drafts, which require the server | Encrypted customer/lead/quote-draft/attendance/follow-up entry; no final offline financial/stock posting |
| Browser refreshed after uncertain command | Whether action already committed | Session retains uncertain operation ID; Sync retries same command |
| Two tabs or devices edit | Who has latest state | One editing tab per account/browser; stale versions require review; separate devices use server state |
| Server restored | Old pending work may no longer fit authoritative records | SQLite epoch change blocks blind replay; provider restore needs external transaction reconciliation |
| Staff account disabled while offline | Cached access is not remotely erased immediately | Cache expiry 24 hours and permission recheck on sync |
| Device shared | Whose actions/data are visible | Separate accounts/logout; offline passphrase is not a replacement for server roles |

Do not call draft-only resilience “complete offline POS”. If the customer requires several days of independent offline final billing, record a product mismatch instead of making a hidden reliability promise.

## Performance and accessibility acceptance

The current snapshot UI paginates rendered tables to 50 rows and uses indexed lookup/aggregate client metrics. CI's previous synchronous DOM benchmark for 2,000 synthetic customers was p50 3.1ms/p95 5.9ms; it excluded browser paint, network and database time. It is not a low-end Android or hosted capacity result. See `VERIFICATION.md`.

For the real deployment measure login/cold start, snapshot size, first useful content, search, record open, quote preview, bill/receipt posting and sync recovery with realistic history/attachments and concurrent users. Proposed starting acceptance: common tap feedback under 100ms locally, readable loading/uncertainty states immediately, and measured p95 common server action within the business's agreed tolerance. No such live hosted SLO has been established.

Test a narrow Android viewport, the owner's PC, keyboard-only primary flows, visible focus, contrast, zoom, readable text and reduced-motion preference. Separate meaningful status from decoration. Validate language/number/date/print fit with actual staff. English-only UI is currently a material adoption question for both countries.

Record failures, device/network/data size and time window. Fix correctness/accessibility/primary-task blockers first, then polish animation or dashboard density. The accepted journey is a staff member completing their work, not the developer navigating a happy-path demonstration.

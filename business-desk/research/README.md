# India and Nepal: business workflow research

Research checked **5 October 2026**. Application baseline **2.2.0-rc.1**. This is a product/operating analysis for garages, vehicle showrooms, retailers/traders and service teams, with adjacent sectors assessed separately. It does not claim every Indian/Nepalese business has the same problem or that every proposed feature is implemented.

The strongest product direction is a business-owned workspace that makes **work, approvals, collections, stock and staff responsibilities** visible together. “Manage everything from a phone” should mean the owner can see the next decision and complete supported actions; complex setup, imports and accounting reconciliation still benefit from a PC and the right specialist.

## Read in this order

| File | What it answers |
|---|---|
| [India country dossier](india/README.md) | Different Indian customer types, payment/credit workflows, GST/accounting boundaries and switching constraints |
| [Nepal country dossier](nepal/README.md) | Nepal-specific dates/language, payments, business constraints, IRD/CBMS and sector fit |
| [Sector and pain-point playbook](workflows/SECTOR_PLAYBOOK.md) | Detailed jobs, roles, exceptions and acceptance examples across the four profiles and adjacent sectors |
| [Full client workflow and problem diagnosis](workflows/FULL_CLIENT_WORKFLOW.md) | 21 sections covering each hand-off, role, required evidence, money/stock effect, exception and first-week validation |
| [Phone and PC journeys](workflows/PHONE_AND_PC.md) | The daily owner/staff interface, interruptions, poor connection and measurable usability |
| [Feature priorities and product boundaries](FEATURE_PRIORITIES.md) | Implemented, partial and proposed work; what to build next and why |
| [Client discovery and switching worksheet](discovery/CLIENT_WORKSHEET.md) | Questions, source documents, configuration decisions, reconciliation and first-week acceptance |
| [Source register](SOURCES.md) | Primary sources, observation dates, evidence scope and limitations |

Also read the existing [detailed India switching playbook](../docs/INDIA_MARKET_AND_SWITCHING_PLAYBOOK.md) and [72-question client questionnaire](../docs/CLIENT_DISCOVERY_QUESTIONNAIRE.md). The new country dossiers extend those documents; they are not duplicate application implementations.

## How to interpret the evidence

- **Public evidence:** dated official statistics, regulation/official notices and research with an identified sample. Source IDs resolve in the register; each fact links to its source near the claim.
- **Vendor capability:** what a vendor documents/promotes. This establishes a category expectation, not independent adoption, market share, customer satisfaction or our feature parity.
- **Workflow hypothesis/design:** our reasoned operating proposal. Validate it by watching the owner's actual work and testing exceptions. No interviews, customer quotations or willingness-to-pay results have been invented.
- **App status:** verified against the current code and recorded tests, with implemented/partial/proposed distinctions. A product wish list is not a release note.

National registrations, survey firms and payment transactions have different denominators. Do not multiply them together to invent a SaaS market size. An insurance workshop is not a spare-parts shop; two branches of one owner are not two unrelated hosted organisations; a collected receipt is not a bank-settled payment.

## First practical outcome

Configure a customer's identity, country/registration, sector vocabulary, work stages, approval/handover rules, client terms, roles and source openings. Then have their staff complete a realistic **request → authorised work/sale → bill → collection → reconciliation → next follow-up** without developer guidance. Fix observed failures before expanding modules.

Use [separate hosting folders](../hosting/README.md) to run that configured business. Localhost is one PC; private HTTPS or Vercel/PostgreSQL is needed for phones and PCs to share authoritative records. The current Vercel connection is blocked by the intended team's 403; preparing files does not establish a live hosted service.

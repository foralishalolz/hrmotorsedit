# Business Desk

Business management for India and Nepal's garages, vehicle showrooms, retailers and service teams.

The runnable application is in **[business-desk](business-desk/)**. The older React quotation-tool files at the repository root are retained as migration references; they are not the entry point for this release.

**Status: 2.2.0-rc.1 — controlled pilot candidate.** This is not a claim of IRD software approval or completed production acceptance.

```sh
cd business-desk
python3 server.py --open
```

Python 3.10+ is sufficient for local use. No Node installation or cloud subscription is needed to run the local app. Windows users can open `business-desk/Start-Windows.bat`.

- [App features and usage](business-desk/README.md)
- [Market, positioning and monetisation plan](business-desk/docs/MARKET_AND_PILOT.md)
- [Private server deployment and recovery](business-desk/docs/DEPLOYMENT.md)
- [Pilot acceptance and remaining release gates](business-desk/docs/RELEASE_GATES.md)
- [Verification evidence](business-desk/VERIFICATION.md)
- [Security boundaries](business-desk/SECURITY.md)
- [Full India/Nepal client workflow research](business-desk/research/README.md)
- [Local, private-server, Vercel and GitHub operating kits](business-desk/hosting/README.md)

GitHub hosts the source and review history. The Python service needs a persistent server for online use; it cannot run on GitHub Pages. No customer records, passwords, setup keys or database backups belong in this repository.

- [India/Nepal product research and SaaS rollout](business-desk/docs/INDIA_NEPAL_PRODUCT_RESEARCH.md)
- [Detailed client discovery questions](business-desk/docs/CLIENT_DISCOVERY_QUESTIONNAIRE.md)

- [Detailed India sector, staff and switching playbook](business-desk/docs/INDIA_MARKET_AND_SWITCHING_PLAYBOOK.md)
- [Vercel/PostgreSQL deployment candidate and remaining launch gates](business-desk/docs/VERCEL_DEPLOYMENT.md)

This candidate adds business-owned branding, guided configuration, CSV migration, opening collections, agreed prices, cash/stock counts and inspections. The connected Vercel team returns 403, so no live Vercel deployment has been provisioned.

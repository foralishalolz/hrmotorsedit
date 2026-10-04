# Business Desk

Business management for Nepal's garages, vehicle showrooms, retailers and service teams.

The runnable application is in **[business-desk](business-desk/)**. The older React quotation-tool files at the repository root are retained as migration references; they are not the entry point for this release.

**Status: 2.0.0-rc.1 — controlled pilot candidate.** This is not a claim of IRD software approval or completed production acceptance.

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

GitHub hosts the source and review history. The Python service needs a persistent server for online use; it cannot run on GitHub Pages. No customer records, passwords, setup keys or database backups belong in this repository.

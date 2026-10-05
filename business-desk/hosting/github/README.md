# GitHub source, checks and operator kits

Repository: [foralishalolz/hrmotorsedit](https://github.com/foralishalolz/hrmotorsedit). The runnable application is `business-desk/`; root-level legacy React files are retained migration references. GitHub stores/reviews source. It does not run this Python business service. [GitHub Pages restrictions](https://docs.github.com/en/pages/getting-started-with-github-pages/github-pages-limits) also exclude commercial SaaS and sensitive transactions.

## Keep releases reviewable

Use a branch and pull request. **Business Desk quality** runs business/security rules, real browser journeys, container/proxy health and real PostgreSQL tests. Inspect the exact commit's checks and browser evidence. Protect `main` with those checks and the review policy appropriate to the repository owner; branch protection has not been silently configured.

Do not commit live databases, `.env`, keys, customer CSVs/photos, backups or operator launch records containing actual client data. The committed `.env.example` files are placeholders. Production credentials belong in the provider's sensitive environment controls, not GitHub artifact ZIPs.

## Download four release kits

After this workflow is on `main`, open **Actions → Business Desk operator kits → Run workflow**. Select `main` or a reviewed branch and `all` or the desired edition. The workflow checks the application rules/package boundaries, builds ZIPs and SHA-256 files, and uploads the selected artifacts for 14 days. Download the artifact, then extract the inner edition ZIP. It contains a `PACKAGE-MANIFEST.json` with hashes of included source files.

No Vercel/Docker/provider credentials are required for the package workflow. It does not create a public GitHub Release, contact customers, deploy, provision a database or perform a migration. Use Vercel's Git integration or the private-server runbook to publish an app after configuration and acceptance.

For local creation:

```sh
python3 business-desk/hosting/package.py --profile all --output business-desk/packages/reviewed-release
```

The GitHub edition uses `git ls-files`; stage newly added source before building it during development. It is a clean focused source kit, not a clone of the full legacy repository/history. Runtime editions need no Git checkout after extraction.

If starting from the extracted GitHub ZIP, run `git init` and `git add README.md business-desk .github` in the extracted root before rebuilding the GitHub kit or running all its source-index checks. This creates only a local index; it does not publish or contact GitHub. Cloning the existing repository is preferable when you need its actual history/branches.

## Verification commands for developers

From `business-desk/`, `python3 -m unittest -q` runs application plus hosting-kit checks; PostgreSQL integration tests require the isolated `DESK_TEST_POSTGRES_URL` fixture. Do not use a customer's database for tests. Browser checks use development-only npm/Playwright dependencies; see `VERIFICATION.md`. Production app operation does not need Node.

Use the [operations launch record](../operations/launch-record.example.json) to connect the Git commit to the actual deployed build, database schema, acceptance and recovery evidence. A green workflow alone is not a signed-off production business.

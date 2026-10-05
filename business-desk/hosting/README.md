# Hosting and running Business Desk

One application, separate operating kits. Version 2.3.0-rc.1 is a tested pilot candidate; completing a package does not complete production acceptance.

| What you need | Folder | Database | Who can connect |
|---|---|---|---|
| Try the app on one PC, without a subscription | [local](local/README.md) | SQLite on that PC | Browser on the same PC |
| Staff phones and PCs for one customer organisation | [private-server](private-server/README.md) | SQLite on a persistent Docker volume | Authorised users over your HTTPS domain |
| Vercel-hosted phones/PCs and private customer organisations | [vercel](vercel/README.md) | Managed PostgreSQL | Authorised users over your HTTPS domain |
| Store code, run tests, download reviewed release kits | [github](github/README.md) | No live database in GitHub | Developers/operators; GitHub is the source host |
| Keep a deployed business working and recover it | [operations](operations/README.md) | Edition-specific backup | Named operator and business owner |

**Start locally:** from the repository root, run `python3 business-desk/server.py --open`. For Windows use `business-desk/Start-Windows.bat`. Use the hosted options when a phone must reach the app. A phone's `localhost` is the phone itself.

**Start Vercel:** import this GitHub repository with **Root Directory = `business-desk`**, Framework = Other, production branch = `main`. Read the Vercel folder before deploying; it requires a durable database and a separate migration. The connected intended Vercel team previously returned 403; no live project or production database was created.

## Make separate downloadable folders

From the repository root:

```sh
python3 business-desk/hosting/package.py --profile all --output business-desk/packages/release-2.3
```

This produces four ZIPs, each with a `business-desk/` application folder, a file/hash manifest and an accompanying SHA-256 checksum. Extract the edition you need. Use a new output folder for each build: existing release files are deliberately not overwritten. The GitHub source edition needs a Git checkout and includes only tracked/staged app files plus the quality/package workflows. Runtime editions use an explicit source list. None includes a customer's database, backups, `.env`, development dependencies or generated `public/` output. The Vercel kit generates `public/` during its build.

The kits are deployment source, not installers or proof of a live service. Generated ZIPs stay outside Git. You can also download them from the manual **Business Desk operator kits** GitHub Actions workflow after it is enabled on `main`.

## Check before running

```sh
python3 business-desk/hosting/preflight.py --profile local
python3 business-desk/hosting/preflight.py --profile private-server --env-file business-desk/deploy/.env
python3 business-desk/hosting/preflight.py --profile vercel --env-file business-desk/hosting/vercel/.env.local
```

Run the command for your edition only. Templates contain placeholders; they must fail until you enter private values. These checks do not contact a provider, create a project, migrate a database or print credentials. Production checks reject an insecure database URL and preview-host enablement. Use `--environment preview` only with isolated preview data.

Read the [India/Nepal research index](../research/README.md), configure the business's actual workflow, and complete the [launch record](operations/launch-record.example.json). Government billing, accounting and statutory payroll acceptance are separate gates. Never place a local database on Vercel function storage or use GitHub Pages for this service.

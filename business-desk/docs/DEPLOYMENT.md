# Private server deployment

## Deployment model

GitHub stores source and review history. GitHub Pages serves static files and does not run this Python application or its database. Its published restrictions also exclude running a commercial SaaS on Pages. Use a persistent private server for the app. Sources: [GitHub Pages creation](https://docs.github.com/en/pages/getting-started-with-github-pages/creating-a-github-pages-site), [Pages limits](https://docs.github.com/en/pages/getting-started-with-github-pages/github-pages-limits).

For the first 3–5 paying pilots, isolate each customer organisation with its own server/container stack, volume and hostname. Multiple businesses inside an instance share owners and backups. This is not public multi-tenant SaaS isolation.

A small Linux server with a persistent disk, Docker Compose and a domain pointed at its public IP is the intended starting environment. The app uses one Waitress process with eight threads and SQLite WAL. Do not increase process/replica counts or put the database on a shared network filesystem. Capacity must be measured with actual pilot data and peak users.

## Configure and start

Check the exact commit's CI first. Install Docker/Compose using the provider's supported instructions, configure DNS and permit inbound 80/443. Keep SSH restricted to administrators. Then:

```sh
git clone https://github.com/foralishalolz/hrmotorsedit.git
cd hrmotorsedit
git switch main
cd business-desk
python3 deploy/configure.py desk.your-domain.com
cd deploy
docker compose up -d --build
docker compose ps
```

`configure.py` writes `deploy/.env` with a random setup key and restrictive file permissions, and refuses to overwrite an existing file. Read this file locally to enter the setup key when creating the first owner account. Never commit it, share it in a support ticket, or place it in a browser bundle. Use a real hostname under your control; the example is not a deployed address.

Caddy obtains HTTPS certificates. The `desk` service has no published port; only Caddy is publicly exposed. The trusted-proxy setting relies on this private Compose network. Never publish port 8080 while trusting all proxy sources. For a different proxy/network, configure the exact trusted proxy and preserve the original Host.

Create the owner, business profile, tax defaults and staff accounts. Verify permissions from a real cashier/technician phone. Enable encrypted offline drafts separately on trusted devices. Remove access and device data during staff offboarding.

The app container runs without root privileges, with a read-only application filesystem and a persistent `/data` volume. Do not use `docker compose down -v` during upgrades: that deletes persistent volumes.

## Backups and restore drill

Automatic local backups are stored in `/data/backups`, with 14 daily copies. Monitor that a recent file exists. This protects against some mistakes, not server loss. Configure a separate encrypted offsite backup destination and a monitored daily transfer before live customer data. The destination, credentials and provider retention are deployment decisions; none are silently provisioned by this repository.

Create a consistent backup through the owner's UI or console:

```sh
docker compose exec desk python admin.py --data-dir /data backup
```

The command prints the exact backup path. Copy that file from the container using `docker compose cp`, encrypt it and transfer it to the chosen backup destination. Do not copy only the live `.sqlite3` file while WAL writes are active.

Run a restore drill on a separate disposable instance: sign in, restore a backup, sign in again with its account, and verify a selected invoice, receipt balance, stock item and original attachment. Record restoration time and backup age. A candidate pilot target is recovery within four hours and no more than one working day of data loss; these are proposed service objectives, not a guarantee of this configuration.

Restoring changes the database epoch. Devices with old queued operations must reconcile against restored records; the app deliberately blocks automatic replay of those commands. Do not manually bypass the epoch check.

## Upgrade and rollback

1. Record the current commit and container image ID. Download a consistent backup.
2. Read migration/release notes and confirm the new commit's tests passed.
3. Arrange a short maintenance period so staff sync pending drafts and stop entering work.
4. Pull the reviewed commit, rebuild and start the stack.
5. Verify health, login, a draft quote, invoice balance, stock quantity and a backup.
6. If a rollback is required, stop writes and preserve the failed-release database first. Restore the pre-upgrade backup with the matching previous image on a separate instance, verify it, then cut over. Do not run an old binary against an unknown newer schema.

Supported v1/v2 backups migrate to schema v3. The original local source remains available through Git history.

## Monitoring and operating ownership

Monitor HTTPS availability, container health/restarts, disk space, daily backup freshness, and failed sync reports. Health being green does not prove tax correctness or successful offsite recovery. Keep logs rotated, restrict access to data/backup volumes, and apply dependency/security updates after testing. Avoid logging request bodies, customer documents, passwords or setup keys.

Assign an operator for upgrades, an owner for restores, and a support contact. Before charging for uptime or recovery commitments, measure the deployment and document actual support coverage.

Runtime references: [Waitress usage](https://docs.pylonsproject.org/projects/waitress/en/stable/usage.html), [Waitress release information](https://pypi.org/project/waitress/), [Caddy reverse proxy](https://caddyserver.com/docs/quick-starts/reverse-proxy).

# Private HTTPS server edition

Use for phones and PCs belonging to one customer organisation. Each unrelated customer gets its own stack, hostname and data volume. This edition uses one Waitress process with SQLite; adding replicas is unsupported. Use the Vercel/PostgreSQL edition for the shared hosted model.

## Configure from a checkout or extracted kit

Install Docker Engine with Compose on a Linux server with a persistent disk. Configure a domain you control to point at its IP. Allow inbound 80/443 for HTTPS and restrict administrator access. The example host below must be replaced.

```sh
cd business-desk
python3 deploy/configure.py desk.your-domain.com
python3 hosting/preflight.py --profile private-server --env-file deploy/.env
cd deploy
docker compose config --quiet
docker compose up -d --build
docker compose ps
```

`configure.py` creates `deploy/.env` once, with a random private setup key and restrictive permissions. It refuses to overwrite an existing configuration. Keep this file out of Git, screenshots, ZIPs and support tickets. Read the setup key locally to create the first owner. `hosting/private-server/.env.example` documents the variables; the canonical runtime file is **`deploy/.env`**.

Caddy handles HTTPS. The app service has no public port. Its trusted-proxy setting depends on the private Compose network; do not expose port 8080. The app runs as a non-root user with a read-only application filesystem and persistent `/data`. Compose commands must run from `business-desk/deploy`, or use `docker compose --project-directory business-desk/deploy --env-file business-desk/deploy/.env -f business-desk/deploy/compose.yaml ...` from the repo root. Keep the project name/directory stable so an upgrade uses the same volumes.

Open your domain on the PC and staff phone. Create separate staff logins; check technician, cashier and stock-clerk access. Add the browser shortcut to the home screen if useful. Do not expose financial data on a shared unlocked phone.

## Backup, upgrade and stop

From `business-desk/deploy`:

```sh
docker compose exec desk python admin.py --data-dir /data backup
```

Copy the **exact path printed** using `docker compose cp desk:/data/backups/ACTUAL-FILENAME.sqlite3 /your/protected/backup-folder/`. Replace the filename and destination; the literal example is not a file. Encrypt and transfer a consistent backup offsite. A volume on the same server is not disaster recovery.

During an upgrade, stop new work after pending drafts are reconciled; back up, record the previous commit/image, update to a tested commit, rebuild, and check a selected bill, receipt, stock item and attachment. Preserve a failed-upgrade database before restoring elsewhere. Old queued commands must be reviewed after a restore.

`docker compose stop` stops services while retaining data. **Do not use `docker compose down -v` for routine stopping or upgrades**: it deletes the volumes. Never run the old application against an unknown newer schema as a rollback shortcut.

Run `python3 ../hosting/operations/check_health.py https://desk.your-domain.com --expect-version 2.2.0-rc.1` from the deploy folder. Before live data, complete the [operations guide](../operations/README.md) and [release gates](../../docs/RELEASE_GATES.md). The [full private-server runbook](../../docs/DEPLOYMENT.md) remains the detailed reference.

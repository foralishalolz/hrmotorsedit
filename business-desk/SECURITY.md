# Security boundaries

Use a separate private server/database per paying customer organisation during the pilot. Businesses inside one instance share its owners, backups and administration; they are not separate SaaS tenants.

Hosted mode uses Waitress behind HTTPS, an explicit allowed origin, Secure/HttpOnly/SameSite cookies, CSRF tokens, a one-time setup key, login rate limiting, role checks, optimistic versions, and transaction-scoped idempotency receipts. Do not expose the local development server or the container's internal port to the internet. The supplied Docker network is the trusted proxy boundary.

Passwords use salted PBKDF2-SHA256 (600,000 iterations). Old v1 hashes are readable for migration. Session storage is in memory: run one process, with threads, per instance. Restarts require sign-in; password changes and disabled accounts invalidate access on the next request.

Offline copies are opt-in and encrypted with AES-GCM and a PBKDF2-derived device passphrase. Payroll and commission records are excluded. Offline access is limited to 24 hours after the last refresh. A device that is already offline cannot receive immediate account revocation; manage trusted devices accordingly. One editing tab per account per browser prevents concurrent vault writers. Other staff use separate devices or browser profiles.

Offline drafts, device passphrases and browser recovery are not substitutes for a server backup. Financial posting, stock allocation and vehicle reservation require server acknowledgement. A conflicting edit requires review; an uncertain financial command must be retried with its original ID. No entire-database file synchronisation is used.

The SQLite database, attachment blobs and backup files are not encrypted by the application on the server. Protect the server volume and encrypt offsite backup storage. Repository and CI data are fictional. Keep `.env`, `data/`, SQLite files and backups out of Git.

This release has not received an independent penetration test. Before public customer onboarding, complete the release gates, assess data retention and contractual requirements, and configure monitored offsite recovery. Report vulnerabilities privately to the repository owner; do not attach customer records to a public issue.

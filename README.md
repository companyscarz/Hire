# Hire POS (ScarZ POS)

Hire POS is a mobile-first point-of-sale and inventory application for small businesses. The active development and deployment branch for this project is `pre-main`; do not merge to `main` without explicit approval.

## Included features

- Business-owner registration, login/logout, password hashing, CSRF protection and production cookie settings.
- Business-scoped products, stock quantities, sales, sale items, expenses and dashboard totals.
- Auditable stock ledger for opening stock, completed-sale deductions, manual adjustments, and sale-void inventory restoration with before/after quantities and reasons.
- Sale voiding that retains the original transaction, requires a reason, records the user/time, permits one void per sale, restores stock transactionally once, and excludes voided sales from dashboard and filtered report/CSV totals. Voiding is not a refund.
- Transactional checkout with stock validation and row locking where supported by the database.
- PostgreSQL through `DATABASE_URL`, Flask application factory, SQLAlchemy, Flask-Migrate and Gunicorn.
- Trial/subscription fields and server-side expiry checks.
- Mobile-first PWA manifest and responsive interface.
- Date-filtered reports for revenue, cost of goods sold, estimated gross profit, expenses, estimated operating result, daily totals and payment-method breakdowns; filtered CSV export and printable receipts.
- CI workflow for Python compilation and pytest on `pre-main` pushes and pull requests.

## Local development (Windows)

1. Install Python 3.12 or newer.
2. Copy `.env.example` to `.env`. Set `DATABASE_URL` to the database you intend to use. **If it points to your hosted/production database, local testing can change real business data. Prefer a separate test database.** For isolated local testing, omit `DATABASE_URL` to use the default SQLite database.
3. In PowerShell, from the repository root:

   ```powershell
   python -m venv .venv
   .\.venv\Scripts\Activate.ps1
   pip install -r requirements.txt
   ```

4. Run the development server:

   ```powershell
   python run.py
   ```

5. Open `http://127.0.0.1:5000`. Stop the server with `Ctrl+C`.

The local `run.py` entry point uses Flask's development server and runs the existing `init-db` bootstrap before starting. This is for local development only. It may create missing tables and apply the additive barcode/scanner schema updates. Do not use this entry point as the production web server.

## Production deployment with Nixpacks and Gunicorn

The repository's `nixpacks.toml` configures Python 3.12 and starts the application with Gunicorn. The production web process binds to **`0.0.0.0:$PORT`**, so the hosting platform can route traffic to it. The command is equivalent to:

```bash
gunicorn --bind 0.0.0.0:${PORT:-8000} \
  --workers ${WEB_CONCURRENCY:-2} \
  --timeout 60 \
  --graceful-timeout 30 \
  --access-logfile - \
  --error-logfile - \
  'scarz_pos:create_app()'
```

Nixpacks builds from the repository root and installs dependencies from `requirements.txt`. Before starting Gunicorn, the production command runs `flask --app 'scarz_pos:create_app()' ensure-db`. This checks for the core `user` table: if it exists, startup leaves the existing schema untouched; if it is absent, the command runs the current schema bootstrap once to initialize a new database. If the database is empty, this step creates the application's tables before the web server starts.

### Required hosting configuration

Set these in the hosting provider's environment settings; never commit production secrets:

- `APP_ENV=production`
- `SECRET_KEY`: a long, random secret unique to this deployment.
- `DATABASE_URL`: connection URL for the intended PostgreSQL database, with SSL settings required by your provider.
- `PORT`: normally injected by the platform. Nixpacks/Gunicorn defaults to port `8000` if it is not set.
- `WEB_CONCURRENCY`: optional Gunicorn worker count; defaults to `2`. Adjust to the available memory and workload.
- `NYLONPAY_API_KEY`, `NYLONPAY_API_SECRET`, `NYLONPAY_WEBHOOK_SECRET`: configure only when enabling subscription payments.
- `SCARZ_POS_PLAN_MONTHLY_UGX`, `SCARZ_POS_PLAN_QUARTERLY_UGX`, `SCARZ_POS_PLAN_ANNUAL_UGX`: configure server-side plan prices before offering paid subscriptions.
- `PUBLIC_BASE_URL`: set to the public HTTPS URL if required by payment callback configuration.

Configure a persistent PostgreSQL service and HTTPS/custom domain with the host. The app exposes `/health/live` for process liveness and `/health/ready` for a basic database readiness check. Use the host's health-check configuration if supported.

### Database setup and schema changes

The production startup command runs `ensure-db`. It checks whether the core `user` table exists and only runs the bootstrap if it does not, so a brand-new empty PostgreSQL database is initialized automatically while a database with an existing `user` table is not modified by this automatic check.

The underlying `init-db` command calls `db.create_all()` and applies additive barcode/scanner schema updates. It is **not** a full migration system and will not update every existing table to match future model changes. If an existing database has a partial or outdated schema, inspect it and use a reviewed migration rather than relying on this bootstrap. Confirm `DATABASE_URL` points to the intended database before deployment, and keep a backup/restore plan for any database containing important data. A checked-in initial Flask-Migrate revision and reviewed migrations for subsequent schema changes are still needed before treating database deployment as fully production-hardened.

## Application health endpoints

- `GET /health/live`: confirms the Flask process is serving requests; it does not prove the database is available.
- `GET /health/ready`: executes a read-only `SELECT 1` against the configured database and returns `503` if the check fails.

## Environment reference

| Variable | Purpose |
| --- | --- |
| `APP_ENV` | Use `production` on the production host. |
| `SECRET_KEY` | Required strong secret; do not reuse the development placeholder. |
| `DATABASE_URL` | PostgreSQL connection URL, for example `postgresql+psycopg://user:password@host:5432/scarz_pos`. Legacy `postgres://` is normalized by the app. |
| `PORT` | Hosting-provided HTTP port; Gunicorn binds to `0.0.0.0`. |
| `WEB_CONCURRENCY` | Optional Gunicorn worker count (default `2`). |
| `NYLONPAY_API_KEY`, `NYLONPAY_API_SECRET`, `NYLONPAY_WEBHOOK_SECRET` | Payment provider credentials. |
| `SCARZ_POS_PLAN_MONTHLY_UGX`, `SCARZ_POS_PLAN_QUARTERLY_UGX`, `SCARZ_POS_PLAN_ANNUAL_UGX` | Server-side subscription plan pricing. |
| `PUBLIC_BASE_URL` | Public base URL used by integrations that need it. |

## Production-readiness status and known limitations

The Nixpacks/Gunicorn startup path and basic health endpoints are configured, but **a successful deployment command alone does not mean the whole product has passed a production security and operations audit**.

Before opening the service broadly to the public:

- Add and review an initial Flask-Migrate revision, then use reviewed migrations for schema changes.
- Run automated tests against a disposable PostgreSQL database and perform a staging smoke test for registration, login, checkout, stock adjustments, sale voids, reports, and tenant isolation.
- Verify database backups and a restore procedure.
- Complete security review, including rate limiting, password recovery/email verification, session behavior, authorization and payment webhook verification.
- Verify Nylon Pay in provider sandbox and then production before enabling paid subscriptions. POS payment-method labels alone do not process electronic payments.
- Test hosting health checks, logs, restart behavior, resource limits and the configured Gunicorn worker count.

Current MVP limitations include missing email verification/password recovery and staff roles, no offline sale synchronization, and no full returns/refunds workflow. Sale voiding does not automatically refund money. Reports are operational estimates, not audited accounting or tax reports. Trial expiry and subscription payment flows require additional end-to-end production verification. Configure the Nylon Pay webhook URL as `https://YOUR-DOMAIN/webhooks/nylonpay/subscriptions` when the integration is ready.

## Safety rules

- Never commit `.env`, database URLs with passwords, or payment secrets.
- Never trust browser-submitted prices or totals; server-side logic must calculate them.
- Use a separate test database for local testing and staging.
- Back up production data before schema changes.
- Do not force-push or merge `pre-main` to `main` without explicit approval.

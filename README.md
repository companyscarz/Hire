# ScarZ POS

ScarZ POS is a mobile-first, subscription-ready point-of-sale and inventory application for small businesses. This branch replaces the Hire application on `pre-main` only; `main` is untouched and Git history is preserved.

## MVP foundation included
- Business-owner registration, login/logout, password hashing, CSRF protection and secure cookie settings in production.
- Tenant-scoped products, stock quantities, sales, sale items, expenses and dashboard totals.
- Auditable stock ledger for opening stock, completed-sale deductions, manual adjustments, and sale-void inventory restoration with before/after quantities and reasons; manual adjustments cannot create negative stock or change another business's inventory.
- Safe sale voiding: original transaction retained, mandatory reason and user/time audit record, one void per sale, stock restored transactionally once, and voided sales excluded from dashboard and date-filtered report/CSV totals. Voiding does not automatically refund money.
- Checkout runs in a database transaction, locks selected product rows where supported, and rejects invalid quantities or insufficient stock.
- PostgreSQL via `DATABASE_URL`, Flask application factory, SQLAlchemy, Flask-Migrate and Gunicorn/Nixpacks entrypoint.
- Trial/subscription fields and server-side expiry checks as the foundation for paid plans.
- Mobile-first PWA manifest and responsive interface.
- Date-filtered reports for sales revenue, cost of goods sold, estimated gross profit, recorded expenses, estimated operating result, daily totals and payment-method breakdowns; filtered CSV export includes sale lines and expenses.
- CSV sales export and printable receipt.
- Automated CI workflow for Python compilation and pytest on `pre-main` pushes and pull requests.

## Important MVP limitations
- Subscription checkout uses the Nylon Pay SDK pattern already used in Digital Read/Qavzuno: pending payment record, Mobile Money collection, signed webhook verification, reference matching, amount/currency checks, and idempotent subscription activation. POS sales' local payment labels are not electronic payment processing.
- The first database bootstrap uses `db.create_all()` for a fresh MVP database. It does not alter existing tables. Before a public production launch, check in an initial Flask-Migrate revision and use migrations for all schema changes.
- Email verification, password recovery, staff roles, sale returns/refunds (voiding is not a refund), offline sale synchronization, rate limiting and a complete security audit remain to be done. Date-filtered business reporting is included, but it is not a replacement for audited accounting or tax reports.
- Trial expiry is enforced for inventory creation, checkout and expense creation. Subscription payment initiation and webhook handling are implemented on this branch, but live provider verification and production tests are still pending. Configure plan prices before offering checkout. Configure Nylon Pay's webhook URL as `https://YOUR-DOMAIN/webhooks/nylonpay/subscriptions`.

## Local setup
1. Install Python 3.12+.
2. Copy `.env.example` to `.env` and set `DATABASE_URL` to the PostgreSQL database you intend to use. A remote hosted database is supported; remember that local actions will affect that database. SQLite can be used for isolated testing by removing `DATABASE_URL` from `.env`.
3. In PowerShell, create and activate the virtual environment:
   ```powershell
   python -m venv .venv
   .\.venv\Scripts\Activate.ps1
   pip install -r requirements.txt
   ```
4. Start the app:
   ```powershell
   python run.py
   ```
5. Open `http://127.0.0.1:5000`. The local entry point runs the existing additive `init-db` bootstrap before starting the server.
6. Stop the server with `Ctrl+C`.

The local entry point uses the `DATABASE_URL` configured in `.env`, including a remote PostgreSQL database if that is your setup. **Use caution:** the app will read and write to that database, and the startup bootstrap may create missing tables and apply its additive barcode/scanner schema updates. Sales, inventory changes, and voids performed locally will affect that same database. Use a dedicated test database/business for testing whenever possible. Production deployments should continue to use the Gunicorn/Nixpacks command rather than Flask's development server.

## Environment
- `SECRET_KEY`: required in production; long random secret.
- `DATABASE_URL`: PostgreSQL URL, e.g. `postgresql+psycopg://user:password@host:5432/scarz_pos`. `postgres://` is normalized.
- `APP_ENV`: set to `production` on hosting.
- `PORT`: hosting-provided port or 8000.
- `NYLONPAY_API_KEY`, `NYLONPAY_API_SECRET`, `NYLONPAY_WEBHOOK_SECRET`: Nylon Pay credentials. Never commit credentials.
- `SCARZ_POS_PLAN_MONTHLY_UGX`, `SCARZ_POS_PLAN_QUARTERLY_UGX`, `SCARZ_POS_PLAN_ANNUAL_UGX`: server-side plan prices in UGX; keep unset until prices are decided.

## Deployment
Nixpacks builds from the repository root and starts Gunicorn on `0.0.0.0:$PORT`. Configure a persistent PostgreSQL database, set environment variables, and configure HTTPS/custom domain at the hosting provider. The startup command only creates missing tables; it is not a migration system and will not modify existing schema. The `subscription_payments` and `sale_void` tables are created on fresh databases by `init-db`. Existing deployments must run `init-db` against the intended database to create these missing tables; this command does not alter existing tables. Back up the database before making deployment changes. A checked-in migration workflow is still recommended before public production use.

## Safety
Do not store payment secrets in source control. Do not trust browser-submitted prices or totals. All money values are decimal and server-calculated. Do not merge `pre-main` to `main` without explicit approval.
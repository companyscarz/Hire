# ScarZ POS

ScarZ POS is a mobile-first, subscription-ready point-of-sale and inventory application for small businesses. This branch replaces the Hire application on `pre-main` only; `main` is untouched and Git history is preserved.

## MVP foundation included
- Business-owner registration, login/logout, password hashing, CSRF protection and secure cookie settings in production.
- Tenant-scoped products, stock quantities, sales, sale items, expenses and dashboard totals.
- Checkout runs in a database transaction, locks selected product rows where supported, and rejects invalid quantities or insufficient stock.
- PostgreSQL via `DATABASE_URL`, Flask application factory, SQLAlchemy, Flask-Migrate and Gunicorn/Nixpacks entrypoint.
- Trial/subscription fields and server-side expiry checks as the foundation for paid plans.
- Mobile-first PWA manifest and responsive interface.
- CSV sales export and printable receipt.

## Important MVP limitations
- Nylon Pay checkout and verified callbacks are **not activated yet**. Exact implementation must follow the official API documentation supplied by the owner; no guessed endpoints or unverified payment callbacks are used. Cash and other payment methods are currently recorded as sale payment labels, not processed electronically.
- The first database bootstrap uses `db.create_all()` for a fresh MVP database. It does not alter existing tables. Before a public production launch, check in an initial Flask-Migrate revision and use migrations for all schema changes.
- Email verification, password recovery, staff roles, returns/refunds, offline sale synchronization, rate limiting, advanced reporting and a complete security audit remain to be done.
- Trial expiry is enforced for inventory creation, checkout and expense creation. The subscription checkout and self-service renewal flow are pending Nylon Pay verification.

## Local setup
1. Install Python 3.12+ and PostgreSQL.
2. Create a database and copy `.env.example` to `.env`.
3. `python -m venv .venv` then activate it.
4. `pip install -r requirements.txt`
5. `flask --app 'scarz_pos:create_app()' init-db`
6. `flask --app 'scarz_pos:create_app()' run --debug`

## Environment
- `SECRET_KEY`: required in production; long random secret.
- `DATABASE_URL`: PostgreSQL URL, e.g. `postgresql+psycopg://user:password@host:5432/scarz_pos`. `postgres://` is normalized.
- `APP_ENV`: set to `production` on hosting.
- `PORT`: hosting-provided port or 8000.
- `NYLONPAY_*`: reserved for the verified integration after reviewing the official API docs. Never commit credentials.

## Deployment
Nixpacks builds from the repository root and starts Gunicorn on `0.0.0.0:$PORT`. Configure a persistent PostgreSQL database, set environment variables, and configure HTTPS/custom domain at the hosting provider. The startup command only creates missing tables; it is not a migration system and will not modify existing schema. Use a checked-in migration revision before introducing schema changes or opening a public production service.

## Safety
Do not store payment secrets in source control. Do not trust browser-submitted prices or totals. All money values are decimal and server-calculated. Do not merge `pre-main` to `main` without explicit approval.
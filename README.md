# Hire — ScarZ Cloud

Hire is being repurposed as Company ScarZ's developer-hosting PWA. The goal is to let developers connect Git repositories, deploy supported applications, view CPU/RAM/storage/network usage, and manage hosting subscriptions without exposing the host server or other customers' resources.

**Current status:** foundation in progress. This branch is not production-ready and must not be used for untrusted customer workloads yet.

## Development branch

- Work on `pre-main`.
- Do not merge to `main` without explicit approval.

## New application foundation

The new service lives in `app/hire_cloud/`, separate from the legacy job-board modules while the migration is underway.

- Flask application factory: `hire_cloud:create_app()`
- PostgreSQL is the intended production database.
- SQLAlchemy models and Flask-Migrate are used for the new domain.
- `app/cloud_requirements.txt` contains a minimal dependency set for the new service.
- Authentication uses Werkzeug password hashing, signed Flask sessions, CSRF tokens for unsafe requests, and tenant-scoped project queries.
- Nixpacks configuration: repository-root `nixpacks.toml`; it installs `app/cloud_requirements.txt` and starts Hire Cloud.
- Tests: `app/tests/`

## Nixpacks / Dokploy deployment

The root `nixpacks.toml` installs the cloud requirements and starts:

```bash
cd app && gunicorn --bind 0.0.0.0:${PORT:-8000} 'hire_cloud:create_app()' --workers 2 --timeout 120
```

Use **port 8000** as the internal application port unless Dokploy explicitly supplies a different `PORT`. The app binds to `0.0.0.0`; route public HTTPS through Dokploy's proxy/domain configuration. Keep the build type set to **Nixpacks**, not Dockerfile.

Add these values in Dokploy's server-side environment settings (never commit real values):

- `APP_ENV=production`
- `SECRET_KEY` — a long random secret, at least 32 random bytes
- `DATABASE_URL` — private PostgreSQL connection string, preferably `postgresql+psycopg://USER:PASSWORD@HOST:5432/DBNAME`
- `PORT=8000` only if Dokploy does not already configure the internal port

The PostgreSQL user should be restricted to this application and must not be a superuser. Do not expose the database publicly unless properly protected.

## Local development

Run locally from the `app` directory:

```bash
python -m venv .venv
source .venv/bin/activate
python -m pip install -r cloud_requirements.txt
cp .env.example .env
# Set DATABASE_URL to a local PostgreSQL database and set SECRET_KEY.
flask --app 'hire_cloud:create_app()' db init
flask --app 'hire_cloud:create_app()' db migrate -m "initial schema"
flask --app 'hire_cloud:create_app()' db upgrade
gunicorn --bind 0.0.0.0:8000 'hire_cloud:create_app()'
```

**Migration status:** the initial Flask-Migrate revision has not yet been generated and reviewed in this branch. Do not run these migration commands against production until a reviewed revision is checked in. Do not run `db init` again once a migrations directory exists. Automated tests use a temporary SQLite database; production requires PostgreSQL.

Implemented account routes: `GET/POST /auth/register`, `GET/POST /auth/login`, `POST /auth/logout`, authenticated `GET /dashboard`, and tenant-scoped `GET /api/workspace/projects`. Email verification, password recovery, MFA, robust rate limiting, tenant switching, billing, live metrics, Git OAuth, provisioning, and object storage are not implemented yet.

Health endpoints:

- `GET /health/live` — process liveness.
- `GET /health/ready` — readiness, including database connectivity.

## Security status and warnings

- Secrets that were previously committed to `app/settings.py` have been removed from the current version of that file and moved to environment-based configuration. **Rotate the old credentials at their providers**; deleting them from the latest revision does not remove them from Git history.
- Keep real `.env` files and credentials out of Git. Use Dokploy's server-side environment/secrets configuration.
- The legacy job-board code still exists during migration and has not received a full security audit.
- No automated customer provisioning, Git OAuth, object-storage access, payment processing, or production resource enforcement is complete yet.
- Do not grant customers Docker socket, host shell, owner-level Dokploy, or broad server access.
- A single shared VPS is not a strong enough boundary for arbitrary untrusted customer workloads. Use a restricted invite-only pilot and plan to separate customer workloads from Company ScarZ's own applications before public self-service hosting.

## Architecture and delivery gates

See [the implementation plan](docs/SCARZ_CLOUD_IMPLEMENTATION_PLAN.md) for the problem/solution map, target architecture, scope, milestones, documentation links, and acceptance criteria.

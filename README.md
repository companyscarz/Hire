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
- Tests: `app/tests/test_hire_cloud_foundation.py`

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
gunicorn 'hire_cloud:create_app()'
```

The migration commands above are the expected first local setup. Review generated migrations before applying them to any non-disposable database. Automated tests use a temporary SQLite database for fast model/health checks; production is configured to require PostgreSQL.

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

#!/usr/bin/env bash
# Nixpacks/Dokploy entrypoint for the single-instance Hire Cloud pilot.
# Fail closed: never serve account routes against an unmigrated database.
set -Eeuo pipefail

cd "$(dirname "$0")"
echo "[hire-cloud] Applying database migrations before starting Gunicorn..."
flask --app 'hire_cloud:create_app()' db upgrade --directory migrations
echo "[hire-cloud] Database migrations are up to date; starting web server."
exec gunicorn --bind "0.0.0.0:${PORT:-8000}" 'hire_cloud:create_app()' --workers "${WEB_CONCURRENCY:-2}" --timeout 120

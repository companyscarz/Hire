"""Local development entry point for ScarZ POS.

Run with: python run.py

For safety, this refuses remote databases unless ALLOW_REMOTE_DATABASE=1 is
explicitly set. Production deployments should continue to use Gunicorn/Nixpacks.
"""
import os
import sys
from urllib.parse import urlparse

from dotenv import load_dotenv

# Load project configuration before importing the application factory.
load_dotenv()

database_url = os.getenv("DATABASE_URL", "sqlite:///scarz_pos.db")
normalized_url = database_url.replace("postgres://", "postgresql://", 1)
parsed_database_url = urlparse(normalized_url)

if parsed_database_url.scheme.startswith("postgresql"):
    database_host = (parsed_database_url.hostname or "").lower()
    local_hosts = {"localhost", "127.0.0.1", "::1"}
    if database_host not in local_hosts and os.getenv("ALLOW_REMOTE_DATABASE") != "1":
        print(
            "Refusing to start with a remote PostgreSQL database for local "
            "development. Point DATABASE_URL to a local/test database, or set "
            "ALLOW_REMOTE_DATABASE=1 only if you deliberately intend to use "
            "that remote database.",
            file=sys.stderr,
        )
        raise SystemExit(2)

from scarz_pos import create_app  # noqa: E402

app = create_app()


def initialize_local_database():
    """Run the project's additive bootstrap for a local development database."""
    with app.app_context():
        app.cli.commands["init-db"].callback()


if __name__ == "__main__":
    initialize_local_database()

    host = os.getenv("HOST", "127.0.0.1")
    production = os.getenv("APP_ENV", "development").strip().lower() in {
        "production",
        "prod",
    }
    port = int(os.getenv("PORT", "5000"))

    # Never expose Flask's interactive debugger on a non-loopback interface.
    debug = not production and host in {"127.0.0.1", "localhost", "::1"}
    print(f"Starting ScarZ POS at http://{host}:{port} (debug={debug})")
    app.run(host=host, port=port, debug=debug)

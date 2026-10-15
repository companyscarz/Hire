"""Development entry point for ScarZ POS.

Run with: python run.py

This uses DATABASE_URL from .env, including a remote PostgreSQL database if
configured. Be careful: sales, inventory changes, and database bootstrap actions
affect the database configured in .env. Production deployments should use
Gunicorn/Nixpacks instead of Flask's development server.
"""
import os

from dotenv import load_dotenv

# Load .env before importing the application factory.
load_dotenv()

from scarz_pos import create_app  # noqa: E402

app = create_app()


def initialize_database():
    """Run the registered init-db command with a proper Flask CLI context."""
    result = app.test_cli_runner().invoke(args=["init-db"])
    if result.exception is not None:
        raise result.exception
    if result.exit_code != 0:
        raise RuntimeError(
            "The init-db command failed: "
            + (result.output.strip() or f"exit code {result.exit_code}")
        )
    if result.output:
        print(result.output, end="" if result.output.endswith("\\n") else "\\n")


if __name__ == "__main__":
    initialize_database()

    host = os.getenv("HOST", "127.0.0.1")
    production = os.getenv("APP_ENV", "development").strip().lower() in {
        "production",
        "prod",
    }
    port = int(os.getenv("LOCAL_PORT", "5000"))

    # Keep the development server bound to loopback by default.
    debug = not production and host in {"127.0.0.1", "localhost", "::1"}
    print(f"Starting ScarZ POS at http://{host}:{port} (debug={debug})")
    print("Database target is the DATABASE_URL configured in your environment.")
    app.run(host=host, port=port, debug=debug)

"""Application factory for the new Hire Cloud PWA/API.

This package is intentionally separate from the legacy job-board modules while
we migrate. Run from the app directory with:
    gunicorn 'hire_cloud:create_app()'
"""
import os
import secrets

from dotenv import load_dotenv
from flask import Flask, jsonify, render_template, send_from_directory
from sqlalchemy import text

from .extensions import db, migrate

load_dotenv()


def create_app(test_config=None):
    app = Flask(__name__, instance_relative_config=True)

    app.config.from_mapping(
        APP_ENV=os.getenv("APP_ENV", "development").strip().lower(),
        SECRET_KEY=os.getenv("SECRET_KEY") or secrets.token_urlsafe(32),
        SQLALCHEMY_DATABASE_URI=os.getenv(
            "DATABASE_URL", "sqlite:///hire_cloud_dev.db"
        ),
        SQLALCHEMY_TRACK_MODIFICATIONS=False,
        SQLALCHEMY_ENGINE_OPTIONS={"pool_pre_ping": True},
        MAX_CONTENT_LENGTH=10 * 1024 * 1024,
        SESSION_COOKIE_HTTPONLY=True,
        SESSION_COOKIE_SAMESITE="Lax",
        SESSION_COOKIE_SECURE=os.getenv("APP_ENV", "development").lower() == "production",
    )
    if test_config:
        app.config.update(test_config)

    database_uri = app.config["SQLALCHEMY_DATABASE_URI"]
    # SQLAlchemy defaults postgresql:// to psycopg2; this service uses psycopg 3.
    if database_uri.startswith("postgresql://"):
        app.config["SQLALCHEMY_DATABASE_URI"] = "postgresql+psycopg://" + database_uri[len("postgresql://"):]

    if app.config["APP_ENV"] == "production":
        if not os.getenv("SECRET_KEY") and not (test_config and test_config.get("SECRET_KEY")):
            raise RuntimeError("SECRET_KEY must be configured in production")
        database_uri = app.config["SQLALCHEMY_DATABASE_URI"]
        if not database_uri.startswith(("postgresql://", "postgresql+psycopg://")):
            raise RuntimeError("Hire Cloud production requires PostgreSQL via DATABASE_URL")
        app.config["SESSION_COOKIE_SECURE"] = True
        app.config["DEBUG"] = False

    db.init_app(app)
    migrate.init_app(app, db)

    # Import model definitions so Flask-Migrate can discover the metadata.
    from . import models  # noqa: F401
    from .auth import auth, install_auth, register_workspace_routes

    install_auth(app)
    app.register_blueprint(auth)
    register_workspace_routes(app)

    @app.get("/")
    def index():
        return render_template("index.html")

    @app.get("/service-worker.js")
    def service_worker():
        response = send_from_directory(app.static_folder, "js/service-worker.js")
        response.headers["Service-Worker-Allowed"] = "/"
        response.headers["Cache-Control"] = "no-cache"
        return response

    @app.get("/health/live")
    def health_live():
        return jsonify({"status": "ok"}), 200

    @app.get("/health/ready")
    def health_ready():
        try:
            db.session.execute(text("SELECT 1"))
            return jsonify({"status": "ready", "database": "ok"}), 200
        except Exception:
            db.session.rollback()
            app.logger.exception("Readiness check failed")
            return jsonify({"status": "not_ready"}), 503

    @app.after_request
    def security_headers(response):
        response.headers.setdefault("X-Content-Type-Options", "nosniff")
        response.headers.setdefault("X-Frame-Options", "DENY")
        response.headers.setdefault("Referrer-Policy", "strict-origin-when-cross-origin")
        response.headers.setdefault("Permissions-Policy", "camera=(), microphone=(), geolocation=()")
        response.headers.setdefault(
            "Content-Security-Policy",
            "default-src 'self'; object-src 'none'; base-uri 'self'; form-action 'self'; frame-ancestors 'none'",
        )
        if app.config["APP_ENV"] == "production":
            response.headers.setdefault("Strict-Transport-Security", "max-age=31536000")
        return response

    return app

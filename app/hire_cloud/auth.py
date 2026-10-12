"""Authentication and tenant-scoped workspace routes for Hire Cloud."""
import hashlib
import hmac
import os
import re
import secrets
from datetime import datetime, timedelta, timezone
from functools import wraps
from urllib.parse import urlsplit

from flask import Blueprint, abort, current_app, flash, g, jsonify, redirect, render_template, request, session, url_for
from sqlalchemy import select, update
from werkzeug.security import check_password_hash, generate_password_hash

from .extensions import db, limiter
from .mailer import send_account_email
from .models import AccountToken, CloudProject, Membership, Tenant, User

auth = Blueprint("auth", __name__, url_prefix="/auth")
TOKEN_TTL = {"verify_email": timedelta(hours=24), "reset_password": timedelta(minutes=30)}


def csrf_token():
    token = session.get("_csrf_token")
    if not token:
        token = secrets.token_urlsafe(32)
        session["_csrf_token"] = token
    return token


def install_auth(app):
    """Install session validation, CSRF protection, and shared request limits."""
    app.jinja_env.globals["csrf_token"] = csrf_token
    app.config.setdefault("RATELIMIT_STORAGE_URI", os.getenv("REDIS_URL", "memory://"))
    app.config.setdefault("RATELIMIT_HEADERS_ENABLED", True)
    app.config.setdefault("PUBLIC_BASE_URL", os.getenv("PUBLIC_BASE_URL", "").rstrip("/"))
    app.config.setdefault("MAIL_SERVER", os.getenv("MAIL_SERVER", ""))
    app.config.setdefault("MAIL_PORT", int(os.getenv("MAIL_PORT", "587")))
    app.config.setdefault("MAIL_USE_TLS", os.getenv("MAIL_USE_TLS", "true").lower() in {"1", "true", "yes"})
    app.config.setdefault("MAIL_USERNAME", os.getenv("MAIL_USERNAME", ""))
    app.config.setdefault("MAIL_PASSWORD", os.getenv("MAIL_PASSWORD", ""))
    app.config.setdefault("MAIL_DEFAULT_SENDER", os.getenv("MAIL_DEFAULT_SENDER", ""))

    if app.config.get("APP_ENV") == "production":
        if not app.config["RATELIMIT_STORAGE_URI"].startswith(("redis://", "rediss://")):
            raise RuntimeError("Production requires shared Redis storage via REDIS_URL")
        if not app.config["PUBLIC_BASE_URL"].startswith("https://"):
            raise RuntimeError("Production requires PUBLIC_BASE_URL with HTTPS")
        if not app.config["MAIL_SERVER"] or not app.config["MAIL_DEFAULT_SENDER"]:
            raise RuntimeError("Production requires MAIL_SERVER and MAIL_DEFAULT_SENDER")
    limiter.init_app(app)

    @app.before_request
    def load_authenticated_user_and_check_csrf():
        g.user = None
        user_id = session.get("user_id")
        if user_id:
            g.user = db.session.get(User, user_id)
            session_version = session.get("session_version")
            if (
                g.user is None
                or not g.user.is_active
                or session_version != g.user.session_version
            ):
                session.clear()
                g.user = None

        if request.method in {"POST", "PUT", "PATCH", "DELETE"}:
            submitted = request.form.get("csrf_token") or request.headers.get("X-CSRF-Token", "")
            expected = session.get("_csrf_token", "")
            if not expected or not submitted or not hmac.compare_digest(expected, submitted):
                abort(400, description="Invalid or missing CSRF token.")

    @app.context_processor
    def inject_auth_context():
        return {"current_user": getattr(g, "user", None)}


def login_required(view):
    @wraps(view)
    def wrapped(*args, **kwargs):
        if not getattr(g, "user", None):
            return redirect(url_for("auth.login", next=request.path))
        return view(*args, **kwargs)
    return wrapped


def _slugify(value):
    slug = re.sub(r"[^a-z0-9]+", "-", value.lower()).strip("-")
    return (slug or "workspace")[:65]


def _utcnow():
    return datetime.now(timezone.utc)


def _expiry_is_future(value):
    if value.tzinfo is None:
        value = value.replace(tzinfo=timezone.utc)
    return value > _utcnow()


def _create_token(user, purpose):
    # Invalidate older unused links of the same purpose before issuing another.
    db.session.execute(
        update(AccountToken)
        .where(
            AccountToken.user_id == user.id,
            AccountToken.purpose == purpose,
            AccountToken.used_at.is_(None),
        )
        .values(used_at=_utcnow())
    )
    raw = secrets.token_urlsafe(32)
    token = AccountToken(
        user_id=user.id,
        purpose=purpose,
        token_hash=hashlib.sha256(raw.encode("utf-8")).hexdigest(),
        expires_at=_utcnow() + TOKEN_TTL[purpose],
    )
    db.session.add(token)
    db.session.flush()
    return raw


def _public_link(endpoint, raw_token):
    path = url_for(endpoint, token=raw_token)
    base = current_app.config.get("PUBLIC_BASE_URL", "").rstrip("/")
    if base:
        return base + path
    # Development/testing only; production startup requires PUBLIC_BASE_URL.
    return request.url_root.rstrip("/") + path


def _send_token(user, purpose, raw_token):
    if purpose == "verify_email":
        link = _public_link("auth.verify_email", raw_token)
        subject = "Verify your Hire email"
        body = (
            f"Hello {user.display_name},\n\n"
            "Confirm your email address by opening this link and submitting the confirmation form:\n"
            f"{link}\n\nThis link expires in 24 hours and can only be used once. "
            "If you did not create a Hire account, you can ignore this message."
        )
    else:
        link = _public_link("auth.reset_password", raw_token)
        subject = "Reset your Hire password"
        body = (
            "A password reset was requested for your Hire account. Open this link to choose a new password:\n"
            f"{link}\n\nThis link expires in 30 minutes and can only be used once. "
            "If you did not request this, you can ignore this message."
        )
    return send_account_email(user.email, subject, body)


def _find_valid_token(raw, purpose):
    if not raw or len(raw) > 200:
        return None
    digest = hashlib.sha256(raw.encode("utf-8")).hexdigest()
    token = db.session.scalar(
        select(AccountToken).where(
            AccountToken.token_hash == digest,
            AccountToken.purpose == purpose,
            AccountToken.used_at.is_(None),
        )
    )
    if not token or not _expiry_is_future(token.expires_at):
        return None
    if not token.user or not token.user.is_active:
        return None
    return token


@auth.route("/register", methods=["GET", "POST"])
@limiter.limit("5 per hour", methods=["POST"])
def register():
    if getattr(g, "user", None):
        return redirect(url_for("workspace"))
    if request.method == "POST":
        email = request.form.get("email", "").strip().lower()
        display_name = request.form.get("display_name", "").strip()
        workspace_name = request.form.get("workspace_name", "").strip()
        password = request.form.get("password", "")

        if not email or len(email) > 320 or not re.fullmatch(r"[^\s@]+@[^\s@]+\.[^\s@]+", email):
            flash("Enter a valid email address.", "error")
        elif not display_name or len(display_name) > 120:
            flash("Enter your name (up to 120 characters).", "error")
        elif not workspace_name or len(workspace_name) > 160:
            flash("Enter a workspace name (up to 160 characters).", "error")
        elif len(password) < 12:
            flash("Use a password with at least 12 characters.", "error")
        elif db.session.scalar(select(User.id).where(User.email == email)):
            flash("An account with that email already exists. Sign in instead.", "error")
        else:
            base_slug = _slugify(workspace_name)
            slug = base_slug
            suffix = 2
            while db.session.scalar(select(Tenant.id).where(Tenant.slug == slug)):
                slug = f"{base_slug[:72]}-{suffix}"
                suffix += 1
            user = User(email=email, display_name=display_name, password_hash=generate_password_hash(password))
            tenant = Tenant(name=workspace_name, slug=slug)
            try:
                db.session.add_all([user, tenant])
                db.session.flush()
                db.session.add(Membership(user_id=user.id, tenant_id=tenant.id, role="owner"))
                raw_token = _create_token(user, "verify_email")
                db.session.commit()
            except Exception:
                db.session.rollback()
                current_app.logger.exception("Account registration failed")
                flash("We could not create the account. Please try again.", "error")
            else:
                try:
                    _send_token(user, "verify_email", raw_token)
                except Exception:
                    current_app.logger.exception("Verification email delivery failed")
                    flash("Your account was created, but the email could not be sent. Try resending verification.", "error")
                else:
                    flash("Account created. Check your email for a verification link before signing in.", "success")
                return redirect(url_for("auth.login"))
    return render_template("auth.html", mode="register")


@auth.route("/login", methods=["GET", "POST"])
@limiter.limit("5 per minute", methods=["POST"])
def login():
    if getattr(g, "user", None):
        return redirect(url_for("workspace"))
    if request.method == "POST":
        email = request.form.get("email", "").strip().lower()
        password = request.form.get("password", "")
        user = db.session.scalar(select(User).where(User.email == email))
        if not user or not user.is_active or not check_password_hash(user.password_hash, password):
            flash("Email or password is incorrect.", "error")
        elif user.email_verified_at is None:
            flash("Please verify your email before signing in. You can request another verification link below.", "error")
        else:
            session.clear()
            session["user_id"] = user.id
            session["session_version"] = user.session_version
            csrf_token()
            next_url = request.args.get("next", "")
            parsed_next = urlsplit(next_url)
            if (
                next_url and "\\" not in next_url and not parsed_next.scheme
                and not parsed_next.netloc and parsed_next.path.startswith("/")
                and not parsed_next.path.startswith("//")
            ):
                return redirect(next_url)
            return redirect(url_for("workspace"))
    return render_template("auth.html", mode="login")


@auth.route("/verify-email", methods=["GET", "POST"])
def verify_email():
    raw = request.args.get("token", "") if request.method == "GET" else request.form.get("token", "")
    token = _find_valid_token(raw, "verify_email")
    if not token:
        return render_template("token_action.html", mode="verify", token="", invalid=True), 400
    if request.method == "POST":
        token.used_at = _utcnow()
        token.user.email_verified_at = _utcnow()
        db.session.commit()
        flash("Email verified. You can now sign in.", "success")
        return redirect(url_for("auth.login"))
    return render_template("token_action.html", mode="verify", token=raw, invalid=False)


@auth.route("/resend-verification", methods=["GET", "POST"])
@limiter.limit("3 per hour", methods=["POST"])
def resend_verification():
    if request.method == "POST":
        email = request.form.get("email", "").strip().lower()
        user = db.session.scalar(select(User).where(User.email == email))
        if user and user.is_active and user.email_verified_at is None:
            try:
                raw = _create_token(user, "verify_email")
                db.session.commit()
                _send_token(user, "verify_email", raw)
            except Exception:
                db.session.rollback()
                current_app.logger.exception("Verification resend failed")
        flash("If that account needs verification, a new link will be sent.", "success")
        return redirect(url_for("auth.login"))
    return render_template("auth.html", mode="resend")


@auth.route("/forgot-password", methods=["GET", "POST"])
@limiter.limit("3 per hour", methods=["POST"])
def forgot_password():
    if request.method == "POST":
        email = request.form.get("email", "").strip().lower()
        user = db.session.scalar(select(User).where(User.email == email))
        if user and user.is_active:
            try:
                raw = _create_token(user, "reset_password")
                db.session.commit()
                _send_token(user, "reset_password", raw)
            except Exception:
                db.session.rollback()
                current_app.logger.exception("Password reset email delivery failed")
        flash("If an active account matches that address, password reset instructions will be sent.", "success")
        return redirect(url_for("auth.login"))
    return render_template("auth.html", mode="forgot")


@auth.route("/reset-password", methods=["GET", "POST"])
@limiter.limit("5 per hour", methods=["POST"])
def reset_password():
    raw = request.args.get("token", "") if request.method == "GET" else request.form.get("token", "")
    token = _find_valid_token(raw, "reset_password")
    if not token:
        return render_template("token_action.html", mode="reset", token="", invalid=True), 400
    if request.method == "POST":
        password = request.form.get("password", "")
        confirmation = request.form.get("confirm_password", "")
        if len(password) < 12:
            flash("Use a password with at least 12 characters.", "error")
        elif password != confirmation:
            flash("The passwords do not match.", "error")
        else:
            token.used_at = _utcnow()
            token.user.password_hash = generate_password_hash(password)
            token.user.session_version += 1
            db.session.execute(
                update(AccountToken)
                .where(AccountToken.user_id == token.user_id, AccountToken.purpose == "reset_password", AccountToken.used_at.is_(None))
                .values(used_at=_utcnow())
            )
            db.session.commit()
            session.clear()
            flash("Password updated. Sign in with your new password.", "success")
            return redirect(url_for("auth.login"))
    return render_template("token_action.html", mode="reset", token=raw, invalid=False)


@auth.post("/logout")
@login_required
def logout():
    session.clear()
    return redirect(url_for("auth.login"))


def register_workspace_routes(app):
    @app.get("/dashboard")
    @login_required
    def workspace():
        membership = db.session.scalar(
            select(Membership).where(Membership.user_id == g.user.id).order_by(Membership.created_at.asc())
        )
        tenant = membership.tenant if membership else None
        return render_template("workspace.html", tenant=tenant, membership=membership)

    @app.get("/api/workspace/projects")
    @login_required
    def workspace_projects():
        membership = db.session.scalar(
            select(Membership).where(Membership.user_id == g.user.id).order_by(Membership.created_at.asc())
        )
        if not membership:
            return jsonify({"projects": []})
        projects = db.session.scalars(
            select(CloudProject).where(CloudProject.tenant_id == membership.tenant_id).order_by(CloudProject.created_at.desc())
        ).all()
        return jsonify({"projects": [{"id": p.id, "name": p.name, "status": p.status} for p in projects]})

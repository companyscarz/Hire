"""Authentication and tenant-scoped workspace routes for Hire Cloud."""
import hmac
import re
import secrets
from functools import wraps

from flask import Blueprint, abort, current_app, flash, g, jsonify, redirect, render_template, request, session, url_for
from sqlalchemy import select
from werkzeug.security import check_password_hash, generate_password_hash

from .extensions import db
from .models import CloudProject, Membership, Tenant, User

auth = Blueprint("auth", __name__, url_prefix="/auth")


def csrf_token():
    token = session.get("_csrf_token")
    if not token:
        token = secrets.token_urlsafe(32)
        session["_csrf_token"] = token
    return token


def install_auth(app):
    """Install CSRF checks and expose the current authenticated user."""
    app.jinja_env.globals["csrf_token"] = csrf_token

    @app.before_request
    def load_authenticated_user_and_check_csrf():
        g.user = None
        user_id = session.get("user_id")
        if user_id:
            g.user = db.session.get(User, user_id)
            if g.user is None or not g.user.is_active:
                session.pop("user_id", None)
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


@auth.route("/register", methods=["GET", "POST"])
def register():
    if getattr(g, "user", None):
        return redirect(url_for("workspace"))
    if request.method == "POST":
        email = request.form.get("email", "").strip().lower()
        display_name = request.form.get("display_name", "").strip()
        workspace_name = request.form.get("workspace_name", "").strip()
        password = request.form.get("password", "")

        if not email or len(email) > 320 or "@" not in email:
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
            user = User(
                email=email,
                display_name=display_name,
                password_hash=generate_password_hash(password),
            )
            tenant = Tenant(name=workspace_name, slug=slug)
            try:
                db.session.add_all([user, tenant])
                db.session.flush()
                db.session.add(Membership(user_id=user.id, tenant_id=tenant.id, role="owner"))
                db.session.commit()
            except Exception:
                db.session.rollback()
                current_app.logger.exception("Account registration failed")
                flash("We could not create the account. Please try again.", "error")
            else:
                session.clear()
                session["user_id"] = user.id
                csrf_token()
                return redirect(url_for("workspace"))
    return render_template("auth.html", mode="register")


@auth.route("/login", methods=["GET", "POST"])
def login():
    if getattr(g, "user", None):
        return redirect(url_for("workspace"))
    if request.method == "POST":
        email = request.form.get("email", "").strip().lower()
        password = request.form.get("password", "")
        user = db.session.scalar(select(User).where(User.email == email))
        if not user or not user.is_active or not check_password_hash(user.password_hash, password):
            # Keep the response generic to avoid confirming registered email addresses.
            flash("Email or password is incorrect.", "error")
        else:
            session.clear()
            session["user_id"] = user.id
            csrf_token()
            next_url = request.args.get("next", "")
            if next_url.startswith("/") and not next_url.startswith("//"):
                return redirect(next_url)
            return redirect(url_for("workspace"))
    return render_template("auth.html", mode="login")


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
            select(Membership)
            .where(Membership.user_id == g.user.id)
            .order_by(Membership.created_at.asc())
        )
        tenant = membership.tenant if membership else None
        return render_template("workspace.html", tenant=tenant, membership=membership)

    @app.get("/api/workspace/projects")
    @login_required
    def workspace_projects():
        membership = db.session.scalar(
            select(Membership)
            .where(Membership.user_id == g.user.id)
            .order_by(Membership.created_at.asc())
        )
        if not membership:
            return jsonify({"projects": []})
        projects = db.session.scalars(
            select(CloudProject)
            .where(CloudProject.tenant_id == membership.tenant_id)
            .order_by(CloudProject.created_at.desc())
        ).all()
        return jsonify({
            "projects": [
                {"id": project.id, "name": project.name, "status": project.status}
                for project in projects
            ]
        })

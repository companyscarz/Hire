import re
from datetime import datetime, timezone

import pytest
from werkzeug.security import check_password_hash, generate_password_hash

from hire_cloud import create_app
from hire_cloud.extensions import db
from hire_cloud.models import CloudProject, Membership, Tenant, User


@pytest.fixture()
def app():
    app = create_app({
        "TESTING": True,
        "APP_ENV": "testing",
        "SECRET_KEY": "test-only-secret-key",
        "SQLALCHEMY_DATABASE_URI": "sqlite://",
        "SQLALCHEMY_ENGINE_OPTIONS": {},
    })
    with app.app_context():
        db.create_all()
        yield app
        db.session.remove()
        db.drop_all()


@pytest.fixture()
def client(app):
    return app.test_client()


@pytest.fixture()
def outbox(monkeypatch):
    messages = []
    monkeypatch.setattr("hire_cloud.auth.send_account_email", lambda recipient, subject, body: messages.append((recipient, subject, body)) or True)
    return messages


def _csrf(client, path):
    response = client.get(path)
    assert response.status_code == 200
    match = re.search(rb'name="csrf_token" value="([^"]+)"', response.data)
    assert match, "form should contain a CSRF token"
    return match.group(1).decode()


def test_registration_creates_hashed_user_and_owner_workspace(client, app, outbox):
    token = _csrf(client, "/auth/register")
    response = client.post("/auth/register", data={
        "csrf_token": token,
        "display_name": "Developer",
        "workspace_name": "My Workspace",
        "email": "DEV@example.test",
        "password": "a-long-test-password",
    })
    assert response.status_code == 302
    assert response.headers["Location"].endswith("/auth/login")
    assert len(outbox) == 1
    assert outbox[0][0] == "dev@example.test"
    assert "verify-email?token=" in outbox[0][2]

    with app.app_context():
        user = db.session.query(User).filter_by(email="dev@example.test").one()
        assert user.password_hash != "a-long-test-password"
        assert check_password_hash(user.password_hash, "a-long-test-password")
        membership = db.session.query(Membership).filter_by(user_id=user.id).one()
        assert membership.role == "owner"
        assert membership.tenant.name == "My Workspace"


def test_registration_rejects_missing_csrf_token(client):
    response = client.post("/auth/register", data={
        "display_name": "Developer",
        "workspace_name": "Workspace",
        "email": "dev@example.test",
        "password": "a-long-test-password",
    })
    assert response.status_code == 400


def test_login_and_logout_require_valid_csrf(client, app):
    with app.app_context():
        user = User(
            email="login@example.test",
            display_name="Login User",
            password_hash=generate_password_hash("a-long-test-password"),
            email_verified_at=datetime.now(timezone.utc),
        )
        tenant = Tenant(name="Login Workspace", slug="login-workspace")
        db.session.add_all([user, tenant])
        db.session.flush()
        db.session.add(Membership(user_id=user.id, tenant_id=tenant.id, role="owner"))
        db.session.commit()

    token = _csrf(client, "/auth/login")
    response = client.post("/auth/login", data={
        "csrf_token": token,
        "email": "LOGIN@example.test",
        "password": "a-long-test-password",
    })
    assert response.status_code == 302
    assert response.headers["Location"].endswith("/dashboard")
    dashboard = client.get("/dashboard")
    assert dashboard.status_code == 200
    assert b"Login Workspace" in dashboard.data

    logout_token = re.search(rb'name="csrf_token" value="([^"]+)"', dashboard.data)
    # Dashboard's form token is generated from the authenticated session.
    assert logout_token
    response = client.post("/auth/logout", data={"csrf_token": logout_token.group(1).decode()})
    assert response.status_code == 302
    assert response.headers["Location"].endswith("/auth/login")
    assert client.get("/dashboard").status_code == 302


def test_workspace_projects_are_scoped_to_signed_in_tenant(client, app):
    with app.app_context():
        user_a = User(email="a@example.test", display_name="A", password_hash="x")
        user_b = User(email="b@example.test", display_name="B", password_hash="x")
        tenant_a = Tenant(name="A workspace", slug="a-workspace")
        tenant_b = Tenant(name="B workspace", slug="b-workspace")
        db.session.add_all([user_a, user_b, tenant_a, tenant_b])
        db.session.flush()
        db.session.add_all([
            Membership(user_id=user_a.id, tenant_id=tenant_a.id, role="owner"),
            Membership(user_id=user_b.id, tenant_id=tenant_b.id, role="owner"),
            CloudProject(tenant_id=tenant_a.id, name="A app", slug="a-app"),
            CloudProject(tenant_id=tenant_b.id, name="B secret app", slug="b-secret-app"),
        ])
        db.session.commit()
        user_a_id = user_a.id

    with client.session_transaction() as session:
        session["user_id"] = user_a_id
        session["session_version"] = 0
        session["_csrf_token"] = "test-csrf"

    response = client.get("/api/workspace/projects")
    assert response.status_code == 200
    payload = response.get_json()
    assert [project["name"] for project in payload["projects"]] == ["A app"]
    assert "B secret app" not in response.get_data(as_text=True)


def test_dashboard_requires_authentication(client):
    response = client.get("/dashboard")
    assert response.status_code == 302
    assert "/auth/login" in response.headers["Location"]


def test_login_rejects_backslash_based_external_redirect(client, app):
    with app.app_context():
        user = User(
            email="redirect@example.test",
            display_name="Redirect User",
            password_hash=generate_password_hash("a-long-test-password"),
            email_verified_at=datetime.now(timezone.utc),
        )
        tenant = Tenant(name="Redirect Workspace", slug="redirect-workspace")
        db.session.add_all([user, tenant])
        db.session.flush()
        db.session.add(Membership(user_id=user.id, tenant_id=tenant.id, role="owner"))
        db.session.commit()

    path = "/auth/login?next=%2F%5Cevil.example"
    token = _csrf(client, path)
    response = client.post(path, data={
        "csrf_token": token,
        "email": "redirect@example.test",
        "password": "a-long-test-password",
    })
    assert response.status_code == 302
    assert response.headers["Location"].endswith("/dashboard")
    assert "evil.example" not in response.headers["Location"]

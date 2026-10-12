import pytest

from hire_cloud import create_app
from hire_cloud.extensions import db
from hire_cloud.models import Membership, Tenant, User


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


def test_live_health_does_not_require_database(client):
    response = client.get("/health/live")
    assert response.status_code == 200
    assert response.get_json()["status"] == "ok"


def test_ready_health_checks_database(client):
    response = client.get("/health/ready")
    assert response.status_code == 200
    assert response.get_json()["database"] == "ok"


def test_tenant_membership_is_unique(app):
    with app.app_context():
        user = User(email="developer@example.test", password_hash="not-a-real-hash")
        tenant = Tenant(name="Example", slug="example")
        db.session.add_all([user, tenant])
        db.session.flush()
        db.session.add(Membership(user_id=user.id, tenant_id=tenant.id, role="owner"))
        db.session.commit()

        db.session.add(Membership(user_id=user.id, tenant_id=tenant.id, role="member"))
        with pytest.raises(Exception):
            db.session.commit()
        db.session.rollback()



def test_dashboard_shell_and_manifest_are_served(client):
    response = client.get("/")
    assert response.status_code == 200
    assert b"Welcome to Hire Cloud" in response.data
    assert b"manifest.webmanifest" in response.data


def test_root_scoped_service_worker_is_served(client):
    response = client.get("/service-worker.js")
    assert response.status_code == 200
    assert b"addEventListener" in response.data
    assert response.headers["Service-Worker-Allowed"] == "/"
    assert b'url.pathname.startsWith("/auth/")' in response.data
    assert b'url.pathname === "/dashboard"' in response.data


def test_manifest_is_standalone_and_has_large_icons(client):
    response = client.get("/static/manifest.webmanifest")
    assert response.status_code == 200
    manifest = response.get_json()
    assert manifest["display"] == "standalone"
    assert manifest["start_url"] == "/"
    assert {icon["sizes"] for icon in manifest["icons"]} >= {"192x192", "512x512"}


def test_production_rejects_sqlite_database():
    with pytest.raises(RuntimeError, match="requires PostgreSQL"):
        create_app({
            "APP_ENV": "production",
            "SECRET_KEY": "test-only-secret-key",
            "SQLALCHEMY_DATABASE_URI": "sqlite://",
        })

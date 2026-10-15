from datetime import timedelta

import pytest
from scarz_pos import create_app
from scarz_pos.extensions import db
from scarz_pos.models import utcnow


@pytest.fixture()
def app():
    app = create_app({
        "TESTING": True,
        "SECRET_KEY": "test-secret-long-enough",
        "SQLALCHEMY_DATABASE_URI": "sqlite:///:memory:",
        "WTF_CSRF_ENABLED": False,
    })
    with app.app_context():
        db.create_all()
        yield app
        db.session.remove()
        db.drop_all()


@pytest.fixture()
def client(app):
    return app.test_client()


def _register(client, email="scanner@example.com"):
    return client.post("/register", data={
        "business_name": "Scanner Shop",
        "full_name": "Scanner Owner",
        "email": email,
        "password": "very-long-password",
        "confirm_password": "very-long-password",
    }, follow_redirects=True)


def test_phone_scanner_pairing_delivers_a_barcode_once(client):
    _register(client)
    paired = client.post("/scanner/pair")
    assert paired.status_code == 200
    token = paired.get_json()["token"]

    assert client.get(f"/scanner/phone/{token}").status_code == 200
    posted = client.post(f"/scanner/phone/{token}/code", json={"code": "0123456789012"})
    assert posted.status_code == 200

    received = client.get(f"/scanner/pair/{token}/next")
    assert received.status_code == 200
    assert received.get_json()["code"] == "0123456789012"
    assert client.get(f"/scanner/pair/{token}/next").get_json()["code"] is None


def test_phone_scanner_rejects_empty_barcode(client):
    _register(client)
    token = client.post("/scanner/pair").get_json()["token"]
    response = client.post(f"/scanner/phone/{token}/code", json={"code": "  "})
    assert response.status_code == 400


def test_phone_scanner_pairing_expires(client, app):
    _register(client)
    token = client.post("/scanner/pair").get_json()["token"]
    from scarz_pos.scanner import PhoneScannerSession
    with app.app_context():
        pairing = PhoneScannerSession.query.filter_by(token=token).one()
        pairing.expires_at = utcnow() - timedelta(seconds=1)
        db.session.commit()
    assert client.get(f"/scanner/phone/{token}").status_code == 404

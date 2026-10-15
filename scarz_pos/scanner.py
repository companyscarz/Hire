import secrets
from datetime import timedelta

from flask import Blueprint, abort, jsonify, render_template, request
from flask_login import current_user, login_required
from .extensions import db
from .models import ensure_utc, utcnow

bp = Blueprint("scanner", __name__, url_prefix="/scanner")


class PhoneScannerSession(db.Model):
    """Short-lived, business-scoped pairing for a phone barcode scanner."""
    id = db.Column(db.Integer, primary_key=True)
    business_id = db.Column(db.Integer, db.ForeignKey("business.id", ondelete="CASCADE"), nullable=False, index=True)
    token = db.Column(db.String(96), nullable=False, unique=True, index=True)
    expires_at = db.Column(db.DateTime(timezone=True), nullable=False, index=True)
    last_code = db.Column(db.String(80))
    code_sequence = db.Column(db.Integer, nullable=False, default=0)
    created_at = db.Column(db.DateTime(timezone=True), nullable=False, default=utcnow)
    updated_at = db.Column(db.DateTime(timezone=True), nullable=False, default=utcnow)


@bp.post("/pair")
@login_required
def create_pairing():
    token = secrets.token_urlsafe(32)
    pairing = PhoneScannerSession(
        business_id=current_user.business_id,
        token=token,
        expires_at=utcnow() + timedelta(minutes=20),
    )
    db.session.add(pairing)
    db.session.commit()
    return jsonify({
        "token": token,
        "url": request.url_root.rstrip("/") + "/scanner/phone/" + token,
        "expires_in": 1200,
    })


def get_active_pairing(token):
    pairing = PhoneScannerSession.query.filter_by(token=token).first()
    if pairing is None or ensure_utc(pairing.expires_at) <= utcnow():
        abort(404)
    return pairing


@bp.get("/phone/<token>")
def phone_scanner(token):
    pairing = get_active_pairing(token)
    return render_template("phone_scanner.html", pairing=pairing)


@bp.post("/phone/<token>/code")
def receive_phone_code(token):
    pairing = get_active_pairing(token)
    payload = request.get_json(silent=True) or {}
    code = str(payload.get("code", "")).strip()
    if not code or len(code) > 80 or not code.isprintable():
        return jsonify({"error": "Invalid barcode."}), 400
    pairing.last_code = code
    pairing.code_sequence += 1
    pairing.updated_at = utcnow()
    db.session.commit()
    return jsonify({"ok": True, "sequence": pairing.code_sequence})


@bp.get("/pair/<token>/next")
@login_required
def next_phone_code(token):
    pairing = get_active_pairing(token)
    if pairing.business_id != current_user.business_id:
        abort(404)
    code = pairing.last_code
    sequence = pairing.code_sequence
    if code:
        pairing.last_code = None
        db.session.commit()
    return jsonify({"code": code, "sequence": sequence})

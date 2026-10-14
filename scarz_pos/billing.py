from __future__ import annotations

import os
import re
import secrets
from datetime import timedelta
from decimal import Decimal, InvalidOperation
from datetime import datetime, timezone

from flask import Blueprint, current_app, flash, redirect, render_template, request, url_for
from flask_login import current_user, login_required
from sqlalchemy import select
from sqlalchemy.orm import Session

from . import csrf
from .extensions import db
from .models import Business, SubscriptionPayment, ensure_utc, utcnow

bp = Blueprint("billing", __name__)


def plan_catalog():
    """Prices are configured server-side; browser form values never set a charge amount."""
    specs = (
        ("monthly", "Monthly", 30, "SCARZ_POS_PLAN_MONTHLY_UGX"),
        ("quarterly", "Quarterly", 90, "SCARZ_POS_PLAN_QUARTERLY_UGX"),
        ("annual", "Annual", 365, "SCARZ_POS_PLAN_ANNUAL_UGX"),
    )
    plans = []
    for key, label, days, env_name in specs:
        raw = current_app.config.get(env_name) or os.getenv(env_name, "")
        try:
            amount = Decimal(str(raw).strip())
            configured = amount.is_finite() and amount > 0 and amount == amount.to_integral_value()
        except (InvalidOperation, ValueError, TypeError):
            amount, configured = Decimal("0"), False
        plans.append({
            "key": key, "label": label, "days": days, "env_name": env_name,
            "amount": int(amount) if configured else None, "configured": configured,
        })
    return plans


def normalize_ug_phone(value: str) -> str | None:
    phone = re.sub(r"[\s\-()]", "", str(value or ""))
    if phone.startswith("+256"):
        phone = phone[1:]
    elif phone.startswith("0"):
        phone = "256" + phone[1:]
    if re.fullmatch(r"2567\d{8}", phone):
        return phone
    return None


def _nylon_client():
    from nylonpay import create_nylon_pay
    api_key = current_app.config.get("NYLONPAY_API_KEY") or os.getenv("NYLONPAY_API_KEY")
    api_secret = current_app.config.get("NYLONPAY_API_SECRET") or os.getenv("NYLONPAY_API_SECRET")
    if not api_key or not api_secret:
        raise RuntimeError("Nylon Pay credentials are not configured.")
    return create_nylon_pay(api_key=api_key, api_secret=api_secret)


def _verify_signature(raw_body: bytes, signature: str) -> bool:
    secret = current_app.config.get("NYLONPAY_WEBHOOK_SECRET") or os.getenv("NYLONPAY_WEBHOOK_SECRET")
    if not secret or not signature:
        return False
    from nylonpay import VerifyWebhookInput, verify_webhook_signature
    return bool(verify_webhook_signature(VerifyWebhookInput(
        payload=raw_body, signature=signature, secret=secret
    )))


def _as_decimal(value):
    try:
        result = Decimal(str(value))
        return result if result.is_finite() else None
    except (InvalidOperation, ValueError, TypeError):
        return None


@bp.route("/subscription", methods=["GET", "POST"])
@login_required
def subscription():
    plans = plan_catalog()
    if request.method == "POST":
        selected_key = (request.form.get("plan") or "").strip()
        selected = next((plan for plan in plans if plan["key"] == selected_key), None)
        if not selected:
            flash("Choose a valid subscription plan.", "error")
            return redirect(url_for("billing.subscription"))
        if not selected["configured"]:
            flash(f"The {selected['label'].lower()} plan price is not configured yet. Please contact support.", "error")
            return redirect(url_for("billing.subscription"))

        phone = normalize_ug_phone(request.form.get("phone_number", ""))
        if not phone:
            flash("Enter a valid Ugandan Mobile Money number, e.g. 0771 234 567.", "error")
            return redirect(url_for("billing.subscription"))

        api_key = current_app.config.get("NYLONPAY_API_KEY") or os.getenv("NYLONPAY_API_KEY")
        api_secret = current_app.config.get("NYLONPAY_API_SECRET") or os.getenv("NYLONPAY_API_SECRET")
        if not api_key or not api_secret:
            flash("Nylon Pay is not configured yet. Please try again later.", "error")
            return redirect(url_for("billing.subscription"))

        reference = secrets.token_hex(7)  # 14 characters, unique per attempt
        payment = SubscriptionPayment(
            business_id=current_user.business_id,
            merchant_reference=reference,
            plan_key=selected["key"],
            duration_days=selected["days"],
            amount=Decimal(selected["amount"]),
            currency="UGX",
            phone_number=phone,
            status="pending",
        )
        db.session.add(payment)
        db.session.commit()  # Persist pending reference before calling the gateway.

        try:
            client = _nylon_client()
            result = client.collect_payment(
                amount=selected["amount"],
                currency="UGX",
                method="mobileMoney",
                customer={
                    "name": current_user.full_name,
                    "phone_number": phone,
                    "email": current_user.email,
                },
                description=f"ScarZ POS {selected['label']} subscription for {current_user.business.name}",
                reference=reference,
            )
            # Initiation is not proof of payment. Only the signed webhook activates the plan.
            payment.status = "processing"
            payment.raw_payload = {
                "initiation_reference": str(getattr(result, "reference", reference)),
                "initiation_status": str(getattr(result, "status", "processing")),
            }
            db.session.commit()
            flash("Payment request sent to your phone. Enter your Mobile Money PIN, then wait for confirmation.", "info")
        except Exception:
            db.session.rollback()
            current_app.logger.exception("Nylon Pay initiation failed for reference %s", reference)
            # Keep the attempt record for reconciliation; do not grant subscription access.
            current_payment = db.session.get(SubscriptionPayment, payment.id)
            if current_payment and current_payment.status != "successful":
                current_payment.status = "initiation_error"
                db.session.commit()
            flash("We could not confirm that the payment request started. Check your phone before retrying.", "error")
        return redirect(url_for("billing.subscription"))

    return render_template(
        "subscription.html",
        plans=plans,
        business=current_user.business,
        recent_payments=SubscriptionPayment.query.filter_by(
            business_id=current_user.business_id
        ).order_by(SubscriptionPayment.created_at.desc()).limit(10).all(),
    )


@bp.post("/webhooks/nylonpay/subscriptions")
@csrf.exempt
def nylonpay_subscription_webhook():
    # cache=True allows Flask to parse the same raw bytes as JSON after signature verification.
    raw_body = request.get_data(cache=True, as_text=False)
    signature = request.headers.get("x-nylon-signature", "")
    try:
        if not _verify_signature(raw_body, signature):
            return {"error": "invalid signature"}, 401
    except Exception:
        current_app.logger.exception("Could not verify Nylon Pay subscription webhook")
        return {"error": "webhook verification unavailable"}, 503

    body = request.get_json(silent=True)
    if not isinstance(body, dict):
        return {"error": "invalid JSON"}, 400
    payload = body.get("payload") or {}
    if not isinstance(payload, dict):
        return {"error": "invalid payload"}, 400
    transaction = payload.get("transaction") or {}
    if not isinstance(transaction, dict):
        transaction = {}

    reference = payload.get("reference") or transaction.get("reference")
    if not reference:
        return {"error": "missing reference"}, 400

    payment = db.session.execute(
        select(SubscriptionPayment)
        .where(SubscriptionPayment.merchant_reference == str(reference))
        .with_for_update()
    ).scalar_one_or_none()
    if payment is None:
        # Acknowledge unknown references to avoid endless retries; never grant access.
        return {"status": "ok", "message": "transaction not found"}, 200

    event = str(body.get("event") or "").strip().lower()
    status = str(payload.get("status") or transaction.get("status") or "").strip().lower()
    provider_id = payload.get("transactionId") or transaction.get("id")
    successful = event in {"transaction.successful", "payment.success", "success"} or status in {"successful", "success", "completed"}
    failed = event in {"transaction.failed", "payment.failed", "failed", "transaction.cancelled", "payment.cancelled", "cancelled"} or status in {"failed", "cancelled"}
    processing = event in {"transaction.processing", "payment.processing", "processing"} or status in {"pending", "processing"}

    if successful and payment.status != "successful":
        # Require provider-supplied amount and currency; don't silently trust stored values.
        amount = _as_decimal(payload.get("amount", transaction.get("amount")))
        currency = str(payload.get("currency") or transaction.get("currency") or "").upper()
        if amount is None or not currency:
            return {"error": "webhook missing amount or currency"}, 400
        if amount != Decimal(str(payment.amount)) or currency != payment.currency.upper():
            current_app.logger.error("Nylon Pay amount/currency mismatch for %s", reference)
            return {"error": "payment amount or currency mismatch"}, 400

        business = db.session.execute(
            select(Business).where(Business.id == payment.business_id).with_for_update()
        ).scalar_one_or_none()
        if business is None:
            return {"error": "business not found"}, 404

        now = utcnow()
        trial_end = ensure_utc(business.trial_ends_at)
        paid_end = ensure_utc(business.subscription_ends_at)
        starts_at = max([value for value in (now, trial_end, paid_end) if value is not None])
        business.plan = payment.plan_key
        business.subscription_ends_at = starts_at + timedelta(days=payment.duration_days)
        payment.status = "successful"
        payment.provider_transaction_id = str(provider_id) if provider_id is not None else None
        payment.paid_at = now
        payment.raw_payload = payload
        db.session.commit()
    elif failed and payment.status != "successful":
        payment.status = "cancelled" if "cancel" in status or "cancel" in event else "failed"
        payment.provider_transaction_id = str(provider_id) if provider_id is not None else None
        payment.raw_payload = payload
        db.session.commit()
    elif processing and payment.status not in {"successful", "failed", "cancelled"}:
        payment.status = "processing" if status == "processing" or "processing" in event else "pending"
        payment.provider_transaction_id = str(provider_id) if provider_id is not None else None
        payment.raw_payload = payload
        db.session.commit()

    return {"status": "ok"}, 200

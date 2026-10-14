from datetime import datetime, timedelta, timezone
from flask_login import UserMixin
from werkzeug.security import check_password_hash, generate_password_hash
from .extensions import db, login_manager


def utcnow():
    return datetime.now(timezone.utc)


def ensure_utc(value):
    if value is None:
        return None
    if value.tzinfo is None:
        return value.replace(tzinfo=timezone.utc)
    return value.astimezone(timezone.utc)


class Business(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(120), nullable=False)
    currency = db.Column(db.String(3), nullable=False, default='UGX')
    created_at = db.Column(db.DateTime(timezone=True), nullable=False, default=utcnow)
    plan = db.Column(db.String(24), nullable=False, default='trial')
    trial_ends_at = db.Column(db.DateTime(timezone=True), nullable=False, default=lambda: utcnow() + timedelta(days=14))
    subscription_ends_at = db.Column(db.DateTime(timezone=True))

    @property
    def subscription_active(self):
        now = utcnow()
        trial_end = ensure_utc(self.trial_ends_at)
        paid_end = ensure_utc(self.subscription_ends_at)
        return (self.plan == 'trial' and trial_end is not None and trial_end > now) or (self.plan != 'trial' and paid_end is not None and paid_end > now)


class User(UserMixin, db.Model):
    id = db.Column(db.Integer, primary_key=True)
    business_id = db.Column(db.Integer, db.ForeignKey('business.id', ondelete='CASCADE'), nullable=False, index=True)
    email = db.Column(db.String(254), nullable=False, unique=True, index=True)
    full_name = db.Column(db.String(120), nullable=False)
    password_hash = db.Column(db.String(255), nullable=False)
    role = db.Column(db.String(20), nullable=False, default='owner')
    created_at = db.Column(db.DateTime(timezone=True), nullable=False, default=utcnow)
    business = db.relationship('Business', backref=db.backref('users', lazy=True))

    def set_password(self, password):
        self.password_hash = generate_password_hash(password)

    def check_password(self, password):
        return check_password_hash(self.password_hash, password)


class Product(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    business_id = db.Column(db.Integer, db.ForeignKey('business.id', ondelete='CASCADE'), nullable=False, index=True)
    name = db.Column(db.String(160), nullable=False)
    sku = db.Column(db.String(80))
    category = db.Column(db.String(80), nullable=False, default='General')
    cost_price = db.Column(db.Numeric(14, 2), nullable=False, default=0)
    selling_price = db.Column(db.Numeric(14, 2), nullable=False)
    quantity = db.Column(db.Integer, nullable=False, default=0)
    low_stock_at = db.Column(db.Integer, nullable=False, default=5)
    active = db.Column(db.Boolean, nullable=False, default=True)
    created_at = db.Column(db.DateTime(timezone=True), nullable=False, default=utcnow)
    __table_args__ = (db.UniqueConstraint('business_id', 'sku', name='uq_product_business_sku'), db.CheckConstraint('cost_price >= 0 AND selling_price >= 0 AND quantity >= 0', name='ck_product_nonnegative'))


class Sale(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    business_id = db.Column(db.Integer, db.ForeignKey('business.id', ondelete='CASCADE'), nullable=False, index=True)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    total = db.Column(db.Numeric(14, 2), nullable=False)
    payment_method = db.Column(db.String(24), nullable=False, default='cash')
    created_at = db.Column(db.DateTime(timezone=True), nullable=False, default=utcnow, index=True)
    items = db.relationship('SaleItem', backref='sale', cascade='all, delete-orphan', lazy=True)


class SaleItem(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    sale_id = db.Column(db.Integer, db.ForeignKey('sale.id', ondelete='CASCADE'), nullable=False, index=True)
    product_id = db.Column(db.Integer, db.ForeignKey('product.id'), nullable=False)
    product_name = db.Column(db.String(160), nullable=False)
    quantity = db.Column(db.Integer, nullable=False)
    unit_price = db.Column(db.Numeric(14, 2), nullable=False)
    unit_cost = db.Column(db.Numeric(14, 2), nullable=False)


class Expense(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    business_id = db.Column(db.Integer, db.ForeignKey('business.id', ondelete='CASCADE'), nullable=False, index=True)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    description = db.Column(db.String(200), nullable=False)
    amount = db.Column(db.Numeric(14, 2), nullable=False)
    created_at = db.Column(db.DateTime(timezone=True), nullable=False, default=utcnow, index=True)


class SubscriptionPayment(db.Model):
    """One auditable Nylon Pay attempt to buy/renew a business subscription."""
    id = db.Column(db.Integer, primary_key=True)
    business_id = db.Column(db.Integer, db.ForeignKey('business.id', ondelete='CASCADE'), nullable=False, index=True)
    merchant_reference = db.Column(db.String(32), nullable=False, unique=True, index=True)
    provider_transaction_id = db.Column(db.String(120))
    plan_key = db.Column(db.String(24), nullable=False)
    duration_days = db.Column(db.Integer, nullable=False)
    amount = db.Column(db.Numeric(14, 2), nullable=False)
    currency = db.Column(db.String(3), nullable=False, default='UGX')
    phone_number = db.Column(db.String(20), nullable=False)
    status = db.Column(db.String(24), nullable=False, default='pending', index=True)
    created_at = db.Column(db.DateTime(timezone=True), nullable=False, default=utcnow)
    paid_at = db.Column(db.DateTime(timezone=True))
    raw_payload = db.Column(db.JSON)
    business = db.relationship('Business', backref=db.backref('subscription_payments', lazy=True))


@login_manager.user_loader
def load_user(user_id):
    try:
        return db.session.get(User, int(user_id))
    except (TypeError, ValueError):
        return None

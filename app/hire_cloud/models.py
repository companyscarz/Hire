"""Initial tenant-aware data model for Hire Cloud.

No access token, password, or provider secret should be stored in plaintext in
these models. Credential references point to a deployment secret store.
"""
from datetime import datetime, timezone
from uuid import uuid4

from sqlalchemy import CheckConstraint, Index, UniqueConstraint

from .extensions import db


def _id():
    return str(uuid4())


def _utcnow():
    return datetime.now(timezone.utc)


class TimestampMixin:
    created_at = db.Column(db.DateTime(timezone=True), nullable=False, default=_utcnow)
    updated_at = db.Column(db.DateTime(timezone=True), nullable=False, default=_utcnow, onupdate=_utcnow)


class User(TimestampMixin, db.Model):
    __tablename__ = "hc_users"

    id = db.Column(db.String(36), primary_key=True, default=_id)
    email = db.Column(db.String(320), nullable=False, unique=True, index=True)
    password_hash = db.Column(db.String(255), nullable=False)
    display_name = db.Column(db.String(120), nullable=False, default="")
    is_active = db.Column(db.Boolean, nullable=False, default=True)
    email_verified_at = db.Column(db.DateTime(timezone=True))

    memberships = db.relationship("Membership", back_populates="user", cascade="all, delete-orphan")


class Tenant(TimestampMixin, db.Model):
    __tablename__ = "hc_tenants"

    id = db.Column(db.String(36), primary_key=True, default=_id)
    name = db.Column(db.String(160), nullable=False)
    slug = db.Column(db.String(80), nullable=False, unique=True, index=True)
    status = db.Column(db.String(24), nullable=False, default="active")

    __table_args__ = (
        CheckConstraint("status IN ('active', 'suspended', 'closed')", name="ck_hc_tenant_status"),
    )

    memberships = db.relationship("Membership", back_populates="tenant", cascade="all, delete-orphan")
    projects = db.relationship("CloudProject", back_populates="tenant")


class Membership(TimestampMixin, db.Model):
    __tablename__ = "hc_memberships"

    id = db.Column(db.String(36), primary_key=True, default=_id)
    user_id = db.Column(db.String(36), db.ForeignKey("hc_users.id", ondelete="CASCADE"), nullable=False)
    tenant_id = db.Column(db.String(36), db.ForeignKey("hc_tenants.id", ondelete="CASCADE"), nullable=False)
    role = db.Column(db.String(24), nullable=False, default="member")

    __table_args__ = (
        UniqueConstraint("user_id", "tenant_id", name="uq_hc_membership_user_tenant"),
        CheckConstraint("role IN ('owner', 'admin', 'member')", name="ck_hc_membership_role"),
        Index("ix_hc_membership_tenant_role", "tenant_id", "role"),
    )

    user = db.relationship("User", back_populates="memberships")
    tenant = db.relationship("Tenant", back_populates="memberships")


class Plan(TimestampMixin, db.Model):
    __tablename__ = "hc_plans"

    id = db.Column(db.String(36), primary_key=True, default=_id)
    code = db.Column(db.String(40), nullable=False, unique=True)
    name = db.Column(db.String(100), nullable=False)
    price_ugx = db.Column(db.Integer, nullable=False, default=0)
    cpu_millicores = db.Column(db.Integer, nullable=False)
    memory_mb = db.Column(db.Integer, nullable=False)
    storage_gb = db.Column(db.Integer, nullable=False)
    bandwidth_gb = db.Column(db.Integer, nullable=False, default=0)
    max_projects = db.Column(db.Integer, nullable=False, default=1)
    is_active = db.Column(db.Boolean, nullable=False, default=True)

    __table_args__ = (
        CheckConstraint("price_ugx >= 0", name="ck_hc_plan_price_nonnegative"),
        CheckConstraint("cpu_millicores > 0", name="ck_hc_plan_cpu_positive"),
        CheckConstraint("memory_mb > 0", name="ck_hc_plan_memory_positive"),
        CheckConstraint("storage_gb > 0", name="ck_hc_plan_storage_positive"),
        CheckConstraint("max_projects > 0", name="ck_hc_plan_projects_positive"),
    )


class Subscription(TimestampMixin, db.Model):
    __tablename__ = "hc_subscriptions"

    id = db.Column(db.String(36), primary_key=True, default=_id)
    tenant_id = db.Column(db.String(36), db.ForeignKey("hc_tenants.id", ondelete="RESTRICT"), nullable=False, index=True)
    plan_id = db.Column(db.String(36), db.ForeignKey("hc_plans.id", ondelete="RESTRICT"), nullable=False)
    status = db.Column(db.String(24), nullable=False, default="pending")
    current_period_start = db.Column(db.DateTime(timezone=True))
    current_period_end = db.Column(db.DateTime(timezone=True))
    cancel_at_period_end = db.Column(db.Boolean, nullable=False, default=False)
    provider_customer_ref = db.Column(db.String(255))
    provider_subscription_ref = db.Column(db.String(255), unique=True)

    __table_args__ = (
        CheckConstraint(
            "status IN ('pending', 'active', 'past_due', 'canceled', 'expired', 'suspended')",
            name="ck_hc_subscription_status",
        ),
        Index("ix_hc_subscription_tenant_status", "tenant_id", "status"),
    )

    tenant = db.relationship("Tenant")
    plan = db.relationship("Plan")


class CloudProject(TimestampMixin, db.Model):
    __tablename__ = "hc_projects"

    id = db.Column(db.String(36), primary_key=True, default=_id)
    tenant_id = db.Column(db.String(36), db.ForeignKey("hc_tenants.id", ondelete="CASCADE"), nullable=False)
    name = db.Column(db.String(120), nullable=False)
    slug = db.Column(db.String(80), nullable=False)
    status = db.Column(db.String(24), nullable=False, default="pending")
    dokploy_project_id = db.Column(db.String(120), unique=True)
    region = db.Column(db.String(80), nullable=False, default="primary")

    __table_args__ = (
        UniqueConstraint("tenant_id", "slug", name="uq_hc_project_tenant_slug"),
        CheckConstraint(
            "status IN ('pending', 'provisioning', 'active', 'failed', 'suspended', 'deleted')",
            name="ck_hc_project_status",
        ),
        Index("ix_hc_project_tenant_status", "tenant_id", "status"),
    )

    tenant = db.relationship("Tenant", back_populates="projects")


class GitConnection(TimestampMixin, db.Model):
    __tablename__ = "hc_git_connections"

    id = db.Column(db.String(36), primary_key=True, default=_id)
    tenant_id = db.Column(db.String(36), db.ForeignKey("hc_tenants.id", ondelete="CASCADE"), nullable=False, index=True)
    provider = db.Column(db.String(32), nullable=False)
    external_account_id = db.Column(db.String(255), nullable=False)
    display_name = db.Column(db.String(160), nullable=False, default="")
    credential_ref = db.Column(db.String(255), nullable=False)
    status = db.Column(db.String(24), nullable=False, default="active")

    __table_args__ = (
        UniqueConstraint("tenant_id", "provider", "external_account_id", name="uq_hc_git_account"),
        CheckConstraint("status IN ('active', 'revoked', 'error')", name="ck_hc_git_connection_status"),
    )


class GitRepository(TimestampMixin, db.Model):
    __tablename__ = "hc_git_repositories"

    id = db.Column(db.String(36), primary_key=True, default=_id)
    tenant_id = db.Column(db.String(36), db.ForeignKey("hc_tenants.id", ondelete="CASCADE"), nullable=False, index=True)
    project_id = db.Column(db.String(36), db.ForeignKey("hc_projects.id", ondelete="CASCADE"), nullable=False, index=True)
    connection_id = db.Column(db.String(36), db.ForeignKey("hc_git_connections.id", ondelete="RESTRICT"), nullable=False)
    provider_repository_id = db.Column(db.String(255), nullable=False)
    clone_url = db.Column(db.String(1000), nullable=False)
    default_branch = db.Column(db.String(255), nullable=False, default="main")
    webhook_secret_ref = db.Column(db.String(255))
    is_private = db.Column(db.Boolean, nullable=False, default=True)

    __table_args__ = (
        UniqueConstraint("tenant_id", "provider_repository_id", name="uq_hc_git_repository_tenant_provider_id"),
    )


class StorageAllocation(TimestampMixin, db.Model):
    __tablename__ = "hc_storage_allocations"

    id = db.Column(db.String(36), primary_key=True, default=_id)
    tenant_id = db.Column(db.String(36), db.ForeignKey("hc_tenants.id", ondelete="CASCADE"), nullable=False, index=True)
    project_id = db.Column(db.String(36), db.ForeignKey("hc_projects.id", ondelete="CASCADE"), nullable=False, index=True)
    provider = db.Column(db.String(40), nullable=False)
    bucket_name = db.Column(db.String(255), nullable=False)
    object_prefix = db.Column(db.String(512), nullable=False)
    quota_bytes = db.Column(db.BigInteger, nullable=False)
    used_bytes = db.Column(db.BigInteger, nullable=False, default=0)

    __table_args__ = (
        UniqueConstraint("provider", "bucket_name", "object_prefix", name="uq_hc_storage_prefix"),
        CheckConstraint("quota_bytes >= 0", name="ck_hc_storage_quota_nonnegative"),
        CheckConstraint("used_bytes >= 0", name="ck_hc_storage_used_nonnegative"),
    )


class ProvisioningJob(TimestampMixin, db.Model):
    __tablename__ = "hc_provisioning_jobs"

    id = db.Column(db.String(36), primary_key=True, default=_id)
    tenant_id = db.Column(db.String(36), db.ForeignKey("hc_tenants.id", ondelete="CASCADE"), nullable=False, index=True)
    project_id = db.Column(db.String(36), db.ForeignKey("hc_projects.id", ondelete="SET NULL"), index=True)
    kind = db.Column(db.String(60), nullable=False)
    status = db.Column(db.String(24), nullable=False, default="queued")
    idempotency_key = db.Column(db.String(160), nullable=False, unique=True)
    payload = db.Column(db.JSON, nullable=False, default=dict)
    attempts = db.Column(db.Integer, nullable=False, default=0)
    error_code = db.Column(db.String(80))
    completed_at = db.Column(db.DateTime(timezone=True))

    __table_args__ = (
        CheckConstraint(
            "status IN ('queued', 'running', 'succeeded', 'failed', 'canceled')",
            name="ck_hc_provisioning_status",
        ),
        Index("ix_hc_provisioning_tenant_status", "tenant_id", "status"),
    )


class UsageSnapshot(db.Model):
    __tablename__ = "hc_usage_snapshots"

    id = db.Column(db.String(36), primary_key=True, default=_id)
    tenant_id = db.Column(db.String(36), db.ForeignKey("hc_tenants.id", ondelete="CASCADE"), nullable=False)
    project_id = db.Column(db.String(36), db.ForeignKey("hc_projects.id", ondelete="CASCADE"), nullable=False)
    service_key = db.Column(db.String(160), nullable=False)
    measured_at = db.Column(db.DateTime(timezone=True), nullable=False, default=_utcnow, index=True)
    cpu_millicores = db.Column(db.Integer, nullable=False, default=0)
    memory_bytes = db.Column(db.BigInteger, nullable=False, default=0)
    storage_bytes = db.Column(db.BigInteger, nullable=False, default=0)
    network_rx_bytes = db.Column(db.BigInteger, nullable=False, default=0)
    network_tx_bytes = db.Column(db.BigInteger, nullable=False, default=0)

    __table_args__ = (
        Index("ix_hc_usage_tenant_project_time", "tenant_id", "project_id", "measured_at"),
        CheckConstraint("cpu_millicores >= 0", name="ck_hc_usage_cpu_nonnegative"),
        CheckConstraint("memory_bytes >= 0", name="ck_hc_usage_memory_nonnegative"),
        CheckConstraint("storage_bytes >= 0", name="ck_hc_usage_storage_nonnegative"),
    )


class PaymentEvent(db.Model):
    __tablename__ = "hc_payment_events"

    id = db.Column(db.String(36), primary_key=True, default=_id)
    provider = db.Column(db.String(40), nullable=False)
    provider_event_id = db.Column(db.String(255), nullable=False)
    tenant_id = db.Column(db.String(36), db.ForeignKey("hc_tenants.id", ondelete="SET NULL"), index=True)
    subscription_id = db.Column(db.String(36), db.ForeignKey("hc_subscriptions.id", ondelete="SET NULL"), index=True)
    amount_ugx = db.Column(db.Integer, nullable=False, default=0)
    currency = db.Column(db.String(3), nullable=False, default="UGX")
    event_type = db.Column(db.String(100), nullable=False)
    signature_verified = db.Column(db.Boolean, nullable=False, default=False)
    processed_at = db.Column(db.DateTime(timezone=True))
    payload_digest = db.Column(db.String(128), nullable=False, default="")

    __table_args__ = (
        UniqueConstraint("provider", "provider_event_id", name="uq_hc_payment_provider_event"),
        CheckConstraint("amount_ugx >= 0", name="ck_hc_payment_amount_nonnegative"),
    )


class AuditEvent(db.Model):
    __tablename__ = "hc_audit_events"

    id = db.Column(db.String(36), primary_key=True, default=_id)
    tenant_id = db.Column(db.String(36), db.ForeignKey("hc_tenants.id", ondelete="SET NULL"), index=True)
    actor_user_id = db.Column(db.String(36), db.ForeignKey("hc_users.id", ondelete="SET NULL"), index=True)
    action = db.Column(db.String(120), nullable=False)
    target_type = db.Column(db.String(80), nullable=False)
    target_id = db.Column(db.String(160))
    details = db.Column(db.JSON, nullable=False, default=dict)
    created_at = db.Column(db.DateTime(timezone=True), nullable=False, default=_utcnow, index=True)

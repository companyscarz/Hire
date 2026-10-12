"
cat /tmp/hire-cloud-migrations/script.py.mako
shell: /usr/bin/bash -e {0}
env:
  pythonLocation: /opt/hostedtoolcache/Python/3.12.15/x64
  PKG_CONFIG_PATH: /opt/hostedtoolcache/Python/3.12.15/x64/lib/pkgconfig
  Python_ROOT_DIR: /opt/hostedtoolcache/Python/3.12.15/x64
  Python2_ROOT_DIR: /opt/hostedtoolcache/Python/3.12.15/x64
  Python3_ROOT_DIR: /opt/hostedtoolcache/Python/3.12.15/x64
  LD_LIBRARY_PATH: /opt/hostedtoolcache/Python/3.12.15/x64/lib
##[endgroup]
Creating directory /tmp/hire-cloud-migrations ...  done
Creating directory /tmp/hire-cloud-migrations/versions ...  done
Generating /tmp/hire-cloud-migrations/script.py.mako ...  done
Generating /tmp/hire-cloud-migrations/env.py ...  done
Generating /tmp/hire-cloud-migrations/README ...  done
Generating /tmp/hire-cloud-migrations/alembic.ini ...  done
Please edit configuration/connection/logging settings in /tmp/hire-cloud-migrations/alembic.ini before proceeding.
INFO  [alembic.runtime.migration] Context impl SQLiteImpl.
INFO  [alembic.runtime.migration] Will assume non-transactional DDL.
INFO  [alembic.runtime.plugins] setting up autogenerate plugin alembic.autogenerate.schemas
INFO  [alembic.runtime.plugins] setting up autogenerate plugin alembic.autogenerate.tables
INFO  [alembic.runtime.plugins] setting up autogenerate plugin alembic.autogenerate.types
INFO  [alembic.runtime.plugins] setting up autogenerate plugin alembic.autogenerate.constraints
INFO  [alembic.runtime.plugins] setting up autogenerate plugin alembic.autogenerate.defaults
INFO  [alembic.runtime.plugins] setting up autogenerate plugin alembic.autogenerate.comments
INFO  [alembic.autogenerate.compare.tables] Detected added table 'hc_plans'
INFO  [alembic.autogenerate.compare.tables] Detected added table 'hc_tenants'
INFO  [alembic.autogenerate.compare.constraints] Detected added index 'ix_hc_tenants_slug' on '('slug',)'
INFO  [alembic.autogenerate.compare.tables] Detected added table 'hc_users'
INFO  [alembic.autogenerate.compare.constraints] Detected added index 'ix_hc_users_email' on '('email',)'
INFO  [alembic.autogenerate.compare.tables] Detected added table 'hc_audit_events'
INFO  [alembic.autogenerate.compare.constraints] Detected added index 'ix_hc_audit_events_actor_user_id' on '('actor_user_id',)'
INFO  [alembic.autogenerate.compare.constraints] Detected added index 'ix_hc_audit_events_created_at' on '('created_at',)'
INFO  [alembic.autogenerate.compare.constraints] Detected added index 'ix_hc_audit_events_tenant_id' on '('tenant_id',)'
INFO  [alembic.autogenerate.compare.tables] Detected added table 'hc_git_connections'
INFO  [alembic.autogenerate.compare.constraints] Detected added index 'ix_hc_git_connections_tenant_id' on '('tenant_id',)'
INFO  [alembic.autogenerate.compare.tables] Detected added table 'hc_memberships'
INFO  [alembic.autogenerate.compare.constraints] Detected added index 'ix_hc_membership_tenant_role' on '('tenant_id', 'role')'
INFO  [alembic.autogenerate.compare.tables] Detected added table 'hc_projects'
INFO  [alembic.autogenerate.compare.constraints] Detected added index 'ix_hc_project_tenant_status' on '('tenant_id', 'status')'
INFO  [alembic.autogenerate.compare.tables] Detected added table 'hc_subscriptions'
INFO  [alembic.autogenerate.compare.constraints] Detected added index 'ix_hc_subscription_tenant_status' on '('tenant_id', 'status')'
INFO  [alembic.autogenerate.compare.constraints] Detected added index 'ix_hc_subscriptions_tenant_id' on '('tenant_id',)'
INFO  [alembic.autogenerate.compare.tables] Detected added table 'hc_git_repositories'
INFO  [alembic.autogenerate.compare.constraints] Detected added index 'ix_hc_git_repositories_project_id' on '('project_id',)'
INFO  [alembic.autogenerate.compare.constraints] Detected added index 'ix_hc_git_repositories_tenant_id' on '('tenant_id',)'
INFO  [alembic.autogenerate.compare.tables] Detected added table 'hc_payment_events'
INFO  [alembic.autogenerate.compare.constraints] Detected added index 'ix_hc_payment_events_subscription_id' on '('subscription_id',)'
INFO  [alembic.autogenerate.compare.constraints] Detected added index 'ix_hc_payment_events_tenant_id' on '('tenant_id',)'
INFO  [alembic.autogenerate.compare.tables] Detected added table 'hc_provisioning_jobs'
INFO  [alembic.autogenerate.compare.constraints] Detected added index 'ix_hc_provisioning_jobs_project_id' on '('project_id',)'
INFO  [alembic.autogenerate.compare.constraints] Detected added index 'ix_hc_provisioning_jobs_tenant_id' on '('tenant_id',)'
INFO  [alembic.autogenerate.compare.constraints] Detected added index 'ix_hc_provisioning_tenant_status' on '('tenant_id', 'status')'
INFO  [alembic.autogenerate.compare.tables] Detected added table 'hc_storage_allocations'
INFO  [alembic.autogenerate.compare.constraints] Detected added index 'ix_hc_storage_allocations_project_id' on '('project_id',)'
INFO  [alembic.autogenerate.compare.constraints] Detected added index 'ix_hc_storage_allocations_tenant_id' on '('tenant_id',)'
INFO  [alembic.autogenerate.compare.tables] Detected added table 'hc_usage_snapshots'
INFO  [alembic.autogenerate.compare.constraints] Detected added index 'ix_hc_usage_snapshots_measured_at' on '('measured_at',)'
INFO  [alembic.autogenerate.compare.constraints] Detected added index 'ix_hc_usage_tenant_project_time' on '('tenant_id', 'project_id', 'measured_at')'
Generating /tmp/hire-cloud-migrations/versions/52a0594f7a52_initial_hire_cloud_schema.py ...  done
=== MIGRATION REVISION ===
"""initial hire cloud schema

Revision ID: 52a0594f7a52
Revises: 
Create Date: 2026-10-12 09:44:07.658694

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = '52a0594f7a52'
down_revision = None
branch_labels = None
depends_on = None


def upgrade():
    # ### commands auto generated by Alembic - please adjust! ###
    op.create_table('hc_plans',
    sa.Column('id', sa.String(length=36), nullable=False),
    sa.Column('code', sa.String(length=40), nullable=False),
    sa.Column('name', sa.String(length=100), nullable=False),
    sa.Column('price_ugx', sa.Integer(), nullable=False),
    sa.Column('cpu_millicores', sa.Integer(), nullable=False),
    sa.Column('memory_mb', sa.Integer(), nullable=False),
    sa.Column('storage_gb', sa.Integer(), nullable=False),
    sa.Column('bandwidth_gb', sa.Integer(), nullable=False),
    sa.Column('max_projects', sa.Integer(), nullable=False),
    sa.Column('is_active', sa.Boolean(), nullable=False),
    sa.Column('created_at', sa.DateTime(timezone=True), nullable=False),
    sa.Column('updated_at', sa.DateTime(timezone=True), nullable=False),
    sa.CheckConstraint('cpu_millicores > 0', name='ck_hc_plan_cpu_positive'),
    sa.CheckConstraint('max_projects > 0', name='ck_hc_plan_projects_positive'),
    sa.CheckConstraint('memory_mb > 0', name='ck_hc_plan_memory_positive'),
    sa.CheckConstraint('price_ugx >= 0', name='ck_hc_plan_price_nonnegative'),
    sa.CheckConstraint('storage_gb > 0', name='ck_hc_plan_storage_positive'),
    sa.PrimaryKeyConstraint('id'),
    sa.UniqueConstraint('code')
    )
    op.create_table('hc_tenants',
    sa.Column('id', sa.String(length=36), nullable=False),
    sa.Column('name', sa.String(length=160), nullable=False),
    sa.Column('slug', sa.String(length=80), nullable=False),
    sa.Column('status', sa.String(length=24), nullable=False),
    sa.Column('created_at', sa.DateTime(timezone=True), nullable=False),
    sa.Column('updated_at', sa.DateTime(timezone=True), nullable=False),
    sa.CheckConstraint("status IN ('active', 'suspended', 'closed')", name='ck_hc_tenant_status'),
    sa.PrimaryKeyConstraint('id')
    )
    with op.batch_alter_table('hc_tenants', schema=None) as batch_op:
        batch_op.create_index(batch_op.f('ix_hc_tenants_slug'), ['slug'], unique=True)

    op.create_table('hc_users',
    sa.Column('id', sa.String(length=36), nullable=False),
    sa.Column('email', sa.String(length=320), nullable=False),
    sa.Column('password_hash', sa.String(length=255), nullable=False),
    sa.Column('display_name', sa.String(length=120), nullable=False),
    sa.Column('is_active', sa.Boolean(), nullable=False),
    sa.Column('email_verified_at', sa.DateTime(timezone=True), nullable=True),
    sa.Column('created_at', sa.DateTime(timezone=True), nullable=False),
    sa.Column('updated_at', sa.DateTime(timezone=True), nullable=False),
    sa.PrimaryKeyConstraint('id')
    )
    with op.batch_alter_table('hc_users', schema=None) as batch_op:
        batch_op.create_index(batch_op.f('ix_hc_users_email'), ['email'], unique=True)

    op.create_table('hc_audit_events',
    sa.Column('id', sa.String(length=36), nullable=False),
    sa.Column('tenant_id', sa.String(length=36), nullable=True),
    sa.Column('actor_user_id', sa.String(length=36), nullable=True),
    sa.Column('action', sa.String(length=120), nullable=False),
    sa.Column('target_type', sa.String(length=80), nullable=False),
    sa.Column('target_id', sa.String(length=160), nullable=True),
    sa.Column('details', sa.JSON(), nullable=False),
    sa.Column('created_at', sa.DateTime(timezone=True), nullable=False),
    sa.ForeignKeyConstraint(['actor_user_id'], ['hc_users.id'], ondelete='SET NULL'),
    sa.ForeignKeyConstraint(['tenant_id'], ['hc_tenants.id'], ondelete='SET NULL'),
    sa.PrimaryKeyConstraint('id')
    )
    with op.batch_alter_table('hc_audit_events', schema=None) as batch_op:
        batch_op.create_index(batch_op.f('ix_hc_audit_events_actor_user_id'), ['actor_user_id'], unique=False)
        batch_op.create_index(batch_op.f('ix_hc_audit_events_created_at'), ['created_at'], unique=False)
        batch_op.create_index(batch_op.f('ix_hc_audit_events_tenant_id'), ['tenant_id'], unique=False)

    op.create_table('hc_git_connections',
    sa.Column('id', sa.String(length=36), nullable=False),
    sa.Column('tenant_id', sa.String(length=36), nullable=False),
    sa.Column('provider', sa.String(length=32), nullable=False),
    sa.Column('external_account_id', sa.String(length=255), nullable=False),
    sa.Column('display_name', sa.String(length=160), nullable=False),
    sa.Column('credential_ref', sa.String(length=255), nullable=False),
    sa.Column('status', sa.String(length=24), nullable=False),
    sa.Column('created_at', sa.DateTime(timezone=True), nullable=False),
    sa.Column('updated_at', sa.DateTime(timezone=True), nullable=False),
    sa.CheckConstraint("status IN ('active', 'revoked', 'error')", name='ck_hc_git_connection_status'),
    sa.ForeignKeyConstraint(['tenant_id'], ['hc_tenants.id'], ondelete='CASCADE'),
    sa.PrimaryKeyConstraint('id'),
    sa.UniqueConstraint('tenant_id', 'provider', 'external_account_id', name='uq_hc_git_account')
    )
    with op.batch_alter_table('hc_git_connections', schema=None) as batch_op:
        batch_op.create_index(batch_op.f('ix_hc_git_connections_tenant_id'), ['tenant_id'], unique=False)

    op.create_table('hc_memberships',
    sa.Column('id', sa.String(length=36), nullable=False),
    sa.Column('user_id', sa.String(length=36), nullable=False),
    sa.Column('tenant_id', sa.String(length=36), nullable=False),
    sa.Column('role', sa.String(length=24), nullable=False),
    sa.Column('created_at', sa.DateTime(timezone=True), nullable=False),
    sa.Column('updated_at', sa.DateTime(timezone=True), nullable=False),
    sa.CheckConstraint("role IN ('owner', 'admin', 'member')", name='ck_hc_membership_role'),
    sa.ForeignKeyConstraint(['tenant_id'], ['hc_tenants.id'], ondelete='CASCADE'),
    sa.ForeignKeyConstraint(['user_id'], ['hc_users.id'], ondelete='CASCADE'),
    sa.PrimaryKeyConstraint('id'),
    sa.UniqueConstraint('user_id', 'tenant_id', name='uq_hc_membership_user_tenant')
    )
    with op.batch_alter_table('hc_memberships', schema=None) as batch_op:
        batch_op.create_index('ix_hc_membership_tenant_role', ['tenant_id', 'role'], unique=False)

    op.create_table('hc_projects',
    sa.Column('id', sa.String(length=36), nullable=False),
    sa.Column('tenant_id', sa.String(length=36), nullable=False),
    sa.Column('name', sa.String(length=120), nullable=False),
    sa.Column('slug', sa.String(length=80), nullable=False),
    sa.Column('status', sa.String(length=24), nullable=False),
    sa.Column('dokploy_project_id', sa.String(length=120), nullable=True),
    sa.Column('region', sa.String(length=80), nullable=False),
    sa.Column('created_at', sa.DateTime(timezone=True), nullable=False),
    sa.Column('updated_at', sa.DateTime(timezone=True), nullable=False),
    sa.CheckConstraint("status IN ('pending', 'provisioning', 'active', 'failed', 'suspended', 'deleted')", name='ck_hc_project_status'),
    sa.ForeignKeyConstraint(['tenant_id'], ['hc_tenants.id'], ondelete='CASCADE'),
    sa.PrimaryKeyConstraint('id'),
    sa.UniqueConstraint('dokploy_project_id'),
    sa.UniqueConstraint('tenant_id', 'slug', name='uq_hc_project_tenant_slug')
    )
    with op.batch_alter_table('hc_projects', schema=None) as batch_op:
        batch_op.create_index('ix_hc_project_tenant_status', ['tenant_id', 'status'], unique=False)

    op.create_table('hc_subscriptions',
    sa.Column('id', sa.String(length=36), nullable=False),
    sa.Column('tenant_id', sa.String(length=36), nullable=False),
    sa.Column('plan_id', sa.String(length=36), nullable=False),
    sa.Column('status', sa.String(length=24), nullable=False),
    sa.Column('current_period_start', sa.DateTime(timezone=True), nullable=True),
    sa.Column('current_period_end', sa.DateTime(timezone=True), nullable=True),
    sa.Column('cancel_at_period_end', sa.Boolean(), nullable=False),
    sa.Column('provider_customer_ref', sa.String(length=255), nullable=True),
    sa.Column('provider_subscription_ref', sa.String(length=255), nullable=True),
    sa.Column('created_at', sa.DateTime(timezone=True), nullable=False),
    sa.Column('updated_at', sa.DateTime(timezone=True), nullable=False),
    sa.CheckConstraint("status IN ('pending', 'active', 'past_due', 'canceled', 'expired', 'suspended')", name='ck_hc_subscription_status'),
    sa.ForeignKeyConstraint(['plan_id'], ['hc_plans.id'], ondelete='RESTRICT'),
    sa.ForeignKeyConstraint(['tenant_id'], ['hc_tenants.id'], ondelete='RESTRICT'),
    sa.PrimaryKeyConstraint('id'),
    sa.UniqueConstraint('provider_subscription_ref')
    )
    with op.batch_alter_table('hc_subscriptions', schema=None) as batch_op:
        batch_op.create_index('ix_hc_subscription_tenant_status', ['tenant_id', 'status'], unique=False)
        batch_op.create_index(batch_op.f('ix_hc_subscriptions_tenant_id'), ['tenant_id'], unique=False)

    op.create_table('hc_git_repositories',
    sa.Column('id', sa.String(length=36), nullable=False),
    sa.Column('tenant_id', sa.String(length=36), nullable=False),
    sa.Column('project_id', sa.String(length=36), nullable=False),
    sa.Column('connection_id', sa.String(length=36), nullable=False),
    sa.Column('provider_repository_id', sa.String(length=255), nullable=False),
    sa.Column('clone_url', sa.String(length=1000), nullable=False),
    sa.Column('default_branch', sa.String(length=255), nullable=False),
    sa.Column('webhook_secret_ref', sa.String(length=255), nullable=True),
    sa.Column('is_private', sa.Boolean(), nullable=False),
    sa.Column('created_at', sa.DateTime(timezone=True), nullable=False),
    sa.Column('updated_at', sa.DateTime(timezone=True), nullable=False),
    sa.ForeignKeyConstraint(['connection_id'], ['hc_git_connections.id'], ondelete='RESTRICT'),
    sa.ForeignKeyConstraint(['project_id'], ['hc_projects.id'], ondelete='CASCADE'),
    sa.ForeignKeyConstraint(['tenant_id'], ['hc_tenants.id'], ondelete='CASCADE'),
    sa.PrimaryKeyConstraint('id'),
    sa.UniqueConstraint('tenant_id', 'provider_repository_id', name='uq_hc_git_repository_tenant_provider_id')
    )
    with op.batch_alter_table('hc_git_repositories', schema=None) as batch_op:
        batch_op.create_index(batch_op.f('ix_hc_git_repositories_project_id'), ['project_id'], unique=False)
        batch_op.create_index(batch_op.f('ix_hc_git_repositories_tenant_id'), ['tenant_id'], unique=False)

    op.create_table('hc_payment_events',
    sa.Column('id', sa.String(length=36), nullable=False),
    sa.Column('provider', sa.String(length=40), nullable=False),
    sa.Column('provider_event_id', sa.String(length=255), nullable=False),
    sa.Column('tenant_id', sa.String(length=36), nullable=True),
    sa.Column('subscription_id', sa.String(length=36), nullable=True),
    sa.Column('amount_ugx', sa.Integer(), nullable=False),
    sa.Column('currency', sa.String(length=3), nullable=False),
    sa.Column('event_type', sa.String(length=100), nullable=False),
    sa.Column('signature_verified', sa.Boolean(), nullable=False),
    sa.Column('processed_at', sa.DateTime(timezone=True), nullable=True),
    sa.Column('payload_digest', sa.String(length=128), nullable=False),
    sa.CheckConstraint('amount_ugx >= 0', name='ck_hc_payment_amount_nonnegative'),
    sa.ForeignKeyConstraint(['subscription_id'], ['hc_subscriptions.id'], ondelete='SET NULL'),
    sa.ForeignKeyConstraint(['tenant_id'], ['hc_tenants.id'], ondelete='SET NULL'),
    sa.PrimaryKeyConstraint('id'),
    sa.UniqueConstraint('provider', 'provider_event_id', name='uq_hc_payment_provider_event')
    )
    with op.batch_alter_table('hc_payment_events', schema=None) as batch_op:
        batch_op.create_index(batch_op.f('ix_hc_payment_events_subscription_id'), ['subscription_id'], unique=False)
        batch_op.create_index(batch_op.f('ix_hc_payment_events_tenant_id'), ['tenant_id'], unique=False)

    op.create_table('hc_provisioning_jobs',
    sa.Column('id', sa.String(length=36), nullable=False),
    sa.Column('tenant_id', sa.String(length=36), nullable=False),
    sa.Column('project_id', sa.String(length=36), nullable=True),
    sa.Column('kind', sa.String(length=60), nullable=False),
    sa.Column('status', sa.String(length=24), nullable=False),
    sa.Column('idempotency_key', sa.String(length=160), nullable=False),
    sa.Column('payload', sa.JSON(), nullable=False),
    sa.Column('attempts', sa.Integer(), nullable=False),
    sa.Column('error_code', sa.String(length=80), nullable=True),
    sa.Column('completed_at', sa.DateTime(timezone=True), nullable=True),
    sa.Column('created_at', sa.DateTime(timezone=True), nullable=False),
    sa.Column('updated_at', sa.DateTime(timezone=True), nullable=False),
    sa.CheckConstraint("status IN ('queued', 'running', 'succeeded', 'failed', 'canceled')", name='ck_hc_provisioning_status'),
    sa.ForeignKeyConstraint(['project_id'], ['hc_projects.id'], ondelete='SET NULL'),
    sa.ForeignKeyConstraint(['tenant_id'], ['hc_tenants.id'], ondelete='CASCADE'),
    sa.PrimaryKeyConstraint('id'),
    sa.UniqueConstraint('idempotency_key')
    )
    with op.batch_alter_table('hc_provisioning_jobs', schema=None) as batch_op:
        batch_op.create_index(batch_op.f('ix_hc_provisioning_jobs_project_id'), ['project_id'], unique=False)
        batch_op.create_index(batch_op.f('ix_hc_provisioning_jobs_tenant_id'), ['tenant_id'], unique=False)
        batch_op.create_index('ix_hc_provisioning_tenant_status', ['tenant_id', 'status'], unique=False)

    op.create_table('hc_storage_allocations',
    sa.Column('id', sa.String(length=36), nullable=False),
    sa.Column('tenant_id', sa.String(length=36), nullable=False),
    sa.Column('project_id', sa.String(length=36), nullable=False),
    sa.Column('provider', sa.String(length=40), nullable=False),
    sa.Column('bucket_name', sa.String(length=255), nullable=False),
    sa.Column('object_prefix', sa.String(length=512), nullable=False),
    sa.Column('quota_bytes', sa.BigInteger(), nullable=False),
    sa.Column('used_bytes', sa.BigInteger(), nullable=False),
    sa.Column('created_at', sa.DateTime(timezone=True), nullable=False),
    sa.Column('updated_at', sa.DateTime(timezone=True), nullable=False),
    sa.CheckConstraint('quota_bytes >= 0', name='ck_hc_storage_quota_nonnegative'),
    sa.CheckConstraint('used_bytes >= 0', name='ck_hc_storage_used_nonnegative'),
    sa.ForeignKeyConstraint(['project_id'], ['hc_projects.id'], ondelete='CASCADE'),
    sa.ForeignKeyConstraint(['tenant_id'], ['hc_tenants.id'], ondelete='CASCADE'),
    sa.PrimaryKeyConstraint('id'),
    sa.UniqueConstraint('provider', 'bucket_name', 'object_prefix', name='uq_hc_storage_prefix')
    )
    with op.batch_alter_table('hc_storage_allocations', schema=None) as batch_op:
        batch_op.create_index(batch_op.f('ix_hc_storage_allocations_project_id'), ['project_id'], unique=False)
        batch_op.create_index(batch_op.f('ix_hc_storage_allocations_tenant_id'), ['tenant_id'], unique=False)

    op.create_table('hc_usage_snapshots',
    sa.Column('id', sa.String(length=36), nullable=False),
    sa.Column('tenant_id', sa.String(length=36), nullable=False),
    sa.Column('project_id', sa.String(length=36), nullable=False),
    sa.Column('service_key', sa.String(length=160), nullable=False),
    sa.Column('measured_at', sa.DateTime(timezone=True), nullable=False),
    sa.Column('cpu_millicores', sa.Integer(), nullable=False),
    sa.Column('memory_bytes', sa.BigInteger(), nullable=False),
    sa.Column('storage_bytes', sa.BigInteger(), nullable=False),
    sa.Column('network_rx_bytes', sa.BigInteger(), nullable=False),
    sa.Column('network_tx_bytes', sa.BigInteger(), nullable=False),
    sa.CheckConstraint('cpu_millicores >= 0', name='ck_hc_usage_cpu_nonnegative'),
    sa.CheckConstraint('memory_bytes >= 0', name='ck_hc_usage_memory_nonnegative'),
    sa.CheckConstraint('storage_bytes >= 0', name='ck_hc_usage_storage_nonnegative'),
    sa.ForeignKeyConstraint(['project_id'], ['hc_projects.id'], ondelete='CASCADE'),
    sa.ForeignKeyConstraint(['tenant_id'], ['hc_tenants.id'], ondelete='CASCADE'),
    sa.PrimaryKeyConstraint('id')
    )
    with op.batch_alter_table('hc_usage_snapshots', schema=None) as batch_op:
        batch_op.create_index(batch_op.f('ix_hc_usage_snapshots_measured_at'), ['measured_at'], unique=False)
        batch_op.create_index('ix_hc_usage_tenant_project_time', ['tenant_id', 'project_id', 'measured_at'], unique=False)

    # ### end Alembic commands ###


def downgrade():
    # ### commands auto generated by Alembic - please adjust! ###
    with op.batch_alter_table('hc_usage_snapshots', schema=None) as batch_op:
        batch_op.drop_index('ix_hc_usage_tenant_project_time')
        batch_op.drop_index(batch_op.f('ix_hc_usage_snapshots_measured_at'))

    op.drop_table('hc_usage_snapshots')
    with op.batch_alter_table('hc_storage_allocations', schema=None) as batch_op:
        batch_op.drop_index(batch_op.f('ix_hc_storage_allocations_tenant_id'))
        batch_op.drop_index(batch_op.f('ix_hc_storage_allocations_project_id'))

    op.drop_table('hc_storage_allocations')
    with op.batch_alter_table('hc_provisioning_jobs', schema=None) as batch_op:
        batch_op.drop_index('ix_hc_provisioning_tenant_status')
        batch_op.drop_index(batch_op.f('ix_hc_provisioning_jobs_tenant_id'))
        batch_op.drop_index(batch_op.f('ix_hc_provisioning_jobs_project_id'))

    op.drop_table('hc_provisioning_jobs')
    with op.batch_alter_table('hc_payment_events', schema=None) as batch_op:
        batch_op.drop_index(batch_op.f('ix_hc_payment_events_tenant_id'))
        batch_op.drop_index(batch_op.f('ix_hc_payment_events_subscription_id'))

    op.drop_table('hc_payment_events')
    with op.batch_alter_table('hc_git_repositories', schema=None) as batch_op:
        batch_op.drop_index(batch_op.f('ix_hc_git_repositories_tenant_id'))
        batch_op.drop_index(batch_op.f('ix_hc_git_repositories_project_id'))

    op.drop_table('hc_git_repositories')
    with op.batch_alter_table('hc_subscriptions', schema=None) as batch_op:
        batch_op.drop_index(batch_op.f('ix_hc_subscriptions_tenant_id'))
        batch_op.drop_index('ix_hc_subscription_tenant_status')

    op.drop_table('hc_subscriptions')
    with op.batch_alter_table('hc_projects', schema=None) as batch_op:
        batch_op.drop_index('ix_hc_project_tenant_status')

    op.drop_table('hc_projects')
    with op.batch_alter_table('hc_memberships', schema=None) as batch_op:
        batch_op.drop_index('ix_hc_membership_tenant_role')

    op.drop_table('hc_memberships')
    with op.batch_alter_table('hc_git_connections', schema=None) as batch_op:
        batch_op.drop_index(batch_op.f('ix_hc_git_connections_tenant_id'))

    op.drop_table('hc_git_connections')
    with op.batch_alter_table('hc_audit_events', schema=None) as batch_op:
        batch_op.drop_index(batch_op.f('ix_hc_audit_events_tenant_id'))
        batch_op.drop_index(batch_op.f('ix_hc_audit_events_created_at'))
        batch_op.drop_index(batch_op.f('ix_hc_audit_events_actor_user_id'))

    op.drop_table('hc_audit_events')
    with op.batch_alter_table('hc_users', schema=None) as batch_op:
        batch_op.drop_index(batch_op.f('ix_hc_users_email'))

    op.drop_table('hc_users')
    with op.batch_alter_table('hc_tenants', schema=None) as batch_op:
        batch_op.drop_index(batch_op.f('ix_hc_tenants_slug'))

    op.drop_table('hc_tenants')
    op.drop_table('hc_plans')
    # ### end Alembic commands ###
=== MIGRATION ENVIRONMENT ===
import logging
from logging.config import fileConfig

from flask import current_app

from alembic import context

# this is the Alembic Config object, which provides
# access to the values within the .ini file in use.
config = context.config

# Interpret the config file for Python logging.
# This line sets up loggers basically.
fileConfig(config.config_file_name)
logger = logging.getLogger('alembic.env')


def get_engine():
    try:
        # this works with Flask-SQLAlchemy<3 and Alchemical
        return current_app.extensions['migrate'].db.get_engine()
    except (TypeError, AttributeError):
        # this works with Flask-SQLAlchemy>=3
        return current_app.extensions['migrate'].db.engine


def get_engine_url():
    try:
        return get_engine().url.render_as_string(hide_password=False).replace(
            '%', '%%')
    except AttributeError:
        return str(get_engine().url).replace('%', '%%')


# add your model's MetaData object here
# for 'autogenerate' support
# from myapp import mymodel
# target_metadata = mymodel.Base.metadata
config.set_main_option('sqlalchemy.url', get_engine_url())
target_db = current_app.extensions['migrate'].db

# other values from the config, defined by the needs of env.py,
# can be acquired:
# my_important_option = config.get_main_option("my_important_option")
# ... etc.


def get_metadata():
    if hasattr(target_db, 'metadatas'):
        return target_db.metadatas[None]
    return target_db.metadata


def run_migrations_offline():
    """Run migrations in 'offline' mode.

    This configures the context with just a URL
    and not an Engine, though an Engine is acceptable
    here as well.  By skipping the Engine creation
    we don't even need a DBAPI to be available.

    Calls to context.execute() here emit the given string to the
    script output.

    """
    url = config.get_main_option("sqlalchemy.url")
    context.configure(
        url=url, target_metadata=get_metadata(), literal_binds=True
    )

    with context.begin_transaction():
        context.run_migrations()


def run_migrations_online():
    """Run migrations in 'online' mode.

    In this scenario we need to create an Engine
    and associate a connection with the context.

    """

    # this callback is used to prevent an auto-migration from being generated
    # when there are no changes to the schema
    # reference: http://alembic.zzzcomputing.com/en/latest/cookbook.html
    def process_revision_directives(context, revision, directives):
        if getattr(config.cmd_opts, 'autogenerate', False):
            script = directives[0]
            if script.upgrade_ops.is_empty():
                directives[:] = []
                logger.info('No changes in schema detected.')

    conf_args = current_app.extensions['migrate'].configure_args
    if conf_args.get("process_revision_directives") is None:
        conf_args["process_revision_directives"] = process_revision_directives

    connectable = get_engine()

    with connectable.connect() as connection:
        context.configure(
            connection=connection,
            target_metadata=get_metadata(),
            **conf_args
        )

        with context.begin_transaction():
            context.run_migrations()


if context.is_offline_mode():
    run_migrations_offline()
else:
    run_migrations_online()
=== MIGRATION TEMPLATE ===
"""${message}

Revision ID: ${up_revision}
Revises: ${down_revision | comma,n}
Create Date: ${create_date}

"""
from alembic import op
import sqlalchemy as sa
${imports if imports else ""}

# revision identifiers, used by Alembic.
revision = ${repr(up_revision)}
down_revision = ${repr(down_revision)}
branch_labels = ${repr(branch_labels)}
depends_on = ${repr(depends_on)}


def upgrade():
    ${upgrades if upgrades else "pass"}


def downgrade():
    ${downgrades if downgrades else "pass"}

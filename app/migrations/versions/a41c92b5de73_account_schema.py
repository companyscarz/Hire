"""Add account security schema."""
from alembic import op
import sqlalchemy as sa

revision = "a41c92b5de73"
down_revision = "52a0594f7a52"
branch_labels = None
depends_on = None


def upgrade():
    op.add_column("hc_users", sa.Column("session_version", sa.Integer(), nullable=False, server_default="0"))
    op.alter_column("hc_users", "session_version", server_default=None)
    op.create_table(
        "hc_account_tokens",
        sa.Column("id", sa.String(36), primary_key=True),
        sa.Column("user_id", sa.String(36), sa.ForeignKey("hc_users.id", ondelete="CASCADE"), nullable=False),
        sa.Column("purpose", sa.String(24), nullable=False),
        sa.Column("token_hash", sa.String(64), nullable=False),
        sa.Column("expires_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("used_at", sa.DateTime(timezone=True)),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.CheckConstraint("purpose IN ('verify_email', 'reset_password')", name="ck_hc_account_token_purpose"),
    )
    op.create_index("ix_hc_account_tokens_user_id", "hc_account_tokens", ["user_id"])
    op.create_index("ix_hc_account_tokens_token_hash", "hc_account_tokens", ["token_hash"], unique=True)
    op.create_index("ix_hc_account_tokens_expires_at", "hc_account_tokens", ["expires_at"])


def downgrade():
    op.drop_index("ix_hc_account_tokens_expires_at", table_name="hc_account_tokens")
    op.drop_index("ix_hc_account_tokens_token_hash", table_name="hc_account_tokens")
    op.drop_index("ix_hc_account_tokens_user_id", table_name="hc_account_tokens")
    op.drop_table("hc_account_tokens")
    op.drop_column("hc_users", "session_version")

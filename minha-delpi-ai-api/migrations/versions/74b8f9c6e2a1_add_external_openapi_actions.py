"""add external openapi actions

Revision ID: 74b8f9c6e2a1
Revises: cc5430afe5fb
Create Date: 2026-05-11 21:30:00.000000

"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql


revision = "74b8f9c6e2a1"
down_revision = "cc5430afe5fb"
branch_labels = None
depends_on = None


def upgrade():
    op.create_table(
        "ai_external_action_providers",
        sa.Column("id", sa.UUID(), nullable=False),
        sa.Column("provider_key", sa.String(length=80), nullable=False),
        sa.Column("name", sa.String(length=150), nullable=False),
        sa.Column("provider_type", sa.String(length=20), nullable=False),
        sa.Column("base_url", sa.Text(), nullable=False),
        sa.Column("openapi_url", sa.Text(), nullable=True),
        sa.Column("auth_mode", sa.String(length=40), nullable=False),
        sa.Column("auth_config", postgresql.JSONB(astext_type=sa.Text()), nullable=True),
        sa.Column("enabled", sa.Boolean(), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("provider_key"),
    )
    with op.batch_alter_table("ai_external_action_providers", schema=None) as batch_op:
        batch_op.create_index(batch_op.f("ix_ai_external_action_providers_created_at"), ["created_at"], unique=False)
        batch_op.create_index(batch_op.f("ix_ai_external_action_providers_enabled"), ["enabled"], unique=False)
        batch_op.create_index(batch_op.f("ix_ai_external_action_providers_provider_key"), ["provider_key"], unique=False)
        batch_op.create_index(batch_op.f("ix_ai_external_action_providers_provider_type"), ["provider_type"], unique=False)

    op.create_table(
        "ai_external_action_schemas",
        sa.Column("id", sa.UUID(), nullable=False),
        sa.Column("provider_id", sa.UUID(), nullable=False),
        sa.Column("schema_json", postgresql.JSONB(astext_type=sa.Text()), nullable=False),
        sa.Column("schema_hash", sa.String(length=128), nullable=False),
        sa.Column("source_type", sa.String(length=20), nullable=False),
        sa.Column("source_url", sa.Text(), nullable=True),
        sa.Column("imported_at", sa.DateTime(timezone=True), nullable=False),
        sa.ForeignKeyConstraint(["provider_id"], ["ai_external_action_providers.id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("id"),
    )
    with op.batch_alter_table("ai_external_action_schemas", schema=None) as batch_op:
        batch_op.create_index(batch_op.f("ix_ai_external_action_schemas_imported_at"), ["imported_at"], unique=False)
        batch_op.create_index(batch_op.f("ix_ai_external_action_schemas_provider_id"), ["provider_id"], unique=False)
        batch_op.create_index(batch_op.f("ix_ai_external_action_schemas_schema_hash"), ["schema_hash"], unique=False)

    op.create_table(
        "ai_external_actions",
        sa.Column("id", sa.UUID(), nullable=False),
        sa.Column("provider_id", sa.UUID(), nullable=False),
        sa.Column("action_id", sa.String(length=220), nullable=False),
        sa.Column("operation_id", sa.String(length=180), nullable=True),
        sa.Column("method", sa.String(length=10), nullable=False),
        sa.Column("path", sa.Text(), nullable=False),
        sa.Column("summary", sa.Text(), nullable=True),
        sa.Column("description", sa.Text(), nullable=True),
        sa.Column("tags", postgresql.JSONB(astext_type=sa.Text()), nullable=True),
        sa.Column("parameters_schema", postgresql.JSONB(astext_type=sa.Text()), nullable=True),
        sa.Column("request_body_schema", postgresql.JSONB(astext_type=sa.Text()), nullable=True),
        sa.Column("response_schema", postgresql.JSONB(astext_type=sa.Text()), nullable=True),
        sa.Column("sensitivity", sa.String(length=30), nullable=False),
        sa.Column("enabled", sa.Boolean(), nullable=False),
        sa.Column("deprecated", sa.Boolean(), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False),
        sa.ForeignKeyConstraint(["provider_id"], ["ai_external_action_providers.id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("action_id"),
    )
    with op.batch_alter_table("ai_external_actions", schema=None) as batch_op:
        batch_op.create_index(batch_op.f("ix_ai_external_actions_action_id"), ["action_id"], unique=False)
        batch_op.create_index(batch_op.f("ix_ai_external_actions_created_at"), ["created_at"], unique=False)
        batch_op.create_index(batch_op.f("ix_ai_external_actions_deprecated"), ["deprecated"], unique=False)
        batch_op.create_index(batch_op.f("ix_ai_external_actions_enabled"), ["enabled"], unique=False)
        batch_op.create_index(batch_op.f("ix_ai_external_actions_method"), ["method"], unique=False)
        batch_op.create_index(batch_op.f("ix_ai_external_actions_operation_id"), ["operation_id"], unique=False)
        batch_op.create_index(batch_op.f("ix_ai_external_actions_provider_id"), ["provider_id"], unique=False)
        batch_op.create_index(batch_op.f("ix_ai_external_actions_sensitivity"), ["sensitivity"], unique=False)


def downgrade():
    with op.batch_alter_table("ai_external_actions", schema=None) as batch_op:
        batch_op.drop_index(batch_op.f("ix_ai_external_actions_sensitivity"))
        batch_op.drop_index(batch_op.f("ix_ai_external_actions_provider_id"))
        batch_op.drop_index(batch_op.f("ix_ai_external_actions_operation_id"))
        batch_op.drop_index(batch_op.f("ix_ai_external_actions_method"))
        batch_op.drop_index(batch_op.f("ix_ai_external_actions_enabled"))
        batch_op.drop_index(batch_op.f("ix_ai_external_actions_deprecated"))
        batch_op.drop_index(batch_op.f("ix_ai_external_actions_created_at"))
        batch_op.drop_index(batch_op.f("ix_ai_external_actions_action_id"))

    op.drop_table("ai_external_actions")

    with op.batch_alter_table("ai_external_action_schemas", schema=None) as batch_op:
        batch_op.drop_index(batch_op.f("ix_ai_external_action_schemas_schema_hash"))
        batch_op.drop_index(batch_op.f("ix_ai_external_action_schemas_provider_id"))
        batch_op.drop_index(batch_op.f("ix_ai_external_action_schemas_imported_at"))

    op.drop_table("ai_external_action_schemas")

    with op.batch_alter_table("ai_external_action_providers", schema=None) as batch_op:
        batch_op.drop_index(batch_op.f("ix_ai_external_action_providers_provider_type"))
        batch_op.drop_index(batch_op.f("ix_ai_external_action_providers_provider_key"))
        batch_op.drop_index(batch_op.f("ix_ai_external_action_providers_enabled"))
        batch_op.drop_index(batch_op.f("ix_ai_external_action_providers_created_at"))

    op.drop_table("ai_external_action_providers")

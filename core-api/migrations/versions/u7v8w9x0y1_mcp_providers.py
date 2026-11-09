"""mcp_providers governed registry

Revision ID: u7v8w9x0y1
Revises: t6u7v8w9x0
Create Date: 2026-11-09

Core-owned MCP provider registration table + base permissions.
Does not store tokens, secrets, or tools/list catalogs.
"""

from alembic import op
import sqlalchemy as sa

revision = "u7v8w9x0y1"
down_revision = "t6u7v8w9x0"
branch_labels = None
depends_on = None


def upgrade():
    op.create_table(
        "mcp_providers",
        sa.Column("provider_ref", sa.String(length=64), nullable=False),
        sa.Column("display_name", sa.String(length=150), nullable=False),
        sa.Column("protocol", sa.String(length=32), nullable=False, server_default="MCP"),
        sa.Column("endpoint_ref", sa.Text(), nullable=False),
        sa.Column("owner_ref", sa.String(length=150), nullable=False),
        sa.Column("auth_strategy_ref", sa.String(length=64), nullable=False),
        sa.Column("resource_client_id", sa.String(length=128), nullable=True),
        sa.Column("audience_scope", sa.String(length=128), nullable=True),
        sa.Column("resource_audience", sa.Text(), nullable=True),
        sa.Column("approval_status", sa.String(length=32), nullable=False),
        sa.Column("enabled", sa.Boolean(), nullable=False, server_default=sa.text("false")),
        sa.Column("risk_tier", sa.String(length=32), nullable=True),
        sa.Column("policy_ref", sa.String(length=128), nullable=True),
        sa.Column("version", sa.Integer(), nullable=False, server_default="1"),
        sa.Column("approved_by_user_id", sa.Uuid(), nullable=True),
        sa.Column("approved_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("last_validated_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            server_default=sa.func.now(),
            nullable=False,
        ),
        sa.Column(
            "updated_at",
            sa.DateTime(timezone=True),
            server_default=sa.func.now(),
            nullable=False,
        ),
        sa.PrimaryKeyConstraint("provider_ref"),
        sa.ForeignKeyConstraint(
            ["approved_by_user_id"],
            ["users.id"],
            ondelete="SET NULL",
        ),
        sa.CheckConstraint("protocol = 'MCP'", name="ck_mcp_providers_protocol_mcp"),
        sa.CheckConstraint("version >= 1", name="ck_mcp_providers_version_positive"),
    )
    op.create_index(
        "ix_mcp_providers_approval_status",
        "mcp_providers",
        ["approval_status"],
    )
    op.create_index(
        "ix_mcp_providers_enabled",
        "mcp_providers",
        ["enabled"],
    )

    conn = op.get_bind()
    for code, name, description in (
        (
            "mcp_providers.view",
            "Visualizar provedores MCP",
            "Listar e consultar registros governados de servidores MCP",
        ),
        (
            "mcp_providers.manage",
            "Gerenciar provedores MCP",
            "Registrar, aprovar, habilitar, desabilitar e revogar provedores MCP",
        ),
    ):
        conn.execute(
            sa.text(
                """
                INSERT INTO permissions (id, code, name, description, module, created_at, updated_at)
                SELECT gen_random_uuid(), :code, :name, :description, 'system', NOW(), NOW()
                WHERE NOT EXISTS (
                    SELECT 1 FROM permissions WHERE code = :code
                )
                """
            ),
            {"code": code, "name": name, "description": description},
        )


def downgrade():
    op.drop_index("ix_mcp_providers_enabled", table_name="mcp_providers")
    op.drop_index("ix_mcp_providers_approval_status", table_name="mcp_providers")
    op.drop_table("mcp_providers")
    # Permissions are additive; leave codes in place on downgrade to avoid
    # breaking role bindings. Seed upsert remains the source of truth.

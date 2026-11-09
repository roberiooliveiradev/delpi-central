"""Persisted MCP provider registration — Core PostgreSQL ownership.

No tokens, secrets, or tools/list catalogs are stored here.
"""

from __future__ import annotations

from app.extensions.db import db
from app.infrastructure.db.base_model import TimestampMixin


class McpProvider(db.Model, TimestampMixin):
    __tablename__ = "mcp_providers"

    provider_ref = db.Column(db.String(64), primary_key=True)
    display_name = db.Column(db.String(150), nullable=False)
    protocol = db.Column(db.String(32), nullable=False, default="MCP")
    endpoint_ref = db.Column(db.Text, nullable=False)
    owner_ref = db.Column(db.String(150), nullable=False)
    auth_strategy_ref = db.Column(db.String(64), nullable=False)
    resource_client_id = db.Column(db.String(128), nullable=True)
    audience_scope = db.Column(db.String(128), nullable=True)
    resource_audience = db.Column(db.Text, nullable=True)
    approval_status = db.Column(db.String(32), nullable=False, index=True)
    enabled = db.Column(db.Boolean, nullable=False, default=False)
    risk_tier = db.Column(db.String(32), nullable=True)
    policy_ref = db.Column(db.String(128), nullable=True)
    version = db.Column(db.Integer, nullable=False, default=1)
    approved_by_user_id = db.Column(
        db.Uuid,
        db.ForeignKey("users.id", ondelete="SET NULL"),
        nullable=True,
    )
    approved_at = db.Column(db.DateTime(timezone=True), nullable=True)
    last_validated_at = db.Column(db.DateTime(timezone=True), nullable=True)

    __table_args__ = (
        db.CheckConstraint(
            "protocol = 'MCP'",
            name="ck_mcp_providers_protocol_mcp",
        ),
        db.CheckConstraint(
            "version >= 1",
            name="ck_mcp_providers_version_positive",
        ),
    )

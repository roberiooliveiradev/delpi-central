import uuid
from datetime import datetime, timezone

from sqlalchemy.dialects.postgresql import UUID

from app.extensions.db import db


class AiChatAgentActionProviderModel(db.Model):
    __tablename__ = "ai_chat_agent_action_providers"

    id = db.Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    agent_id = db.Column(
        UUID(as_uuid=True),
        db.ForeignKey("ai_chat_agents.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    provider_key = db.Column(db.String(120), nullable=False, index=True)
    enabled = db.Column(db.Boolean, nullable=False, default=True, server_default="true", index=True)
    allow_read = db.Column(db.Boolean, nullable=False, default=True, server_default="true")
    allow_write = db.Column(db.Boolean, nullable=False, default=False, server_default="false")
    allow_admin = db.Column(db.Boolean, nullable=False, default=False, server_default="false")
    requires_confirmation_for_write = db.Column(
        db.Boolean,
        nullable=False,
        default=True,
        server_default="true",
    )
    created_at = db.Column(
        db.DateTime(timezone=True),
        nullable=False,
        default=lambda: datetime.now(timezone.utc),
    )
    updated_at = db.Column(
        db.DateTime(timezone=True),
        nullable=False,
        default=lambda: datetime.now(timezone.utc),
        onupdate=lambda: datetime.now(timezone.utc),
    )

    __table_args__ = (
        db.UniqueConstraint(
            "agent_id",
            "provider_key",
            name="uq_ai_chat_agent_action_providers_agent_provider",
        ),
    )

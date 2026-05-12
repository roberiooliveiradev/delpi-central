import uuid
from datetime import datetime, timezone

from sqlalchemy.dialects.postgresql import UUID

from app.extensions.db import db


class AiChatAgentActionModel(db.Model):
    __tablename__ = "ai_chat_agent_actions"

    id = db.Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    agent_id = db.Column(
        UUID(as_uuid=True),
        db.ForeignKey("ai_chat_agents.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    provider_key = db.Column(db.String(120), nullable=False)
    action_id = db.Column(db.String(300), nullable=False)
    enabled = db.Column(db.Boolean, nullable=False, default=True, server_default="true", index=True)
    sensitivity = db.Column(db.String(40), nullable=False, default="read", server_default="read")
    requires_confirmation = db.Column(db.Boolean, nullable=False, default=False, server_default="false")
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

import uuid
from datetime import datetime, timezone

from sqlalchemy.dialects.postgresql import UUID

from app.extensions.db import db


class AiChatAgentShareModel(db.Model):
    __tablename__ = "ai_chat_agent_shares"

    id = db.Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    agent_id = db.Column(
        UUID(as_uuid=True),
        db.ForeignKey("ai_chat_agents.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    target_user_id = db.Column(UUID(as_uuid=True), nullable=False, index=True)
    role = db.Column(db.String(20), nullable=False, default="viewer", server_default="viewer")
    created_at = db.Column(
        db.DateTime(timezone=True),
        nullable=False,
        default=lambda: datetime.now(timezone.utc),
    )

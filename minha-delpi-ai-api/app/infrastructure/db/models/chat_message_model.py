import uuid
from datetime import datetime, timezone

from sqlalchemy.dialects.postgresql import JSONB, UUID

from app.extensions.db import db


class AiChatMessageModel(db.Model):
    __tablename__ = "ai_chat_messages"

    id = db.Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    session_id = db.Column(
        UUID(as_uuid=True),
        db.ForeignKey("ai_chat_sessions.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    role = db.Column(db.String(20), nullable=False, index=True)
    content = db.Column(db.Text, nullable=False)
    message_metadata = db.Column("metadata", JSONB, nullable=True)
    created_at = db.Column(
        db.DateTime(timezone=True),
        nullable=False,
        default=lambda: datetime.now(timezone.utc),
        index=True,
    )
    parent_message_id = db.Column(
        UUID(as_uuid=True),
        db.ForeignKey("ai_chat_messages.id", ondelete="SET NULL"),
        nullable=True,
        index=True,
    )

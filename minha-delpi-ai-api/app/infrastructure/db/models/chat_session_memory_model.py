import uuid
from datetime import datetime, timezone

from sqlalchemy.dialects.postgresql import JSONB, UUID

from app.extensions.db import db


class AiChatSessionMemoryModel(db.Model):
    __tablename__ = "ai_chat_session_memory"

    id = db.Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    session_id = db.Column(
        UUID(as_uuid=True),
        db.ForeignKey("ai_chat_sessions.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    memory_type = db.Column(db.String(32), nullable=False)
    key = db.Column(db.String(64), nullable=False)
    value_json = db.Column(JSONB, nullable=False)
    source_message_id = db.Column(
        UUID(as_uuid=True),
        db.ForeignKey("ai_chat_messages.id", ondelete="SET NULL"),
        nullable=True,
        index=True,
    )
    scope = db.Column(db.String(16), nullable=False, default="session", server_default="session")
    confidence = db.Column(db.Numeric(4, 3), nullable=True)
    active = db.Column(db.Boolean, nullable=False, default=True, server_default="true")
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
    expires_at = db.Column(db.DateTime(timezone=True), nullable=True)

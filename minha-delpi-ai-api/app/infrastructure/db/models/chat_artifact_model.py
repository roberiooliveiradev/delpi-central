import uuid
from datetime import datetime, timezone

from sqlalchemy.dialects.postgresql import JSONB, UUID

from app.extensions.db import db


class AiChatArtifactModel(db.Model):
    __tablename__ = "ai_chat_artifacts"

    id = db.Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    session_id = db.Column(
        UUID(as_uuid=True),
        db.ForeignKey("ai_chat_sessions.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    message_id = db.Column(
        UUID(as_uuid=True),
        db.ForeignKey("ai_chat_messages.id", ondelete="SET NULL"),
        nullable=True,
        index=True,
    )
    user_id = db.Column(UUID(as_uuid=True), nullable=False, index=True)
    type = db.Column(db.String(40), nullable=False, index=True)
    title = db.Column(db.String(180), nullable=False)
    content = db.Column(db.Text, nullable=False)
    artifact_metadata = db.Column("metadata", JSONB, nullable=True)
    created_at = db.Column(
        db.DateTime(timezone=True),
        nullable=False,
        default=lambda: datetime.now(timezone.utc),
        index=True,
    )
    updated_at = db.Column(
        db.DateTime(timezone=True),
        nullable=False,
        default=lambda: datetime.now(timezone.utc),
        onupdate=lambda: datetime.now(timezone.utc),
    )

import uuid
from datetime import datetime, timezone

from sqlalchemy.dialects.postgresql import JSONB, UUID

from app.extensions.db import db


class AiChatAttachmentModel(db.Model):
    __tablename__ = "ai_chat_attachments"

    id = db.Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    user_id = db.Column(UUID(as_uuid=True), nullable=False, index=True)
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
    project_id = db.Column(
        UUID(as_uuid=True),
        db.ForeignKey("ai_chat_projects.id", ondelete="SET NULL"),
        nullable=True,
        index=True,
    )
    agent_id = db.Column(
        UUID(as_uuid=True),
        db.ForeignKey("ai_chat_agents.id", ondelete="SET NULL"),
        nullable=True,
        index=True,
    )
    filename = db.Column(db.String(255), nullable=False)
    original_filename = db.Column(db.String(255), nullable=False)
    content_type = db.Column(db.String(160), nullable=True)
    size_bytes = db.Column(db.Integer, nullable=False)
    storage_path = db.Column(db.String(600), nullable=False)
    status = db.Column(db.String(40), nullable=False, default="uploaded", server_default="uploaded", index=True)
    attachment_metadata = db.Column("metadata", JSONB, nullable=True)
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

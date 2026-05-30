import uuid
from datetime import datetime, timezone

from sqlalchemy.dialects.postgresql import JSONB, UUID

from app.extensions.db import db


class AiChatProjectModel(db.Model):
    __tablename__ = "ai_chat_projects"

    id = db.Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    user_id = db.Column(UUID(as_uuid=True), nullable=False, index=True)
    name = db.Column(db.String(120), nullable=False)
    description = db.Column(db.String(500), nullable=True)
    instructions = db.Column(db.Text, nullable=True)
    default_agent_id = db.Column(
        UUID(as_uuid=True),
        db.ForeignKey("ai_chat_agents.id", ondelete="SET NULL"),
        nullable=True,
        index=True,
    )
    visibility = db.Column(db.String(20), nullable=False, default="private", server_default="private", index=True)
    icon = db.Column(db.String(60), nullable=True)
    color = db.Column(db.String(40), nullable=True)
    archived_at = db.Column(db.DateTime(timezone=True), nullable=True, index=True)
    project_metadata = db.Column("metadata", JSONB, nullable=True)
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

import uuid
from datetime import datetime, timezone

from sqlalchemy.dialects.postgresql import JSONB, UUID

from app.extensions.db import db


class AiChatAgentModel(db.Model):
    __tablename__ = "ai_chat_agents"

    id = db.Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    name = db.Column(db.String(120), nullable=False)
    description = db.Column(db.String(800), nullable=True)
    system_prompt = db.Column(db.Text, nullable=True)
    owner_user_id = db.Column(UUID(as_uuid=True), nullable=True, index=True)
    visibility = db.Column(db.String(20), nullable=False, default="system", server_default="system", index=True)
    category = db.Column(db.String(80), nullable=True)
    icon = db.Column(db.String(60), nullable=True)
    response_style = db.Column(db.String(40), nullable=True)
    max_tool_calls = db.Column(db.Integer, nullable=False, default=5, server_default="5")
    requires_confirmation_for_write = db.Column(db.Boolean, nullable=False, default=True, server_default="true")
    enabled = db.Column(db.Boolean, nullable=False, default=True, server_default="true", index=True)
    published_version = db.Column(db.Integer(), nullable=False, default=0, server_default="0")
    published_at = db.Column(db.DateTime(timezone=True), nullable=True)
    published_config = db.Column(JSONB, nullable=True)
    agent_metadata = db.Column("metadata", JSONB, nullable=True)
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

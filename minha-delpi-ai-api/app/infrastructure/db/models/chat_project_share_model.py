import uuid
from datetime import datetime, timezone

from sqlalchemy.dialects.postgresql import UUID

from app.extensions.db import db


class AiChatProjectShareModel(db.Model):
    __tablename__ = "ai_chat_project_shares"

    id = db.Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    project_id = db.Column(
        UUID(as_uuid=True),
        db.ForeignKey("ai_chat_projects.id", ondelete="CASCADE"),
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

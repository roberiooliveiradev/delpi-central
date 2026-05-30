from datetime import datetime, timezone

from sqlalchemy.dialects.postgresql import UUID

from app.extensions.db import db


class AiChatMessageFeedbackModel(db.Model):
    __tablename__ = "ai_chat_message_feedback"

    id = db.Column(db.BigInteger, primary_key=True, autoincrement=True)
    message_id = db.Column(
        UUID(as_uuid=True),
        db.ForeignKey("ai_chat_messages.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    user_id = db.Column(UUID(as_uuid=True), nullable=False, index=True)
    rating = db.Column(db.SmallInteger, nullable=False)
    reason = db.Column(db.String(64), nullable=True)
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

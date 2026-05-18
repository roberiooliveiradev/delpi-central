from datetime import datetime, timezone

from sqlalchemy.dialects.postgresql import JSONB, UUID

from app.extensions.db import db


class AiResponseEvaluationModel(db.Model):
    __tablename__ = "ai_response_evaluations"

    id = db.Column(db.BigInteger, primary_key=True, autoincrement=True)
    message_id = db.Column(
        UUID(as_uuid=True),
        db.ForeignKey("ai_chat_messages.id", ondelete="CASCADE"),
        nullable=False,
        unique=True,
    )
    session_id = db.Column(
        UUID(as_uuid=True),
        db.ForeignKey("ai_chat_sessions.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    evaluator_user_id = db.Column(UUID(as_uuid=True), nullable=False, index=True)
    score = db.Column(db.Integer, nullable=False)
    verdict = db.Column(db.String(20), nullable=False, index=True)
    comment = db.Column(db.Text, nullable=True)
    suggestions = db.Column(JSONB, nullable=True)
    evaluation_metadata = db.Column("evaluation_metadata", JSONB, nullable=True)
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

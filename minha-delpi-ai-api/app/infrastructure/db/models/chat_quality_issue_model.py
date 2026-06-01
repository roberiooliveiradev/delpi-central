from datetime import datetime, timezone

from sqlalchemy.dialects.postgresql import JSONB

from app.extensions.db import db


class AiChatQualityIssueModel(db.Model):
    __tablename__ = "ai_chat_quality_issues"

    id = db.Column(db.BigInteger, primary_key=True, autoincrement=True)
    code = db.Column(db.String(96), nullable=False, index=True)
    title = db.Column(db.String(240), nullable=False)
    description = db.Column(db.Text, nullable=False)
    status = db.Column(db.String(24), nullable=False, default="open", index=True)
    source = db.Column(db.String(32), nullable=False, default="feedback_auto")
    issue_metadata = db.Column(JSONB, nullable=True)
    external_url = db.Column(db.String(512), nullable=True)
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
    resolved_at = db.Column(db.DateTime(timezone=True), nullable=True)

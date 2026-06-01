from datetime import datetime, timezone

from sqlalchemy.dialects.postgresql import JSONB

from app.extensions.db import db


class AiChatQualityReportModel(db.Model):
    __tablename__ = "ai_chat_quality_reports"

    id = db.Column(db.BigInteger, primary_key=True, autoincrement=True)
    report_type = db.Column(db.String(32), nullable=False, default="weekly")
    period_start = db.Column(db.DateTime(timezone=True), nullable=False, index=True)
    period_end = db.Column(db.DateTime(timezone=True), nullable=False, index=True)
    summary_json = db.Column(JSONB, nullable=False)
    markdown = db.Column(db.Text, nullable=False)
    created_at = db.Column(
        db.DateTime(timezone=True),
        nullable=False,
        default=lambda: datetime.now(timezone.utc),
        index=True,
    )

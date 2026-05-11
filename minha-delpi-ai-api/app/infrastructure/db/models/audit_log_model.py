from datetime import datetime, timezone

from sqlalchemy.dialects.postgresql import JSONB, UUID

from app.extensions.db import db


class AiAuditLogModel(db.Model):
    __tablename__ = "ai_audit_logs"

    id = db.Column(db.BigInteger, primary_key=True, autoincrement=True)
    user_id = db.Column(UUID(as_uuid=True), nullable=True, index=True)
    action = db.Column(db.String(100), nullable=False, index=True)
    prompt_hash = db.Column(db.String(128), nullable=True, index=True)
    context = db.Column(db.String(50), nullable=True, index=True)
    tool_calls = db.Column(JSONB, nullable=True)
    audit_metadata = db.Column("metadata", JSONB, nullable=True)
    created_at = db.Column(
        db.DateTime(timezone=True),
        nullable=False,
        default=lambda: datetime.now(timezone.utc),
        index=True,
    )

from datetime import datetime, timezone

from sqlalchemy.dialects.postgresql import JSONB, UUID

from app.extensions.db import db


class AiFineTuningSampleModel(db.Model):
    __tablename__ = "ai_fine_tuning_samples"

    id = db.Column(db.BigInteger, primary_key=True, autoincrement=True)
    dataset_id = db.Column(db.BigInteger, db.ForeignKey("ai_fine_tuning_datasets.id", ondelete="SET NULL"))
    category = db.Column(db.String(32), nullable=False, default="routing", server_default="routing")
    source = db.Column(db.String(48), nullable=False)
    source_ref = db.Column(db.String(120), nullable=True)
    status = db.Column(db.String(24), nullable=False, default="captured", server_default="captured")
    messages_json = db.Column(JSONB, nullable=False)
    intent_label = db.Column(db.String(80), nullable=True)
    quality_score = db.Column(db.Numeric(4, 3), nullable=True)
    anonymized = db.Column(db.Boolean, nullable=False, default=False, server_default="false")
    risk_level = db.Column(db.String(16), nullable=True)
    reviewer_id = db.Column(UUID(as_uuid=True), nullable=True)
    created_by = db.Column(UUID(as_uuid=True), nullable=True)
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

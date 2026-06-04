from datetime import datetime, timezone

from sqlalchemy.dialects.postgresql import JSONB, UUID

from app.extensions.db import db


class AiFineTuningDatasetModel(db.Model):
    __tablename__ = "ai_fine_tuning_datasets"

    id = db.Column(db.BigInteger, primary_key=True, autoincrement=True)
    name = db.Column(db.String(120), nullable=False)
    description = db.Column(db.Text, nullable=True)
    status = db.Column(db.String(24), nullable=False, default="draft", server_default="draft")
    target_model = db.Column(
        db.String(64), nullable=False, default="intent_classifier", server_default="intent_classifier"
    )
    dataset_metadata = db.Column("dataset_metadata", JSONB, nullable=True)
    created_by = db.Column(UUID(as_uuid=True), nullable=True)
    approved_by = db.Column(UUID(as_uuid=True), nullable=True)
    approved_at = db.Column(db.DateTime(timezone=True), nullable=True)
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

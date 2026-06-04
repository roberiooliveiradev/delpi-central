from datetime import datetime, timezone

from sqlalchemy.dialects.postgresql import JSONB, UUID

from app.extensions.db import db


class AiFineTuningRunModel(db.Model):
    __tablename__ = "ai_fine_tuning_runs"

    id = db.Column(db.BigInteger, primary_key=True, autoincrement=True)
    dataset_id = db.Column(
        db.BigInteger,
        db.ForeignKey("ai_fine_tuning_datasets.id", ondelete="CASCADE"),
        nullable=False,
    )
    status = db.Column(db.String(24), nullable=False, default="pending", server_default="pending")
    target_model = db.Column(db.String(64), nullable=False)
    export_format = db.Column(db.String(16), nullable=False, default="jsonl", server_default="jsonl")
    export_stats = db.Column(JSONB, nullable=True)
    metrics = db.Column(JSONB, nullable=True)
    error_message = db.Column(db.Text, nullable=True)
    active_deploy = db.Column(db.Boolean, nullable=False, default=False, server_default="false")
    created_by = db.Column(UUID(as_uuid=True), nullable=True)
    started_at = db.Column(db.DateTime(timezone=True), nullable=True)
    completed_at = db.Column(db.DateTime(timezone=True), nullable=True)
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

import uuid
from datetime import datetime, timezone

from sqlalchemy.dialects.postgresql import JSONB, UUID

from app.extensions.db import db


class ExternalActionImportJobModel(db.Model):
    __tablename__ = "ai_external_action_import_jobs"

    id = db.Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    provider_key = db.Column(db.String(120), nullable=False, index=True)
    agent_id = db.Column(UUID(as_uuid=True), nullable=True, index=True)
    user_id = db.Column(UUID(as_uuid=True), nullable=True, index=True)
    status = db.Column(db.String(20), nullable=False, default="queued", index=True)
    phase = db.Column(db.String(40), nullable=False, default="queued")
    progress_done = db.Column(db.Integer, nullable=False, default=0)
    progress_total = db.Column(db.Integer, nullable=False, default=0)
    result = db.Column(JSONB, nullable=True)
    error = db.Column(db.Text, nullable=True)
    started_at = db.Column(
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

import uuid
from datetime import datetime, timezone

from sqlalchemy.dialects.postgresql import JSONB, UUID

from app.extensions.db import db


class AiAdminGuidelineModel(db.Model):
    __tablename__ = "ai_admin_guidelines"

    id = db.Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    title = db.Column(db.String(180), nullable=False)
    description = db.Column(db.Text, nullable=False, default="")
    content = db.Column(db.Text, nullable=False, default="")
    category = db.Column(db.String(40), nullable=False, default="behavior", index=True)
    environment = db.Column(db.String(30), nullable=False, default="global", index=True)
    status = db.Column(db.String(30), nullable=False, default="draft", index=True)
    guideline_metadata = db.Column("metadata", JSONB, nullable=True)
    created_by = db.Column(db.String(120), nullable=True, index=True)
    updated_by = db.Column(db.String(120), nullable=True)
    published_at = db.Column(db.DateTime(timezone=True), nullable=True)
    archived_at = db.Column(db.DateTime(timezone=True), nullable=True)
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

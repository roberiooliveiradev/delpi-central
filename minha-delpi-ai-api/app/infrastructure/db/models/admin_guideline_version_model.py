import uuid
from datetime import datetime, timezone

from sqlalchemy.dialects.postgresql import JSONB, UUID

from app.extensions.db import db


class AiAdminGuidelineVersionModel(db.Model):
    __tablename__ = "ai_admin_guideline_versions"

    id = db.Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    guideline_id = db.Column(
        UUID(as_uuid=True),
        db.ForeignKey("ai_admin_guidelines.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    version = db.Column(db.Integer, nullable=False)
    title = db.Column(db.String(180), nullable=False)
    description = db.Column(db.Text, nullable=False, default="")
    content = db.Column(db.Text, nullable=False, default="")
    category = db.Column(db.String(40), nullable=False, default="behavior")
    status = db.Column(db.String(30), nullable=False, default="draft")
    event = db.Column(db.String(40), nullable=False, default="saved", index=True)
    guideline_metadata = db.Column("metadata", JSONB, nullable=True)
    created_by = db.Column(db.String(120), nullable=True, index=True)
    created_at = db.Column(
        db.DateTime(timezone=True),
        nullable=False,
        default=lambda: datetime.now(timezone.utc),
        index=True,
    )

    __table_args__ = (
        db.UniqueConstraint(
            "guideline_id",
            "version",
            name="uq_ai_admin_guideline_versions_guideline_version",
        ),
    )

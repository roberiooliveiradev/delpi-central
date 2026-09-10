from datetime import datetime, timezone

from app.extensions.db import db


class PresentationFieldLabelCacheModel(db.Model):
    """Runtime cache of LLM-generated table header labels. Not human-editable vocabulary."""

    __tablename__ = "presentation_field_label_cache"

    field_key = db.Column(db.String(160), primary_key=True)
    label = db.Column(db.String(160), nullable=False)
    source = db.Column(
        db.String(48),
        nullable=False,
        default="LLM_LOCALIZATION",
        server_default="LLM_LOCALIZATION",
    )
    updated_at = db.Column(
        db.DateTime(timezone=True),
        nullable=False,
        default=lambda: datetime.now(timezone.utc),
        onupdate=lambda: datetime.now(timezone.utc),
    )

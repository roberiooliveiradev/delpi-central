from datetime import datetime, timezone

from app.extensions.db import db


class ActionDisplayLabelCacheModel(db.Model):
    """Runtime cache of LLM-localized action display labels (external providers)."""

    __tablename__ = "action_display_label_cache"

    cache_key = db.Column(db.String(64), primary_key=True)
    label = db.Column(db.String(240), nullable=False)
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

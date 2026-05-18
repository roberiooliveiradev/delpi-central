from datetime import datetime, timezone

from sqlalchemy.dialects.postgresql import JSONB

from app.extensions.db import db


class AiAdminRuntimeSettingsModel(db.Model):
    __tablename__ = "ai_admin_runtime_settings"

    key = db.Column(db.String(100), primary_key=True)
    value = db.Column(JSONB, nullable=False)
    updated_at = db.Column(
        db.DateTime(timezone=True),
        nullable=False,
        default=lambda: datetime.now(timezone.utc),
        onupdate=lambda: datetime.now(timezone.utc),
    )

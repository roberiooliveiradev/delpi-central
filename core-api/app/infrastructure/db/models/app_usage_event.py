# app/infrastructure/db/models/app_usage_event.py

import uuid

from app.extensions.db import db
from app.infrastructure.db.base_model import TimestampMixin


class AppUsageEvent(db.Model, TimestampMixin):
    __tablename__ = "app_usage_events"

    id = db.Column(db.Uuid, primary_key=True, default=uuid.uuid4)
    user_id = db.Column(
        db.Uuid,
        db.ForeignKey("users.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    app_id = db.Column(
        db.String(50),
        db.ForeignKey("apps.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    route_path = db.Column(db.String(255), nullable=True)
    opened_at = db.Column(db.DateTime, nullable=False, index=True)

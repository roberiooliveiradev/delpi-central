# app/infrastructure/db/models/user_notification_preference.py

from datetime import datetime

from app.extensions.db import db


class UserNotificationPreference(db.Model):
    __tablename__ = "user_notification_preferences"

    user_id = db.Column(
        db.Uuid,
        db.ForeignKey("users.id", ondelete="CASCADE"),
        primary_key=True,
    )
    muted_categories = db.Column(db.JSON, nullable=False, default=list)
    updated_at = db.Column(db.DateTime, nullable=False, default=datetime.utcnow, onupdate=datetime.utcnow)

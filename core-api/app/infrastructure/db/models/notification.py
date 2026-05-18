# app/infrastructure/db/models/notification.py

import uuid
from datetime import datetime

from app.extensions.db import db


class Notification(db.Model):
    __tablename__ = "notifications"

    id = db.Column(db.UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)

    user_id = db.Column(
        db.UUID(as_uuid=True),
        nullable=False,
        index=True,
    )

    title = db.Column(db.String(120), nullable=True)
    message = db.Column(db.String(500), nullable=False)

    type = db.Column(db.String(40), nullable=False, default="info")
    category = db.Column(db.String(40), nullable=False, default="system")
    presentation = db.Column(db.String(20), nullable=False, default="text")
    html_content = db.Column(db.Text, nullable=True)

    action_type = db.Column(db.String(30), nullable=True)
    action_label = db.Column(db.String(80), nullable=True)
    action_target = db.Column(db.String(500), nullable=True)

    icon = db.Column(db.String(40), nullable=True)
    notification_metadata = db.Column("metadata", db.JSON, nullable=True)
    expires_at = db.Column(db.DateTime, nullable=True)

    is_important = db.Column(db.Boolean, nullable=False, default=False, index=True)
    read_at = db.Column(db.DateTime, nullable=True)
    deleted_at = db.Column(db.DateTime, nullable=True, index=True)
    created_at = db.Column(db.DateTime, nullable=False, default=datetime.utcnow)

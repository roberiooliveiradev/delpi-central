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
        index=True
    )

    title = db.Column(db.String(120), nullable=True)
    message = db.Column(db.String(500), nullable=False)

    type = db.Column(db.String(40), nullable=False, default="info")
    read_at = db.Column(db.DateTime, nullable=True)

    created_at = db.Column(db.DateTime, nullable=False, default=datetime.utcnow)
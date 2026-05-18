# app/infrastructure/db/models/notification_dispatch.py

import uuid
from datetime import datetime

from app.extensions.db import db


class NotificationDispatch(db.Model):
    __tablename__ = "notification_dispatches"

    id = db.Column(db.UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)

    created_by_user_id = db.Column(db.UUID(as_uuid=True), nullable=True, index=True)

    status = db.Column(db.String(20), nullable=False, default="pending", index=True)
    scheduled_at = db.Column(db.DateTime, nullable=True, index=True)
    processed_at = db.Column(db.DateTime, nullable=True)

    broadcast = db.Column(db.Boolean, nullable=False, default=False)
    recipient_count = db.Column(db.Integer, nullable=False, default=0)
    created_count = db.Column(db.Integer, nullable=False, default=0)

    title = db.Column(db.String(120), nullable=True)
    category = db.Column(db.String(40), nullable=False, default="system")
    presentation = db.Column(db.String(20), nullable=False, default="text")
    template_id = db.Column(db.String(80), nullable=True)
    source_app = db.Column(db.String(80), nullable=True)

    payload = db.Column(db.JSON, nullable=False)
    notification_ids = db.Column(db.JSON, nullable=True)
    error_message = db.Column(db.Text, nullable=True)

    created_at = db.Column(db.DateTime, nullable=False, default=datetime.utcnow, index=True)

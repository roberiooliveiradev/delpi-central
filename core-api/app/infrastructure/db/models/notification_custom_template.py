# app/infrastructure/db/models/notification_custom_template.py

import uuid
from datetime import datetime

from app.extensions.db import db


class NotificationCustomTemplate(db.Model):
    __tablename__ = "notification_custom_templates"

    id = db.Column(db.String(80), primary_key=True)
    label = db.Column(db.String(120), nullable=False)
    category = db.Column(db.String(40), nullable=False, default="custom")
    default_type = db.Column(db.String(20), nullable=False, default="info")
    title_template = db.Column(db.String(120), nullable=False)
    message_template = db.Column(db.String(500), nullable=False)
    layout = db.Column(db.JSON, nullable=True)
    required_vars = db.Column(db.JSON, nullable=False, default=list)
    optional_vars = db.Column(db.JSON, nullable=False, default=list)
    recipient_vars = db.Column(db.JSON, nullable=False, default=list)
    active = db.Column(db.Boolean, nullable=False, default=True)
    created_at = db.Column(db.DateTime, nullable=False, default=datetime.utcnow)

    @staticmethod
    def new_id() -> str:
        return f"custom_{uuid.uuid4()}"

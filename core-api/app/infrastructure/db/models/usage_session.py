# app/infrastructure/db/models/usage_session.py

import uuid

from app.extensions.db import db
from app.infrastructure.db.base_model import TimestampMixin


class UsageSession(db.Model, TimestampMixin):
    __tablename__ = "usage_sessions"

    id = db.Column(db.Uuid, primary_key=True, default=uuid.uuid4)
    user_id = db.Column(
        db.Uuid,
        db.ForeignKey("users.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    app_id = db.Column(
        db.String(50),
        db.ForeignKey("apps.id", ondelete="SET NULL"),
        nullable=True,
        index=True,
    )
    route_path = db.Column(db.String(255), nullable=True)
    started_at = db.Column(db.DateTime, nullable=False, index=True)
    ended_at = db.Column(db.DateTime, nullable=False)
    duration_seconds = db.Column(db.Integer, nullable=False)
    source = db.Column(db.String(32), nullable=False)
    socket_session_id = db.Column(db.String(128), nullable=True)

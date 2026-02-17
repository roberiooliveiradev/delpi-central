# app/infrastructure/db/models/audit_log.py

from app.extensions.db import db
from app.infrastructure.db.base_model import TimestampMixin


class AuditLog(db.Model, TimestampMixin):
    __tablename__ = "audit_logs"

    id = db.Column(db.Integer, primary_key=True)

    user_id = db.Column(
        db.Uuid,
        db.ForeignKey("users.id"),
        nullable=True,
        index=True,
    )

    action = db.Column(db.String(100), nullable=False, index=True)

    entity_type = db.Column(db.String(100), nullable=True)
    entity_id = db.Column(db.String(100), nullable=True)

    payload = db.Column(db.JSON, nullable=True)

    ip_address = db.Column(db.String(45), nullable=True)

    user = db.relationship("User")

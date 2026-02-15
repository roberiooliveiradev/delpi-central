# app/infrastructure/db/models/audit_log.py

from app.extensions.db import db
from app.infrastructure.db.base_model import TimestampMixin

class AuditLog(db.Model, TimestampMixin):
    __tablename__ = "audit_logs"

    id = db.Column(db.BigInteger, primary_key=True, autoincrement=True)
    user_id = db.Column(db.Uuid, nullable=True)

    action = db.Column(db.String(100), nullable=False)
    resource_type = db.Column(db.String(100), nullable=False)
    resource_id = db.Column(db.String(100), nullable=True)

    metadata_json = db.Column("metadata", db.JSON, nullable=True)

    ip_address = db.Column(db.String(50), nullable=True)

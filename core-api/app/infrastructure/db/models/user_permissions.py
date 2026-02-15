# app/infrastructure/db/models/user_permissions.py

from app.extensions.db import db
from app.infrastructure.db.base_model import TimestampMixin

class UserPermission(db.Model, TimestampMixin):
    __tablename__ = "user_permissions"

    user_id = db.Column(db.Uuid, db.ForeignKey("users.id", ondelete="CASCADE"), primary_key=True)
    permission_id = db.Column(db.Uuid, db.ForeignKey("permissions.id", ondelete="CASCADE"), primary_key=True)
    granted = db.Column(db.Boolean, default=True, nullable=False)

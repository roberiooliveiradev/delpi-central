# app/infrastructure/db/models/permission.py

from app.extensions import db
from app.infrastructure.db.base_model import TimestampMixin

class Permission(db.Model, TimestampMixin):
    __tablename__ = "permissions"

    id = db.Column(db.Uuid, primary_key=True, server_default=db.text("gen_random_uuid()"))
    code = db.Column(db.String(150), unique=True, nullable=False)
    description = db.Column(db.Text, nullable=True)
    module = db.Column(db.String(100), nullable=True, index=True)

    roles = db.relationship("Role", secondary="role_permissions", back_populates="permissions")

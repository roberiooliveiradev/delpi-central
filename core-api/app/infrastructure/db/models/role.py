# app/infrastructure/db/models/role.py

from app.extensions.db import db
from app.infrastructure.db.base_model import TimestampMixin

class Role(db.Model, TimestampMixin):
    __tablename__ = "roles"

    id = db.Column(db.Uuid, primary_key=True, server_default=db.text("gen_random_uuid()"))
    name = db.Column(db.String(100), unique=True, nullable=False)
    description = db.Column(db.Text, nullable=True)
    system_role = db.Column(db.Boolean, default=False, nullable=False)

    users = db.relationship("User", secondary="user_roles", back_populates="roles")
    groups = db.relationship("Group", secondary="group_roles", back_populates="roles")
    permissions = db.relationship("Permission", secondary="role_permissions", back_populates="roles")

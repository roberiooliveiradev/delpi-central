# app/infrastructure/db/models/role_permissions.py

from app.extensions import db

role_permissions = db.Table(
    "role_permissions",
    db.Column("role_id", db.Uuid, db.ForeignKey("roles.id", ondelete="CASCADE"), primary_key=True),
    db.Column("permission_id", db.Uuid, db.ForeignKey("permissions.id", ondelete="CASCADE"), primary_key=True),
)

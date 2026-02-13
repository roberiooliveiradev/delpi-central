# app/infrastructure/db/models/group_roles.py

from app.extensions import db

group_roles = db.Table(
    "group_roles",
    db.Column("group_id", db.Uuid, db.ForeignKey("groups.id", ondelete="CASCADE"), primary_key=True),
    db.Column("role_id", db.Uuid, db.ForeignKey("roles.id", ondelete="CASCADE"), primary_key=True),
)

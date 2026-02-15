# app/infrastructure/db/models/user_roles.py

from app.extensions.db import db

user_roles = db.Table(
    "user_roles",
    db.Column("user_id", db.Uuid, db.ForeignKey("users.id", ondelete="CASCADE"), primary_key=True),
    db.Column("role_id", db.Uuid, db.ForeignKey("roles.id", ondelete="CASCADE"), primary_key=True),
)

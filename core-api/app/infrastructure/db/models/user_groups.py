# app/infrastructure/db/models/user_groups.py

from app.extensions.db import db

user_groups = db.Table(
    "user_groups",
    db.Column("user_id", db.Uuid, db.ForeignKey("users.id", ondelete="CASCADE"), primary_key=True),
    db.Column("group_id", db.Uuid, db.ForeignKey("groups.id", ondelete="CASCADE"), primary_key=True),
)

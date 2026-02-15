# app/infrastructure/db/models/group.py

from app.extensions.db import db
from app.infrastructure.db.base_model import TimestampMixin

class Group(db.Model, TimestampMixin):
    __tablename__ = "groups"

    id = db.Column(db.Uuid, primary_key=True, server_default=db.text("gen_random_uuid()"))
    name = db.Column(db.String(100), unique=True, nullable=False)
    description = db.Column(db.Text, nullable=True)
    active = db.Column(db.Boolean, default=True, nullable=False)

    users = db.relationship("User", secondary="user_groups", back_populates="groups")
    roles = db.relationship("Role", secondary="group_roles", back_populates="groups")

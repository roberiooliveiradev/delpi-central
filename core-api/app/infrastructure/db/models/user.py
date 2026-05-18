# app/infrastructure/db/models/user.py
import uuid
from app.extensions.db import db
from app.infrastructure.db.base_model import TimestampMixin

class User(db.Model, TimestampMixin):
    __tablename__ = "users"

    id = db.Column(db.Uuid, primary_key=True, default=uuid.uuid4)
    name = db.Column(db.String(150), nullable=False)
    email = db.Column(db.String(150), unique=True, nullable=False, index=True)
    active = db.Column(db.Boolean, default=True, nullable=False)
    is_superadmin = db.Column(db.Boolean, default=False, nullable=False)
    last_login_at = db.Column(db.DateTime, nullable=True)
    birth_date = db.Column(db.Date, nullable=True, index=True)

    roles = db.relationship("Role", secondary="user_roles", back_populates="users")
    groups = db.relationship("Group", secondary="user_groups", back_populates="users")

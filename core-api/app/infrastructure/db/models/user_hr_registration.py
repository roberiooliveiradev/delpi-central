"""Verified employee registration <-> Core user association (not SYS_USR)."""

from app.extensions.db import db
from app.infrastructure.db.base_model import TimestampMixin


class UserHrRegistration(db.Model, TimestampMixin):
    __tablename__ = "user_hr_registrations"

    user_id = db.Column(
        db.Uuid,
        db.ForeignKey("users.id", ondelete="CASCADE"),
        primary_key=True,
    )
    # Opaque RH registration: "001" and "1" are different identifiers.
    registration = db.Column(db.String(30), unique=True, nullable=False)
    verified_by_user_id = db.Column(
        db.Uuid,
        db.ForeignKey("users.id", ondelete="SET NULL"),
        nullable=True,
    )
    verified_at = db.Column(db.DateTime(timezone=True), nullable=False)

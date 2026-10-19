from app.extensions.db import db
from app.infrastructure.db.base_model import TimestampMixin


class UserProtheusIdentity(db.Model, TimestampMixin):
    """Authoritative portal user ↔ Protheus SYS_USR association."""

    __tablename__ = "user_protheus_identities"

    user_id = db.Column(
        db.Uuid,
        db.ForeignKey("users.id", ondelete="CASCADE"),
        primary_key=True,
    )
    # Preserve leading zeros from SYS_USR.USR_ID — never coerce to int.
    protheus_user_id = db.Column(db.Text, nullable=True)
    protheus_user_code = db.Column(db.Text, nullable=True)
    mapping_status = db.Column(db.Text, nullable=False, default="unmapped")
    mapping_source = db.Column(db.Text, nullable=True)
    verified = db.Column(db.Boolean, nullable=False, default=False)
    updated_by_user_id = db.Column(
        db.Uuid,
        db.ForeignKey("users.id", ondelete="SET NULL"),
        nullable=True,
    )

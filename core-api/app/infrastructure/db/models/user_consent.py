import uuid
from app.extensions.db import db
from app.infrastructure.db.base_model import TimestampMixin


class UserConsent(db.Model, TimestampMixin):
    __tablename__ = "user_consents"

    id = db.Column(db.Uuid, primary_key=True, default=uuid.uuid4)
    user_id = db.Column(db.Uuid, db.ForeignKey("users.id", ondelete="CASCADE"), nullable=False, index=True)
    purpose = db.Column(db.String(100), nullable=False, index=True)
    granted = db.Column(db.Boolean, nullable=False, default=True)
    granted_at = db.Column(db.DateTime(timezone=True), nullable=True)
    revoked_at = db.Column(db.DateTime(timezone=True), nullable=True)
    ip_address = db.Column(db.String(45), nullable=True)
    user_agent = db.Column(db.String(500), nullable=True)

    __table_args__ = (
        db.UniqueConstraint("user_id", "purpose", name="uq_user_consents_user_purpose"),
    )

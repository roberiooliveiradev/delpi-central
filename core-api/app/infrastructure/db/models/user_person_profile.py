from app.extensions.db import db
from app.infrastructure.db.base_model import TimestampMixin


class UserPersonProfile(db.Model, TimestampMixin):
    """Platform person profile extension (photo, job title, contacts)."""

    __tablename__ = "user_person_profiles"

    user_id = db.Column(
        db.Uuid,
        db.ForeignKey("users.id", ondelete="CASCADE"),
        primary_key=True,
    )
    job_title = db.Column(db.Text, nullable=True)
    phone_e164 = db.Column(db.Text, nullable=True)
    mobile_e164 = db.Column(db.Text, nullable=True)
    whatsapp_e164 = db.Column(db.Text, nullable=True)
    photo_storage_key = db.Column(db.Text, nullable=True)
    photo_file_name = db.Column(db.Text, nullable=True)
    photo_content_type = db.Column(db.Text, nullable=True)
    photo_byte_size = db.Column(db.Integer, nullable=True)

import uuid
from datetime import datetime, timezone

from sqlalchemy.dialects.postgresql import JSONB, UUID

from app.extensions.db import db


class ExternalActionProviderModel(db.Model):
    __tablename__ = "ai_external_action_providers"

    id = db.Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    provider_key = db.Column(db.String(80), nullable=False, unique=True, index=True)
    name = db.Column(db.String(150), nullable=False)
    provider_type = db.Column(db.String(20), nullable=False, index=True)
    base_url = db.Column(db.Text, nullable=False)
    openapi_url = db.Column(db.Text, nullable=True)
    auth_mode = db.Column(db.String(40), nullable=False, default="none")
    auth_config = db.Column(JSONB, nullable=True)
    enabled = db.Column(db.Boolean, nullable=False, default=True, index=True)
    created_at = db.Column(
        db.DateTime(timezone=True),
        nullable=False,
        default=lambda: datetime.now(timezone.utc),
        index=True,
    )
    updated_at = db.Column(
        db.DateTime(timezone=True),
        nullable=False,
        default=lambda: datetime.now(timezone.utc),
        onupdate=lambda: datetime.now(timezone.utc),
    )

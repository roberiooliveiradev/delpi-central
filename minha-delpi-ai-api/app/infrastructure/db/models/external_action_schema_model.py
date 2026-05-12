import uuid
from datetime import datetime, timezone

from sqlalchemy.dialects.postgresql import JSONB, UUID

from app.extensions.db import db


class ExternalActionSchemaModel(db.Model):
    __tablename__ = "ai_external_action_schemas"

    id = db.Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    provider_id = db.Column(
        UUID(as_uuid=True),
        db.ForeignKey("ai_external_action_providers.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    schema_json = db.Column(JSONB, nullable=False)
    schema_hash = db.Column(db.String(128), nullable=False, index=True)
    source_type = db.Column(db.String(20), nullable=False)
    source_url = db.Column(db.Text, nullable=True)
    imported_at = db.Column(
        db.DateTime(timezone=True),
        nullable=False,
        default=lambda: datetime.now(timezone.utc),
        index=True,
    )

import uuid
from datetime import datetime, timezone

from pgvector.sqlalchemy import Vector
from sqlalchemy.dialects.postgresql import JSONB, UUID

from app.extensions.db import db
from app.infrastructure.config.settings import Settings


class ExternalActionModel(db.Model):
    __tablename__ = "ai_external_actions"

    id = db.Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    provider_id = db.Column(
        UUID(as_uuid=True),
        db.ForeignKey("ai_external_action_providers.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    action_id = db.Column(db.String(220), nullable=False, unique=True, index=True)
    operation_id = db.Column(db.String(180), nullable=True, index=True)
    method = db.Column(db.String(10), nullable=False, index=True)
    path = db.Column(db.Text, nullable=False)
    summary = db.Column(db.Text, nullable=True)
    description = db.Column(db.Text, nullable=True)
    tags = db.Column(JSONB, nullable=True)
    parameters_schema = db.Column(JSONB, nullable=True)
    request_body_schema = db.Column(JSONB, nullable=True)
    response_schema = db.Column(JSONB, nullable=True)
    sensitivity = db.Column(db.String(30), nullable=False, default="read", index=True)
    embedding = db.Column(Vector(Settings.EMBEDDING_DIMENSIONS), nullable=True)
    enabled = db.Column(db.Boolean, nullable=False, default=True, index=True)
    deprecated = db.Column(db.Boolean, nullable=False, default=False, index=True)
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

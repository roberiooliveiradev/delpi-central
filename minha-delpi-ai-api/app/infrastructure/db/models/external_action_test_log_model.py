import uuid
from datetime import datetime, timezone

from sqlalchemy.dialects.postgresql import JSONB, UUID

from app.extensions.db import db


class ExternalActionTestLogModel(db.Model):
    __tablename__ = "ai_external_action_test_logs"

    id = db.Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    user_id = db.Column(db.String(120), nullable=False, index=True)
    agent_id = db.Column(UUID(as_uuid=True), nullable=False, index=True)
    provider_key = db.Column(db.String(120), nullable=False, index=True)
    action_id = db.Column(db.String(220), nullable=False, index=True)
    method = db.Column(db.String(10), nullable=False)
    url = db.Column(db.Text, nullable=False)
    request_payload = db.Column(JSONB, nullable=True)
    status_code = db.Column(db.Integer, nullable=True)
    ok = db.Column(db.Boolean, nullable=False, default=False, index=True)
    duration_ms = db.Column(db.Integer, nullable=True)
    response_preview = db.Column(db.Text, nullable=True)
    error_message = db.Column(db.Text, nullable=True)
    created_at = db.Column(
        db.DateTime(timezone=True),
        nullable=False,
        default=lambda: datetime.now(timezone.utc),
        index=True,
    )

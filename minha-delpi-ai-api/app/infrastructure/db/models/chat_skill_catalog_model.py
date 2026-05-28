import uuid
from datetime import datetime, timezone

from sqlalchemy.dialects.postgresql import UUID

from app.extensions.db import db


class AiChatSkillCatalogModel(db.Model):
    __tablename__ = "ai_chat_skill_catalog"

    id = db.Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    skill_key = db.Column(db.String(80), nullable=False, unique=True, index=True)
    label = db.Column(db.String(160), nullable=False)
    description = db.Column(db.Text, nullable=False, default="")
    policy_content = db.Column(db.Text, nullable=True)
    policy_file = db.Column(db.String(120), nullable=True)
    metadata_flag = db.Column(db.String(80), nullable=False, default="enabled", server_default="enabled")
    legacy_metadata_flag = db.Column(db.String(80), nullable=True)
    execution_path_hint = db.Column(db.String(200), nullable=True)
    execution_derived_key = db.Column(db.String(80), nullable=True)
    is_active = db.Column(db.Boolean, nullable=False, default=True, server_default="true", index=True)
    sort_order = db.Column(db.Integer, nullable=False, default=0, server_default="0")
    created_at = db.Column(
        db.DateTime(timezone=True),
        nullable=False,
        default=lambda: datetime.now(timezone.utc),
    )
    updated_at = db.Column(
        db.DateTime(timezone=True),
        nullable=False,
        default=lambda: datetime.now(timezone.utc),
        onupdate=lambda: datetime.now(timezone.utc),
    )

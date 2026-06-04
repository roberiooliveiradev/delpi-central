from datetime import datetime, timezone

from sqlalchemy.dialects.postgresql import UUID

from app.extensions.db import db


class AiVocabularyTermModel(db.Model):
    """Termo de vocabulário aprendido (typo, abreviação, sigla, definição)."""

    __tablename__ = "ai_vocabulary_terms"

    id = db.Column(db.BigInteger, primary_key=True, autoincrement=True)
    term = db.Column(db.String(160), nullable=False, index=True)
    normalized_term = db.Column(db.String(160), nullable=False)
    meaning = db.Column(db.Text, nullable=True)
    type = db.Column(db.String(32), nullable=False, default="typo", server_default="typo")
    scope = db.Column(db.String(16), nullable=False, default="global", server_default="global")
    project_id = db.Column(UUID(as_uuid=True), nullable=True)
    source = db.Column(db.String(48), nullable=False, default="promotion", server_default="promotion")
    confidence = db.Column(db.Numeric(4, 3), nullable=True)
    evidence_count = db.Column(db.Integer, nullable=False, default=0, server_default="0")
    approved = db.Column(db.Boolean, nullable=False, default=False, server_default="false")
    active = db.Column(db.Boolean, nullable=False, default=True, server_default="true")
    created_by = db.Column(UUID(as_uuid=True), nullable=True)
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

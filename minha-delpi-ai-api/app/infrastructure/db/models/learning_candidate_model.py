from datetime import datetime, timezone

from sqlalchemy.dialects.postgresql import JSONB, UUID

from app.extensions.db import db


class AiLearningCandidateModel(db.Model):
    """Candidato de conhecimento aprendido, à espera de validação/promoção."""

    __tablename__ = "ai_learning_candidates"

    id = db.Column(db.BigInteger, primary_key=True, autoincrement=True)
    candidate_type = db.Column(db.String(32), nullable=False)
    term = db.Column(db.String(160), nullable=True, index=True)
    input_text = db.Column(db.Text, nullable=False)
    proposed_rule = db.Column(db.String(240), nullable=True)
    proposed_meaning = db.Column(db.Text, nullable=True)
    evidence_json = db.Column(JSONB, nullable=True)
    confidence = db.Column(db.Numeric(4, 3), nullable=True)
    evidence_count = db.Column(db.Integer, nullable=False, default=1, server_default="1")
    risk_level = db.Column(db.String(16), nullable=False, default="low", server_default="low")
    scope = db.Column(db.String(16), nullable=False, default="global", server_default="global")
    project_id = db.Column(UUID(as_uuid=True), nullable=True)
    status = db.Column(db.String(24), nullable=False, default="pending", server_default="pending")
    source = db.Column(db.String(48), nullable=False, default="auto", server_default="auto")
    created_by = db.Column(UUID(as_uuid=True), nullable=True)
    reviewer_id = db.Column(UUID(as_uuid=True), nullable=True)
    promoted_term_id = db.Column(db.BigInteger, nullable=True)
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
    reviewed_at = db.Column(db.DateTime(timezone=True), nullable=True)

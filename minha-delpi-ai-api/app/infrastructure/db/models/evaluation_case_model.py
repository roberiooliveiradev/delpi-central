from datetime import datetime, timezone

from sqlalchemy.dialects.postgresql import UUID

from app.extensions.db import db


class AiEvaluationCaseModel(db.Model):
    """Caso de regressão para validar aprendizado antes de promover (playbook Fase 6)."""

    __tablename__ = "ai_evaluation_cases"

    id = db.Column(db.BigInteger, primary_key=True, autoincrement=True)
    category = db.Column(db.String(32), nullable=False, index=True)
    input = db.Column(db.Text, nullable=False)
    expected_intent = db.Column(db.String(80), nullable=True)
    expected_answer = db.Column(db.Text, nullable=True)
    expected_normalized = db.Column(db.String(240), nullable=True)
    must_not_use_tools = db.Column(db.Boolean, nullable=False, default=False, server_default="false")
    must_not_use_rag = db.Column(db.Boolean, nullable=False, default=False, server_default="false")
    source_feedback_id = db.Column(db.BigInteger, nullable=True)
    linked_candidate_id = db.Column(db.BigInteger, nullable=True)
    status = db.Column(db.String(16), nullable=False, default="active", server_default="active")
    last_run_at = db.Column(db.DateTime(timezone=True), nullable=True)
    last_passed = db.Column(db.Boolean, nullable=True)
    last_failure_reason = db.Column(db.Text, nullable=True)
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

from datetime import datetime, timezone

from sqlalchemy.dialects.postgresql import JSONB, UUID

from app.extensions.db import db


class AiMemoryItemModel(db.Model):
    """Memória persistente do usuário/projeto (cross-sessão).

    Guarda preferências, correções e fatos estáveis com governança via `status`
    (active/forgotten/expired). `embedding` fica reservado para recuperação
    semântica futura (Fase 5).
    """

    __tablename__ = "ai_memory_items"

    id = db.Column(db.BigInteger, primary_key=True, autoincrement=True)
    user_id = db.Column(UUID(as_uuid=True), nullable=True)
    project_id = db.Column(UUID(as_uuid=True), nullable=True)
    session_id = db.Column(UUID(as_uuid=True), nullable=True)
    scope = db.Column(db.String(16), nullable=False, default="user", server_default="user")
    type = db.Column(db.String(32), nullable=False)
    content = db.Column(db.Text, nullable=False)
    content_norm = db.Column(db.String(320), nullable=False)
    content_json = db.Column(JSONB, nullable=True)
    embedding = db.Column(JSONB, nullable=True)
    confidence = db.Column(db.Numeric(4, 3), nullable=True)
    evidence_count = db.Column(db.Integer, nullable=False, default=1, server_default="1")
    source = db.Column(db.String(48), nullable=False, default="auto", server_default="auto")
    status = db.Column(db.String(24), nullable=False, default="active", server_default="active")
    created_by = db.Column(UUID(as_uuid=True), nullable=True)
    reviewer_id = db.Column(UUID(as_uuid=True), nullable=True)
    expires_at = db.Column(db.DateTime(timezone=True), nullable=True)
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

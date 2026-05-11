import uuid
from datetime import datetime, timezone

from pgvector.sqlalchemy import Vector
from sqlalchemy.dialects.postgresql import JSONB, UUID

from app.extensions.db import db
from app.infrastructure.config.settings import Settings


class AiKnowledgeChunkModel(db.Model):
    __tablename__ = "ai_knowledge_chunks"

    id = db.Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)

    document_id = db.Column(
        UUID(as_uuid=True),
        db.ForeignKey("ai_knowledge_documents.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )

    chunk_index = db.Column(db.Integer, nullable=False)
    content = db.Column(db.Text, nullable=False)

    embedding = db.Column(Vector(Settings.EMBEDDING_DIMENSIONS), nullable=False)

    chunk_metadata = db.Column("metadata", JSONB, nullable=True)

    created_at = db.Column(
        db.DateTime(timezone=True),
        nullable=False,
        default=lambda: datetime.now(timezone.utc),
        index=True,
    )

    __table_args__ = (
        db.UniqueConstraint(
            "document_id",
            "chunk_index",
            name="uq_ai_knowledge_chunks_document_index",
        ),
    )

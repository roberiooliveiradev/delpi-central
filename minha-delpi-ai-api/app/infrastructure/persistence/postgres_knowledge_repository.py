from datetime import datetime, timezone
from uuid import UUID

from app.domain.entities.knowledge_chunk import KnowledgeChunk
from app.domain.entities.knowledge_document import KnowledgeDocument
from app.domain.ports.knowledge_repository_port import KnowledgeRepositoryPort
from app.extensions.db import db
from app.infrastructure.db.models.knowledge_chunk_model import AiKnowledgeChunkModel
from app.infrastructure.db.models.knowledge_document_model import AiKnowledgeDocumentModel


class PostgresKnowledgeRepository(KnowledgeRepositoryPort):
    def create_document(
        self,
        title: str,
        source_type: str,
        source_ref: str | None,
        content: str,
        metadata: dict | None = None,
    ) -> KnowledgeDocument:
        model = AiKnowledgeDocumentModel(
            title=title,
            source_type=source_type,
            source_ref=source_ref,
            content=content,
            document_metadata=metadata,
            active=True,
        )

        db.session.add(model)
        db.session.flush()

        return self._to_document_entity(model)

    def create_chunk(
        self,
        document_id: UUID,
        chunk_index: int,
        content: str,
        embedding: list[float],
        metadata: dict | None = None,
    ) -> KnowledgeChunk:
        model = AiKnowledgeChunkModel(
            document_id=document_id,
            chunk_index=chunk_index,
            content=content,
            embedding=embedding,
            chunk_metadata=metadata,
        )

        db.session.add(model)
        db.session.flush()

        return self._to_chunk_entity(model)

    def search_similar_chunks(
        self,
        embedding: list[float],
        limit: int,
    ) -> list[KnowledgeChunk]:
        rows = (
            db.session.query(
                AiKnowledgeChunkModel,
                AiKnowledgeDocumentModel,
                AiKnowledgeChunkModel.embedding.cosine_distance(embedding).label("distance"),
            )
            .join(
                AiKnowledgeDocumentModel,
                AiKnowledgeDocumentModel.id == AiKnowledgeChunkModel.document_id,
            )
            .filter(AiKnowledgeDocumentModel.active.is_(True))
            .order_by(AiKnowledgeChunkModel.embedding.cosine_distance(embedding))
            .limit(limit)
            .all()
        )

        result: list[KnowledgeChunk] = []

        for chunk_model, document_model, distance in rows:
            chunk = self._to_chunk_entity(chunk_model)
            result.append(
                KnowledgeChunk(
                    id=chunk.id,
                    document_id=chunk.document_id,
                    chunk_index=chunk.chunk_index,
                    content=chunk.content,
                    metadata=chunk.metadata,
                    created_at=chunk.created_at,
                    score=float(1 - distance) if distance is not None else None,
                    title=document_model.title,
                    source_type=document_model.source_type,
                    source_ref=document_model.source_ref,
                )
            )

        return result


    def list_documents(self, limit: int = 100) -> list[KnowledgeDocument]:
        models = (
            AiKnowledgeDocumentModel.query
            .order_by(AiKnowledgeDocumentModel.created_at.desc())
            .limit(limit)
            .all()
        )

        return [self._to_document_entity(model) for model in models]

    def deactivate_document(self, document_id: UUID) -> KnowledgeDocument | None:
        model = AiKnowledgeDocumentModel.query.filter(
            AiKnowledgeDocumentModel.id == document_id
        ).first()

        if not model:
            return None

        model.active = False
        model.updated_at = datetime.now(timezone.utc)

        db.session.flush()

        return self._to_document_entity(model)


    def reactivate_document(self, document_id: UUID) -> KnowledgeDocument | None:
        model = AiKnowledgeDocumentModel.query.filter(
            AiKnowledgeDocumentModel.id == document_id
        ).first()

        if not model:
            return None

        model.active = True
        model.updated_at = datetime.now(timezone.utc)

        db.session.flush()

        return self._to_document_entity(model)

    def _to_document_entity(self, model: AiKnowledgeDocumentModel) -> KnowledgeDocument:
        return KnowledgeDocument(
            id=model.id,
            title=model.title,
            source_type=model.source_type,
            source_ref=model.source_ref,
            content=model.content,
            metadata=model.document_metadata,
            active=model.active,
            created_at=model.created_at,
            updated_at=model.updated_at,
        )

    def _to_chunk_entity(self, model: AiKnowledgeChunkModel) -> KnowledgeChunk:
        return KnowledgeChunk(
            id=model.id,
            document_id=model.document_id,
            chunk_index=model.chunk_index,
            content=model.content,
            metadata=model.chunk_metadata,
            created_at=model.created_at,
        )

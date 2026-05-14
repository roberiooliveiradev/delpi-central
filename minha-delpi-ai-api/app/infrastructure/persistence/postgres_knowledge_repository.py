from datetime import datetime, timezone
from uuid import UUID

from sqlalchemy import or_

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
        filters: dict | None = None,
    ) -> list[KnowledgeChunk]:
        query = (
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
        )

        query = self._apply_scope_filters(query, filters or {})

        rows = (
            query
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





    def list_documents_with_chunk_count(
        self,
        limit: int = 100,
        offset: int = 0,
        search: str | None = None,
        active: bool | None = None,
    ) -> list[tuple[KnowledgeDocument, int]]:
        query = (
            db.session.query(
                AiKnowledgeDocumentModel,
                db.func.count(AiKnowledgeChunkModel.id).label("chunk_count"),
            )
            .outerjoin(
                AiKnowledgeChunkModel,
                AiKnowledgeChunkModel.document_id == AiKnowledgeDocumentModel.id,
            )
        )

        query = self._apply_document_filters(query, search=search, active=active)

        rows = (
            query
            .group_by(AiKnowledgeDocumentModel.id)
            .order_by(AiKnowledgeDocumentModel.created_at.desc())
            .offset(offset)
            .limit(limit)
            .all()
        )

        return [
            (self._to_document_entity(document_model), int(chunk_count or 0))
            for document_model, chunk_count in rows
        ]

    def count_documents(
        self,
        search: str | None = None,
        active: bool | None = None,
    ) -> int:
        query = db.session.query(AiKnowledgeDocumentModel)
        query = self._apply_document_filters(query, search=search, active=active)

        return int(query.count())


    def list_documents_by_metadata(
        self,
        *,
        filters: dict,
        limit: int = 100,
        active: bool | None = True,
    ) -> list[tuple[KnowledgeDocument, int]]:
        query = (
            db.session.query(
                AiKnowledgeDocumentModel,
                db.func.count(AiKnowledgeChunkModel.id).label("chunk_count"),
            )
            .outerjoin(
                AiKnowledgeChunkModel,
                AiKnowledgeChunkModel.document_id == AiKnowledgeDocumentModel.id,
            )
        )

        if active is not None:
            query = query.filter(AiKnowledgeDocumentModel.active.is_(active))

        for key, value in filters.items():
            if value is None:
                continue

            query = query.filter(
                AiKnowledgeDocumentModel.document_metadata[key].astext == str(value)
            )

        rows = (
            query
            .group_by(AiKnowledgeDocumentModel.id)
            .order_by(AiKnowledgeDocumentModel.created_at.desc())
            .limit(limit)
            .all()
        )

        return [
            (self._to_document_entity(document_model), int(chunk_count or 0))
            for document_model, chunk_count in rows
        ]


    def get_document_by_id(self, document_id: UUID) -> KnowledgeDocument | None:
        model = AiKnowledgeDocumentModel.query.filter(
            AiKnowledgeDocumentModel.id == document_id
        ).first()

        if not model:
            return None

        return self._to_document_entity(model)

    def delete_chunks_by_document_id(self, document_id: UUID) -> None:
        AiKnowledgeChunkModel.query.filter(
            AiKnowledgeChunkModel.document_id == document_id
        ).delete(synchronize_session=False)

        db.session.flush()

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



    def _apply_scope_filters(self, query, filters: dict):
        if not filters:
            return query

        metadata = AiKnowledgeDocumentModel.document_metadata
        allowed_clauses = []

        if filters.get("include_global", True):
            allowed_clauses.append(
                db.or_(
                    metadata.is_(None),
                    metadata["scope"].astext.is_(None),
                    metadata["scope"].astext == "global",
                )
            )

        session_id = filters.get("session_id")
        if session_id:
            allowed_clauses.append(
                db.and_(
                    metadata["scope"].astext == "session_source",
                    metadata["sessionId"].astext == str(session_id),
                )
            )

        project_id = filters.get("project_id")
        if project_id:
            allowed_clauses.append(
                db.and_(
                    metadata["scope"].astext == "project_source",
                    metadata["projectId"].astext == str(project_id),
                )
            )

        agent_key = filters.get("agent_key")
        if agent_key:
            allowed_clauses.append(
                db.and_(
                    metadata["scope"].astext == "agent_source",
                    metadata["agentKey"].astext == str(agent_key),
                )
            )

        user_id = filters.get("user_id")
        if user_id:
            query = query.filter(
                db.or_(
                    metadata["userId"].astext.is_(None),
                    metadata["userId"].astext == str(user_id),
                )
            )

        attachment_ids = [
            str(item)
            for item in (filters.get("attachment_ids") or [])
            if item
        ]

        if attachment_ids:
            query = query.filter(metadata["attachmentId"].astext.in_(attachment_ids))

        if not allowed_clauses:
            return query

        return query.filter(db.or_(*allowed_clauses))


    def _apply_document_filters(self, query, search: str | None, active: bool | None):
        if active is not None:
            query = query.filter(AiKnowledgeDocumentModel.active.is_(active))

        normalized_search = str(search or "").strip()

        if normalized_search:
            pattern = f"%{normalized_search}%"
            query = query.filter(
                or_(
                    AiKnowledgeDocumentModel.title.ilike(pattern),
                    AiKnowledgeDocumentModel.source_type.ilike(pattern),
                    AiKnowledgeDocumentModel.source_ref.ilike(pattern),
                )
            )

        return query

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

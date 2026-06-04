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

    def search_keyword_chunks(
        self,
        query: str,
        limit: int,
        filters: dict | None = None,
        *,
        use_fts: bool = True,
    ) -> list[KnowledgeChunk]:
        from app.domain.services.keyword_similarity import keyword_overlap_score, tokenize

        normalized_query = str(query or "").strip()

        if not normalized_query:
            return []

        rows = []

        if use_fts:
            rows = self._search_keyword_chunks_fts(normalized_query, limit=limit, filters=filters)

        if not rows:
            terms = tokenize(normalized_query)[:8]

            if not terms:
                return []

            db_query = (
                db.session.query(
                    AiKnowledgeChunkModel,
                    AiKnowledgeDocumentModel,
                )
                .join(
                    AiKnowledgeDocumentModel,
                    AiKnowledgeDocumentModel.id == AiKnowledgeChunkModel.document_id,
                )
                .filter(AiKnowledgeDocumentModel.active.is_(True))
            )

            db_query = self._apply_scope_filters(db_query, filters or {})
            db_query = db_query.filter(
                db.or_(*[AiKnowledgeChunkModel.content.ilike(f"%{term}%") for term in terms])
            )

            rows = (
                db_query.order_by(AiKnowledgeChunkModel.created_at.desc())
                .limit(max(limit * 4, limit))
                .all()
            )

        scored: list[tuple[float, KnowledgeChunk]] = []

        for chunk_model, document_model in rows:
            chunk = self._to_chunk_entity(chunk_model)
            score = keyword_overlap_score(query, chunk.content or "")
            scored.append(
                (
                    score,
                    KnowledgeChunk(
                        id=chunk.id,
                        document_id=chunk.document_id,
                        chunk_index=chunk.chunk_index,
                        content=chunk.content,
                        metadata=chunk.metadata,
                        created_at=chunk.created_at,
                        score=score,
                        title=document_model.title,
                        source_type=document_model.source_type,
                        source_ref=document_model.source_ref,
                    ),
                )
            )

        scored.sort(key=lambda item: item[0], reverse=True)

        return [chunk for score, chunk in scored[:limit] if score > 0]

    def _search_keyword_chunks_fts(
        self,
        query: str,
        *,
        limit: int,
        filters: dict | None,
    ) -> list:
        from sqlalchemy import func

        ts_query = func.plainto_tsquery("simple", query)

        db_query = (
            db.session.query(
                AiKnowledgeChunkModel,
                AiKnowledgeDocumentModel,
            )
            .join(
                AiKnowledgeDocumentModel,
                AiKnowledgeDocumentModel.id == AiKnowledgeChunkModel.document_id,
            )
            .filter(AiKnowledgeDocumentModel.active.is_(True))
            .filter(
                func.to_tsvector("simple", AiKnowledgeChunkModel.content).op("@@")(ts_query)
            )
        )

        db_query = self._apply_scope_filters(db_query, filters or {})

        return (
            db_query.order_by(AiKnowledgeChunkModel.created_at.desc())
            .limit(max(limit * 4, limit))
            .all()
        )

    def list_documents_with_chunk_count(
        self,
        limit: int = 100,
        offset: int = 0,
        search: str | None = None,
        active: bool | None = None,
        scope: str | None = None,
        curatorial_filters: dict | None = None,
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

        query = self._apply_document_filters(
            query,
            search=search,
            active=active,
            scope=scope,
            curatorial_filters=curatorial_filters,
        )

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
        scope: str | None = None,
        curatorial_filters: dict | None = None,
    ) -> int:
        query = db.session.query(AiKnowledgeDocumentModel)
        query = self._apply_document_filters(
            query,
            search=search,
            active=active,
            scope=scope,
            curatorial_filters=curatorial_filters,
        )

        return int(query.count())

    def update_document_metadata(self, document_id: UUID, metadata: dict) -> KnowledgeDocument | None:
        return self.update_document(document_id, metadata=metadata)

    def update_document(
        self,
        document_id: UUID,
        *,
        content: str | None = None,
        metadata: dict | None = None,
    ) -> KnowledgeDocument | None:
        model = AiKnowledgeDocumentModel.query.filter(
            AiKnowledgeDocumentModel.id == document_id
        ).first()

        if not model:
            return None

        if content is not None:
            model.content = content

        if metadata is not None:
            model.document_metadata = metadata

        model.updated_at = datetime.now(timezone.utc)
        db.session.flush()

        return self._to_document_entity(model)

    def get_global_curatorial_facets(self) -> dict:
        models = (
            AiKnowledgeDocumentModel.query.filter(
                db.or_(
                    AiKnowledgeDocumentModel.document_metadata.is_(None),
                    AiKnowledgeDocumentModel.document_metadata["scope"].astext.is_(None),
                    AiKnowledgeDocumentModel.document_metadata["scope"].astext == "global",
                )
            )
            .order_by(AiKnowledgeDocumentModel.created_at.desc())
            .limit(500)
            .all()
        )

        categories: set[str] = set()
        namespaces: set[str] = set()
        domains: set[str] = set()
        tags: set[str] = set()
        source_types: set[str] = set()

        for model in models:
            metadata = model.document_metadata or {}
            source_types.add(model.source_type)

            if metadata.get("category"):
                categories.add(str(metadata["category"]))

            if metadata.get("namespace"):
                namespaces.add(str(metadata["namespace"]))

            if metadata.get("domain"):
                domains.add(str(metadata["domain"]))

            for tag in metadata.get("tags") or []:
                if tag:
                    tags.add(str(tag))

        return {
            "categories": sorted(categories),
            "namespaces": sorted(namespaces),
            "domains": sorted(domains),
            "tags": sorted(tags),
            "sourceTypes": sorted(source_types),
        }

    def get_global_document_summary(self) -> dict[str, int]:
        return {
            "total": self.count_documents(scope="global"),
            "active": self.count_documents(active=True, scope="global"),
            "inactive": self.count_documents(active=False, scope="global"),
            "pendingIndex": self.count_documents_without_chunks(
                active=True,
                scope="global",
            ),
        }

    def count_documents_without_chunks(
        self,
        *,
        active: bool | None = True,
        scope: str | None = "global",
    ) -> int:
        query = (
            db.session.query(AiKnowledgeDocumentModel.id)
            .outerjoin(
                AiKnowledgeChunkModel,
                AiKnowledgeChunkModel.document_id == AiKnowledgeDocumentModel.id,
            )
        )
        query = self._apply_document_filters(query, search=None, active=active, scope=scope)
        query = query.group_by(AiKnowledgeDocumentModel.id).having(
            db.func.count(AiKnowledgeChunkModel.id) == 0,
        )

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

    def list_chunks_by_document_id(
        self,
        document_id: UUID,
        *,
        limit: int = 12,
    ) -> list[KnowledgeChunk]:
        rows = (
            AiKnowledgeChunkModel.query.filter(
                AiKnowledgeChunkModel.document_id == document_id,
            )
            .order_by(AiKnowledgeChunkModel.chunk_index.asc())
            .limit(max(1, limit))
            .all()
        )

        return [self._to_chunk_entity(row) for row in rows]

    def find_global_document_by_content_hash(
        self,
        content_hash: str,
        source_ref: str | None = None,
    ) -> KnowledgeDocument | None:
        normalized_hash = str(content_hash or "").strip()

        if not normalized_hash:
            return None

        metadata = AiKnowledgeDocumentModel.document_metadata
        query = AiKnowledgeDocumentModel.query.filter(
            metadata["contentHash"].astext == normalized_hash,
            db.or_(
                metadata.is_(None),
                metadata["scope"].astext.is_(None),
                metadata["scope"].astext == "global",
            ),
        )

        normalized_source_ref = str(source_ref or "").strip()

        if normalized_source_ref:
            query = query.filter(AiKnowledgeDocumentModel.source_ref == normalized_source_ref)

        model = query.order_by(AiKnowledgeDocumentModel.updated_at.desc()).first()

        if not model:
            return None

        return self._to_document_entity(model)

    def find_document_by_source_ref(
        self,
        source_ref: str,
        *,
        source_type: str | None = None,
    ) -> KnowledgeDocument | None:
        normalized = str(source_ref or "").strip()

        if not normalized:
            return None

        query = AiKnowledgeDocumentModel.query.filter(
            AiKnowledgeDocumentModel.source_ref == normalized
        )

        if source_type:
            query = query.filter(AiKnowledgeDocumentModel.source_type == source_type)

        model = query.order_by(AiKnowledgeDocumentModel.updated_at.desc()).first()

        return self._to_document_entity(model) if model else None

    def delete_chunks_by_document_id(self, document_id: UUID) -> None:
        AiKnowledgeChunkModel.query.filter(
            AiKnowledgeChunkModel.document_id == document_id
        ).delete(synchronize_session=False)

        db.session.flush()

    def delete_document(self, document_id: UUID) -> None:
        self.delete_chunks_by_document_id(document_id)

        AiKnowledgeDocumentModel.query.filter(
            AiKnowledgeDocumentModel.id == document_id
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

        shared_session_ids = [
            str(item)
            for item in (filters.get("shared_session_ids") or [])
            if item
        ]

        if shared_session_ids:
            allowed_clauses.append(
                db.and_(
                    metadata["scope"].astext == "session_source",
                    metadata["sessionId"].astext.in_(shared_session_ids),
                )
            )
        else:
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

        agent_id = filters.get("agent_id") or filters.get("agentId")
        if agent_id:
            allowed_clauses.append(
                db.and_(
                    metadata["scope"].astext == "agent_source",
                    metadata["agentId"].astext == str(agent_id),
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

        document_id = filters.get("document_id")
        if document_id:
            query = query.filter(AiKnowledgeDocumentModel.id == str(document_id))

        if allowed_clauses:
            query = query.filter(db.or_(*allowed_clauses))

        return self._apply_curatorial_scope_filters(query, filters.get("curatorial"))


    def _apply_curatorial_scope_filters(self, query, curatorial: dict | None):
        if not curatorial:
            return query

        metadata = AiKnowledgeDocumentModel.document_metadata

        domains = [str(item).strip() for item in (curatorial.get("domains") or []) if str(item).strip()]

        if domains:
            query = query.filter(metadata["domain"].astext.in_(domains))

        namespaces = [
            str(item).strip() for item in (curatorial.get("namespaces") or []) if str(item).strip()
        ]

        if namespaces:
            query = query.filter(metadata["namespace"].astext.in_(namespaces))

        categories = [
            str(item).strip() for item in (curatorial.get("categories") or []) if str(item).strip()
        ]

        if categories:
            query = query.filter(metadata["category"].astext.in_(categories))

        tag = str(curatorial.get("tag") or "").strip().lower()

        if tag:
            query = query.filter(metadata["tags"].astext.ilike(f'%"{tag}"%'))

        tags = [str(item).strip().lower() for item in (curatorial.get("tags") or []) if str(item).strip()]

        if tags:
            tag_clauses = [metadata["tags"].astext.ilike(f'%"{item}"%') for item in tags]
            query = query.filter(db.or_(*tag_clauses))

        return query

    def _apply_document_filters(
        self,
        query,
        search: str | None,
        active: bool | None,
        scope: str | None = None,
        curatorial_filters: dict | None = None,
    ):
        if active is not None:
            query = query.filter(AiKnowledgeDocumentModel.active.is_(active))

        normalized_scope = str(scope or "").strip()

        if normalized_scope == "global":
            metadata = AiKnowledgeDocumentModel.document_metadata
            query = query.filter(
                db.or_(
                    metadata.is_(None),
                    metadata["scope"].astext.is_(None),
                    metadata["scope"].astext == "global",
                )
            )
        elif normalized_scope:
            query = query.filter(
                AiKnowledgeDocumentModel.document_metadata["scope"].astext == normalized_scope
            )

        normalized_search = str(search or "").strip()

        if normalized_search:
            pattern = f"%{normalized_search}%"
            metadata = AiKnowledgeDocumentModel.document_metadata
            query = query.filter(
                or_(
                    AiKnowledgeDocumentModel.title.ilike(pattern),
                    AiKnowledgeDocumentModel.source_type.ilike(pattern),
                    AiKnowledgeDocumentModel.source_ref.ilike(pattern),
                    metadata["category"].astext.ilike(pattern),
                    metadata["namespace"].astext.ilike(pattern),
                    metadata["domain"].astext.ilike(pattern),
                    metadata["tags"].astext.ilike(pattern),
                )
            )

        filters = curatorial_filters or {}
        metadata = AiKnowledgeDocumentModel.document_metadata

        category = str(filters.get("category") or "").strip()
        if category:
            query = query.filter(metadata["category"].astext == category)

        namespace = str(filters.get("namespace") or "").strip()
        if namespace:
            query = query.filter(metadata["namespace"].astext == namespace)

        domain = str(filters.get("domain") or "").strip()
        if domain:
            query = query.filter(metadata["domain"].astext == domain)

        tag = str(filters.get("tag") or "").strip().lower()
        if tag:
            query = query.filter(metadata["tags"].astext.ilike(f'%"{tag}"%'))

        source_type = str(filters.get("sourceType") or "").strip()
        if source_type:
            query = query.filter(AiKnowledgeDocumentModel.source_type == source_type)

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

from app.application.services.knowledge_curatorial_metadata_service import enrich_document_payload
from app.domain.ports.knowledge_repository_port import KnowledgeRepositoryPort


class ListAdminKnowledgeDocumentsUseCase:
    def __init__(self, knowledge_repository: KnowledgeRepositoryPort):
        self.knowledge_repository = knowledge_repository

    def execute(
        self,
        limit: int = 20,
        offset: int = 0,
        search: str | None = None,
        active: str | None = None,
        category: str | None = None,
        namespace: str | None = None,
        domain: str | None = None,
        tag: str | None = None,
        source_type: str | None = None,
    ) -> dict:
        safe_limit = max(1, min(int(limit), 100))
        safe_offset = max(0, int(offset))
        active_filter = self._parse_active(active)
        curatorial_filters = {
            "category": category,
            "namespace": namespace,
            "domain": domain,
            "tag": tag,
            "sourceType": source_type,
        }

        rows = self.knowledge_repository.list_documents_with_chunk_count(
            limit=safe_limit,
            offset=safe_offset,
            search=search,
            active=active_filter,
            scope="global",
            curatorial_filters=curatorial_filters,
        )

        total = self.knowledge_repository.count_documents(
            search=search,
            active=active_filter,
            scope="global",
            curatorial_filters=curatorial_filters,
        )

        facets = self.knowledge_repository.get_global_curatorial_facets()

        return {
            "items": [
                {
                    "id": str(document.id),
                    "title": document.title,
                    "sourceType": document.source_type,
                    "sourceRef": document.source_ref,
                    "active": document.active,
                    "chunkCount": chunk_count,
                    "metadata": document.metadata,
                    **enrich_document_payload(document.metadata),
                    "createdAt": document.created_at.isoformat(),
                    "updatedAt": document.updated_at.isoformat(),
                }
                for document, chunk_count in rows
            ],
            "pagination": {
                "limit": safe_limit,
                "offset": safe_offset,
                "total": total,
                "hasNext": safe_offset + safe_limit < total,
                "hasPrevious": safe_offset > 0,
            },
            "filters": {
                "search": search or "",
                "active": active_filter,
                "category": category or "",
                "namespace": namespace or "",
                "domain": domain or "",
                "tag": tag or "",
                "sourceType": source_type or "",
            },
            "facets": facets,
        }

    def _parse_active(self, value: str | None) -> bool | None:
        if value is None or value == "":
            return None

        normalized = str(value).lower().strip()

        if normalized in {"true", "1", "active", "ativo"}:
            return True

        if normalized in {"false", "0", "inactive", "inativo"}:
            return False

        return None

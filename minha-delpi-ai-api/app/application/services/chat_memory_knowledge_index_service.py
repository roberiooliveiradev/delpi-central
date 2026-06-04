import hashlib
from uuid import UUID

from app.infrastructure.config.settings import Settings

_SOURCE_TYPE = "user_memory"
_SCOPE = "user_memory"


class ChatMemoryKnowledgeIndexService:
    """Indexa memórias persistentes ativas no RAG (recuperação semântica por embedding).

    Complementa a injeção lexical do `ChatUserMemoryService`: o turno pode recuperar
    memórias relevantes por similaridade, não só as mais recentes.
    """

    def __init__(self, *, knowledge_repository=None, embedding_gateway=None):
        self._knowledge_repository = knowledge_repository
        self._embedding_gateway = embedding_gateway

    def _repo(self):
        if self._knowledge_repository is None:
            from app.infrastructure.persistence.postgres_knowledge_repository import (
                PostgresKnowledgeRepository,
            )

            self._knowledge_repository = PostgresKnowledgeRepository()

        return self._knowledge_repository

    def _embedder(self):
        if self._embedding_gateway is None:
            from app.infrastructure.embeddings.local_embedding_gateway import (
                LocalEmbeddingGateway,
            )

            self._embedding_gateway = LocalEmbeddingGateway()

        return self._embedding_gateway

    @staticmethod
    def _enabled() -> bool:
        return bool(
            Settings.CHAT_USER_MEMORY_ENABLED and Settings.CHAT_USER_MEMORY_RAG_INDEX
        )

    @staticmethod
    def build_content(item: dict) -> str:
        type_label = {
            "preference": "Preferência",
            "profile": "Perfil",
            "correction": "Correção",
        }.get(str(item.get("type") or ""), "Memória")
        content = str(item.get("content") or "").strip()
        return f"[{type_label}] {content}"

    @staticmethod
    def _source_ref(item_id) -> str:
        return f"memory:{item_id}"

    def sync_item(self, item: dict) -> dict | None:
        if not self._enabled() or not isinstance(item, dict):
            return None

        if str(item.get("status")) != "active":
            return self.deindex_item(item.get("id"))

        user_id = item.get("userId")
        content = str(item.get("content") or "").strip()
        item_id = item.get("id")

        if not user_id or not content or item_id is None:
            return None

        return self.index_item(item)

    def reindex_all(self, items: list[dict]) -> dict:
        if not self._enabled():
            return {"enabled": False, "processed": 0, "indexed": 0, "skipped": 0}

        indexed = skipped = removed = 0

        for item in items or []:
            try:
                result = self.sync_item(item)
            except Exception:
                continue

            if result is None:
                removed += 1
            elif result.get("skipped"):
                skipped += 1
            else:
                indexed += 1

        return {
            "enabled": True,
            "processed": len(items or []),
            "indexed": indexed,
            "skipped": skipped,
            "removed": removed,
        }

    def index_item(self, item: dict) -> dict | None:
        if not self._enabled() or not isinstance(item, dict):
            return None

        content = self.build_content(item)
        item_id = item.get("id")
        user_id = str(item.get("userId") or "").strip()
        project_id = item.get("projectId")

        if not content or item_id is None or not user_id:
            return None

        source_ref = self._source_ref(item_id)
        metadata = {
            "scope": _SCOPE,
            "source": _SOURCE_TYPE,
            "origin": _SOURCE_TYPE,
            "memoryItemId": int(item_id) if isinstance(item_id, int) else str(item_id),
            "userId": user_id,
            "type": str(item.get("type") or "preference"),
            "contentHash": self._hash(content),
        }

        if project_id:
            metadata["projectId"] = str(project_id)

        title = content[:200]

        try:
            return self._upsert(
                title=title,
                content=content,
                source_ref=source_ref,
                metadata=metadata,
            )
        except Exception:
            return None

    def deindex_item(self, item_id) -> bool:
        if item_id is None:
            return False

        try:
            repo = self._repo()
            existing = repo.find_document_by_source_ref(
                self._source_ref(item_id),
                source_type=_SOURCE_TYPE,
            )

            if existing is None:
                return False

            repo.delete_document(self._as_uuid(existing.id))
            return True
        except Exception:
            return False

    def _upsert(self, *, title: str, content: str, source_ref: str, metadata: dict) -> dict:
        repo = self._repo()
        existing = repo.find_document_by_source_ref(source_ref, source_type=_SOURCE_TYPE)

        if existing is not None:
            existing_hash = (
                (existing.metadata or {}).get("contentHash")
                if getattr(existing, "metadata", None)
                else None
            )

            if existing_hash == metadata["contentHash"]:
                return {"id": str(existing.id), "skipped": True}

            document_id = self._as_uuid(existing.id)
            repo.update_document(document_id, content=content, metadata=metadata)
            repo.delete_chunks_by_document_id(document_id)
            self._embed_chunk(document_id, content, metadata)
            return {"id": str(existing.id), "reindexed": True}

        document = repo.create_document(
            title=title,
            source_type=_SOURCE_TYPE,
            content=content,
            source_ref=source_ref,
            metadata=metadata,
        )
        self._embed_chunk(self._as_uuid(document.id), content, metadata)
        return {"id": str(document.id), "created": True}

    def _embed_chunk(self, document_id: UUID, content: str, metadata: dict) -> None:
        embedding = self._embedder().embed(content)
        self._repo().create_chunk(
            document_id=document_id,
            chunk_index=0,
            content=content,
            embedding=embedding,
            metadata=dict(metadata),
        )

    @staticmethod
    def _hash(content: str) -> str:
        return hashlib.sha256((content or "").encode("utf-8")).hexdigest()

    @staticmethod
    def _as_uuid(value) -> UUID:
        if isinstance(value, UUID):
            return value
        return UUID(str(value))

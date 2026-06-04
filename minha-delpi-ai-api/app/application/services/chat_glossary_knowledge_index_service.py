import hashlib
from uuid import UUID

from app.infrastructure.config.settings import Settings

_SOURCE_TYPE = "glossary"


class ChatGlossaryKnowledgeIndexService:
    """Indexa termos de glossário aprovados como conhecimento RAG (playbook Fase 5).

    Faz upsert por `source_ref` estável (`glossary:{termId}`): cria, reindexa quando
    o significado muda e remove quando o termo é desativado. O documento entra no
    RAG existente (embedding + chunk), com fonte citável (`sourceType=glossary`).
    Gated por flag e best-effort: nunca quebra a promoção/edição admin.
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
            Settings.CHAT_LEARNING_ENABLED and Settings.CHAT_LEARNING_GLOSSARY_RAG_INDEX
        )

    @staticmethod
    def build_content(term: str, meaning: str) -> str:
        return f"{term}: {meaning}"

    @staticmethod
    def _source_ref(term_id) -> str:
        return f"glossary:{term_id}"

    def sync_term(self, term: dict) -> dict | None:
        """Reconcilia o índice RAG com o estado do termo (promoção/edição admin).

        Termo aprovado/ativo com significado é indexado; caso contrário, removido.
        """
        if not self._enabled() or not isinstance(term, dict):
            return None

        if str(term.get("type")) != "term_definition":
            return None

        is_active = bool(term.get("active", True)) and bool(term.get("approved", True))
        has_meaning = bool(str(term.get("meaning") or "").strip())

        if is_active and has_meaning:
            return self.index_term(term)

        self.deindex_term(term.get("id"))
        return None

    def reindex_all(self, terms: list[dict]) -> dict:
        """Backfill: reconcilia o índice RAG para uma lista de termos de glossário."""
        if not self._enabled():
            return {"enabled": False, "processed": 0, "indexed": 0, "skipped": 0}

        indexed = skipped = removed = 0

        for term in terms or []:
            try:
                result = self.sync_term(term)
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
            "processed": len(terms or []),
            "indexed": indexed,
            "skipped": skipped,
            "removed": removed,
        }

    def index_term(self, term: dict) -> dict | None:
        """Cria/atualiza o documento de conhecimento de um termo de glossário."""
        if not self._enabled() or not isinstance(term, dict):
            return None

        if str(term.get("type")) != "term_definition":
            return None

        term_text = str(term.get("term") or "").strip()
        meaning = str(term.get("meaning") or "").strip()
        term_id = term.get("id")

        if not term_text or not meaning or term_id is None:
            return None

        content = self.build_content(term_text, meaning)
        source_ref = self._source_ref(term_id)
        project_id = term.get("projectId")
        scope = "project_source" if project_id else "global"

        metadata = {
            "scope": scope,
            "source": _SOURCE_TYPE,
            "origin": _SOURCE_TYPE,
            "vocabularyTermId": int(term_id) if isinstance(term_id, int) else str(term_id),
            "term": term_text[:160],
            "type": "term_definition",
            "contentHash": self._hash(content),
        }

        if project_id:
            metadata["projectId"] = str(project_id)

        try:
            return self._upsert(
                title=term_text[:200],
                content=content,
                source_ref=source_ref,
                metadata=metadata,
            )
        except Exception:
            return None

    def deindex_term(self, term_id) -> bool:
        """Remove o documento de conhecimento do termo (desativação/rejeição)."""
        if term_id is None:
            return False

        try:
            repo = self._repo()
            existing = repo.find_document_by_source_ref(
                self._source_ref(term_id),
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
            source_ref=source_ref,
            content=content,
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

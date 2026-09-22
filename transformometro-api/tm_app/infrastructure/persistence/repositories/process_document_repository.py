from __future__ import annotations

from datetime import datetime, timezone
from typing import Any
from uuid import uuid4

from tm_app.domain.entities.process_document import ProcessDocument
from tm_app.domain.ports.process_document_repository_port import ProcessDocumentRepositoryPort
from tm_app.infrastructure.persistence.plugins.plugin_base_repository import (
    PluginBaseRepository,
)

_S = "transformometro"

_SELECT = f"""
SELECT
    d.document_id AS id,
    d.processo_id,
    d.title,
    d.content_md,
    d.created_by_user_id,
    d.updated_by_user_id,
    d.created_at,
    d.updated_at,
    d.deleted_at
FROM {_S}.process_documents d
"""


def _doc(row: dict[str, Any] | None) -> ProcessDocument | None:
    if not row:
        return None
    return ProcessDocument(
        id=str(row["id"]),
        processo_id=str(row["processo_id"]),
        title=str(row["title"] or ""),
        content_md=str(row.get("content_md") or ""),
        created_by_user_id=str(row["created_by_user_id"] or ""),
        updated_by_user_id=str(row["updated_by_user_id"] or ""),
        created_at=row.get("created_at"),
        updated_at=row.get("updated_at"),
        deleted_at=row.get("deleted_at"),
    )


class ProcessDocumentRepository(PluginBaseRepository, ProcessDocumentRepositoryPort):
    def process_exists(self, processo_id: str) -> bool:
        row = self.fetch_one(
            f"""
            SELECT 1 AS ok
            FROM {_S}.processos
            WHERE processo_id = %s::uuid AND deletado = FALSE
            """,
            (processo_id,),
        )
        return row is not None

    def list_by_processo(self, processo_id: str) -> list[ProcessDocument]:
        rows = self.fetch_all(
            f"""
            {_SELECT}
            WHERE d.processo_id = %s::uuid
              AND d.deleted_at IS NULL
            ORDER BY d.updated_at DESC, d.document_id DESC
            """,
            (processo_id,),
        )
        return [doc for row in rows if (doc := _doc(row)) is not None]

    def get(self, *, processo_id: str, document_id: str) -> ProcessDocument | None:
        row = self.fetch_one(
            f"""
            {_SELECT}
            WHERE d.processo_id = %s::uuid
              AND d.document_id = %s::uuid
              AND d.deleted_at IS NULL
            """,
            (processo_id, document_id),
        )
        return _doc(row)

    def get_by_document_id(self, document_id: str) -> ProcessDocument | None:
        row = self.fetch_one(
            f"""
            {_SELECT}
            WHERE d.document_id = %s::uuid
              AND d.deleted_at IS NULL
            """,
            (document_id,),
        )
        return _doc(row)

    def create(
        self,
        *,
        processo_id: str,
        title: str,
        content_md: str,
        actor_user_id: str,
    ) -> ProcessDocument:
        row = self.execute_returning_one(
            f"""
            INSERT INTO {_S}.process_documents (
                processo_id, title, content_md,
                created_by_user_id, updated_by_user_id
            ) VALUES (%s::uuid, %s, %s, %s, %s)
            RETURNING document_id
            """,
            (processo_id, title, content_md, actor_user_id, actor_user_id),
        )
        created = self.get(processo_id=processo_id, document_id=str(row["document_id"])) if row else None
        if created is None:
            raise RuntimeError("OUTCOME_VERIFICATION_FAILED")
        return created

    def update(
        self,
        *,
        processo_id: str,
        document_id: str,
        title: str | None,
        content_md: str | None,
        actor_user_id: str,
    ) -> ProcessDocument | None:
        sets: list[str] = ["updated_by_user_id = %s", "updated_at = NOW()"]
        params: list[Any] = [actor_user_id]
        if title is not None:
            sets.append("title = %s")
            params.append(title)
        if content_md is not None:
            sets.append("content_md = %s")
            params.append(content_md)
        params.extend([processo_id, document_id])
        self.execute(
            f"""
            UPDATE {_S}.process_documents
            SET {", ".join(sets)}
            WHERE processo_id = %s::uuid
              AND document_id = %s::uuid
              AND deleted_at IS NULL
            """,
            tuple(params),
        )
        return self.get(processo_id=processo_id, document_id=document_id)

    def soft_delete(
        self,
        *,
        processo_id: str,
        document_id: str,
        actor_user_id: str,
    ) -> ProcessDocument | None:
        row = self.fetch_one(
            f"""
            {_SELECT}
            WHERE d.processo_id = %s::uuid
              AND d.document_id = %s::uuid
              AND d.deleted_at IS NULL
            """,
            (processo_id, document_id),
        )
        if not row:
            return None
        self.execute(
            f"""
            UPDATE {_S}.process_documents
            SET deleted_at = NOW(),
                updated_by_user_id = %s,
                updated_at = NOW()
            WHERE processo_id = %s::uuid
              AND document_id = %s::uuid
              AND deleted_at IS NULL
            """,
            (actor_user_id, processo_id, document_id),
        )
        # Return deleted snapshot (get filters deleted_at IS NULL).
        now = datetime.now(timezone.utc)
        base = _doc(row)
        if base is None:
            return None
        return ProcessDocument(
            id=base.id,
            processo_id=base.processo_id,
            title=base.title,
            content_md=base.content_md,
            created_by_user_id=base.created_by_user_id,
            updated_by_user_id=actor_user_id,
            created_at=base.created_at,
            updated_at=now,
            deleted_at=now,
        )


class InMemoryProcessDocumentRepository(ProcessDocumentRepositoryPort):
    def __init__(self) -> None:
        self.processes: set[str] = set()
        self.documents: dict[str, ProcessDocument] = {}

    def process_exists(self, processo_id: str) -> bool:
        return processo_id in self.processes

    def list_by_processo(self, processo_id: str) -> list[ProcessDocument]:
        items = [
            doc
            for doc in self.documents.values()
            if doc.processo_id == processo_id and doc.deleted_at is None
        ]
        return sorted(
            items,
            key=lambda d: (d.updated_at or datetime.min.replace(tzinfo=timezone.utc), d.id),
            reverse=True,
        )

    def get(self, *, processo_id: str, document_id: str) -> ProcessDocument | None:
        doc = self.documents.get(document_id)
        if doc is None or doc.processo_id != processo_id or doc.deleted_at is not None:
            return None
        return doc

    def get_by_document_id(self, document_id: str) -> ProcessDocument | None:
        doc = self.documents.get(document_id)
        if doc is None or doc.deleted_at is not None:
            return None
        return doc

    def create(
        self,
        *,
        processo_id: str,
        title: str,
        content_md: str,
        actor_user_id: str,
    ) -> ProcessDocument:
        now = datetime.now(timezone.utc)
        doc = ProcessDocument(
            id=str(uuid4()),
            processo_id=processo_id,
            title=title,
            content_md=content_md,
            created_by_user_id=actor_user_id,
            updated_by_user_id=actor_user_id,
            created_at=now,
            updated_at=now,
        )
        self.documents[doc.id] = doc
        return doc

    def update(
        self,
        *,
        processo_id: str,
        document_id: str,
        title: str | None,
        content_md: str | None,
        actor_user_id: str,
    ) -> ProcessDocument | None:
        existing = self.get(processo_id=processo_id, document_id=document_id)
        if existing is None:
            return None
        now = datetime.now(timezone.utc)
        updated = ProcessDocument(
            id=existing.id,
            processo_id=existing.processo_id,
            title=title if title is not None else existing.title,
            content_md=content_md if content_md is not None else existing.content_md,
            created_by_user_id=existing.created_by_user_id,
            updated_by_user_id=actor_user_id,
            created_at=existing.created_at,
            updated_at=now,
        )
        self.documents[updated.id] = updated
        return updated

    def soft_delete(
        self,
        *,
        processo_id: str,
        document_id: str,
        actor_user_id: str,
    ) -> ProcessDocument | None:
        existing = self.get(processo_id=processo_id, document_id=document_id)
        if existing is None:
            return None
        now = datetime.now(timezone.utc)
        deleted = ProcessDocument(
            id=existing.id,
            processo_id=existing.processo_id,
            title=existing.title,
            content_md=existing.content_md,
            created_by_user_id=existing.created_by_user_id,
            updated_by_user_id=actor_user_id,
            created_at=existing.created_at,
            updated_at=now,
            deleted_at=now,
        )
        self.documents[deleted.id] = deleted
        return deleted

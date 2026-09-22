from __future__ import annotations

from typing import Any

from tm_app.application.security.authorization_policy import TransformometroAuthorizationPolicy
from tm_app.application.services.process_activity_touch import touch_processo_updated_at
from tm_app.domain.entities.process_document import ProcessDocument
from tm_app.domain.ports.process_document_repository_port import ProcessDocumentRepositoryPort
from tm_app.domain.services.process_document_rules import (
    normalize_document_actor,
    normalize_document_content_md,
    normalize_document_id,
    normalize_document_title,
    normalize_processo_id,
)


def _actor(user: Any) -> str:
    return normalize_document_actor(str(getattr(user, "id", "") or ""))


class ProcessDocumentUseCases:
    def __init__(
        self,
        repo: ProcessDocumentRepositoryPort,
        policy: TransformometroAuthorizationPolicy | None = None,
    ) -> None:
        self._repo = repo
        self._policy = policy or TransformometroAuthorizationPolicy()

    def list_documents(self, user: Any, processo_id: str) -> list[ProcessDocument]:
        self._policy.require_access(user)
        pid = normalize_processo_id(processo_id)
        if not self._repo.process_exists(pid):
            raise LookupError("Processo não encontrado.")
        return self._repo.list_by_processo(pid)

    def get_document(self, user: Any, processo_id: str, document_id: str) -> ProcessDocument:
        self._policy.require_access(user)
        pid = normalize_processo_id(processo_id)
        if not self._repo.process_exists(pid):
            raise LookupError("Processo não encontrado.")
        doc = self._repo.get(processo_id=pid, document_id=normalize_document_id(document_id))
        if doc is None:
            raise LookupError("Documento não encontrado.")
        return doc

    def get_document_by_id(self, user: Any, document_id: str) -> ProcessDocument:
        """Resolve by document PK (UUID unique). Used by GPT/MCP record adapters."""
        self._policy.require_access(user)
        doc = self._repo.get_by_document_id(normalize_document_id(document_id))
        if doc is None:
            raise LookupError("Documento não encontrado.")
        return doc

    def create_document(
        self,
        user: Any,
        processo_id: str,
        *,
        title: str,
        content_md: str = "",
    ) -> ProcessDocument:
        self._policy.require_access(user)
        actor = _actor(user)
        pid = normalize_processo_id(processo_id)
        if not self._repo.process_exists(pid):
            raise LookupError("Processo não encontrado.")
        normalized_title = normalize_document_title(title)
        normalized_content = normalize_document_content_md(content_md)
        created = self._repo.create(
            processo_id=pid,
            title=normalized_title,
            content_md=normalized_content,
            actor_user_id=actor,
        )
        confirmed = self._repo.get(processo_id=pid, document_id=created.id)
        if (
            confirmed is None
            or confirmed.processo_id != pid
            or confirmed.title != normalized_title
            or confirmed.content_md != normalized_content
            or confirmed.created_by_user_id != actor
        ):
            raise RuntimeError("OUTCOME_VERIFICATION_FAILED")
        touch_processo_updated_at(pid)
        return confirmed

    def update_document(
        self,
        user: Any,
        processo_id: str,
        document_id: str,
        *,
        title: str | None = None,
        content_md: str | None = None,
    ) -> ProcessDocument:
        self._policy.require_access(user)
        actor = _actor(user)
        pid = normalize_processo_id(processo_id)
        if not self._repo.process_exists(pid):
            raise LookupError("Processo não encontrado.")
        existing = self._repo.get(
            processo_id=pid,
            document_id=normalize_document_id(document_id),
        )
        if existing is None:
            raise LookupError("Documento não encontrado.")
        if title is None and content_md is None:
            raise ValueError("Informe título e/ou conteúdo para atualizar.")
        next_title = normalize_document_title(title) if title is not None else None
        next_content = (
            normalize_document_content_md(content_md) if content_md is not None else None
        )
        updated = self._repo.update(
            processo_id=pid,
            document_id=existing.id,
            title=next_title,
            content_md=next_content,
            actor_user_id=actor,
        )
        if updated is None:
            raise LookupError("Documento não encontrado.")
        expected_title = next_title if next_title is not None else existing.title
        expected_content = next_content if next_content is not None else existing.content_md
        confirmed = self._repo.get(processo_id=pid, document_id=existing.id)
        if (
            confirmed is None
            or confirmed.title != expected_title
            or confirmed.content_md != expected_content
            or confirmed.updated_by_user_id != actor
        ):
            raise RuntimeError("OUTCOME_VERIFICATION_FAILED")
        touch_processo_updated_at(pid)
        return confirmed

    def delete_document(self, user: Any, processo_id: str, document_id: str) -> ProcessDocument:
        self._policy.require_access(user)
        actor = _actor(user)
        pid = normalize_processo_id(processo_id)
        if not self._repo.process_exists(pid):
            raise LookupError("Processo não encontrado.")
        existing = self._repo.get(
            processo_id=pid,
            document_id=normalize_document_id(document_id),
        )
        if existing is None:
            raise LookupError("Documento não encontrado.")
        deleted = self._repo.soft_delete(
            processo_id=pid,
            document_id=existing.id,
            actor_user_id=actor,
        )
        if deleted is None or deleted.deleted_at is None:
            raise RuntimeError("OUTCOME_VERIFICATION_FAILED")
        confirmed = self._repo.get(processo_id=pid, document_id=existing.id)
        if confirmed is not None:
            raise RuntimeError("OUTCOME_VERIFICATION_FAILED")
        touch_processo_updated_at(pid)
        return deleted

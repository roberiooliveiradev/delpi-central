"""Caso de uso P2-Upload SLICE-1 — U1 upload, U2 list, U3 get, U4 download.

Orquestra a sequência C2 do doc 103: validação de envelope → `.part` em
chunks com cap mid-stream → sha256 + validação de conteúdo → idempotência
D-U7 → `os.replace` atômico → transação Postgres única → compensação
`unlink` em falha recuperável. Nenhuma atomicidade distribuída é
declarada; falha de compensação é log sem sucesso falso.
"""

from __future__ import annotations

import hashlib
import json
import logging
import uuid
from pathlib import Path
from typing import Iterable

from controllership_finance_app.domain.closing_checklist.errors import (
    DocumentNotFound,
    FileMissing,
    IdempotencyConflict,
    InvalidUpload,
    ItemNotFound,
)
from controllership_finance_app.domain.closing_documents.file_validation import (
    sanitize_original_name,
    validate_upload_content,
)
from controllership_finance_app.domain.closing_documents.resource_scope import (
    normalize_request_scope,
    scope_in_context,
)
from controllership_finance_app.infrastructure.persistence.closing_document_repository import (
    ClosingDocumentRepository,
)
from controllership_finance_app.infrastructure.storage.closing_document_storage import (
    ClosingDocumentStorage,
)

logger = logging.getLogger(__name__)


def _request_hash(
    *,
    snapshot_item_id: str | None,
    title: str | None,
    attachment_role: str,
    checksum_sha256: str,
) -> str:
    """Hash canônico do request (padrão supplies-api): campos do payload
    + hash do binário — replay idêntico ⇒ deduplica; divergente ⇒ 409.
    O hash de conteúdo NÃO colapsa evidências: só entra no request_hash
    junto dos demais campos para distinguir replays de chamadas novas."""
    canonical = json.dumps(
        {
            "snapshot_item_id": snapshot_item_id,
            "title": title,
            "attachment_role": attachment_role,
            "checksum_sha256": checksum_sha256,
        },
        sort_keys=True,
        separators=(",", ":"),
    )
    return hashlib.sha256(canonical.encode("utf-8")).hexdigest()


class ClosingDocumentService:
    def __init__(
        self,
        repository: ClosingDocumentRepository | None = None,
        storage: ClosingDocumentStorage | None = None,
    ) -> None:
        self._repository = repository or ClosingDocumentRepository()
        self._storage = storage or ClosingDocumentStorage()

    # -- U1 --------------------------------------------------------------------

    def upload(
        self,
        *,
        period: str,
        actor: str,
        original_name: str,
        declared_mime: str | None,
        chunks: Iterable[bytes],
        snapshot_item_id: str | None,
        title: str | None,
        attachment_role: str | None,
        idempotency_key: str,
        branch_scope: str | None = None,
    ) -> tuple[dict, bool]:
        """Cria evidência `ATTACHED`; retorna ``(documento, created)``.

        ``created=False`` ⇒ replay idempotente (deduplicated). O item do
        snapshot nunca muda de estado — continua `EXPECTED`.

        Resource scope (doc 103): o documento herda o `branch_scope` do
        item; item fora do filial-contexto declarado é `item_not_found`
        (404 — existência nunca vaza).
        """
        competence_id = self._repository.get_competence_id(period)
        request_scope = normalize_request_scope(branch_scope)

        key = (idempotency_key or "").strip()
        if not 1 <= len(key) <= 128:
            raise InvalidUpload(
                "idempotency_key deve ter entre 1 e 128 caracteres."
            )
        role = (attachment_role or "generic").strip() or "generic"
        if role != "generic":
            raise InvalidUpload(
                "attachment_role deve ser 'generic' nesta versão."
            )

        link_kind = "competence"
        item_id = None
        if snapshot_item_id:
            item = self._repository.get_snapshot_item(
                competence_id, snapshot_item_id
            )
            if not scope_in_context(
                request_scope=request_scope,
                document_scope=item.get("branch_scope"),
            ):
                raise ItemNotFound("Item do checklist não encontrado.")
            item_id = str(item["snapshot_item_id"])
            link_kind = "competence_item"

        display_name = sanitize_original_name(original_name)
        clean_title = (title or "").strip()[:255] or None
        file_uuid = uuid.uuid4()

        tmp_path, checksum, size = self._storage.write_temp(
            file_uuid, chunks
        )
        try:
            content = tmp_path.read_bytes()
            extension, mime_type = validate_upload_content(
                original_name=display_name,
                declared_mime=declared_mime,
                content=content,
            )
            request_hash = _request_hash(
                snapshot_item_id=item_id,
                title=clean_title,
                attachment_role=role,
                checksum_sha256=checksum,
            )
            existing = self._repository.find_document_by_idempotency(
                competence_id, key
            )
        except Exception:
            # Rejeitado antes da publicação: `.part` nunca permanece.
            self._storage.discard_temp(file_uuid)
            raise

        if existing is not None:
            self._storage.discard_temp(file_uuid)
            if existing["request_hash"] != request_hash:
                raise IdempotencyConflict(
                    "Chave de idempotência já utilizada com payload "
                    "divergente."
                )
            return (
                self._repository.get_document_by_id(
                    competence_id, str(existing["document_id"])
                ),
                False,
            )

        try:
            storage_key, stored_name, _final_path = self._storage.publish(
                tmp_path,
                competence_id=competence_id,
                file_uuid=file_uuid,
                extension=extension,
            )
        except Exception:
            self._storage.discard_temp(file_uuid)
            raise
        try:
            document, created = self._repository.create_document(
                competence_id=competence_id,
                snapshot_item_id=item_id,
                link_kind=link_kind,
                title=clean_title,
                attachment_role=role,
                idempotency_key=key,
                request_hash=request_hash,
                storage_key=storage_key,
                original_name=display_name,
                stored_name=stored_name,
                mime_type=mime_type,
                extension=extension,
                size_bytes=size,
                checksum_sha256=checksum,
                actor=actor,
            )
        except Exception:
            # Compensação C2: binário publicado sem metadado ⇒ remove.
            if not self._storage.remove(storage_key):
                logger.warning(
                    "orphan_binary_after_persistence_failure "
                    "storage_key=%s",
                    storage_key,
                )
            raise
        if not created:
            # Corrida perdida: nosso binário ficou órfão ⇒ compensa.
            self._storage.remove(storage_key)
        return document, created

    # -- U2/U3 -----------------------------------------------------------------

    def list_documents(
        self,
        *,
        period: str,
        snapshot_item_id: str | None,
        link_kind: str | None,
        state: str | None,
        branch_scope: str | None,
        limit: int,
        offset: int,
    ) -> dict:
        competence_id = self._repository.get_competence_id(period)
        request_scope = normalize_request_scope(branch_scope)
        return self._repository.list_documents(
            competence_id,
            snapshot_item_id=snapshot_item_id,
            link_kind=link_kind,
            state=state,
            branch_scope=(
                request_scope if request_scope != "BOTH" else None
            ),
            limit=limit,
            offset=offset,
        )

    def get_document(
        self, *, period: str, document_id: str, branch_scope: str | None
    ) -> dict:
        competence_id = self._repository.get_competence_id(period)
        request_scope = normalize_request_scope(branch_scope)
        row = self._repository.get_document_by_id(
            competence_id, document_id
        )
        # Resource scope: fora do filial-contexto declarado = 404.
        if not scope_in_context(
            request_scope=request_scope,
            document_scope=row.get("branch_scope"),
        ):
            raise DocumentNotFound("Documento não encontrado.")
        return row

    # -- U4 --------------------------------------------------------------------

    def resolve_download(
        self,
        *,
        period: str,
        document_id: str,
        version_no: int,
        actor: str,
        branch_scope: str | None = None,
    ) -> tuple[Path, dict]:
        """Versão + arquivo + auditoria `DOCUMENT_DOWNLOADED` (D-U3=A).

        O evento registra a *decisão de autorização* — nunca a entrega:
        `FileResponse` não prova que os bytes chegaram ao cliente, logo
        conclusão/interrupção de transferência não é reivindicada.

        - `AUTHORIZED`/`phase=authorization`: authz concedida e binário
          confirmado disponível; a resposta só então é iniciada.
        - `DENIED`/`phase=authorization`: documento existe mas está fora
          do filial-contexto declarado — auditável (ator+recurso
          conhecidos); a resposta permanece 404 sem vazar existência.
        - `FAILED`/`phase=delivery`: autorizado, porém o binário está
          ausente/inválido — entrega impossível antes da transmissão.
        """
        competence_id = self._repository.get_competence_id(period)
        request_scope = normalize_request_scope(branch_scope)
        version_file = self._repository.get_version_file(
            competence_id, document_id, version_no
        )
        if not scope_in_context(
            request_scope=request_scope,
            document_scope=version_file.get("branch_scope"),
        ):
            self._repository.audit_download(
                competence_id=competence_id,
                document_id=document_id,
                version_no=version_no,
                actor=actor,
                result="DENIED",
            )
            raise DocumentNotFound("Documento não encontrado.")
        try:
            path = self._storage.resolve(version_file["storage_key"])
        except FileMissing:
            self._repository.audit_download(
                competence_id=competence_id,
                document_id=document_id,
                version_no=version_no,
                actor=actor,
                result="FAILED",
            )
            raise
        self._repository.audit_download(
            competence_id=competence_id,
            document_id=document_id,
            version_no=version_no,
            actor=actor,
            result="AUTHORIZED",
        )
        return path, version_file

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
    DocumentCancelled,
    DocumentNotAttached,
    DocumentNotFound,
    FileMissing,
    Forbidden,
    IdempotencyConflict,
    InvalidUpload,
    ItemNotFound,
    StaleRevision,
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


def _version_request_hash(*, checksum_sha256: str) -> str:
    """Hash canônico do request de substituição (D-U7=A no aggregate
    `document_version`): o payload da mutação é o binário — `revision`
    é entrada de OCC, não identidade do request; `branch_scope` é
    contexto, não conteúdo. Replay idêntico (mesma key + mesmo binário)
    deduplica; mesma key + binário divergente ⇒ `idempotency_conflict`."""
    canonical = json.dumps(
        {"checksum_sha256": checksum_sha256},
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

    # -- U5 — substituição (SLICE-2) -------------------------------------------

    def replace_document(
        self,
        *,
        period: str,
        document_id: str,
        actor: str,
        can_manage: bool,
        original_name: str,
        declared_mime: str | None,
        chunks: Iterable[bytes],
        expected_revision: int,
        idempotency_key: str,
        branch_scope: str | None = None,
    ) -> tuple[dict, bool]:
        """Versão N+1 `ATTACHED`; retorna ``(documento, created)``.

        ``created=False`` ⇒ replay idempotente (deduplicated): a mesma
        `idempotency_key`+`request_hash` já produziu a versão — nenhuma
        versão, evento ou binário novo é criado. Autorização D-U1=A:
        uploader original OU `manage` efetivo — sempre somado a `access`
        + resource scope + business rule (`manage` sozinho não chega
        aqui — a rota exige `access` antes). OCC: `revision` reavaliada
        sob `FOR UPDATE` — concorrente obsoleto recebe `stale_revision`;
        a anterior fica `SUPERSEDED` por derivação de
        `current_version_no`, nunca por UPDATE na linha imutável.
        """
        document = self._document_in_scope(
            period=period,
            document_id=document_id,
            branch_scope=branch_scope,
        )
        _assert_active_state(document["state"])
        _assert_owner_or_manage(document, actor, can_manage)
        key = (idempotency_key or "").strip()
        if not 1 <= len(key) <= 128:
            raise InvalidUpload(
                "idempotency_key deve ter entre 1 e 128 caracteres."
            )
        competence_id = str(document["competence_id"])

        display_name = sanitize_original_name(original_name)
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
        except Exception:
            self._storage.discard_temp(file_uuid)
            raise

        # D-U7=A no aggregate da mutação: a key identifica ESTE request
        # de substituição (nunca a key U1). Replay idêntico deduplica
        # antes de publicar binário novo; divergente = 409; a checagem
        # sob lock em add_version é a autoridade final de corrida.
        request_hash = _version_request_hash(checksum_sha256=checksum)
        prior = self._repository.find_version_by_idempotency(
            str(document["document_id"]), key
        )
        if prior is not None:
            self._storage.discard_temp(file_uuid)
            if prior["request_hash"] != request_hash:
                raise IdempotencyConflict(
                    "Chave de idempotência já utilizada com payload "
                    "divergente."
                )
            return (
                self._repository.get_document_by_id(
                    competence_id, str(document["document_id"])
                ),
                False,
            )
        if document["revision"] != expected_revision:
            # Fail-fast honesto antes de escrever bytes; o repositório
            # revalida sob lock (corrida real ainda é `stale_revision`).
            self._storage.discard_temp(file_uuid)
            raise StaleRevision(
                "O documento foi alterado. Atualize e tente novamente."
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
            document, created = self._repository.add_version(
                competence_id=competence_id,
                document_id=str(document["document_id"]),
                expected_revision=expected_revision,
                storage_key=storage_key,
                original_name=display_name,
                stored_name=stored_name,
                mime_type=mime_type,
                extension=extension,
                size_bytes=size,
                checksum_sha256=checksum,
                idempotency_key=key,
                request_hash=request_hash,
                actor=actor,
            )
            if not created:
                # Corrida perdida sob lock: o vencedor já materializou a
                # versão — o binário que publicamos é órfão e sai.
                self._storage.remove(storage_key)
            return document, created
        except Exception:
            # Compensação C2 — binário novo publicado sem versão ⇒ remove.
            # O binário da versão anterior NUNCA é tocado.
            if not self._storage.remove(storage_key):
                logger.warning(
                    "orphan_binary_after_version_failure "
                    "storage_key=%s",
                    storage_key,
                )
            raise

    # -- U7 — cancelamento (SLICE-2) --------------------------------------------

    def cancel_document(
        self,
        *,
        period: str,
        document_id: str,
        actor: str,
        can_manage: bool,
        expected_revision: int,
        branch_scope: str | None = None,
    ) -> dict:
        """Cancelamento lógico — `CANCELLED != DELETED`: arquivos,
        versões e auditoria permanecem consultáveis (U3/U6/U8)."""
        document = self._document_in_scope(
            period=period,
            document_id=document_id,
            branch_scope=branch_scope,
        )
        _assert_active_state(document["state"])
        _assert_owner_or_manage(document, actor, can_manage)
        return self._repository.cancel_document(
            competence_id=str(document["competence_id"]),
            document_id=str(document["document_id"]),
            expected_revision=expected_revision,
            actor=actor,
        )

    # -- U6/U8 — histórico e eventos (SLICE-2) -----------------------------------

    def list_document_versions(
        self, *, period: str, document_id: str, branch_scope: str | None
    ) -> list[dict]:
        document = self._document_in_scope(
            period=period,
            document_id=document_id,
            branch_scope=branch_scope,
        )
        return self._repository.list_document_versions(
            str(document["competence_id"]), str(document["document_id"])
        )

    def list_document_events(
        self,
        *,
        period: str,
        document_id: str,
        branch_scope: str | None,
        limit: int,
        offset: int,
    ) -> dict:
        document = self._document_in_scope(
            period=period,
            document_id=document_id,
            branch_scope=branch_scope,
        )
        return self._repository.list_document_events(
            str(document["competence_id"]),
            str(document["document_id"]),
            limit=limit,
            offset=offset,
        )

    # -- internals ----------------------------------------------------------------

    def _document_in_scope(
        self, *, period: str, document_id: str, branch_scope: str | None
    ) -> dict:
        """Documento da competência do path + filial-contexto declarado.

        Cross-competence e cross-scope são 404 — existência nunca vaza
        (resource scope do contrato, mesmo critério de U3/U4)."""
        competence_id = self._repository.get_competence_id(period)
        request_scope = normalize_request_scope(branch_scope)
        row = self._repository.get_document_by_id(
            competence_id, document_id
        )
        if not scope_in_context(
            request_scope=request_scope,
            document_scope=row.get("branch_scope"),
        ):
            raise DocumentNotFound("Documento não encontrado.")
        return row


def _assert_active_state(state: str) -> None:
    """Mutações documentais só partem de `ATTACHED`; `CANCELLED` é
    terminal (`CANCELLED != DELETED` — histórico continua consultável)."""
    if state == "CANCELLED":
        raise DocumentCancelled(
            "Documento cancelado não pode ser alterado."
        )
    if state != "ATTACHED":
        raise DocumentNotAttached(
            "Documento não está em estado que permita alteração."
        )


def _assert_owner_or_manage(
    document: dict, actor: str, can_manage: bool
) -> None:
    """D-U1=A — mutação só pelo uploader original ou `manage` efetivo."""
    if str(document["uploaded_by"]) != actor and not can_manage:
        raise Forbidden(
            "Somente quem anexou ou um gestor pode alterar esta evidência."
        )

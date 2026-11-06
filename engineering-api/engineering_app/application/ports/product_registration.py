"""Ports do bounded context Product Registration.

Persistência: adapter Postgres dedicado (principal próprio —
``ENG_PRC_DB_*``, nunca ``PLUGINS_DB_*``), in-memory para dev/testes,
unavailable fail-honest.

Leitura oficial: ``OfficialProductReaderPort`` — contrato READ-ONLY do
owner (api-delpi → TOTVS); a Engineering API nunca escreve no ERP.

Payloads de retorno são dicts prontos para o envelope ``ok()`` do edge.
"""

from __future__ import annotations

from typing import Any, Protocol


class ProductRegistrationRepository(Protocol):
    """Persistência do módulo — owner: Engineering API."""

    # --- idempotência -------------------------------------------------------

    def find_idempotent(
        self, *, actor_or_source: str, operation: str, idempotency_key: str
    ) -> dict[str, Any] | None:
        """Registro gravado da chave — ``None`` se inexistente/expirado."""
        ...

    def save_idempotent(
        self,
        *,
        actor_or_source: str,
        operation: str,
        idempotency_key: str,
        request_fingerprint: str,
        request_id: str | None,
        response_status: int,
        response_payload: dict[str, Any],
    ) -> None: ...

    # --- requests + drafts ---------------------------------------------------

    def create_request(
        self, *, request: dict[str, Any], draft: dict[str, Any], event: dict[str, Any]
    ) -> dict[str, Any]:
        """Insere request + draft + evento submitted na mesma transação."""
        ...

    def get_request(self, request_id: str) -> dict[str, Any] | None:
        """Request + draft (1:1); ``None`` quando inexistente."""
        ...

    def get_request_by_external_ref(
        self, *, source: str, external_request_id: str, external_item_id: str | None
    ) -> dict[str, Any] | None: ...

    def list_requests(
        self,
        *,
        status: str | None = None,
        request_type: str | None = None,
        assignee: str | None = None,
        source: str | None = None,
        search: str | None = None,
        date_from: str | None = None,
        date_to: str | None = None,
        requester_subject: str | None = None,
        global_scope: bool = False,
        page: int = 1,
        page_size: int = 25,
    ) -> dict[str, Any]: ...

    def apply_transition(
        self,
        *,
        request_id: str,
        expected_version: int,
        allowed_from: frozenset[str],
        actor_label: str,
        actor_subject: str,
        event_type: str,
        next_status: str,
        set_fields: dict[str, Any],
        reason: str | None,
        event_meta: dict[str, Any],
    ) -> dict[str, Any]:
        """CAS atômico: revalida status+row_version, aplica transição,
        incrementa row_version e grava evento na mesma transação."""
        ...

    def update_draft(
        self,
        *,
        request_id: str,
        expected_version: int,
        actor_subject: str,
        changes: list[dict[str, Any]],
        event_meta: dict[str, Any],
    ) -> dict[str, Any]:
        """CAS do draft em ``in_progress``: aplica changes campo-a-campo,
        bump row_version (request+draft) e grava evento draft_changed."""
        ...

    # --- verificações oficiais -------------------------------------------------

    def insert_verification(
        self, *, request_id: str, verification: dict[str, Any]
    ) -> dict[str, Any]: ...

    def list_verifications(self, request_id: str) -> list[dict[str, Any]]: ...

    # --- technical records + revisions -----------------------------------------

    def get_record(self, record_id: str) -> dict[str, Any] | None: ...

    def get_record_by_official_code(
        self, *, official_source: str, official_code: str
    ) -> dict[str, Any] | None: ...

    def list_revisions(self, record_id: str) -> list[dict[str, Any]]: ...

    def get_revision(
        self, record_id: str, revision_number: int
    ) -> dict[str, Any] | None: ...

    def complete_request(
        self,
        *,
        request_id: str,
        expected_version: int,
        actor_subject: str,
        official_code: str,
        official_source: str,
        base_revision: int | None,
        revision_snapshot: dict[str, Any],
        revision_changes: list[dict[str, Any]],
        verification: dict[str, Any],
        reason: str | None,
        event_meta: dict[str, Any],
    ) -> dict[str, Any]:
        """Transação única de conclusão: revalida CAS/estado/revisão-base,
        cria revision imutável, move ponteiro do record, marca request
        ``completed`` e grava verification matched + evento."""
        ...


class OfficialProductReaderPort(Protocol):
    """Leitura oficial read-only de produto+fornecedores (TOTVS).

    Retorna dict honesto:
    ``{"status": available|not_found|forbidden|unavailable|timeout|contract_error,
       "product": {...view=engineering}, "suppliers": [...], "reason": str}``
    """

    async def read_product(
        self, *, access_token: str, request_id: str, official_code: str
    ) -> dict[str, Any]: ...

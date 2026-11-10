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

    # --- attendance flags (D16) -----------------------------------------------

    def create_flag(
        self, *, flag: dict[str, Any], event: dict[str, Any]
    ) -> dict[str, Any]:
        """Insere bandeira + evento flag.created na mesma transação."""
        ...

    def get_flag(
        self, *, request_id: str, flag_id: str, include_deleted: bool = False
    ) -> dict[str, Any] | None: ...

    def list_flags(
        self,
        *,
        request_id: str,
        status: str | None = None,
        page: int = 1,
        page_size: int = 25,
    ) -> dict[str, Any]:
        """Lista não deletadas; status=OPEN|RESOLVED|None(all)."""
        ...

    def update_flag(
        self,
        *,
        request_id: str,
        flag_id: str,
        expected_version: int,
        patch: dict[str, Any],
        actor_subject: str,
        actor_display_name: str | None,
        event: dict[str, Any],
    ) -> dict[str, Any]:
        """CAS + evento flag.updated."""
        ...

    def transition_flag(
        self,
        *,
        request_id: str,
        flag_id: str,
        expected_version: int,
        next_status: str,
        actor_subject: str,
        actor_display_name: str | None,
        event: dict[str, Any],
    ) -> dict[str, Any]:
        """resolve/reopen com CAS + evento."""
        ...

    def soft_delete_flag(
        self,
        *,
        request_id: str,
        flag_id: str,
        expected_version: int,
        actor_subject: str,
        actor_display_name: str | None,
        event: dict[str, Any],
    ) -> dict[str, Any]:
        """Soft-delete + evento flag.deleted; preserva histórico."""
        ...

    # --- information rounds (PRC-REF-019) ------------------------------------

    def create_information_round(
        self,
        *,
        request_id: str,
        expected_version: int,
        allowed_from: frozenset[str],
        next_status: str,
        actor_label: str,
        actor_subject: str,
        actor_email: str | None,
        event_type: str,
        reason: str | None,
        event_meta: dict[str, Any],
        round_row: dict[str, Any],
        questions: list[dict[str, Any]],
        set_fields: dict[str, Any] | None = None,
    ) -> dict[str, Any]:
        """CAS + transição do caso + insert rodada/perguntas + evento."""
        ...

    def get_information_round(
        self, *, request_id: str, round_id: str
    ) -> dict[str, Any] | None: ...

    def list_information_rounds(
        self, *, request_id: str
    ) -> list[dict[str, Any]]: ...

    def save_information_answers_draft(
        self,
        *,
        request_id: str,
        round_id: str,
        expected_round_version: int,
        actor_subject: str,
        answers: list[dict[str, Any]],
        event: dict[str, Any],
    ) -> dict[str, Any]:
        """Persiste rascunhos por pergunta; CAS da rodada."""
        ...

    def submit_information_answers(
        self,
        *,
        request_id: str,
        round_id: str,
        expected_round_version: int,
        actor_subject: str,
        answers: list[dict[str, Any]],
        event: dict[str, Any],
    ) -> dict[str, Any]:
        """Envia respostas; rodada → awaiting_review; CAS."""
        ...

    def accept_information_question(
        self,
        *,
        request_id: str,
        round_id: str,
        question_id: str,
        expected_round_version: int,
        actor_subject: str,
        actor_display_name: str | None,
        event: dict[str, Any],
    ) -> dict[str, Any]:
        """Aceita esclarecimento de uma pergunta; resolve rodada se todas."""
        ...

    def create_information_follow_up(
        self,
        *,
        request_id: str,
        parent_round_id: str,
        expected_parent_version: int,
        actor_label: str,
        actor_subject: str,
        actor_email: str | None,
        event: dict[str, Any],
        round_row: dict[str, Any],
        questions: list[dict[str, Any]],
        follow_up_question_ids: list[str],
    ) -> dict[str, Any]:
        """Encerra perguntas alvo na rodada pai e abre nova rodada."""
        ...

    def resolve_open_information_rounds(
        self,
        *,
        request_id: str,
        actor_subject: str,
        actor_display_name: str | None,
        event: dict[str, Any],
    ) -> list[dict[str, Any]]:
        """Resolve rodadas abertas (dispensa explícita no resume)."""
        ...

    # --- correction returns (PRC-REF-022) ------------------------------------

    def get_correction_return(
        self, *, request_id: str, return_id: str
    ) -> dict[str, Any] | None: ...

    def get_open_correction_return(
        self, *, request_id: str
    ) -> dict[str, Any] | None: ...

    def list_correction_returns(
        self, *, request_id: str
    ) -> list[dict[str, Any]]: ...

    def create_correction_return(
        self,
        *,
        request_id: str,
        expected_version: int,
        actor_subject: str,
        actor_label: str,
        actor_email: str | None,
        reason: str | None,
        event_meta: dict[str, Any],
        return_row: dict[str, Any],
        targets: list[dict[str, Any]],
    ) -> dict[str, Any]:
        """CAS in_progress → needs_correction + ciclo aberto + evento."""
        ...

    def update_returned_fields(
        self,
        *,
        request_id: str,
        expected_version: int,
        actor_subject: str,
        actor_display_name: str | None,
        actor_email: str | None,
        changes: list[dict[str, Any]],
        addressed_supplier_keys: set[str] | None = None,
        event_meta: dict[str, Any],
    ) -> dict[str, Any]:
        """Patch allowlisted no draft sob needs_correction + marca alvos."""
        ...

    def resubmit_correction(
        self,
        *,
        request_id: str,
        expected_version: int,
        actor_subject: str,
        actor_label: str,
        actor_email: str | None,
        event_meta: dict[str, Any],
    ) -> dict[str, Any]:
        """Fecha ciclo aberto e retorna caso a in_progress."""
        ...

    # --- PRC-REF-023 — vínculo documental -------------------------------------

    def create_attachment(self, *, attachment: dict[str, Any]) -> dict[str, Any]:
        """Persiste metadado do anexo já gravado no storage."""
        ...

    def list_attachments(self, *, request_id: str) -> list[dict[str, Any]]:
        """Documentos do caso (estados visíveis; nunca storage_key)."""
        ...

    def get_attachment(
        self, *, request_id: str, attachment_id: str
    ) -> dict[str, Any] | None:
        """Anexo do caso — identidade composta (nunca id solto)."""
        ...

    def find_attachment_by_hash(
        self, *, request_id: str, sha256: str, original_file_name: str
    ) -> dict[str, Any] | None:
        """Dedup idempotente: mesmo bytes+nome no mesmo caso."""
        ...


class AttachmentStoragePort(Protocol):
    """PRC-REF-023 — port de bytes (provider governado).

    storage_key é opaco e nunca exposto em DTO/log de request.
    """

    def save(self, key: str, content: bytes) -> None: ...

    def exists(self, key: str) -> bool: ...

    def open_path(self, key: str): ...

    def delete(self, key: str) -> None: ...


class OfficialProductReaderPort(Protocol):
    """Leitura oficial read-only de produto+fornecedores (TOTVS).

    Retorna dict honesto:
    ``{"status": available|not_found|forbidden|unavailable|timeout|contract_error,
       "product": {...view=engineering}, "suppliers": [...], "reason": str}``
    """

    async def read_product(
        self, *, access_token: str, request_id: str, official_code: str
    ) -> dict[str, Any]: ...

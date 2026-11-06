"""Erros de domínio/aplicação do Product Registration → estados honestos.

Mapeamento no edge (PRODUCT-REGISTRATION-MVP-TECHNICAL-CONTRACT §3):
400 malformed · 401 unauthenticated · 403 forbidden · 404 not_found ·
409 state_conflict|stale_version|duplicate_external_reference|erp_mismatch ·
422 validation_error|unverifiable_field · 502 official_contract_error ·
503 official_unavailable · 504 official_timeout.
"""

from __future__ import annotations


class PrcRepositoryError(Exception):
    """Falha técnica da persistência → `unavailable` (503 no edge)."""


class PrcNotFoundError(Exception):
    """Recurso inexistente → 404 no edge."""

    def __init__(self, resource: str, resource_id: str) -> None:
        super().__init__(f"{resource} {resource_id} not found")
        self.resource = resource
        self.resource_id = resource_id


class PrcValidationError(Exception):
    """Payload inválido → 400/422 com detalhes de campo."""

    def __init__(self, message: str, fields: dict[str, str] | None = None) -> None:
        super().__init__(message)
        self.fields = fields or {}


class PrcUnverifiableFieldError(PrcValidationError):
    """Campo sem leitura oficial autorizada → 422 `unverifiable_field`."""


class PrcConcurrencyError(Exception):
    """Conflito otimista (expectedVersion/row_version) → 409 stale_version."""


class PrcStaleRevisionError(PrcConcurrencyError):
    """baseRevision != revisão vigente do record → 409 stale_revision."""


class PrcStateConflictError(Exception):
    """Transição inválida para o estado atual → 409 state_conflict."""


class PrcForbiddenError(Exception):
    """Recurso fora do escopo do ator → 403 no edge."""


class PrcDuplicateError(Exception):
    """Referência externa/idempotency key com payload divergente → 409."""


class PrcOfficialError(Exception):
    """Falha/divergência da fonte oficial (TOTVS via api-delpi).

    ``kind``:
    - ``not_found``      → produto inexistente no ERP (404 ao cliente? não —
      o caso permanece under_review; edge devolve 409 erp_mismatch? Não:
      contrato define 404 somente para recurso inexistente; produto não
      encontrado é falha de verificação → ``result=not_found``, 409);
    - ``mismatch``       → 409 ``erp_mismatch`` com field_results redigidos;
    - ``unverifiable``   → 422 ``unverifiable_field``;
    - ``forbidden``      → 403;
    - ``unavailable``    → 503 ``official_unavailable``;
    - ``timeout``        → 504 ``official_timeout``;
    - ``contract_error`` → 502 ``official_contract_error``.

    ``verification`` carrega o attempt persistido (auditoria) para o edge
    devolver evidência honesta sem vazar payload oficial.
    """

    def __init__(
        self,
        kind: str,
        message: str,
        *,
        verification: dict | None = None,
        field_results: dict | None = None,
    ) -> None:
        super().__init__(message)
        self.kind = kind
        self.verification = verification
        self.field_results = field_results

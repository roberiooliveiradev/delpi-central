"""Contratos internos da exportação de XML de NF-e. Não alteram a NF-e pública."""

from __future__ import annotations

from dataclasses import dataclass
from datetime import date


STATUS_PROCESSING = "processing"
STATUS_SUCCESS = "success"
STATUS_FAILED = "failed"
STATUS_IGNORED = "ignored"

EXPORT_STATUSES = frozenset(
    {STATUS_PROCESSING, STATUS_SUCCESS, STATUS_FAILED, STATUS_IGNORED}
)
TERMINAL_SKIP_STATUSES = frozenset({STATUS_SUCCESS, STATUS_IGNORED})


@dataclass(frozen=True)
class QuestorNfeListing:
    """Linha da listagem NF-e com os dois identificadores do portal.

    provider_file_id é o XmlFilename (parâmetro Id do download).
    provider_entity_id é o Id da linha (parâmetro IdEntity do download).
    O document_id público da NF-e continua sendo o XmlFilename do DANFE.
    """

    provider_file_id: str
    provider_entity_id: str
    access_key: str
    invoice_number: str
    series: str
    issuer_cnpj: str | None
    emission_at: str | None
    branch_code: str


@dataclass(frozen=True)
class NfeExportListingPage:
    total_items: int
    items: tuple[QuestorNfeListing, ...]


@dataclass(frozen=True)
class NfeExportRecord:
    access_key: str
    branch_code: str
    provider_document_id: str | None
    provider_file_id: str | None
    invoice_number: str | None
    series: str | None
    emission_date: date | None
    filename: str | None
    status: str
    attempts: int
    last_error_code: str | None
    last_error_message: str | None


@dataclass(frozen=True)
class NfeExportSettings:
    enabled: bool
    directory: str
    interval_seconds: int
    start_date: date | None
    page_size: int
    max_pages: int
    max_bytes: int


@dataclass(frozen=True)
class BranchExportResult:
    branch_code: str
    status: str
    found: int = 0
    eligible: int = 0
    already_success: int = 0
    exported: int = 0
    ignored: int = 0
    failed: int = 0
    reconciled: int = 0
    rejected: int = 0
    duration_ms: int = 0
    error_code: str | None = None


@dataclass(frozen=True)
class CycleResult:
    status: str
    branches: tuple[BranchExportResult, ...] = ()
    duration_ms: int = 0
    error_code: str | None = None

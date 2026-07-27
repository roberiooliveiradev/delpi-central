"""Normalização fiscal do domínio lançamento-notas-fiscais."""
from __future__ import annotations

from dataclasses import dataclass


class FiscalNormalizationError(ValueError):
    """Entrada fiscal inválida para persistência."""


@dataclass(frozen=True, slots=True)
class NormalizedDocument:
    document_number: str
    document_match_key: str


def normalize_document(raw: str | None) -> NormalizedDocument:
    cleaned = str(raw or "").strip()
    if not cleaned or not cleaned.isdigit():
        raise FiscalNormalizationError(
            "Número da nota deve conter somente dígitos (1 a 9)."
        )
    if len(cleaned) < 1 or len(cleaned) > 9:
        raise FiscalNormalizationError(
            "Número da nota deve ter entre 1 e 9 dígitos."
        )
    document_number = cleaned.zfill(9)
    document_match_key = cleaned.zfill(9)
    return NormalizedDocument(
        document_number=document_number,
        document_match_key=document_match_key,
    )


def normalize_series(raw: str | None, *, required: bool = False) -> str:
    series = str(raw or "").strip().upper()
    if len(series) > 3:
        raise FiscalNormalizationError("Série deve ter no máximo 3 caracteres.")
    if required and not series:
        raise FiscalNormalizationError(
            "Informe a série da nota (como no Protheus)."
        )
    return series


def normalize_branch(raw: str | None) -> str:
    branch = str(raw or "").strip()
    if branch not in {"01", "02"}:
        raise FiscalNormalizationError("Filial deve ser 01 ou 02.")
    return branch


BLOCK_REASONS = frozenset(
    {
        "purchase_order",
        "supplier_registration",
        "information_correction",
        "other",
    }
)

TERMINAL_STATUSES = frozenset({"posted", "cancelled"})
NON_TERMINAL_STATUSES = frozenset({"pending", "in_progress", "blocked"})
RECONCILIATION_ELIGIBLE_STATUSES = NON_TERMINAL_STATUSES

# Filtro de listagem: fila aberta (não confundir com status persistido `pending`).
LIST_STATUS_FILTER_OPEN = "open"
VALID_LIST_STATUS_FILTERS = frozenset(
    {*NON_TERMINAL_STATUSES, *TERMINAL_STATUSES, LIST_STATUS_FILTER_OPEN}
)


def resolve_list_status_filter(status: str | None) -> tuple[str, ...] | None:
    """Converte o query ``status`` da listagem em tupla de status persistidos.

    ``open`` → pending + in_progress + blocked.
    Status individual → singleton.
    Vazio → sem filtro de status.
    """
    if status is None:
        return None
    normalized = str(status).strip().lower()
    if not normalized:
        return None
    if normalized not in VALID_LIST_STATUS_FILTERS:
        raise ValueError(
            "status inválido. Use open, pending, in_progress, blocked, posted ou cancelled."
        )
    if normalized == LIST_STATUS_FILTER_OPEN:
        return tuple(sorted(NON_TERMINAL_STATUSES))
    return (normalized,)

DEFAULT_RECONCILIATION_LIMIT = 50
MAX_RECONCILIATION_LIMIT = 200
RECONCILIATION_REFRESH_COOLDOWN_SECONDS = 45

# pg_advisory_lock(classid, objid) — exclusivo do reconciliador LNF
RECONCILIATION_LOCK_CLASS_ID = 88442201
RECONCILIATION_LOCK_OBJECT_ID = 1

"""Helpers de domínio — janela de ruptura projetada (Delpi Reports)."""

from __future__ import annotations

from datetime import date, timedelta
from typing import Any, Mapping

from app.domain.services.supplies.safety_stock_classification_service import TOLERANCE

PROVIDER_KEY = "safety_stock_shortage_30d"
DEFAULT_HORIZON_DAYS = 30
VALID_BRANCHES = frozenset({"01", "02"})

DATASET_COLUMNS = (
    "product_code",
    "product_description",
    "branch",
    "available_stock",
    "first_shortage_date",
    "shortage_balance",
    "observation",
)

# Colunas do e-mail — filial só no cabeçalho (não repetir na tabela).
EMAIL_COLUMNS = tuple(col for col in DATASET_COLUMNS if col != "branch")

COLUMN_LABELS_PT = {
    "product_code": "Código",
    "product_description": "Descrição",
    "branch": "Filial",
    "available_stock": "Saldo atual",
    "first_shortage_date": "Data da ruptura",
    "shortage_balance": "Saldo no evento",
    "observation": "Observação",
}

BRANCH_LABELS_PT = {
    "01": "Jaraguá do Sul/SC",
    "02": "Rio Bananal/ES",
}

# Larguras relativas para Outlook (descrição larga; data só o necessário).
EMAIL_COLUMN_STYLES: dict[str, str] = {
    "product_description": "min-width:220px;width:36%;",
    "first_shortage_date": "min-width:96px;width:96px;white-space:nowrap;",
    "available_stock": "width:72px;white-space:nowrap;",
    "shortage_balance": "width:88px;white-space:nowrap;",
}


def format_branch_label(branch: Any) -> str:
    """Rótulo de unidade (01/02) para e-mail; desconhecido → código cru."""
    code = str(branch or "").strip()
    if not code:
        return ""
    return BRANCH_LABELS_PT.get(code, code)


def format_date_br(value: Any) -> str:
    """Converte data ISO (ou ``date``) para ``DD/MM/AAAA``; demais valores intactos."""
    if value is None:
        return ""
    if isinstance(value, date):
        return value.strftime("%d/%m/%Y")
    text = str(value).strip()
    if not text:
        return ""
    iso_candidate = text[:10]
    try:
        return date.fromisoformat(iso_candidate).strftime("%d/%m/%Y")
    except ValueError:
        return text


def shortage_date_in_horizon(
    first_shortage_date: str | None,
    *,
    as_of: date,
    horizon_days: int,
) -> bool:
    """Inclui só se ``first_shortage_date`` ∈ ``[as_of, as_of + horizon_days]``."""
    if not first_shortage_date:
        return False
    try:
        shortage = date.fromisoformat(str(first_shortage_date).strip()[:10])
    except ValueError:
        return False
    end = as_of + timedelta(days=max(int(horizon_days), 0))
    return as_of <= shortage <= end


def balance_at_first_shortage(projection: Mapping[str, Any]) -> float | None:
    """``running_balance`` no primeiro evento com saldo projetado negativo."""
    for row in projection.get("items") or []:
        running = float(row.get("running_balance") or 0)
        if running + TOLERANCE < 0:
            return running
    return None


def observation_from_summary(summary: Mapping[str, Any]) -> str:
    warnings = summary.get("warnings") or []
    if not isinstance(warnings, (list, tuple)):
        return ""
    parts = [str(item).strip() for item in warnings if str(item).strip()]
    return " | ".join(parts)

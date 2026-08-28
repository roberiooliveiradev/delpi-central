"""Regras canônicas — relatório agendado de saldos PA (Delpi Reports)."""

from __future__ import annotations

from datetime import date, datetime
from typing import Any, Mapping, Sequence
from zoneinfo import ZoneInfo

PROVIDER_KEY = "stock_balances_pa"
PROVIDER_DISPLAY_NAME = "Saldos PA (armazém 01)"

WAREHOUSE = "01"
ONLY_POSITIVE = True
QUANTITY_EXPORT_FACTOR = 1000
FETCH_PAGE_SIZE = 500
MAX_FETCH_PAGES = 40
DEFAULT_TIMEZONE = "America/Sao_Paulo"

TITLE_BRANCH_01 = "ESTOQUE MATRIZ"
TITLE_BRANCH_02 = "SALDO FILIAL"

PRODUCT_CODE_PREFIXES_BY_BRANCH: dict[str, tuple[str, ...]] = {
    "01": ("9",),
    "02": ("8", "9"),
}

# Exclusões após o filtro de inclusão (ex.: família 9035…).
EXCLUDED_PRODUCT_CODE_PREFIXES: tuple[str, ...] = ("9035",)

COLUMN_PRODUCT = "product_code"
COLUMN_QUANTITY = "quantity"
DATASET_COLUMNS = (COLUMN_PRODUCT, COLUMN_QUANTITY)

XLSX_CONTENT_TYPE = (
    "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
)


def normalize_branch(value: Any) -> str:
    text = str(value or "").strip()
    if text in {"01", "02"}:
        return text
    raise ValueError("params.branch deve ser 01 ou 02.")


def prefixes_for_branch(branch: str) -> tuple[str, ...]:
    return PRODUCT_CODE_PREFIXES_BY_BRANCH.get(branch, ("8", "9"))


def product_code_matches_prefixes(product_code: str | None, prefixes: Sequence[str]) -> bool:
    code = (product_code or "").strip()
    if not code or not prefixes:
        return False
    return any(code.startswith(prefix) for prefix in prefixes if prefix)


def product_code_excluded(product_code: str | None) -> bool:
    return product_code_matches_prefixes(product_code, EXCLUDED_PRODUCT_CODE_PREFIXES)


def product_code_in_stock_balances_scope(
    product_code: str | None, *, branch: str
) -> bool:
    """Inclusão por filial e exclusões canônicas (ex.: 9035)."""
    code = (product_code or "").strip()
    if not code:
        return False
    if product_code_excluded(code):
        return False
    return product_code_matches_prefixes(code, prefixes_for_branch(branch))


def title_for_branch(branch: str) -> str:
    return TITLE_BRANCH_02 if branch == "02" else TITLE_BRANCH_01


def _as_date(value: date | datetime | str | None) -> date:
    if isinstance(value, datetime):
        return value.date()
    if isinstance(value, date):
        return value
    if isinstance(value, str) and value.strip():
        try:
            return date.fromisoformat(value.strip()[:10])
        except ValueError:
            pass
    return datetime.now(ZoneInfo(DEFAULT_TIMEZONE)).date()


def format_issue_date(value: date | datetime | str | None = None) -> str:
    day = _as_date(value)
    return f"{day.day:02d}-{day.month:02d}-{day.year:04d}"


def export_file_base(branch: str, issued_on: date | datetime | str | None = None) -> str:
    return f"{title_for_branch(branch)} - {format_issue_date(issued_on)}"


def export_quantity(raw: Any) -> float:
    try:
        return float(raw or 0) * QUANTITY_EXPORT_FACTOR
    except (TypeError, ValueError):
        return 0.0


def parse_branch_param(params: Mapping[str, Any] | None) -> str:
    raw = (params or {}).get("branch")
    return normalize_branch(raw)

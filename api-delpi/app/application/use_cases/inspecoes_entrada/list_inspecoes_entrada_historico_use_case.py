from __future__ import annotations

from datetime import date, datetime
from decimal import Decimal
from typing import Any

from app.application.dto.inspecoes_entrada.inspecoes_entrada_historico_filters import (
    InspecoesEntradaHistoricoFilters,
)
from app.application.dto.inspecoes_entrada.inspecoes_entrada_historico_response import (
    InspecoesEntradaHistoricoItemResponse,
    InspecoesEntradaHistoricoResponse,
)
from app.application.dto.inspecoes_entrada.inspecoes_entrada_pendentes_response import (
    InspecoesEntradaPendentesPagination,
)
from app.domain.ports.inspecoes_entrada.inspecoes_entrada_repository_port import (
    InspecoesEntradaRepositoryPort,
)

VALID_BRANCHES = frozenset({"01", "02"})
VALID_RESULTS = frozenset({"APROVADA", "REJEITADA"})
DEFAULT_PAGE_SIZE = 50
MAX_PAGE_SIZE = 200


def _as_str(value: Any) -> str:
    if value is None:
        return ""
    return str(value).strip()


def _as_int(value: Any) -> int:
    if value is None or value == "":
        return 0
    if isinstance(value, (int, float, Decimal)):
        return int(value)
    text = str(value).strip().replace(",", ".")
    return int(float(text))


def _as_float(value: Any) -> float:
    if value is None or value == "":
        return 0.0
    if isinstance(value, (int, float, Decimal)):
        return float(value)
    text = str(value).strip().replace(",", ".")
    return float(text)


def _as_float_or_none(value: Any) -> float | None:
    if value is None or value == "":
        return None
    return _as_float(value)


def _as_bool(value: Any) -> bool:
    if value is None or value == "":
        return False
    if isinstance(value, bool):
        return value
    if isinstance(value, (int, float, Decimal)):
        return int(value) != 0
    text = str(value).strip().lower()
    return text in {"1", "true", "s", "sim", "y", "yes"}


def _format_date(value: Any) -> str | None:
    if value is None or value == "":
        return None
    if isinstance(value, datetime):
        return value.date().isoformat()
    if isinstance(value, date):
        return value.isoformat()
    if hasattr(value, "isoformat"):
        return value.isoformat()[:10]
    raw = _as_str(value)
    if len(raw) == 8 and raw.isdigit():
        return f"{raw[:4]}-{raw[4:6]}-{raw[6:8]}"
    return raw or None


def _format_time(value: Any) -> str | None:
    if value is None or value == "":
        return None
    raw = _as_str(value)
    return raw or None


def _parse_iso_date(value: str | None, *, field_name: str) -> date | None:
    if value is None:
        return None
    normalized = str(value).strip()
    if not normalized:
        return None
    try:
        return date.fromisoformat(normalized)
    except ValueError as exc:
        raise ValueError(f"{field_name} inválida. Use o formato YYYY-MM-DD.") from exc


def _normalize_optional_text(value: str | None) -> str | None:
    if value is None:
        return None
    normalized = value.strip()
    return normalized or None


def _optional_str(value: Any) -> str | None:
    text = _as_str(value)
    return text or None


def _normalize_item(row: dict, branch: str) -> InspecoesEntradaHistoricoItemResponse:
    return InspecoesEntradaHistoricoItemResponse(
        branch=_as_str(row.get("Filial")) or branch,
        inspection_id=_as_str(row.get("Id_Inspecao")),
        received_date=_format_date(row.get("Data_Recebimento")),
        received_time=_format_time(row.get("Hora_Recebimento")),
        report_date=_format_date(row.get("Data_Laudo")),
        report_time=_format_time(row.get("Hora_Laudo")),
        invoice_number=_as_str(row.get("Nota_Fiscal")),
        invoice_series=_as_str(row.get("Serie_Nota_Fiscal")),
        invoice_item=_as_str(row.get("Item_Nota_Fiscal")),
        supplier_code=_as_str(row.get("Codigo_Fornecedor")),
        supplier_store=_as_str(row.get("Loja_Fornecedor")),
        supplier_name=_as_str(row.get("Nome_Fornecedor")),
        product_code=_as_str(row.get("Codigo_Produto")),
        product_description=_optional_str(row.get("Descricao_Produto")),
        lot=_as_str(row.get("Lote")),
        supplier_lot=_as_str(row.get("Lote_Fornecedor")),
        quantity=_as_float(row.get("Quantidade")),
        unit=_as_str(row.get("Unidade_Medida")),
        status_code=_as_str(row.get("Codigo_Situacao")),
        inspection_status=_as_str(row.get("Status_Inspecao")),
        result=_as_str(row.get("Resultado_Resumo")),
        report_code=_as_str(row.get("Codigo_Laudo")),
        approved_quantity=_as_float_or_none(row.get("Quantidade_Aprovada")),
        rejected_quantity=_as_float_or_none(row.get("Quantidade_Rejeitada")),
        report_justification=_as_str(row.get("Justificativa_Laudo")),
        inspector_registration=_as_str(row.get("Matricula_Ensaiador")),
        inspector_name=_as_str(row.get("Nome_Ensaiador")),
        inspector_login=_as_str(row.get("Login_Ensaiador")),
        tests_count=_as_int(row.get("Qtde_Ensaios")),
        failed_tests_count=_as_int(row.get("Qtde_Ensaios_Reprovados")),
        is_approved=_as_bool(row.get("Eh_Aprovada")),
        is_rejected=_as_bool(row.get("Eh_Rejeitada")),
    )


class ListInspecoesEntradaHistoricoUseCase:
    def __init__(self, repository: InspecoesEntradaRepositoryPort) -> None:
        self._repository = repository

    def execute(
        self,
        *,
        branch: str,
        page: int = 1,
        page_size: int = DEFAULT_PAGE_SIZE,
        result: str | None = None,
        date_from: str | None = None,
        date_to: str | None = None,
        supplier: str | None = None,
        product_code: str | None = None,
        inspector: str | None = None,
        invoice_number: str | None = None,
        lot: str | None = None,
    ) -> InspecoesEntradaHistoricoResponse:
        normalized_branch = str(branch or "").strip()
        if normalized_branch not in VALID_BRANCHES:
            raise ValueError("branch inválida. Use 01 ou 02.")

        normalized_result = _normalize_optional_text(result)
        if normalized_result and normalized_result not in VALID_RESULTS:
            raise ValueError("result inválido. Use APROVADA ou REJEITADA.")

        parsed_date_from = _parse_iso_date(date_from, field_name="date_from")
        parsed_date_to = _parse_iso_date(date_to, field_name="date_to")
        if parsed_date_from and parsed_date_to and parsed_date_from > parsed_date_to:
            raise ValueError("date_from deve ser menor ou igual a date_to.")

        filters = InspecoesEntradaHistoricoFilters(
            result=normalized_result,
            date_from=parsed_date_from.isoformat() if parsed_date_from else None,
            date_to=parsed_date_to.isoformat() if parsed_date_to else None,
            supplier=_normalize_optional_text(supplier),
            product_code=_normalize_optional_text(product_code),
            inspector=_normalize_optional_text(inspector),
            invoice_number=_normalize_optional_text(invoice_number),
            lot=_normalize_optional_text(lot),
        )

        resolved_page = max(page, 1)
        resolved_page_size = min(max(page_size, 1), MAX_PAGE_SIZE)

        total = self._repository.count_historico_by_branch(normalized_branch, filters)
        rows = self._repository.list_historico_by_branch(
            normalized_branch,
            page=resolved_page,
            page_size=resolved_page_size,
            filters=filters,
        )
        items = [_normalize_item(row, normalized_branch) for row in rows]
        total_pages = max((total + resolved_page_size - 1) // resolved_page_size, 1) if total else 1

        return InspecoesEntradaHistoricoResponse(
            branch=normalized_branch,
            items=items,
            pagination=InspecoesEntradaPendentesPagination(
                page=resolved_page,
                page_size=resolved_page_size,
                total=total,
                total_pages=total_pages,
            ),
            filters=filters,
        )

from __future__ import annotations

from decimal import Decimal
from typing import Any

from app.application.dto.inspecoes_entrada.inspecoes_entrada_pendentes_response import (
    InspecoesEntradaPendenteItemResponse,
    InspecoesEntradaPendentesPagination,
    InspecoesEntradaPendentesResponse,
)
from app.domain.ports.inspecoes_entrada.inspecoes_entrada_repository_port import (
    InspecoesEntradaRepositoryPort,
)

VALID_BRANCHES = frozenset({"01", "02"})
DEFAULT_PAGE_SIZE = 50
MAX_PAGE_SIZE = 200


def _as_str(value: Any) -> str:
    if value is None:
        return ""
    return str(value).strip()


def _as_float(value: Any) -> float:
    if value is None or value == "":
        return 0.0
    if isinstance(value, (int, float, Decimal)):
        return float(value)
    text = str(value).strip().replace(",", ".")
    return float(text)


def _optional_str(value: Any) -> str | None:
    text = _as_str(value)
    return text or None


def _format_received_date(value: Any) -> str | None:
    if value is None or value == "":
        return None

    if hasattr(value, "isoformat"):
        return value.isoformat()[:10]

    raw = _as_str(value)
    if len(raw) == 8 and raw.isdigit():
        return f"{raw[:4]}-{raw[4:6]}-{raw[6:8]}"
    return raw or None


def _format_received_time(value: Any) -> str | None:
    if value is None or value == "":
        return None
    raw = _as_str(value)
    return raw or None


def _normalize_item(row: dict, branch: str) -> InspecoesEntradaPendenteItemResponse:
    return InspecoesEntradaPendenteItemResponse(
        branch=_as_str(row.get("Filial")) or branch,
        received_date=_format_received_date(row.get("Data_Recebimento")),
        received_time=_format_received_time(row.get("Hora_Recebimento")),
        invoice_number=_as_str(row.get("Nota_Fiscal")),
        supplier_code=_as_str(row.get("Codigo_Fornecedor")),
        supplier_store=_as_str(row.get("Loja_Fornecedor")),
        supplier_name=_as_str(row.get("Nome_Fornecedor")),
        product_code=_as_str(row.get("Codigo_Produto")),
        product_description=_optional_str(row.get("Descricao_Produto")),
        quantity=_as_float(row.get("Quantidade")),
        unit=_as_str(row.get("Unidade_Medida")),
        status_code=_as_str(row.get("Codigo_Situacao")),
        inspection_status=_as_str(row.get("Status_Inspecao")),
    )


class ListInspecoesEntradaPendentesUseCase:
    def __init__(self, repository: InspecoesEntradaRepositoryPort) -> None:
        self._repository = repository

    def execute(
        self,
        *,
        branch: str,
        page: int = 1,
        page_size: int = DEFAULT_PAGE_SIZE,
    ) -> InspecoesEntradaPendentesResponse:
        normalized_branch = str(branch or "").strip()
        if normalized_branch not in VALID_BRANCHES:
            raise ValueError("branch inválida. Use 01 ou 02.")

        resolved_page = max(page, 1)
        resolved_page_size = min(max(page_size, 1), MAX_PAGE_SIZE)

        total = self._repository.count_pendentes_by_branch(normalized_branch)
        rows = self._repository.list_pendentes_by_branch(
            normalized_branch,
            page=resolved_page,
            page_size=resolved_page_size,
        )
        items = [_normalize_item(row, normalized_branch) for row in rows]
        total_pages = max((total + resolved_page_size - 1) // resolved_page_size, 1)

        return InspecoesEntradaPendentesResponse(
            branch=normalized_branch,
            items=items,
            pagination=InspecoesEntradaPendentesPagination(
                page=resolved_page,
                page_size=resolved_page_size,
                total=total,
                total_pages=total_pages,
            ),
        )

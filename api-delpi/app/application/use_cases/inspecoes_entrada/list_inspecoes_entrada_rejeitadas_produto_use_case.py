from __future__ import annotations

from datetime import date, datetime
from decimal import Decimal
from typing import Any

from app.application.dto.inspecoes_entrada.inspecoes_entrada_rejeitadas_produto_response import (
    InspecoesEntradaRejeitadaProdutoItemResponse,
    InspecoesEntradaRejeitadasProdutoResponse,
)
from app.domain.ports.inspecoes_entrada.inspecoes_entrada_repository_port import (
    InspecoesEntradaRepositoryPort,
)

VALID_BRANCHES = frozenset({"01", "02"})
DEFAULT_LIMIT = 50
MAX_LIMIT = 200


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


def _normalize_item(row: dict, branch: str) -> InspecoesEntradaRejeitadaProdutoItemResponse:
    return InspecoesEntradaRejeitadaProdutoItemResponse(
        branch=_as_str(row.get("Filial")) or branch,
        inspection_id=_as_str(row.get("Id_Inspecao")),
        report_date=_format_date(row.get("Data_Laudo")),
        report_time=_format_time(row.get("Hora_Laudo")),
        invoice_number=_as_str(row.get("Nota_Fiscal")),
        supplier_name=_as_str(row.get("Nome_Fornecedor")),
        product_code=_as_str(row.get("Codigo_Produto")),
        product_description=_optional_str(row.get("Descricao_Produto")),
        lot=_as_str(row.get("Lote")),
        quantity=_as_float(row.get("Quantidade")),
        unit=_as_str(row.get("Unidade_Medida")),
    )


class ListInspecoesEntradaRejeitadasProdutoUseCase:
    def __init__(self, repository: InspecoesEntradaRepositoryPort) -> None:
        self._repository = repository

    def execute(
        self,
        *,
        branch: str,
        limit: int = DEFAULT_LIMIT,
    ) -> InspecoesEntradaRejeitadasProdutoResponse:
        normalized_branch = str(branch or "").strip()
        if normalized_branch not in VALID_BRANCHES:
            raise ValueError("branch inválida. Use 01 ou 02.")

        resolved_limit = min(max(limit, 1), MAX_LIMIT)
        total = self._repository.count_rejeitadas_by_branch(normalized_branch)
        rows = self._repository.list_rejeitadas_by_branch(
            normalized_branch,
            limit=resolved_limit,
        )
        items = [_normalize_item(row, normalized_branch) for row in rows]

        return InspecoesEntradaRejeitadasProdutoResponse(
            branch=normalized_branch,
            items=items,
            total=total,
        )

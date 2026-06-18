from __future__ import annotations

from decimal import Decimal
from typing import Any

from app.application.dto.inspecoes_entrada.inspecoes_entrada_pendentes_fornecedor_response import (
    InspecoesEntradaPendenteFornecedorItemResponse,
    InspecoesEntradaPendentesFornecedorResponse,
)
from app.domain.ports.inspecoes_entrada.inspecoes_entrada_repository_port import (
    InspecoesEntradaRepositoryPort,
)

VALID_BRANCHES = frozenset({"01", "02"})


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


def _normalize_item(row: dict, branch: str) -> InspecoesEntradaPendenteFornecedorItemResponse:
    return InspecoesEntradaPendenteFornecedorItemResponse(
        branch=_as_str(row.get("Filial")) or branch,
        supplier_name=_as_str(row.get("Nome_Fornecedor")),
        pending_count=_as_int(row.get("Qtde_Pendentes")),
    )


class ListInspecoesEntradaPendentesFornecedorUseCase:
    def __init__(self, repository: InspecoesEntradaRepositoryPort) -> None:
        self._repository = repository

    def execute(self, *, branch: str) -> InspecoesEntradaPendentesFornecedorResponse:
        normalized_branch = str(branch or "").strip()
        if normalized_branch not in VALID_BRANCHES:
            raise ValueError("branch inválida. Use 01 ou 02.")

        rows = self._repository.list_pendentes_fornecedor_by_branch(normalized_branch)
        items = [_normalize_item(row, normalized_branch) for row in rows]
        total_pending = sum(item.pending_count for item in items)

        return InspecoesEntradaPendentesFornecedorResponse(
            branch=normalized_branch,
            items=items,
            total_suppliers=len(items),
            total_pending=total_pending,
        )

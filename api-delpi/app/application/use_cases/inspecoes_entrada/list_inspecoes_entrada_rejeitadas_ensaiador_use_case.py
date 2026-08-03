from __future__ import annotations

from decimal import Decimal
from typing import Any

from app.application.dto.inspecoes_entrada.inspecoes_entrada_rejeitadas_ensaiador_response import (
    InspecoesEntradaRejeitadaEnsaiadorItemResponse,
    InspecoesEntradaRejeitadasEnsaiadorResponse,
)
from app.domain.ports.inspecoes_entrada.inspecoes_entrada_repository_port import (
    InspecoesEntradaRepositoryPort,
)
from app.domain.quality.inspecoes_entrada.inspecoes_entrada_scope import (
    normalize_optional_branch,
)


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


def _normalize_item(
    row: dict,
    scope_branch: str | None,
) -> InspecoesEntradaRejeitadaEnsaiadorItemResponse:
    return InspecoesEntradaRejeitadaEnsaiadorItemResponse(
        branch=_as_str(row.get("Filial")) or (scope_branch or ""),
        inspector_registration=_as_str(row.get("Matricula_Ensaiador")),
        inspector_name=_as_str(row.get("Nome_Ensaiador")),
        inspector_login=_as_str(row.get("Login_Ensaiador")),
        rejected_inspections=_as_int(row.get("Qtde_Inspecoes_Rejeitadas")),
    )


class ListInspecoesEntradaRejeitadasEnsaiadorUseCase:
    def __init__(self, repository: InspecoesEntradaRepositoryPort) -> None:
        self._repository = repository

    def execute(
        self, *, branch: str | None
    ) -> InspecoesEntradaRejeitadasEnsaiadorResponse:
        normalized_branch = normalize_optional_branch(branch)

        rows = self._repository.list_rejeitadas_ensaiador_by_branch(normalized_branch)
        items = [_normalize_item(row, normalized_branch) for row in rows]
        total_rejected = sum(item.rejected_inspections for item in items)

        return InspecoesEntradaRejeitadasEnsaiadorResponse(
            branch=normalized_branch,
            items=items,
            total_inspectors=len(items),
            total_rejected=total_rejected,
        )

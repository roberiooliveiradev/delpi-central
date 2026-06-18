from __future__ import annotations

from typing import Any

from app.application.dto.inspecoes_entrada.inspecoes_entrada_resumo_response import (
    InspecoesEntradaResumoResponse,
)
from app.domain.ports.inspecoes_entrada.inspecoes_entrada_repository_port import (
    InspecoesEntradaRepositoryPort,
)

VALID_BRANCHES = frozenset({"01", "02"})


def _as_int(value: Any) -> int:
    if value is None or value == "":
        return 0
    return int(value)


def _as_float(value: Any) -> float:
    if value is None or value == "":
        return 0.0
    return float(value)


class GetInspecoesEntradaResumoUseCase:
    def __init__(self, repository: InspecoesEntradaRepositoryPort) -> None:
        self._repository = repository

    def execute(self, *, branch: str) -> InspecoesEntradaResumoResponse:
        normalized_branch = str(branch or "").strip()
        if normalized_branch not in VALID_BRANCHES:
            raise ValueError("branch inválida. Use 01 ou 02.")

        row = self._repository.get_resumo_by_branch(normalized_branch)
        if not row:
            return InspecoesEntradaResumoResponse(branch=normalized_branch)

        return InspecoesEntradaResumoResponse(
            branch=normalized_branch,
            pending_inspections=_as_int(row.get("Inspecoes_Pendentes")),
            inspected=_as_int(row.get("Ja_Inspecionados")),
            approved_inspections=_as_int(row.get("Inspecoes_Aprovadas")),
            rejected_inspections=_as_int(row.get("Inspecoes_Rejeitadas")),
            approval_rate=_as_float(row.get("Taxa_Aprovacao")),
            inspections_with_time=_as_int(row.get("Qtde_Inspecoes_Com_Tempo")),
            average_time_hours=_as_float(row.get("Tempo_Medio_Horas")),
            average_time_days=_as_float(row.get("Tempo_Medio_Dias")),
        )

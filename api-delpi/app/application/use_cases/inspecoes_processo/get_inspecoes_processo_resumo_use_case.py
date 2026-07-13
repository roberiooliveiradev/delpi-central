from __future__ import annotations

from datetime import date, datetime
from typing import Any

from app.application.dto.inspecoes_processo.inspecoes_processo_resumo_response import (
    InspecoesProcessoResumoResponse,
)
from app.domain.ports.inspecoes_processo.inspecoes_processo_repository_port import (
    InspecoesProcessoRepositoryPort,
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


def _as_str(value: Any) -> str:
    if value is None:
        return ""
    return str(value).strip()


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


class GetInspecoesProcessoResumoUseCase:
    def __init__(self, repository: InspecoesProcessoRepositoryPort) -> None:
        self._repository = repository

    def execute(self, *, branch: str) -> InspecoesProcessoResumoResponse:
        normalized_branch = str(branch or "").strip()
        if normalized_branch not in VALID_BRANCHES:
            raise ValueError("branch inválida. Use 01 ou 02.")

        row = self._repository.get_resumo_by_branch(normalized_branch)
        if not row:
            return InspecoesProcessoResumoResponse(filial=normalized_branch)

        return InspecoesProcessoResumoResponse(
            filial=_as_str(row.get("Filial")) or normalized_branch,
            unidade=_as_str(row.get("Unidade")),
            qtde_ops=_as_int(row.get("Qtde_OPs")),
            qtde_ensaios=_as_int(row.get("Qtde_Ensaios")),
            qtde_ensaios_aprovados=_as_int(row.get("Qtde_Ensaios_Aprovados")),
            qtde_ensaios_reprovados=_as_int(row.get("Qtde_Ensaios_Reprovados")),
            qtde_ensaios_tolerancia=_as_int(row.get("Qtde_Ensaios_Tolerancia")),
            qtde_ops_aprovadas=_as_int(row.get("Qtde_OPs_Aprovadas")),
            qtde_ops_reprovadas=_as_int(row.get("Qtde_OPs_Reprovadas")),
            qtde_ops_tolerancia=_as_int(row.get("Qtde_OPs_Tolerancia")),
            qtde_ops_nao_identificadas=_as_int(row.get("Qtde_OPs_Nao_Identificadas")),
            qtde_produtos=_as_int(row.get("Qtde_Produtos")),
            qtde_operacoes=_as_int(row.get("Qtde_Operacoes")),
            qtde_ensaiadores=_as_int(row.get("Qtde_Ensaiadores")),
            primeira_data_medicao=_format_date(row.get("Primeira_Data_Medicao_Date")),
            ultima_data_medicao=_format_date(row.get("Ultima_Data_Medicao_Date")),
            percentual_ops_aprovadas=_as_float(row.get("Percentual_OPs_Aprovadas")),
            percentual_ops_reprovadas=_as_float(row.get("Percentual_OPs_Reprovadas")),
            percentual_ensaios_aprovados=_as_float(row.get("Percentual_Ensaios_Aprovados")),
            percentual_ensaios_reprovados=_as_float(
                row.get("Percentual_Ensaios_Reprovados")
            ),
        )

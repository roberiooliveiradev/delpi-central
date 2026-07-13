from __future__ import annotations

from datetime import date, datetime
from typing import Any

from app.application.dto.inspecoes_processo.inspecoes_processo_por_produto_response import (
    InspecoesProcessoPorProdutoItemResponse,
)
from app.domain.ports.inspecoes_processo.inspecoes_processo_repository_port import (
    InspecoesProcessoRepositoryPort,
)

VALID_BRANCHES = frozenset({"01", "02"})
DEFAULT_LIMIT = 10
MAX_LIMIT = 50


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


def _normalize_item(
    row: dict,
    branch: str,
) -> InspecoesProcessoPorProdutoItemResponse:
    return InspecoesProcessoPorProdutoItemResponse(
        filial=_as_str(row.get("Filial")) or branch,
        unidade=_as_str(row.get("Unidade")),
        codigo_produto=_as_str(row.get("Codigo_Produto")),
        descricao_produto=_as_str(row.get("Descricao_Produto")),
        revisao_produto=_as_str(row.get("Revisao_Produto")),
        qtde_ops=_as_int(row.get("Qtde_OPs")),
        qtde_ensaios=_as_int(row.get("Qtde_Ensaios")),
        qtde_ensaios_aprovados=_as_int(row.get("Qtde_Ensaios_Aprovados")),
        qtde_ensaios_reprovados=_as_int(row.get("Qtde_Ensaios_Reprovados")),
        qtde_ensaios_tolerancia=_as_int(row.get("Qtde_Ensaios_Tolerancia")),
        qtde_ops_aprovadas=_as_int(row.get("Qtde_OPs_Aprovadas")),
        qtde_ops_reprovadas=_as_int(row.get("Qtde_OPs_Reprovadas")),
        qtde_ops_tolerancia=_as_int(row.get("Qtde_OPs_Tolerancia")),
        qtde_ensaios_distintos=_as_int(row.get("Qtde_Ensaios_Distintos")),
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


class ListInspecoesProcessoPorProdutoUseCase:
    def __init__(self, repository: InspecoesProcessoRepositoryPort) -> None:
        self._repository = repository

    def execute(
        self,
        *,
        branch: str,
        limit: int = DEFAULT_LIMIT,
    ) -> list[InspecoesProcessoPorProdutoItemResponse]:
        normalized_branch = str(branch or "").strip()
        if normalized_branch not in VALID_BRANCHES:
            raise ValueError("branch inválida. Use 01 ou 02.")

        resolved_limit = min(max(int(limit), 1), MAX_LIMIT)
        rows = self._repository.list_por_produto_by_branch(
            normalized_branch,
            limit=resolved_limit,
        )
        return [_normalize_item(row, normalized_branch) for row in rows]

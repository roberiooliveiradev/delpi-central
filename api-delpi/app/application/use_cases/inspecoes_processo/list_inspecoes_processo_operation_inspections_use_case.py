from __future__ import annotations

from typing import Any

from app.application.use_cases.inspecoes_processo.list_inspecoes_processo_historico_use_case import (
    _as_str,
    _format_date,
    _format_time,
)
from app.domain.ports.inspecoes_processo.inspecoes_processo_repository_port import (
    InspecoesProcessoRepositoryPort,
)
from app.domain.quality.inspecoes_processo.inspecoes_processo_scope import (
    normalize_branch_code,
)


class ListInspecoesProcessoOperationInspectionsUseCase:
    """Lista sessões de inspeção (quem/quando/resultado) da OP+operação — sem ensaios."""

    def __init__(self, repository: InspecoesProcessoRepositoryPort) -> None:
        self._repository = repository

    def execute(
        self,
        *,
        branch: str,
        production_order: str,
        operation: str,
    ) -> dict[str, Any]:
        code = normalize_branch_code(branch)
        order = _as_str(production_order)
        oper = _as_str(operation)
        if not order:
            raise ValueError("production_order é obrigatório.")
        if not oper:
            raise ValueError("operation é obrigatório.")

        rows = self._repository.list_operation_inspections(
            branch=code,
            production_order=order,
            operation=oper,
        )
        items = [_normalize_item(row) for row in rows]
        return {
            "branch": code,
            "production_order": order,
            "operation": oper,
            "items": items,
            "summary": {"inspection_count": len(items)},
        }


def _normalize_item(row: dict) -> dict[str, Any]:
    result_code = _as_str(row.get("result_code") or row.get("Resultado_Codigo"))
    result = _as_str(row.get("result") or row.get("Resultado")) or _result_label(result_code)
    return {
        "inspector_name": _as_str(row.get("inspector_name") or row.get("Nome_Ensaiador")),
        "inspector_registration": _as_str(
            row.get("inspector_registration") or row.get("Matricula_Ensaiador")
        ),
        "measurement_date": _format_date(
            row.get("measurement_date") or row.get("Data_Medicao_Date")
        ),
        "measurement_time": _format_time(
            row.get("measurement_time") or row.get("Hora_Medicao")
        ),
        "result_code": result_code,
        "result": result,
        # PT aliases for legacy consumers
        "nome_ensaiador": _as_str(row.get("inspector_name") or row.get("Nome_Ensaiador")),
        "matricula_ensaiador": _as_str(
            row.get("inspector_registration") or row.get("Matricula_Ensaiador")
        ),
        "data_medicao": _format_date(
            row.get("measurement_date") or row.get("Data_Medicao_Date")
        ),
        "hora_medicao": _format_time(
            row.get("measurement_time") or row.get("Hora_Medicao")
        ),
        "resultado_codigo": result_code,
        "resultado": result,
    }


def _result_label(code: str) -> str:
    return {
        "A": "APROVADO",
        "R": "REPROVADO",
        "T": "TOLERANCIA",
    }.get(code, "REALIZADA")

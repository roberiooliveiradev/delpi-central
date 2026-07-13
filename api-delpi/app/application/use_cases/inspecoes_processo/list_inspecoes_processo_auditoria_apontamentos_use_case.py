from __future__ import annotations

from datetime import date, datetime
from typing import Any

from app.application.dto.inspecoes_processo.inspecoes_processo_auditoria_apontamentos_response import (
    InspecoesProcessoAuditoriaApontamentoItemResponse,
    InspecoesProcessoAuditoriaApontamentosResponse,
    InspecoesProcessoAuditoriaApontamentosSummaryResponse,
)
from app.domain.ports.inspecoes_processo.inspecoes_processo_repository_port import (
    InspecoesProcessoRepositoryPort,
)

VALID_BRANCHES = frozenset({"01", "02"})
DEFAULT_PAGE = 1
DEFAULT_PAGE_SIZE = 50
MAX_PAGE_SIZE = 100


def _as_int(value: Any) -> int:
    if value is None or value == "":
        return 0
    return int(value)


def _as_str(value: Any) -> str:
    if value is None:
        return ""
    return str(value).strip()


def _as_bool(value: Any) -> bool:
    if isinstance(value, bool):
        return value
    if value is None or value == "":
        return False
    if isinstance(value, (int, float)):
        return int(value) != 0
    return str(value).strip().lower() in {"1", "true", "yes", "s", "sim"}


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
    if isinstance(value, datetime):
        return value.strftime("%H:%M")
    raw = _as_str(value)
    if not raw:
        return None
    if len(raw) >= 5 and raw[2] == ":":
        return raw[:5]
    if len(raw) == 4 and raw.isdigit():
        return f"{raw[:2]}:{raw[2:]}"
    if len(raw) == 6 and raw.isdigit():
        return f"{raw[:2]}:{raw[2:4]}"
    return raw


def _parse_data(value: str | None) -> str:
    if value is None or not str(value).strip():
        return date.today().isoformat()
    text = str(value).strip()
    try:
        return date.fromisoformat(text[:10]).isoformat()
    except ValueError as exc:
        raise ValueError("data inválida. Use YYYY-MM-DD.") from exc


def _normalize_item(
    row: dict,
    branch: str,
) -> InspecoesProcessoAuditoriaApontamentoItemResponse:
    return InspecoesProcessoAuditoriaApontamentoItemResponse(
        filial=_as_str(row.get("Filial")) or branch,
        cod_operador=_as_str(row.get("Cod_Operador")),
        login_operador=_as_str(row.get("Login_Operador")),
        nome_operador=_as_str(row.get("Nome_Operador")),
        op=_as_str(row.get("Ordem_Producao")),
        produto=_as_str(row.get("Codigo_Produto")),
        descricao_produto=_as_str(row.get("Descricao_Produto")),
        revisao_produto=_as_str(row.get("Revisao_Produto")),
        operacao=_as_str(row.get("Operacao")),
        centro_trabalho=_as_str(row.get("Centro_Trabalho")),
        data_producao=_format_date(row.get("Data_Producao")),
        hora_inicio=_format_time(row.get("Hora_Inicio")),
        hora_final=_format_time(row.get("Hora_Final")),
        qtd_apontamentos=_as_int(row.get("Qtde_Apontamentos")),
        operador_inspecionou=_as_bool(row.get("Operador_Inspecionou")),
        tem_inspecao_na_op_operacao=_as_bool(row.get("Tem_Inspecao_Na_Op_Operacao")),
        tem_inspecao_amarrada=_as_bool(row.get("Tem_Inspecao_Amarrada")),
        tem_inspecao_executada=_as_bool(
            row.get("Operador_Inspecionou")
            if row.get("Operador_Inspecionou") is not None
            else row.get("Tem_Inspecao_Executada")
        ),
    )


def _normalize_summary(
    row: dict,
) -> InspecoesProcessoAuditoriaApontamentosSummaryResponse:
    return InspecoesProcessoAuditoriaApontamentosSummaryResponse(
        operadores_pendentes=_as_int(row.get("Operadores_Pendentes")),
        apontamentos_pendentes=_as_int(row.get("Apontamentos_Pendentes")),
        ops_operacoes_pendentes=_as_int(row.get("Ops_Operacoes_Pendentes")),
        apontamentos_com_inspecao=_as_int(row.get("Apontamentos_Com_Inspecao")),
        apontamentos_total=_as_int(row.get("Apontamentos_Total")),
    )


class ListInspecoesProcessoAuditoriaApontamentosUseCase:
    def __init__(self, repository: InspecoesProcessoRepositoryPort) -> None:
        self._repository = repository

    def execute(
        self,
        *,
        branch: str,
        data: str | None = None,
        page: int = DEFAULT_PAGE,
        page_size: int = DEFAULT_PAGE_SIZE,
    ) -> InspecoesProcessoAuditoriaApontamentosResponse:
        normalized_branch = str(branch or "").strip()
        if normalized_branch not in VALID_BRANCHES:
            raise ValueError("branch inválida. Use 01 ou 02.")

        resolved_data = _parse_data(data)
        resolved_page = max(int(page), 1)
        resolved_page_size = min(max(int(page_size), 1), MAX_PAGE_SIZE)
        offset = (resolved_page - 1) * resolved_page_size
        fetch_next = resolved_page_size + 1

        summary_row, rows = self._repository.list_auditoria_apontamentos_page(
            normalized_branch,
            data=resolved_data,
            offset=offset,
            fetch_next=fetch_next,
        )

        has_next = len(rows) > resolved_page_size
        items = [
            _normalize_item(row, normalized_branch)
            for row in rows[:resolved_page_size]
        ]
        return InspecoesProcessoAuditoriaApontamentosResponse(
            summary=_normalize_summary(summary_row),
            items=items,
            page=resolved_page,
            page_size=resolved_page_size,
            has_next=has_next,
            data=resolved_data,
        )

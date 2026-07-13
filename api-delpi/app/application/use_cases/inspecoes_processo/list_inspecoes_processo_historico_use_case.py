from __future__ import annotations

import calendar
from datetime import date, datetime
from typing import Any

from app.application.dto.inspecoes_processo.inspecoes_processo_historico_response import (
    InspecoesProcessoHistoricoItemResponse,
    InspecoesProcessoHistoricoResponse,
)
from app.domain.ports.inspecoes_processo.inspecoes_processo_repository_port import (
    InspecoesProcessoRepositoryPort,
)

VALID_BRANCHES = frozenset({"01", "02"})
VALID_RESULTADOS = frozenset({"A", "R", "T"})
DEFAULT_PAGE = 1
DEFAULT_PAGE_SIZE = 25
MAX_PAGE_SIZE = 50
HISTORICO_LOOKBACK_MONTHS = 12


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


def _parse_optional_date(value: str | None, field_name: str) -> str | None:
    if value is None:
        return None
    text = str(value).strip()
    if not text:
        return None
    try:
        return date.fromisoformat(text[:10]).isoformat()
    except ValueError as exc:
        raise ValueError(f"{field_name} inválida. Use YYYY-MM-DD.") from exc


def _months_ago(reference: date, months: int) -> date:
    year = reference.year
    month = reference.month - months
    while month <= 0:
        month += 12
        year -= 1
    day = min(reference.day, calendar.monthrange(year, month)[1])
    return date(year, month, day)


def historico_lookback_floor(today: date | None = None) -> str:
    """Limite inferior canônico: últimos 12 meses (inclusive)."""
    return _months_ago(today or date.today(), HISTORICO_LOOKBACK_MONTHS).isoformat()


def _resolve_data_inicio(parsed_inicio: str | None, *, today: date | None = None) -> str:
    floor = historico_lookback_floor(today)
    if parsed_inicio is None or parsed_inicio < floor:
        return floor
    return parsed_inicio


def _normalize_item(
    row: dict,
    branch: str,
) -> InspecoesProcessoHistoricoItemResponse:
    return InspecoesProcessoHistoricoItemResponse(
        filial=_as_str(row.get("Filial")) or branch,
        unidade=_as_str(row.get("Unidade")),
        ordem_producao=_as_str(row.get("Ordem_Producao")),
        codigo_produto=_as_str(row.get("Codigo_Produto")),
        descricao_produto=_as_str(row.get("Descricao_Produto")),
        revisao_produto=_as_str(row.get("Revisao_Produto")),
        quantidade_op=_as_float(row.get("Quantidade_OP")),
        chave_cabecalho_inspecao=_as_str(row.get("Chave_Cabecalho_Inspecao")),
        origem_inspecao=_as_str(row.get("Origem_Inspecao")),
        qtde_ensaios=_as_int(row.get("Qtde_Ensaios")),
        qtde_ensaios_aprovados=_as_int(row.get("Qtde_Ensaios_Aprovados")),
        qtde_ensaios_reprovados=_as_int(row.get("Qtde_Ensaios_Reprovados")),
        qtde_ensaios_tolerancia=_as_int(row.get("Qtde_Ensaios_Tolerancia")),
        qtde_operacoes=_as_int(row.get("Qtde_Operacoes")),
        qtde_ensaiadores=_as_int(row.get("Qtde_Ensaiadores")),
        resultado_inspecao_codigo=_as_str(row.get("Resultado_Inspecao_Codigo")),
        resultado_inspecao=_as_str(row.get("Resultado_Inspecao")),
        primeira_data_medicao=_format_date(row.get("Primeira_Data_Medicao_Date")),
        ultima_data_medicao=_format_date(row.get("Ultima_Data_Medicao_Date")),
        ultima_hora_medicao=_format_time(row.get("Ultima_Hora_Medicao")),
        matricula_ultimo_ensaiador=_as_str(row.get("Matricula_Ultimo_Ensaiador")),
        nome_ultimo_ensaiador=_as_str(row.get("Nome_Ultimo_Ensaiador")),
    )


class ListInspecoesProcessoHistoricoUseCase:
    def __init__(self, repository: InspecoesProcessoRepositoryPort) -> None:
        self._repository = repository

    def execute(
        self,
        *,
        branch: str,
        page: int = DEFAULT_PAGE,
        page_size: int = DEFAULT_PAGE_SIZE,
        ordem_producao: str | None = None,
        codigo_produto: str | None = None,
        resultado: str | None = None,
        data_inicio: str | None = None,
        data_fim: str | None = None,
    ) -> InspecoesProcessoHistoricoResponse:
        normalized_branch = str(branch or "").strip()
        if normalized_branch not in VALID_BRANCHES:
            raise ValueError("branch inválida. Use 01 ou 02.")

        resolved_page = max(int(page), 1)
        resolved_page_size = min(max(int(page_size), 1), MAX_PAGE_SIZE)

        normalized_op = _as_str(ordem_producao) or None
        normalized_product = _as_str(codigo_produto) or None
        normalized_resultado = _as_str(resultado).upper() or None
        if normalized_resultado and normalized_resultado not in VALID_RESULTADOS:
            raise ValueError("resultado inválido. Use A, R ou T.")

        parsed_inicio = _parse_optional_date(data_inicio, "data_inicio")
        parsed_fim = _parse_optional_date(data_fim, "data_fim")
        if parsed_inicio and parsed_fim and parsed_inicio > parsed_fim:
            raise ValueError("data_inicio não pode ser maior que data_fim.")

        # Listagem sem produto/OP estoura timeout no TOTVS (mesmo com período).
        if not (normalized_op or normalized_product):
            raise ValueError(
                "Informe ordem de produção ou código de produto para buscar o histórico."
            )

        # Sempre limita a janela aos últimos 12 meses para aliviar o TOTVS.
        resolved_inicio = _resolve_data_inicio(parsed_inicio)

        offset = (resolved_page - 1) * resolved_page_size
        fetch_next = resolved_page_size + 1
        rows = self._repository.list_historico_by_branch(
            normalized_branch,
            offset=offset,
            fetch_next=fetch_next,
            ordem_producao=normalized_op,
            codigo_produto=normalized_product,
            resultado=normalized_resultado,
            data_inicio=resolved_inicio,
            data_fim=parsed_fim,
        )

        has_next = len(rows) > resolved_page_size
        items = [
            _normalize_item(row, normalized_branch)
            for row in rows[:resolved_page_size]
        ]
        return InspecoesProcessoHistoricoResponse(
            items=items,
            page=resolved_page,
            page_size=resolved_page_size,
            has_next=has_next,
        )

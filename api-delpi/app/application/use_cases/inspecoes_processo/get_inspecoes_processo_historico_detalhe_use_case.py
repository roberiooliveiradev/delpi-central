from __future__ import annotations

from typing import Any

from app.application.dto.inspecoes_processo.inspecoes_processo_historico_detalhe_response import (
    InspecoesProcessoHistoricoDetalheItemResponse,
    InspecoesProcessoHistoricoDetalheResponse,
)
from app.application.use_cases.inspecoes_processo.list_inspecoes_processo_historico_use_case import (
    _as_int,
    _as_str,
    _format_date,
    _format_time,
    _normalize_item,
)
from app.domain.ports.inspecoes_processo.inspecoes_processo_repository_port import (
    InspecoesProcessoRepositoryPort,
)

VALID_BRANCHES = frozenset({"01", "02"})
DEFAULT_PAGE = 1
DEFAULT_PAGE_SIZE = 100
MAX_PAGE_SIZE = 200


def _optional_str(value: Any) -> str | None:
    text = _as_str(value)
    return text or None


def _optional_float(value: Any) -> float | None:
    if value is None or value == "":
        return None
    return float(value)


def _optional_int(value: Any) -> int | None:
    if value is None or value == "":
        return None
    return _as_int(value)


def _normalize_detalhe_item(
    row: dict,
    branch: str,
) -> InspecoesProcessoHistoricoDetalheItemResponse:
    return InspecoesProcessoHistoricoDetalheItemResponse(
        inspecao_id=_as_str(row.get("Inspecao_Id")),
        ensaio_id=_as_str(row.get("Ensaio_Id")),
        filial=_as_str(row.get("Filial")) or branch,
        unidade=_as_str(row.get("Unidade")),
        ordem_producao=_as_str(row.get("Ordem_Producao")),
        codigo_produto=_as_str(row.get("Codigo_Produto")),
        descricao_produto=_as_str(row.get("Descricao_Produto")),
        revisao_produto=_as_str(row.get("Revisao_Produto")),
        roteiro=_as_str(row.get("Roteiro")),
        operacao=_as_str(row.get("Operacao")),
        recurso=_as_str(row.get("Recurso")),
        ferramenta=_as_str(row.get("Ferramenta")),
        centro_trabalho=_as_str(row.get("Centro_Trabalho")),
        descricao_operacao=_as_str(row.get("Descricao_Operacao")),
        laboratorio=_as_str(row.get("Laboratorio")),
        codigo_ensaio=_as_str(row.get("Codigo_Ensaio")),
        nome_ensaio=_as_str(row.get("Nome_Ensaio")),
        especificacao_textual=_optional_str(row.get("Especificacao_Textual")),
        valor_nominal=_optional_str(row.get("Valor_Nominal")),
        limite_inferior_especificacao=_optional_str(
            row.get("Limite_Inferior_Especificacao")
        ),
        limite_superior_especificacao=_optional_str(
            row.get("Limite_Superior_Especificacao")
        ),
        limite_inferior_controle=_optional_str(row.get("Limite_Inferior_Controle")),
        limite_superior_controle=_optional_str(row.get("Limite_Superior_Controle")),
        regra_min_max=_optional_str(row.get("Regra_Min_Max")),
        unidade_especificacao=_optional_str(row.get("Unidade_Especificacao")),
        especificacao_esperada=_optional_str(row.get("Especificacao_Esperada")),
        medicao_textual=_optional_str(row.get("Medicao_Textual")),
        medicao_numerica_a=_optional_float(row.get("Medicao_Numerica_A")),
        medicao_numerica_n=_optional_float(row.get("Medicao_Numerica_N")),
        medicao_numerica=_optional_str(row.get("Medicao_Numerica")),
        modo_medicao_numerica=_optional_str(row.get("Modo_Medicao_Numerica")),
        fonte_medicao=_optional_str(row.get("Fonte_Medicao")),
        resultado_codigo=_as_str(row.get("Resultado_Codigo")),
        resultado=_as_str(row.get("Resultado")),
        data_medicao=_format_date(row.get("Data_Medicao_Date")),
        hora_medicao=_format_time(row.get("Hora_Medicao")),
        matricula_ensaiador=_as_str(row.get("Matricula_Ensaiador")),
        nome_ensaiador=_as_str(row.get("Nome_Ensaiador")),
        chave_medicao=_optional_str(row.get("Chave_Medicao")),
        qpr_recno=_optional_int(row.get("QPR_RECNO")),
    )


class GetInspecoesProcessoHistoricoDetalheUseCase:
    def __init__(self, repository: InspecoesProcessoRepositoryPort) -> None:
        self._repository = repository

    def execute(
        self,
        *,
        branch: str,
        ordem_producao: str,
        page: int = DEFAULT_PAGE,
        page_size: int = DEFAULT_PAGE_SIZE,
    ) -> InspecoesProcessoHistoricoDetalheResponse | None:
        normalized_branch = str(branch or "").strip()
        if normalized_branch not in VALID_BRANCHES:
            raise ValueError("branch inválida. Use 01 ou 02.")

        normalized_op = _as_str(ordem_producao)
        if not normalized_op:
            raise ValueError("ordem_producao é obrigatória.")

        resolved_page = max(int(page), 1)
        resolved_page_size = min(max(int(page_size), 1), MAX_PAGE_SIZE)

        header_row = self._repository.get_historico_cabecalho_by_op(
            normalized_branch,
            ordem_producao=normalized_op,
        )
        if not header_row:
            return None

        offset = (resolved_page - 1) * resolved_page_size
        fetch_next = resolved_page_size + 1
        item_rows = self._repository.list_historico_detalhe_itens_by_op(
            normalized_branch,
            ordem_producao=normalized_op,
            offset=offset,
            fetch_next=fetch_next,
        )

        has_next = len(item_rows) > resolved_page_size
        items = [
            _normalize_detalhe_item(row, normalized_branch)
            for row in item_rows[:resolved_page_size]
        ]
        return InspecoesProcessoHistoricoDetalheResponse(
            cabecalho=_normalize_item(header_row, normalized_branch),
            items=items,
            page=resolved_page,
            page_size=resolved_page_size,
            has_next=has_next,
        )

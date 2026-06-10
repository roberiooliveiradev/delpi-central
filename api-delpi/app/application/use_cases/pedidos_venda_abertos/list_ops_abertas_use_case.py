from __future__ import annotations

from typing import Any

from app.application.dto.pedidos_venda_abertos.list_ops_abertas_response import (
    ListOpsAbertasResponse,
)
from app.domain.ports.pedidos_venda_abertos.ops_abertas_query_repository_port import (
    OpsAbertasQueryRepositoryPort,
)


def _optional_date(value: Any) -> str | None:
    if value is None or value == "":
        return None
    return str(value)


def _as_float(value: Any) -> float:
    if value is None or value == "":
        return 0.0
    return float(value)


def _as_int(value: Any) -> int:
    if value is None or value == "":
        return 0
    return int(value)


def _as_str(value: Any) -> str:
    if value is None:
        return ""
    return str(value).strip()


def _normalize_detalhe(row: dict) -> dict:
    return {
        "filial": _as_str(row.get("filial")),
        "numero_op": _as_str(row.get("numero_op")),
        "produto": _as_str(row.get("produto")),
        "descricao_produto": _as_str(row.get("descricao_produto")),
        "tipo_produto": _as_str(row.get("tipo_produto")),
        "quantidade_op": _as_float(row.get("quantidade_op")),
        "quantidade_produzida": _as_float(row.get("quantidade_produzida")),
        "saldo_op": _as_float(row.get("saldo_op")),
        "data_emissao_op": _optional_date(row.get("data_emissao_op")),
        "data_inicio_prevista_op": _optional_date(row.get("data_inicio_prevista_op")),
        "data_fim_prevista_op": _optional_date(row.get("data_fim_prevista_op")),
        "armazem": _as_str(row.get("armazem")),
        "observacao_op": _as_str(row.get("observacao_op")),
    }


def _normalize_resumo(row: dict) -> dict:
    return {
        "filial": _as_str(row.get("filial")),
        "produto": _as_str(row.get("produto")),
        "descricao_produto": _as_str(row.get("descricao_produto")),
        "tipo_produto": _as_str(row.get("tipo_produto")),
        "quantidade_ops_abertas": _as_int(row.get("quantidade_ops_abertas")),
        "quantidade_total_ops": _as_float(row.get("quantidade_total_ops")),
        "quantidade_total_produzida": _as_float(row.get("quantidade_total_produzida")),
        "saldo_total_ops": _as_float(row.get("saldo_total_ops")),
        "primeira_data_prevista_op": _optional_date(row.get("primeira_data_prevista_op")),
        "ultima_data_prevista_op": _optional_date(row.get("ultima_data_prevista_op")),
    }


class ListOpsAbertasUseCase:

    def __init__(self, repository: OpsAbertasQueryRepositoryPort):
        self._repository = repository

    def execute(self) -> ListOpsAbertasResponse:
        raw_items, raw_resumo = self._repository.list_open_ops()
        items = [_normalize_detalhe(row) for row in raw_items]
        resumo = [_normalize_resumo(row) for row in raw_resumo]
        return ListOpsAbertasResponse(items=items, resumo=resumo)

from __future__ import annotations
from pydantic import BaseModel, Field
from typing import List, Dict, Any, Optional, Union


class JoinModel(BaseModel):
    type: Optional[str] = "INNER"
    table: Optional[str] = None
    left: str
    right: str


class FilterCondition(BaseModel):
    op: str = "="
    value: Optional[Any] = None


class FilterGroup(BaseModel):
    and_: Optional[List[Any]] = Field(None, alias="and")
    or_: Optional[List[Any]] = Field(None, alias="or")


class OrderByModel(BaseModel):
    field: str
    direction: Optional[str] = "ASC"


class DataQueryRequest(BaseModel):
    """
    Modelo de requisição da rota /data/query.

    - Suporta CTEs via campo `with` (mapeamento nome -> subconsulta completa).
    - Qualquer coisa válida na consulta principal também é válida dentro de uma CTE
      (tabelas, joins, filtros, group_by, having, aggregates, order_by, auto_aggregate).
    """

    # CTEs nomeadas
    with_: Optional[Dict[str, "DataQueryRequest"]] = Field(
        None,
        alias="with",
        description="Mapeamento de CTEs nomeadas (WITH nome AS (...))."
    )

    # Consulta principal ou da CTE
    tables: List[str] = Field(..., description="Tabelas ou CTEs (com ou sem alias).")
    columns: List[str] = Field(
        default_factory=lambda: ["*"],
        description="Lista de colunas/expressões a serem retornadas."
    )
    joins: Optional[List[JoinModel]] = Field(
        None,
        description="JOINs entre tabelas/CTEs."
    )
    filters: Optional[Union[Dict[str, Any], FilterGroup, List[Any]]] = Field(
        None,
        description="Filtros (AND/OR recursivos)."
    )

    group_by: Optional[List[str]] = Field(
        None,
        description="Campos de agrupamento."
    )
    aggregates: Optional[Dict[str, str]] = Field(
        None,
        description="Mapeamento campo -> função de agregação (SUM, COUNT, ...)."
    )
    having: Optional[Dict[str, FilterCondition]] = Field(
        None,
        description="Filtros sobre agregações (HAVING)."
    )

    rollup: Optional[bool] = Field(
        False,
        description="Ativa GROUP BY ROLLUP."
    )
    cube: Optional[bool] = Field(
        False,
        description="Ativa GROUP BY CUBE."
    )
    auto_aggregate: Optional[bool] = Field(
        False,
        description="Se true e houver group_by, agrega automaticamente colunas não agrupadas com SUM."
    )

    order_by: Optional[List[OrderByModel]] = Field(
        None,
        description="Ordenação (campo + direção)."
    )

    aliases: Optional[Dict[str, str]] = Field(
        None,
        description="Mapeamento tabela base -> alias (aplicado automaticamente se não especificado)."
    )

    page: Optional[int] = Field(
        None,
        description="Página da consulta principal (CTE nunca pagina)."
    )
    page_size: Optional[int] = Field(
        None,
        description="Tamanho da página da consulta principal."
    )

class DataQueryRequestOpenAPI(BaseModel):
    with_: Optional[Dict[str, Dict[str, Any]]] = Field(None, alias="with")
    tables: List[str]
    columns: Optional[List[str]] = ["*"]
    joins: Optional[List[Dict[str, Any]]] = None
    filters: Optional[Any] = None
    group_by: Optional[List[str]] = None
    aggregates: Optional[Dict[str, str]] = None
    having: Optional[Dict[str, Any]] = None
    rollup: Optional[bool] = False
    cube: Optional[bool] = False
    auto_aggregate: Optional[bool] = False
    order_by: Optional[List[Dict[str, Any]]] = None
    aliases: Optional[Dict[str, str]] = None
    page: Optional[int] = 1
    page_size: Optional[int] = 50


DataQueryRequest.model_rebuild()

class RawSqlRequest(BaseModel):
    sql: str = Field(..., description="Instrução SQL bruta (pode conter quebras de linha).",
                     json_schema_extra={"format": "textarea"},
                     )
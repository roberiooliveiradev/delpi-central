"""Schemas OpenAPI por perfil de resposta (envelope api-delpi)."""

from __future__ import annotations

from typing import Any

from pydantic import BaseModel, ConfigDict, Field

from app.interface.http.schemas.openapi_examples import (
    PRODUCT_ANALYSER_EXAMPLE,
    PRODUCT_DETAIL_EXAMPLE,
    PRODUCT_FACTORY_STATUS_EXAMPLE,
    PRODUCT_SEARCH_EXAMPLE,
    PRODUCT_STOCK_EXAMPLE,
    PRODUCT_STRUCTURE_EXAMPLE,
    PRODUCT_SUMMARY_EXAMPLE,
)


class ApiDelpiErrorBlock(BaseModel):
    code: str | None = Field(default=None, description="Código de erro estável")
    recoverable: bool = Field(default=True, description="Indica se o cliente pode tentar novamente")


class ResponseMetaSchema(BaseModel):
    dataVersion: str = Field(..., description="Versão do contrato de resposta")
    operationId: str = Field(..., description="Identificador estável da operação")
    entity: str = Field(..., description="Entidade semântica do payload")
    shape: str = Field(
        ...,
        description="Perfil do payload: paged_list, hierarchy, product_snapshot, composite_analysis, scalar",
    )
    pagination: dict[str, Any] | None = None
    fields: dict[str, str] | None = Field(
        default=None,
        description="Glossário curto de campos em data",
    )
    relatedRoutes: dict[str, str] | None = None


class StockItemSchema(BaseModel):
    product_code: str = Field(..., title="Código do produto")
    branch: str = Field(..., title="Filial")
    warehouse: str | None = Field(default=None, title="Armazém")
    current_quantity: float | None = Field(default=None, title="Quantidade atual")
    committed_quantity: float | None = Field(default=None, title="Quantidade empenhada")
    reserved_quantity: float | None = Field(default=None, title="Quantidade reservada")
    available_quantity: float | None = Field(
        default=None,
        title="Saldo disponível",
        description="Atual - empenhado - reservado",
    )


class PagedListDataSchema(BaseModel):
    items: list[dict[str, Any]] = Field(default_factory=list, description="Itens da página")
    page: int = Field(..., description="Página atual")
    page_size: int = Field(..., description="Tamanho da página")
    total: int = Field(..., description="Total de registros")
    total_pages: int | None = Field(default=None, description="Total de páginas")


class PagedListStockDataSchema(BaseModel):
    items: list[StockItemSchema] = Field(default_factory=list)
    page: int
    page_size: int
    total: int
    total_pages: int | None = None


class HierarchyDataSchema(BaseModel):
    root: dict[str, Any] | None = Field(default=None, description="Nó raiz da hierarquia")
    items: list[dict[str, Any]] = Field(default_factory=list, description="Filhos diretos ou árvore")
    page: int | None = None
    page_size: int | None = None
    total: int | None = None
    total_pages: int | None = None


class ProductSnapshotDataSchema(BaseModel):
    product: dict[str, Any] = Field(..., description="Dados cadastrais do produto")
    stock: list[dict[str, Any]] | None = None
    prices: list[dict[str, Any]] | None = None


class CompositeAnalysisDataSchema(BaseModel):
    model_config = ConfigDict(extra="allow")

    product: dict[str, Any] | None = None
    structure: dict[str, Any] | None = None
    guide: dict[str, Any] | None = None
    inspection: dict[str, Any] | None = None
    factory_status: str | None = None
    production: dict[str, Any] | None = None
    shipping: dict[str, Any] | None = None


class ApiDelpiSuccessEnvelope(BaseModel):
    success: bool = True
    message: str
    data: Any = None
    error: ApiDelpiErrorBlock | None = None
    meta: ResponseMetaSchema | None = None


class PagedListResponse(ApiDelpiSuccessEnvelope):
    data: PagedListDataSchema | None = None


class PagedListStockResponse(ApiDelpiSuccessEnvelope):
    model_config = ConfigDict(json_schema_extra={"examples": [PRODUCT_STOCK_EXAMPLE]})

    data: PagedListStockDataSchema | None = None


class HierarchyResponse(ApiDelpiSuccessEnvelope):
    model_config = ConfigDict(json_schema_extra={"examples": [PRODUCT_STRUCTURE_EXAMPLE]})

    data: HierarchyDataSchema | None = None


class ProductDetailResponse(ApiDelpiSuccessEnvelope):
    model_config = ConfigDict(json_schema_extra={"examples": [PRODUCT_DETAIL_EXAMPLE]})

    data: ProductSnapshotDataSchema | dict[str, Any] | None = None


class ProductSnapshotResponse(ApiDelpiSuccessEnvelope):
    model_config = ConfigDict(json_schema_extra={"examples": [PRODUCT_SUMMARY_EXAMPLE]})

    data: ProductSnapshotDataSchema | dict[str, Any] | None = None


class CompositeAnalysisResponse(ApiDelpiSuccessEnvelope):
    model_config = ConfigDict(json_schema_extra={"examples": [PRODUCT_ANALYSER_EXAMPLE]})

    data: CompositeAnalysisDataSchema | dict[str, Any] | None = None


class PlaybookReportResponse(ApiDelpiSuccessEnvelope):
    model_config = ConfigDict(json_schema_extra={"examples": [PRODUCT_FACTORY_STATUS_EXAMPLE]})

    data: dict[str, Any] | None = None


class ProductSearchResponse(PagedListResponse):
    model_config = ConfigDict(json_schema_extra={"examples": [PRODUCT_SEARCH_EXAMPLE]})

"""Authenticated BFF adapter; the TOTVS owner computes all IDF business rules."""

from typing import Literal

from flask import Blueprint, Response, g, jsonify, request
from pydantic import BaseModel, ConfigDict, Field, ValidationError

from app.application.security.supplies_permissions import can_use_analytics
from app.infrastructure.gateways.delpi_api_gateway import (
    DelpiApiGateway,
    DelpiApiGatewayError,
)
from app.infrastructure.gateways.delpi_envelope import unwrap_delpi_envelope
from app.infrastructure.export.supplier_performance_xlsx import (
    EXPORT_FILENAME, XLSX_MIME, build_supplier_performance_xlsx,
)
from app.interfaces.http.auth_decorators import require_policy, require_units

supplier_performance_bp = Blueprint("supplier_performance", __name__)
_GATEWAY = DelpiApiGateway()


class ComponentDto(BaseModel):
    model_config = ConfigDict(allow_inf_nan=False, strict=True)
    assessed_count: int = Field(ge=0)
    positive_count: int = Field(ge=0)
    negative_count: int = Field(ge=0)
    unknown_count: int = Field(ge=0)
    conditional_count: int = Field(ge=0)
    urgent_count: int = Field(ge=0)
    index: float | None = Field(ge=0, le=100)


class SupplierDto(BaseModel):
    model_config = ConfigDict(allow_inf_nan=False, strict=True)
    supplier_code: str
    supplier_store: str
    supplier_name: str
    branches: list[str]
    quality: ComponentDto
    delivery: ComponentDto
    idf: float | None = Field(ge=0, le=100)
    quality_contribution: float | None
    delivery_contribution: float | None
    status: Literal["complete", "missing_quality", "missing_delivery", "inconsistent"]


class SummaryDto(BaseModel):
    model_config = ConfigDict(allow_inf_nan=False, strict=True)
    suppliers: int
    evaluated: int
    incomplete: int
    average_idf: float | None
    average_quality: float | None
    average_delivery: float | None
    inspection_count: int
    receipt_count: int


class MethodologyDto(BaseModel):
    quality_weight: Literal[70]
    delivery_weight: Literal[30]
    scale: Literal[100]
    classification_bands: None
    model_config = ConfigDict(extra="allow")


class PeriodDto(BaseModel):
    from_date: str = Field(alias="from", pattern=r"^[0-9]{4}-[0-9]{2}-[0-9]{2}$")
    to: str = Field(pattern=r"^[0-9]{4}-[0-9]{2}-[0-9]{2}$")


class PerformanceDto(BaseModel):
    items: list[SupplierDto]
    summary: SummaryDto
    methodology: MethodologyDto
    period: PeriodDto
    branches: list[str]
    calculated_at: str


class PerformanceExportDto(PerformanceDto):
    inspections: list[dict]
    deliveries: list[dict]
    supplier_selected: dict[str, str] | None = None


@supplier_performance_bp.get("/analytics/supplier-performance")
@require_policy(can_use_analytics)
@require_units("branch")
def get_portal_supplier_performance():
    """operationId: get_portal_supplier_performance"""
    allowed = {"branch", "date_from", "date_to"}
    if any(key not in allowed for key in request.args) or any(
        len(request.args.getlist(key)) != 1 for key in ("date_from", "date_to")
    ):
        return (
            jsonify(
                {
                    "detail": "Informe filial e um período válido.",
                    "code": "unprocessable",
                }
            ),
            422,
        )
    params = [
        (key, value) for key in request.args for value in request.args.getlist(key)
    ]
    try:
        payload = _GATEWAY.get(
            "/supplies/supplier-performance",
            access_token=g.current_user.access_token or "",
            params=params,
        )
    except DelpiApiGatewayError as exc:
        if exc.status_code == 422:
            return (
                jsonify(
                    {
                        "detail": "Revise o período (máximo de 367 dias) e as filiais.",
                        "code": "unprocessable",
                    }
                ),
                422,
            )
        if exc.status_code in (401, 403):
            return jsonify({"detail": "Acesso negado.", "code": "forbidden"}), 403
        return (
            jsonify(
                {
                    "detail": "Não foi possível consultar o IDF. Tente novamente.",
                    "code": "bad_gateway",
                }
            ),
            502,
        )
    try:
        data = PerformanceDto.model_validate(unwrap_delpi_envelope(payload)).model_dump(
            by_alias=True
        )
    except ValidationError:
        return (
            jsonify(
                {"detail": "Resposta inválida do indicador IDF.", "code": "bad_gateway"}
            ),
            502,
        )
    return jsonify(data), 200


@supplier_performance_bp.get("/analytics/supplier-performance/export")
@require_policy(can_use_analytics)
@require_units("branch")
def export_portal_supplier_performance():
    """operationId: export_portal_supplier_performance — XLSX with source evidence."""
    allowed = {"branch", "date_from", "date_to", "supplier_code", "supplier_store"}
    keys = set(request.args.keys())
    has_code = "supplier_code" in keys
    has_store = "supplier_store" in keys
    if (
        keys - allowed
        or has_code != has_store
        or any(len(request.args.getlist(key)) != 1 for key in ("date_from", "date_to"))
        or any(
            len(request.args.getlist(key)) != 1
            for key in ("supplier_code", "supplier_store")
            if key in keys
        )
    ):
        return jsonify({"detail": "Revise os filtros do relatório.", "code": "unprocessable"}), 422
    pairs = [
        (key, value) for key in request.args for value in request.args.getlist(key)
    ]
    try:
        payload = _GATEWAY.get(
            "/supplies/supplier-performance/evidence-export",
            access_token=g.current_user.access_token or "",
            params=pairs,
        )
    except DelpiApiGatewayError as exc:
        if exc.status_code == 422:
            return jsonify({
                "detail": "Revise o período ou escolha um fornecedor: máximo de 12.000 registros por aba.",
                "code": "unprocessable",
            }), 422
        if exc.status_code in (401, 403):
            return jsonify({"detail": "Acesso negado.", "code": "forbidden"}), 403
        return jsonify({
            "detail": "Não foi possível consultar as evidências do IDF.",
            "code": "bad_gateway",
        }), 502
    try:
        data = PerformanceExportDto.model_validate(
            unwrap_delpi_envelope(payload)
        ).model_dump(by_alias=True)
        if len(data["inspections"]) > 12000 or len(data["deliveries"]) > 12000:
            raise ValueError("Limite de exportação excedido.")
        body = build_supplier_performance_xlsx(data)
    except (ValidationError, ValueError, TypeError, KeyError):
        return jsonify({
            "detail": "A base do relatório não pôde ser validada.",
            "code": "bad_gateway",
        }), 502
    return Response(
        body,
        status=200,
        mimetype=XLSX_MIME,
        headers={
            "Content-Disposition": f'attachment; filename="{EXPORT_FILENAME}"',
            "Cache-Control": "no-store",
            "X-Content-Type-Options": "nosniff",
        },
    )

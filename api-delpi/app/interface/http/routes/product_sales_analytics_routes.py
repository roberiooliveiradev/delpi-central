"""Raio-X de vendas do produto para o Portal PCP. Leitura somente."""

from __future__ import annotations

from fastapi import APIRouter, Path, Query
from app.interface.http.supplies_bff_service_access import require_any_permission_or_trusted_caller

from app.application.security.api_delpi_permissions import KPI_PRODUCTION_ACCESS
from app.core.exceptions import DatabaseConnectionError
from app.core.responses import error_response, not_found_response, success_response
from app.infrastructure.persistence.totvs.product_repositories.product_sales_analytics_repository import (
    ProductSalesAnalyticsRepository,
)
from app.utils.logger import log_error

router = APIRouter(prefix="/products", tags=["products"])


@router.get("/{code}/sales/analytics")
@require_any_permission_or_trusted_caller(KPI_PRODUCTION_ACCESS, caller="production-control-api")
def get_product_sales_analytics(
    code: str = Path(..., min_length=1, max_length=40, pattern=r"^[A-Za-z0-9_.-]+$"),
    branch: str = Query(..., pattern=r"^(01|02)$"),
    months: int = Query(12, description="Janela de 12, 24 ou 36 meses"),
):
    if months not in {12, 24, 36}:
        return error_response("Período inválido. Use 12, 24 ou 36 meses.", status_code=422)
    try:
        result = ProductSalesAnalyticsRepository().get_product_sales(
            branch=branch, product_code=code.strip(), months=months
        )
        if result is None:
            return not_found_response("Produto não encontrado no cadastro SB1 da filial.")
        return success_response(result, "Estatísticas de vendas consultadas com sucesso.")
    except DatabaseConnectionError as exc:
        log_error(f"Falha de consulta ao Protheus (Raio-X): {exc}")
        return error_response("Fonte TOTVS indisponível para a consulta.", status_code=503)
    except Exception as exc:
        log_error(f"Falha no Raio-X do produto: {exc}")
        return error_response("Não foi possível consultar as vendas do produto.", status_code=500)

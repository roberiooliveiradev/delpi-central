from typing import Literal, Optional

from fastapi import APIRouter, Query
from delpi_auth.authorization import require_permission

from app.application.dto.production.production_operational_request import (
    ProductionOperationalRequest,
)
from app.application.security.api_delpi_permissions import API_DELPI_ACCESS
from app.composition.production_operational_composer import (
    build_get_production_consumption_top_items_use_case,
    build_get_production_losses_records_use_case,
    build_get_production_losses_top_materials_use_case,
    build_get_production_schedule_today_use_case,
)
from app.core.responses import error_response
from app.interface.http.openapi_agent_metadata import (
    PRODUCTION_CONSUMPTION_TOP_ITEMS,
    PRODUCTION_LOSSES_RECORDS,
    PRODUCTION_LOSSES_TOP_MATERIALS,
    PRODUCTION_SCHEDULE_TODAY,
)
from app.interface.http.route_response_helpers import api_delpi_success
from app.utils.logger import log_error

router = APIRouter(prefix="/production", tags=["Produção operacional"])


@router.get("/consumption/top-items", **PRODUCTION_CONSUMPTION_TOP_ITEMS)
@require_permission(API_DELPI_ACCESS)
def get_consumption_top_items(
    date_start: Optional[str] = Query(default=None),
    date_end: Optional[str] = Query(default=None),
    branch: Optional[str] = Query(default=None, min_length=2, max_length=2),
    limit: Optional[int] = Query(default=None, ge=1, le=200),
    group_by: Literal["general", "branch"] = Query(default="general"),
):
    try:
        dto = ProductionOperationalRequest(
            date_start=date_start,
            date_end=date_end,
            branch=branch,
            limit=limit,
            group_by=group_by,
        )
        result = build_get_production_consumption_top_items_use_case().execute(dto)
        return api_delpi_success(
            result,
            operation_id=PRODUCTION_CONSUMPTION_TOP_ITEMS["operation_id"],
            message="Itens mais consumidos consultados com sucesso.",
        )
    except ValueError as exc:
        log_error(f"Erro de validação em consumption/top-items: {exc}")
        return error_response(str(exc), status_code=400)
    except Exception as exc:
        log_error(f"Erro em consumption/top-items: {exc}")
        return error_response(str(exc), status_code=500)


@router.get("/losses/records", **PRODUCTION_LOSSES_RECORDS)
@require_permission(API_DELPI_ACCESS)
def get_losses_records(
    date_start: Optional[str] = Query(default=None),
    date_end: Optional[str] = Query(default=None),
    branch: Optional[str] = Query(default=None, min_length=2, max_length=2),
    limit: Optional[int] = Query(default=None, ge=1, le=200),
    loss_type: Literal["refugo", "scrap", "both"] = Query(default="both"),
):
    try:
        dto = ProductionOperationalRequest(
            date_start=date_start,
            date_end=date_end,
            branch=branch,
            limit=limit,
            loss_type=loss_type,
        )
        result = build_get_production_losses_records_use_case().execute(dto)
        return api_delpi_success(
            result,
            operation_id=PRODUCTION_LOSSES_RECORDS["operation_id"],
            message="Registros de perdas consultados com sucesso.",
        )
    except ValueError as exc:
        log_error(f"Erro de validação em losses/records: {exc}")
        return error_response(str(exc), status_code=400)
    except Exception as exc:
        log_error(f"Erro em losses/records: {exc}")
        return error_response(str(exc), status_code=500)


@router.get("/losses/top-materials", **PRODUCTION_LOSSES_TOP_MATERIALS)
@require_permission(API_DELPI_ACCESS)
def get_losses_top_materials(
    date_start: Optional[str] = Query(default=None),
    date_end: Optional[str] = Query(default=None),
    branch: Optional[str] = Query(default=None, min_length=2, max_length=2),
    limit: Optional[int] = Query(default=None, ge=1, le=200),
    loss_type: Literal["refugo", "scrap", "both"] = Query(default="both"),
):
    try:
        dto = ProductionOperationalRequest(
            date_start=date_start,
            date_end=date_end,
            branch=branch,
            limit=limit,
            loss_type=loss_type,
        )
        result = build_get_production_losses_top_materials_use_case().execute(dto)
        return api_delpi_success(
            result,
            operation_id=PRODUCTION_LOSSES_TOP_MATERIALS["operation_id"],
            message="Matérias-primas com mais perdas consultadas com sucesso.",
        )
    except ValueError as exc:
        log_error(f"Erro de validação em losses/top-materials: {exc}")
        return error_response(str(exc), status_code=400)
    except Exception as exc:
        log_error(f"Erro em losses/top-materials: {exc}")
        return error_response(str(exc), status_code=500)


@router.get("/schedule/today", **PRODUCTION_SCHEDULE_TODAY)
@require_permission(API_DELPI_ACCESS)
def get_schedule_today(
    reference_date: Optional[str] = Query(default=None),
    branch: Optional[str] = Query(default=None, min_length=2, max_length=2),
    limit: Optional[int] = Query(default=None, ge=1, le=200),
):
    try:
        dto = ProductionOperationalRequest(
            reference_date=reference_date,
            branch=branch,
            limit=limit,
        )
        result = build_get_production_schedule_today_use_case().execute(dto)
        return api_delpi_success(
            result,
            operation_id=PRODUCTION_SCHEDULE_TODAY["operation_id"],
            message="Programação de produção do dia consultada com sucesso.",
        )
    except ValueError as exc:
        log_error(f"Erro de validação em schedule/today: {exc}")
        return error_response(str(exc), status_code=400)
    except Exception as exc:
        log_error(f"Erro em schedule/today: {exc}")
        return error_response(str(exc), status_code=500)

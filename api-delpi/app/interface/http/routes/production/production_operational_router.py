from typing import Literal, Optional

from fastapi import APIRouter, Query
from delpi_auth.authorization import require_permission

from app.application.dto.production.get_production_order_by_op_request import (
    GetProductionOrderByOpRequest,
)
from app.application.dto.production.production_operational_request import (
    ProductionOperationalRequest,
)
from app.application.security.api_delpi_permissions import API_DELPI_ACCESS
from app.composition.production_operational_composer import (
    build_get_production_allocation_gaps_use_case,
    build_get_production_consumption_by_item_use_case,
    build_get_production_consumption_top_items_use_case,
    build_get_production_consumption_top_items_by_work_center_use_case,
    build_get_production_consumption_top_items_validated_use_case,
    build_get_production_losses_records_use_case,
    build_get_production_losses_top_materials_use_case,
    build_get_production_order_by_op_use_case,
    build_get_production_orders_finished_use_case,
    build_get_production_orders_finished_without_consumption_use_case,
    build_get_production_orders_open_use_case,
    build_get_production_planned_vs_real_time_use_case,
    build_get_production_schedule_today_use_case,
    build_get_production_work_center_average_planned_time_use_case,
    build_get_production_work_center_order_summary_use_case,
)
from app.core.responses import error_response, not_found_response
from app.domain.services.production.production_consumption_top_items_group_by_service import (
    ProductionConsumptionTopItemsGroupByService,
)
from app.interface.http.openapi_agent_metadata import (
    PRODUCTION_ALLOCATION_GAPS,
    PRODUCTION_CONSUMPTION_BY_ITEM,
    PRODUCTION_CONSUMPTION_TOP_ITEMS,
    PRODUCTION_CONSUMPTION_TOP_ITEMS_BY_WORK_CENTER,
    PRODUCTION_CONSUMPTION_TOP_ITEMS_VALIDATED,
    PRODUCTION_LOSSES_RECORDS,
    PRODUCTION_LOSSES_TOP_MATERIALS,
    PRODUCTION_ORDER_BY_OP,
    PRODUCTION_ORDERS_FINISHED,
    PRODUCTION_ORDERS_FINISHED_WITHOUT_CONSUMPTION,
    PRODUCTION_ORDERS_OPEN,
    PRODUCTION_PLANNED_VS_REAL_TIME,
    PRODUCTION_SCHEDULE_TODAY,
    PRODUCTION_WORK_CENTER_AVERAGE_PLANNED_TIME,
    PRODUCTION_WORK_CENTER_ORDER_SUMMARY,
)
from app.interface.http.route_response_helpers import api_delpi_success
from app.utils.logger import log_error

router = APIRouter(prefix="/production", tags=["Produção operacional"])


@router.get("/orders/by-op/{production_order}", **PRODUCTION_ORDER_BY_OP)
@require_permission(API_DELPI_ACCESS)
def get_production_order_by_op(
    production_order: str,
    branch: Optional[str] = Query(default=None, min_length=2, max_length=2),
    product_type: Optional[Literal["PA", "PI"]] = Query(default=None),
    linked_sort_by: Optional[str] = Query(default=None),
    linked_sort_dir: str = Query(default="asc", pattern="^(asc|desc)$"),
):
    try:
        result = build_get_production_order_by_op_use_case().execute(
            GetProductionOrderByOpRequest(
                production_order=production_order,
                branch=branch,
                product_type=product_type,
                linked_sort_by=linked_sort_by,
                linked_sort_dir=linked_sort_dir,
            )
        )
        if result is None:
            return not_found_response(
                f"Ordem de produção {production_order} não encontrada.",
                code="PRODUCTION_ORDER_NOT_FOUND",
            )

        return api_delpi_success(
            result,
            operation_id=PRODUCTION_ORDER_BY_OP["operation_id"],
            message="Detalhe da ordem de produção carregado com sucesso.",
        )
    except ValueError as exc:
        log_error(f"Erro de validação em orders/by-op: {exc}")
        return error_response(str(exc), status_code=400)
    except Exception as exc:
        log_error(f"Erro em orders/by-op: {exc}")
        return error_response(
            "Erro interno ao buscar detalhe da ordem de produção.",
            status_code=500,
        )


@router.get("/consumption/top-items", **PRODUCTION_CONSUMPTION_TOP_ITEMS)
@require_permission(API_DELPI_ACCESS)
def get_consumption_top_items(
    date_start: Optional[str] = Query(default=None),
    date_end: Optional[str] = Query(default=None),
    branch: Optional[str] = Query(default=None, min_length=2, max_length=2),
    limit: Optional[int] = Query(default=None, ge=1, le=200),
    group_by: str = Query(default="general"),
):
    try:
        normalized_group_by = ProductionConsumptionTopItemsGroupByService.normalize(group_by)
        dto = ProductionOperationalRequest(
            date_start=date_start,
            date_end=date_end,
            branch=branch,
            limit=limit,
            group_by=normalized_group_by,
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
    limit: Optional[int] = Query(default=None, ge=1, le=500),
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


@router.get("/orders/open", **PRODUCTION_ORDERS_OPEN)
@require_permission(API_DELPI_ACCESS)
def get_orders_open(
    reference_date: Optional[str] = Query(default=None),
    branch: Optional[str] = Query(default=None, min_length=2, max_length=2),
    work_center: Optional[str] = Query(default=None),
    limit: Optional[int] = Query(default=None, ge=1, le=200),
):
    try:
        dto = ProductionOperationalRequest(
            reference_date=reference_date,
            branch=branch,
            work_center=work_center,
            limit=limit,
        )
        result = build_get_production_orders_open_use_case().execute(dto)
        return api_delpi_success(
            result,
            operation_id=PRODUCTION_ORDERS_OPEN["operation_id"],
            message="OPs em aberto consultadas com sucesso.",
        )
    except ValueError as exc:
        log_error(f"Erro de validação em orders/open: {exc}")
        return error_response(str(exc), status_code=400)
    except Exception as exc:
        log_error(f"Erro em orders/open: {exc}")
        return error_response(str(exc), status_code=500)


@router.get("/orders/finished", **PRODUCTION_ORDERS_FINISHED)
@require_permission(API_DELPI_ACCESS)
def get_orders_finished(
    reference_date: Optional[str] = Query(default=None),
    branch: Optional[str] = Query(default=None, min_length=2, max_length=2),
    work_center: Optional[str] = Query(default=None),
    limit: Optional[int] = Query(default=None, ge=1, le=200),
):
    try:
        dto = ProductionOperationalRequest(
            reference_date=reference_date,
            branch=branch,
            work_center=work_center,
            limit=limit,
        )
        result = build_get_production_orders_finished_use_case().execute(dto)
        return api_delpi_success(
            result,
            operation_id=PRODUCTION_ORDERS_FINISHED["operation_id"],
            message="OPs finalizadas consultadas com sucesso.",
        )
    except ValueError as exc:
        log_error(f"Erro de validação em orders/finished: {exc}")
        return error_response(str(exc), status_code=400)
    except Exception as exc:
        log_error(f"Erro em orders/finished: {exc}")
        return error_response(str(exc), status_code=500)


@router.get("/work-centers/order-summary", **PRODUCTION_WORK_CENTER_ORDER_SUMMARY)
@require_permission(API_DELPI_ACCESS)
def get_work_center_order_summary(
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
        result = build_get_production_work_center_order_summary_use_case().execute(dto)
        return api_delpi_success(
            result,
            operation_id=PRODUCTION_WORK_CENTER_ORDER_SUMMARY["operation_id"],
            message="Resumo de OPs por centro de trabalho consultado com sucesso.",
        )
    except ValueError as exc:
        log_error(f"Erro de validação em work-centers/order-summary: {exc}")
        return error_response(str(exc), status_code=400)
    except Exception as exc:
        log_error(f"Erro em work-centers/order-summary: {exc}")
        return error_response(str(exc), status_code=500)


@router.get(
    "/consumption/top-items-by-work-center",
    **PRODUCTION_CONSUMPTION_TOP_ITEMS_BY_WORK_CENTER,
)
@require_permission(API_DELPI_ACCESS)
def get_consumption_top_items_by_work_center(
    date_start: Optional[str] = Query(default=None),
    date_end: Optional[str] = Query(default=None),
    branch: Optional[str] = Query(default=None, min_length=2, max_length=2),
    work_center: Optional[str] = Query(default=None),
    limit: Optional[int] = Query(default=None, ge=1, le=200),
):
    try:
        dto = ProductionOperationalRequest(
            date_start=date_start,
            date_end=date_end,
            branch=branch,
            work_center=work_center,
            limit=limit,
        )
        result = build_get_production_consumption_top_items_by_work_center_use_case().execute(
            dto
        )
        return api_delpi_success(
            result,
            operation_id=PRODUCTION_CONSUMPTION_TOP_ITEMS_BY_WORK_CENTER["operation_id"],
            message="Consumo por centro de trabalho consultado com sucesso.",
        )
    except ValueError as exc:
        log_error(f"Erro de validação em consumption/top-items-by-work-center: {exc}")
        return error_response(str(exc), status_code=400)
    except Exception as exc:
        log_error(f"Erro em consumption/top-items-by-work-center: {exc}")
        return error_response(str(exc), status_code=500)


@router.get(
    "/consumption/top-items-validated",
    **PRODUCTION_CONSUMPTION_TOP_ITEMS_VALIDATED,
)
@require_permission(API_DELPI_ACCESS)
def get_consumption_top_items_validated(
    date_start: Optional[str] = Query(default=None),
    date_end: Optional[str] = Query(default=None),
    branch: Optional[str] = Query(default=None, min_length=2, max_length=2),
    limit: Optional[int] = Query(default=None, ge=1, le=200),
):
    try:
        dto = ProductionOperationalRequest(
            date_start=date_start,
            date_end=date_end,
            branch=branch,
            limit=limit,
        )
        result = build_get_production_consumption_top_items_validated_use_case().execute(dto)
        return api_delpi_success(
            result,
            operation_id=PRODUCTION_CONSUMPTION_TOP_ITEMS_VALIDATED["operation_id"],
            message="Consumo validado por apontamento consultado com sucesso.",
        )
    except ValueError as exc:
        log_error(f"Erro de validação em consumption/top-items-validated: {exc}")
        return error_response(str(exc), status_code=400)
    except Exception as exc:
        log_error(f"Erro em consumption/top-items-validated: {exc}")
        return error_response(str(exc), status_code=500)


@router.get("/allocation-gaps", **PRODUCTION_ALLOCATION_GAPS)
@require_permission(API_DELPI_ACCESS)
def get_allocation_gaps(
    reference_date: Optional[str] = Query(default=None),
    branch: Optional[str] = Query(default=None, min_length=2, max_length=2),
    work_center: Optional[str] = Query(default=None),
    limit: Optional[int] = Query(default=None, ge=1, le=200),
):
    try:
        dto = ProductionOperationalRequest(
            reference_date=reference_date,
            branch=branch,
            work_center=work_center,
            limit=limit,
        )
        result = build_get_production_allocation_gaps_use_case().execute(dto)
        return api_delpi_success(
            result,
            operation_id=PRODUCTION_ALLOCATION_GAPS["operation_id"],
            message="Componentes sem empenho consultados com sucesso.",
        )
    except ValueError as exc:
        log_error(f"Erro de validação em allocation-gaps: {exc}")
        return error_response(str(exc), status_code=400)
    except Exception as exc:
        log_error(f"Erro em allocation-gaps: {exc}")
        return error_response(str(exc), status_code=500)


@router.get(
    "/orders/finished-without-consumption",
    **PRODUCTION_ORDERS_FINISHED_WITHOUT_CONSUMPTION,
)
@require_permission(API_DELPI_ACCESS)
def get_orders_finished_without_consumption(
    reference_date: Optional[str] = Query(default=None),
    branch: Optional[str] = Query(default=None, min_length=2, max_length=2),
    work_center: Optional[str] = Query(default=None),
    limit: Optional[int] = Query(default=None, ge=1, le=200),
):
    try:
        dto = ProductionOperationalRequest(
            reference_date=reference_date,
            branch=branch,
            work_center=work_center,
            limit=limit,
        )
        result = build_get_production_orders_finished_without_consumption_use_case().execute(
            dto
        )
        return api_delpi_success(
            result,
            operation_id=PRODUCTION_ORDERS_FINISHED_WITHOUT_CONSUMPTION["operation_id"],
            message="OPs finalizadas sem consumo consultadas com sucesso.",
        )
    except ValueError as exc:
        log_error(f"Erro de validação em orders/finished-without-consumption: {exc}")
        return error_response(str(exc), status_code=400)
    except Exception as exc:
        log_error(f"Erro em orders/finished-without-consumption: {exc}")
        return error_response(str(exc), status_code=500)


@router.get(
    "/work-centers/average-planned-time",
    **PRODUCTION_WORK_CENTER_AVERAGE_PLANNED_TIME,
)
@require_permission(API_DELPI_ACCESS)
def get_work_center_average_planned_time(
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
        result = build_get_production_work_center_average_planned_time_use_case().execute(
            dto
        )
        return api_delpi_success(
            result,
            operation_id=PRODUCTION_WORK_CENTER_AVERAGE_PLANNED_TIME["operation_id"],
            message="Tempo médio planejado por CT consultado com sucesso.",
        )
    except ValueError as exc:
        log_error(f"Erro de validação em work-centers/average-planned-time: {exc}")
        return error_response(str(exc), status_code=400)
    except Exception as exc:
        log_error(f"Erro em work-centers/average-planned-time: {exc}")
        return error_response(str(exc), status_code=500)


@router.get("/consumption/by-item/{code}", **PRODUCTION_CONSUMPTION_BY_ITEM)
@require_permission(API_DELPI_ACCESS)
def get_consumption_by_item(
    code: str,
    date_start: Optional[str] = Query(default=None),
    date_end: Optional[str] = Query(default=None),
    branch: Optional[str] = Query(default=None, min_length=2, max_length=2),
    product_group: Optional[str] = Query(default=None, min_length=4, max_length=4),
    limit: Optional[int] = Query(default=None, ge=1, le=200),
):
    try:
        dto = ProductionOperationalRequest(
            item_code=code,
            date_start=date_start,
            date_end=date_end,
            branch=branch,
            product_group=product_group,
            limit=limit,
        )
        result = build_get_production_consumption_by_item_use_case().execute(dto)
        return api_delpi_success(
            result,
            operation_id=PRODUCTION_CONSUMPTION_BY_ITEM["operation_id"],
            message="Consumo real do item por produto consultado com sucesso.",
        )
    except ValueError as exc:
        log_error(f"Erro de validação em consumption/by-item/{{code}}: {exc}")
        return error_response(str(exc), status_code=400)
    except Exception as exc:
        log_error(f"Erro em consumption/by-item/{{code}}: {exc}")
        return error_response(str(exc), status_code=500)


@router.get("/planned-vs-real-time", **PRODUCTION_PLANNED_VS_REAL_TIME)
@require_permission(API_DELPI_ACCESS)
def get_planned_vs_real_time(
    reference_date: Optional[str] = Query(default=None),
    branch: Optional[str] = Query(default=None, min_length=2, max_length=2),
    work_center: Optional[str] = Query(default=None),
    limit: Optional[int] = Query(default=None, ge=1, le=200),
):
    try:
        dto = ProductionOperationalRequest(
            reference_date=reference_date,
            branch=branch,
            work_center=work_center,
            limit=limit,
        )
        result = build_get_production_planned_vs_real_time_use_case().execute(dto)
        return api_delpi_success(
            result,
            operation_id=PRODUCTION_PLANNED_VS_REAL_TIME["operation_id"],
            message="Comparação planejado × real consultada com sucesso.",
        )
    except ValueError as exc:
        log_error(f"Erro de validação em planned-vs-real-time: {exc}")
        return error_response(str(exc), status_code=400)
    except Exception as exc:
        log_error(f"Erro em planned-vs-real-time: {exc}")
        return error_response(str(exc), status_code=500)

"""Rotas — carga máquina (operações alocadas por centro de trabalho, SH8010)."""

from __future__ import annotations

from typing import Optional

from fastapi import APIRouter, Body, Depends, Query
from pydantic import BaseModel, Field
from delpi_auth.authorization import require_any_permission

from app.application.dto.production.machine_load_request import (
    MachineLoadFilterRequest,
    MachineLoadOperationsRequest,
    MachineLoadWindow,
)
from app.application.security.api_delpi_permissions import KPI_PRODUCTION_ACCESS
from app.composition.machine_load_composer import (
    build_get_production_machine_load_appointment_status_use_case,
    build_get_production_machine_load_operations_use_case,
    build_get_production_machine_load_work_centers_use_case,
)
from app.core.exceptions import DatabaseConnectionError
from app.core.responses import error_response
from app.domain.production.machine_load_scope import (
    DEFAULT_PAGE_SIZE,
    DEFAULT_SORT,
    MAX_PAGE_SIZE,
    SORT_VALUES,
)
from app.interface.http.openapi_agent_metadata_builder import OpenApiAgentMetadataBuilder
from app.interface.http.query_param_enums import BRANCH_QUERY_OPTIONAL
from app.interface.http.route_response_helpers import api_delpi_success
from app.utils.logger import log_error

router = APIRouter(
    prefix="/production/machine-load",
    tags=["Produção — Carga máquina"],
)

_CODE_PATTERN = r"^.{0,40}$"
_OP_PATTERN = r"^.{0,30}$"

_WORK_CENTER_FIELDS = {
    "work_center": {"label": "Centro de trabalho", "type": "string"},
    "work_center_name": {"label": "Nome do centro", "type": "string"},
    "operation_count": {"label": "Operações", "type": "integer"},
    "order_count": {"label": "OPs", "type": "integer"},
    "in_production_count": {"label": "Em produção", "type": "integer"},
    "first_scheduled_date": {
        "label": "Primeira programação",
        "type": "string",
        "format": "date",
    },
    "last_scheduled_date": {
        "label": "Última programação",
        "type": "string",
        "format": "date",
    },
    "first_due_date": {
        "label": "Entrega mais antiga",
        "type": "string",
        "format": "date",
    },
    "last_due_date": {
        "label": "Entrega mais distante",
        "type": "string",
        "format": "date",
    },
    "missing_due_date_count": {"label": "Sem data de entrega", "type": "integer"},
}

_OPERATION_FIELDS = {
    "scheduled_date": {"label": "Data programada", "type": "string", "format": "date"},
    "scheduled_start_time": {"label": "Hora início", "type": "string"},
    "work_center": {"label": "Centro de trabalho", "type": "string"},
    "production_order": {"label": "OP", "type": "string"},
    "operation_code": {"label": "Operação", "type": "string"},
    "operation_description": {"label": "Descrição da operação", "type": "string"},
    "tool": {"label": "Ferramenta", "type": "string"},
    "product_code": {"label": "Produto", "type": "string"},
    "product_description": {"label": "Descrição do produto", "type": "string"},
    "planned_qty": {"label": "Quantidade", "type": "number"},
    "pending_qty": {"label": "Saldo", "type": "number"},
    "unit": {"label": "Unidade", "type": "string"},
    "pa_due_date": {"label": "Entrega do PA", "type": "string", "format": "date"},
    "due_date": {"label": "Entrega efetiva", "type": "string", "format": "date"},
    "due_date_source": {"label": "Origem da entrega", "type": "string"},
    "pa_product_code": {"label": "PA", "type": "string"},
    "production_status": {"label": "Status de produção", "type": "string"},
    "is_in_production": {"label": "Em produção agora", "type": "boolean"},
    "active_operator_name": {"label": "Operador", "type": "string"},
    "production_started_date": {
        "label": "Início da produção",
        "type": "string",
        "format": "date",
    },
    "production_started_time": {"label": "Hora de início", "type": "string"},
}


_APPOINTMENT_STATUS_FIELDS = {
    "production_order": {"label": "OP", "type": "string"},
    "operation_code": {"label": "Operação", "type": "string"},
    "production_status": {"label": "Status de produção", "type": "string"},
    "is_in_production": {"label": "Em produção agora", "type": "boolean"},
    "active_operator_name": {"label": "Operador", "type": "string"},
    "production_started_date": {
        "label": "Início da produção",
        "type": "string",
        "format": "date",
    },
    "production_started_time": {"label": "Hora de início", "type": "string"},
}


class AppointmentStatusItem(BaseModel):
    production_order: str = Field(..., min_length=1, max_length=30)
    operation_code: str = Field(..., min_length=1, max_length=10)


class AppointmentStatusRequest(BaseModel):
    branch: str = Field(..., pattern=r"^(01|02)$")
    items: list[AppointmentStatusItem] = Field(default_factory=list)


class MachineLoadCommonQuery:
    def __init__(
        self,
        branch: str | None = None,
        scheduled_start: str | None = None,
        scheduled_end: str | None = None,
        delivery_start: str | None = None,
        delivery_end: str | None = None,
        work_center: str | None = None,
        product_code: str | None = None,
        production_order: str | None = None,
        tool: str | None = None,
        open_only: bool | None = None,
    ) -> None:
        self.branch = branch
        self.scheduled_start = scheduled_start
        self.scheduled_end = scheduled_end
        self.delivery_start = delivery_start
        self.delivery_end = delivery_end
        self.work_center = work_center
        self.product_code = product_code
        self.production_order = production_order
        self.tool = tool
        self.open_only = open_only


def machine_load_common_query(
    branch: str | None = BRANCH_QUERY_OPTIONAL(),
    scheduled_start: Optional[str] = Query(
        default=None,
        description="Scheduled start range begin (H8_DTINI, YYYY-MM-DD). Defaults to today.",
    ),
    scheduled_end: Optional[str] = Query(
        default=None,
        description="Scheduled start range end (H8_DTINI, YYYY-MM-DD). Defaults to today + 7 days.",
    ),
    delivery_start: Optional[str] = Query(
        default=None,
        description=(
            "Effective delivery date range begin (mother order DT_ENTREGA, "
            "C2_DATPRF fallback; YYYY-MM-DD). Replaces the scheduled window."
        ),
    ),
    delivery_end: Optional[str] = Query(
        default=None,
        description=(
            "Effective delivery date range end (mother order DT_ENTREGA, "
            "C2_DATPRF fallback; YYYY-MM-DD). Replaces the scheduled window."
        ),
    ),
    work_center: Optional[str] = Query(
        default=None,
        description="Work center code filter (H8_CTRAB).",
        pattern=_CODE_PATTERN,
    ),
    product_code: Optional[str] = Query(
        default=None,
        description="Product code filter (C2_PRODUTO).",
        pattern=_CODE_PATTERN,
    ),
    production_order: Optional[str] = Query(
        default=None,
        description="Production order key filter (H8_OP).",
        pattern=_OP_PATTERN,
    ),
    tool: Optional[str] = Query(
        default=None,
        description="Tool code filter (H8_FERRAM). MOD means manual labor.",
        pattern=_CODE_PATTERN,
    ),
    open_only: Optional[bool] = Query(
        default=None,
        description="When true (default), only open orders (C2_QUANT > C2_QUJE).",
    ),
) -> MachineLoadCommonQuery:
    return MachineLoadCommonQuery(
        branch=branch,
        scheduled_start=scheduled_start,
        scheduled_end=scheduled_end,
        delivery_start=delivery_start,
        delivery_end=delivery_end,
        work_center=work_center,
        product_code=product_code,
        production_order=production_order,
        tool=tool,
        open_only=open_only,
    )


def _window(common: MachineLoadCommonQuery) -> MachineLoadWindow:
    return MachineLoadWindow.resolve(
        branch=common.branch,
        scheduled_start=common.scheduled_start,
        scheduled_end=common.scheduled_end,
        delivery_start=common.delivery_start,
        delivery_end=common.delivery_end,
    )


def _handle_errors(action: str, exc: Exception):
    if isinstance(exc, ValueError):
        log_error(f"Erro de validação ao {action}: {exc}")
        return error_response(str(exc), status_code=400)
    if isinstance(exc, DatabaseConnectionError):
        log_error(f"Erro de banco ao {action}: {exc}")
        return error_response(
            f"Erro de conexão com o banco ao {action}.",
            status_code=503,
        )
    log_error(f"Erro ao {action}: {exc}")
    return error_response(f"Erro interno ao {action}.", status_code=500)


@router.get(
    "/work-centers",
    **OpenApiAgentMetadataBuilder.from_contract(
        "get_production_machine_load_work_centers",
        path="/production/machine-load/work-centers",
    ),
)
@require_any_permission(KPI_PRODUCTION_ACCESS)
def get_production_machine_load_work_centers(
    common: MachineLoadCommonQuery = Depends(machine_load_common_query),
):
    try:
        request = MachineLoadFilterRequest.from_params(
            window=_window(common),
            work_center=common.work_center,
            product_code=common.product_code,
            production_order=common.production_order,
            tool=common.tool,
            open_only=common.open_only,
        )
        result = build_get_production_machine_load_work_centers_use_case().execute(
            request
        )
        return api_delpi_success(
            result,
            operation_id="get_production_machine_load_work_centers",
            message="Centros de trabalho da carga máquina buscados com sucesso.",
            fields=_WORK_CENTER_FIELDS,
        )
    except Exception as exc:
        return _handle_errors("buscar centros de trabalho da carga máquina", exc)


@router.get(
    "/operations",
    **OpenApiAgentMetadataBuilder.from_contract(
        "get_production_machine_load_operations",
        path="/production/machine-load/operations",
    ),
)
@require_any_permission(KPI_PRODUCTION_ACCESS)
def get_production_machine_load_operations(
    common: MachineLoadCommonQuery = Depends(machine_load_common_query),
    page: int = Query(default=1, ge=1, description="Page number (1-based)."),
    page_size: int = Query(
        default=DEFAULT_PAGE_SIZE,
        ge=1,
        le=MAX_PAGE_SIZE,
        description="Page size.",
    ),
    sort: str = Query(
        default=DEFAULT_SORT,
        description=f"Sort: {', '.join(SORT_VALUES)}.",
        pattern="^(" + "|".join(SORT_VALUES) + ")$",
    ),
):
    try:
        request = MachineLoadOperationsRequest.from_params(
            window=_window(common),
            work_center=common.work_center,
            product_code=common.product_code,
            production_order=common.production_order,
            tool=common.tool,
            open_only=common.open_only,
            page=page,
            page_size=page_size,
            sort=sort,
        )
        result = build_get_production_machine_load_operations_use_case().execute(request)
        return api_delpi_success(
            result,
            operation_id="get_production_machine_load_operations",
            message="Operações da carga máquina buscadas com sucesso.",
            fields=_OPERATION_FIELDS,
        )
    except Exception as exc:
        return _handle_errors("buscar operações da carga máquina", exc)


@router.post(
    "/appointment-status",
    **OpenApiAgentMetadataBuilder.from_contract(
        "get_production_machine_load_appointment_status",
        path="/production/machine-load/appointment-status",
    ),
)
@require_any_permission(KPI_PRODUCTION_ACCESS)
def get_production_machine_load_appointment_status(
    body: AppointmentStatusRequest = Body(...),
):
    try:
        result = build_get_production_machine_load_appointment_status_use_case().execute(
            branch=body.branch,
            items=[item.model_dump() for item in body.items],
        )
        return api_delpi_success(
            result,
            operation_id="get_production_machine_load_appointment_status",
            message="Status de apontamento da carga máquina buscado com sucesso.",
            fields=_APPOINTMENT_STATUS_FIELDS,
        )
    except Exception as exc:
        return _handle_errors("buscar status de apontamento da carga máquina", exc)

"""Dashboard consolidado de chamados Helpdesk (GLPI via helpdesk-api)."""

from __future__ import annotations

from datetime import date

from fastapi import APIRouter, Query, Request

from delpi_auth.authorization import require_any_permission
from delpi_auth.request_context import get_request_authorization

from app.application.security.api_delpi_permissions import API_DELPI_ACCESS
from app.application.use_cases.helpdesk.dashboard_summary_access import (
    DashboardSummaryAccessError,
    load_summary_service_identity,
    service_summary_is_denied,
)
from app.application.services.response_meta_builder import ResponseMetaBuilder
from app.application.use_cases.helpdesk.get_helpdesk_dashboard_summary_use_case import (
    build_get_helpdesk_dashboard_summary_use_case,
)
from app.core.responses import error_response, success_response
from app.infrastructure.gateways.helpdesk_bff_gateway import (
    HelpdeskBffGatewayError,
)
from app.interface.http.openapi_agent_metadata import HELPDESK_DASHBOARD_SUMMARY

router = APIRouter(prefix="/helpdesk", tags=["Helpdesk"])

_HELPDESK_ACCESS = [API_DELPI_ACCESS]
_LINK_REQUIRED = "glpi_link_required"
_UPSTREAM_ERROR = "HELPDESK_UPSTREAM_ERROR"
_TRANSIENT_UPSTREAM = {408, 429, 502, 503, 504}
_PASSTHROUGH_CODES = {
    "glpi_link_required": 409,
    "institutional_read_denied": 403,
    "institutional_credential_invalid": 401,
    "institutional_reader_unavailable": 503,
}


def helpdesk_upstream_error(exc: HelpdeskBffGatewayError):
    """Publish typed Helpdesk failures; other upstream failures stay generic."""
    expected = _PASSTHROUGH_CODES.get(exc.error_code or "")
    if expected is not None and exc.status_code == expected:
        return error_response(
            str(exc),
            status_code=exc.status_code,
            code=exc.error_code,
            recoverable=exc.error_code == _LINK_REQUIRED or exc.status_code in _TRANSIENT_UPSTREAM,
        )
    return error_response(
        str(exc),
        status_code=exc.status_code,
        code=_UPSTREAM_ERROR,
        recoverable=exc.status_code in _TRANSIENT_UPSTREAM,
    )


@router.get("/dashboard/summary", **HELPDESK_DASHBOARD_SUMMARY)
@require_any_permission(_HELPDESK_ACCESS)
def get_helpdesk_dashboard_summary(
    request: Request,
    start_date: date | None = Query(
        default=None,
        description=(
            "Start of the period window (YYYY-MM-DD, inclusive). Bounds `resolved` "
            "(solved_at) and `total_created_in_period` (created_at)."
        ),
    ),
    end_date: date | None = Query(
        default=None,
        description=(
            "End of the period window (YYYY-MM-DD, inclusive). Bounds `resolved` "
            "(solved_at) and `total_created_in_period` (created_at)."
        ),
    ),
    assignee_id: int | None = Query(
        default=None,
        ge=1,
        description="Filter tickets by assignee (GLPI technician user id).",
    ),
    category_id: int | None = Query(
        default=None,
        ge=1,
        description="Filter tickets by GLPI category id.",
    ),
    urgency_id: int | None = Query(
        default=None,
        ge=1,
        le=5,
        description="Filter tickets by GLPI urgency id (1-5).",
    ),
    scope: str | None = Query(
        default=None,
        description=(
            "Informational scope label echoed in meta.scope. Ticket visibility is always "
            "the authorized GLPI scope of the caller's session — this parameter never "
            "widens access."
        ),
    ),
):
    """GET /helpdesk/dashboard/summary — consolidated ticket KPIs."""
    if start_date is not None and end_date is not None and start_date > end_date:
        return error_response(
            "Período inválido: start_date deve ser anterior ou igual a end_date.",
            status_code=422,
            code="VALIDATION_ERROR",
            recoverable=True,
        )
    authorization = str(get_request_authorization() or "")
    if not authorization:
        return error_response(
            "Sessão autenticada necessária para consultar o Helpdesk.",
            status_code=401,
            code="UNAUTHORIZED",
            recoverable=False,
        )
    user = getattr(request.state, "user", None)
    try:
        identity = load_summary_service_identity(
            request.headers,
            principal_type=getattr(user, "principal_type", None),
        )
    except DashboardSummaryAccessError as exc:
        return error_response(
            str(exc),
            status_code=exc.status_code,
            code=exc.code,
            recoverable=exc.status_code in _TRANSIENT_UPSTREAM,
        )
    if service_summary_is_denied(user, identity):
        return error_response(
            "Leitura institucional do Helpdesk não autorizada.",
            status_code=403,
            code="institutional_read_denied",
            recoverable=False,
        )
    service_authorization = None
    if getattr(user, "principal_type", None) == "service" and identity is not None:
        service_authorization = request.headers.get("X-Delpi-Service-Authorization")
    try:
        result = build_get_helpdesk_dashboard_summary_use_case().execute(
            authorization=authorization,
            start_date=start_date,
            end_date=end_date,
            assignee_id=assignee_id,
            category_id=category_id,
            urgency_id=urgency_id,
            scope=scope,
            service_authorization=service_authorization,
        )
    except HelpdeskBffGatewayError as exc:
        return helpdesk_upstream_error(exc)

    meta = ResponseMetaBuilder.build(
        operation_id=HELPDESK_DASHBOARD_SUMMARY["operation_id"],
        entity="helpdesk_dashboard_summary",
        shape="scalar",
    )
    meta.update(result["meta"])
    return success_response(
        data=result["data"],
        message="Indicadores de chamados do Helpdesk consolidados com sucesso.",
        meta=meta,
    )

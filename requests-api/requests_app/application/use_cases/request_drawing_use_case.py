"""Consulta ao desenho do produto acabado vinculado a um process-issue (P4).

A autorização é a mesma do detalhe da solicitação (GetRequestUseCase):
owner ou view-all/process/manage + escopo de filial por registro. O código do
PA vem SEMPRE do payload persistido — o cliente nunca escolhe o código.
"""

from __future__ import annotations

from typing import Any

from requests_app.application.errors import ApplicationError
from requests_app.application.security.requests_permissions import (
    actor_for,
    has_record_branch_access,
)
from requests_app.domain.ports.product_drawing_port import (
    ProductDrawingFile,
    ProductDrawingGatewayPort,
)
from requests_app.domain.ports import (
    RequestRepositoryPort,
    RequestTypeRepositoryPort,
)
from requests_app.domain.process_issue_catalog import PROCESS_ISSUE_TYPE_CODE


def _pa_code_from_payload(payload: dict[str, Any]) -> str | None:
    operation = payload.get("operation")
    if not isinstance(operation, dict):
        return None
    code = str(operation.get("paProductCode") or "").strip()
    return code or None


class GetRequestProductDrawingUseCase:
    def __init__(
        self,
        types: RequestTypeRepositoryPort,
        requests: RequestRepositoryPort,
        drawings: ProductDrawingGatewayPort,
    ) -> None:
        self._types = types
        self._requests = requests
        self._drawings = drawings

    def execute(self, *, user, request_id: str) -> ProductDrawingFile:
        request = self._requests.get(request_id)
        if request is None:
            raise ApplicationError(code="not_found", status_code=404)
        request_type = self._types.get_by_code(request.type_code)
        if request_type is None:
            raise ApplicationError(code="type_not_found", status_code=404)
        actor = actor_for(user, request_type)
        is_owner = request.created_by_user_id == actor.user_id
        if not (
            is_owner or actor.has_view_all or actor.has_process or actor.has_manage
        ):
            raise ApplicationError(code="forbidden", status_code=403)
        if not has_record_branch_access(actor, request):
            raise ApplicationError(code="branch_forbidden", status_code=403)
        if request.type_code != PROCESS_ISSUE_TYPE_CODE:
            raise ApplicationError(
                code="drawing_not_applicable",
                status_code=404,
                detail="Desenho disponível apenas para problemas de processo.",
            )
        pa_code = _pa_code_from_payload(request.payload or {})
        if not pa_code:
            raise ApplicationError(
                code="pa_missing",
                status_code=404,
                detail="Produto acabado não informado no momento do reporte.",
            )
        return self._drawings.resolve_pdf(pa_code)

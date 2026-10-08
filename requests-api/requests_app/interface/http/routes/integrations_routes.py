"""Integrações S2S do Requests API (P2).

POST /integrations/requests cria solicitações em nome de sistemas internos —
nesta etapa SOMENTE ``production-control`` → ``process-issue``. A rota fica
fora do JWT de usuário (middleware whitelist), mas o handler falha fechado:
sem X-Delpi-Service-Token válido, sem caller app esperado ou fora da
allowlist → nada é criado.

O contrato NÃO é uma porta administrativa universal: novos emissores/tipos
devem ser adicionados explicitamente a _ALLOWED_INTEGRATION_TYPES.
"""

from __future__ import annotations

from typing import Any

from fastapi import APIRouter, Header, Request
from pydantic import BaseModel, Field

from delpi_auth.service_token import request_has_valid_internal_service_token

from requests_app.application.errors import ApplicationError
from requests_app.composition.requests_composer import build_create_request_use_case
from requests_app.core.responses import fail, ok

router = APIRouter(prefix="/integrations", tags=["Requests integrations"])

#: Caller esperado no header X-Delpi-Caller-App (convenção DELPI_API_CALLER_APP).
EXPECTED_CALLER_APP = "production-control-api"

#: Allowlist fechada: sourceApp → typeCodes que essa origem pode criar.
_ALLOWED_INTEGRATION_TYPES: dict[str, frozenset[str]] = {
    "production-control": frozenset({"process-issue"}),
}


class IntegrationRequesterBody(BaseModel):
    model_config = {"populate_by_name": True, "extra": "forbid"}

    external_id: str = Field(..., alias="externalId", min_length=1, max_length=120)
    name: str = Field(..., min_length=1, max_length=200)


class IntegrationCreateRequestBody(BaseModel):
    model_config = {"populate_by_name": True, "extra": "forbid"}

    source_app: str = Field(..., alias="sourceApp", min_length=1, max_length=60)
    type_code: str = Field(..., alias="typeCode", min_length=1, max_length=60)
    branch: str | None = Field(default=None, max_length=4)
    priority: str = Field(default="normal", max_length=20)
    requester: IntegrationRequesterBody
    payload: dict[str, Any] = Field(default_factory=dict)


def _handle(exc: ApplicationError):
    data: dict[str, Any] = {"code": exc.code}
    if exc.field:
        data["field"] = exc.field
    return fail(exc.message, status_code=exc.status_code, data=data)


@router.post("/requests")
def create_integration_request(
    body: IntegrationCreateRequestBody,
    request: Request,
    idempotency_key: str | None = Header(default=None, alias="Idempotency-Key"),
):
    if not request_has_valid_internal_service_token(request):
        return fail("Credencial de serviço interno inválida ou ausente.", 401)
    caller = str(request.headers.get("x-delpi-caller-app") or "").strip()
    if caller != EXPECTED_CALLER_APP:
        return fail("Chamador não autorizado para esta integração.", 403)
    allowed = _ALLOWED_INTEGRATION_TYPES.get(body.source_app)
    if allowed is None or body.type_code not in allowed:
        return fail("Tipo de solicitação não permitido nesta integração.", 403)
    try:
        data = build_create_request_use_case().execute_external(
            requester_id=body.requester.external_id,
            requester_name=body.requester.name,
            type_code=body.type_code,
            payload=body.payload,
            branch_code=body.branch,
            priority=body.priority,
            idempotency_key=idempotency_key,
        )
    except ApplicationError as exc:
        return _handle(exc)
    return ok(data, message="Solicitação criada.", status_code=201)

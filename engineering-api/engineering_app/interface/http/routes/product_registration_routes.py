"""Rotas Product Registration — contrato §4 (18 operações).

Prefixo interno ``/v1/product-registration`` (público:
``/apps/engineering-api/v1/product-registration``).

AuthZ: permissões granulares ``engineering.product-registration.*``
(Core) — fail-closed; ``engineering.access`` NÃO concede o módulo.
Principal humano obrigatório; requester é sempre o ``sub`` do JWT —
nunca vem do payload. Idempotency-Key em POST mutável; expectedVersion
(CAS) em mudanças de estado/draft.
"""

from fastapi import APIRouter, Body, Header, Path, Query
from pydantic import BaseModel, Field

from delpi_auth.authorization import require_any_permission
from delpi_auth.context_resolver import resolve_user_context

from engineering_app.application.use_cases.product_registration.actor import (
    prc_actor_from_principal,
)
from engineering_app.composition.prc_composer import build_prc_service
from engineering_app.core.responses import fail, ok
from engineering_app.domain.product_registration.errors import (
    PrcConcurrencyError,
    PrcDuplicateError,
    PrcForbiddenError,
    PrcNotFoundError,
    PrcOfficialError,
    PrcRepositoryError,
    PrcStateConflictError,
    PrcUnverifiableFieldError,
    PrcValidationError,
)
from engineering_app.domain.product_registration.models import ENG_ACCESS
from engineering_app.middleware.request_observability_middleware import (
    get_request_id,
)

router = APIRouter()

# Modelo PO: `engineering.access` abre o CRUD operacional completo do
# módulo (fail-closed). `engineering.manager` é reservado a administração
# futura — nenhum endpoint o exige neste MVP.
_READ_PERMS = [ENG_ACCESS]
_PROCESS_PERMS = [ENG_ACCESS]
_CREATE_PERMS = [ENG_ACCESS]


def _user(operation_id: str):
    user = resolve_user_context()
    if getattr(user, "principal_type", None) != "user":
        return None, fail(
            "Operação exige principal humano.", 403,
            operation_id=operation_id,
        )
    return user, None


def _actor(user, channel: str = "portal"):
    return prc_actor_from_principal(user, channel=channel)


def _err(exc: Exception, operation_id: str):
    if isinstance(exc, PrcNotFoundError):
        return fail("Recurso não encontrado.", 404, operation_id=operation_id)
    if isinstance(exc, PrcUnverifiableFieldError):
        return fail(
            str(exc), 422, data={"code": "unverifiable_field",
                                 "fields": exc.fields},
            operation_id=operation_id,
        )
    if isinstance(exc, PrcValidationError):
        return fail(
            str(exc), 422, data={"code": "validation_error",
                                 "fields": exc.fields},
            operation_id=operation_id,
        )
    if isinstance(exc, PrcDuplicateError):
        return fail(
            str(exc), 409, data={"code": "duplicate_external_reference"},
            operation_id=operation_id,
        )
    if isinstance(exc, PrcConcurrencyError):
        return fail(str(exc), 409, data={"code": "stale_version"},
                    operation_id=operation_id)
    if isinstance(exc, PrcStateConflictError):
        return fail(str(exc), 409, data={"code": "state_conflict"},
                    operation_id=operation_id)
    if isinstance(exc, PrcForbiddenError):
        return fail(str(exc), 403, data={"code": "forbidden"},
                    operation_id=operation_id)
    if isinstance(exc, PrcOfficialError):
        status = {
            "not_found": 409,
            "mismatch": 409,
            "unverifiable": 422,
            "forbidden": 403,
            "unavailable": 503,
            "timeout": 504,
            "contract_error": 502,
        }.get(exc.kind, 502)
        code = {
            "not_found": "erp_mismatch",
            "mismatch": "erp_mismatch",
            "unverifiable": "unverifiable_field",
            "forbidden": "forbidden",
            "unavailable": "official_unavailable",
            "timeout": "official_timeout",
            "contract_error": "official_contract_error",
        }.get(exc.kind, "official_contract_error")
        data = {"code": code, "verification": exc.verification}
        if exc.field_results is not None:
            data["fieldResults"] = exc.field_results
        return fail(str(exc), status, data=data, operation_id=operation_id)
    if isinstance(exc, PrcRepositoryError):
        return fail(str(exc), 503, data={"code": "unavailable"},
                    operation_id=operation_id)
    return fail("Erro interno no Product Registration.", 500,
                operation_id=operation_id)


def _uuid_or_fail(value: str, operation_id: str):
    from uuid import UUID

    try:
        return str(UUID(value)), None
    except (ValueError, AttributeError):
        return None, fail(
            "Identificador inválido (UUID).", 400,
            operation_id=operation_id,
        )


def _expected_version(body, operation_id: str):
    value = getattr(body, "expected_version", None)
    if value is None:
        return None, fail(
            "expectedVersion é obrigatório.", 422,
            data={"code": "validation_error",
                  "fields": {"expectedVersion": "required"}},
            operation_id=operation_id,
        )
    return int(value), None


# --- Schemas ----------------------------------------------------------------


class IntakeBody(BaseModel):
    source: str = Field(..., min_length=1, max_length=100)
    externalRequestId: str | None = Field(default=None, max_length=200)
    externalItemId: str | None = Field(default=None, max_length=200)
    requestType: str = Field(..., pattern="^(create|update)$")
    productType: str = Field(default="raw_material", max_length=64)
    schemaVersion: int = Field(default=1, ge=1)
    requestedData: dict | None = None
    officialProductCode: str | None = Field(default=None, max_length=100)
    baseRevision: int | None = Field(default=None, ge=1)
    changes: list[dict] | None = None


class ActionBody(BaseModel):
    expectedVersion: int = Field(..., ge=1)
    reason: str | None = Field(default=None, max_length=1000)


class RequestInformationBody(ActionBody):
    pendingFields: list[str] = Field(default_factory=list)


class RejectBody(ActionBody):
    reason: str = Field(..., min_length=1, max_length=1000)


class VerifyBody(ActionBody):
    officialCode: str | None = Field(default=None, max_length=100)


class DraftChange(BaseModel):
    path: str = Field(..., min_length=1, max_length=120)
    proposedValue: object = None
    reason: str = Field(..., min_length=1, max_length=500)


class DraftBody(BaseModel):
    expectedVersion: int = Field(..., ge=1)
    changes: list[DraftChange] = Field(..., min_length=1)


# --- 01 intake ---------------------------------------------------------------


@router.post(
    "/v1/product-registration/intake/requests",
    operation_id="prc_intake_submit",
    summary="01 — Intake versionado de solicitação create/update",
)
@require_any_permission(_CREATE_PERMS)
async def prc_intake_submit(
    body: IntakeBody = Body(...),
    idempotency_key: str | None = Header(default=None, max_length=200),
):
    op = "prc_intake_submit"
    user, denied = _user(op)
    if denied is not None:
        return denied
    try:
        data = build_prc_service().submit_request(
            actor=_actor(user),
            source=body.source.strip(),
            external_request_id=(
                body.externalRequestId.strip()[:200]
                if body.externalRequestId else None
            ),
            external_item_id=(
                body.externalItemId.strip()[:200]
                if body.externalItemId else None
            ),
            request_type=body.requestType,
            product_type=body.productType,
            schema_version=body.schemaVersion,
            payload={
                "requestedData": body.requestedData,
                "officialProductCode": body.officialProductCode,
                "baseRevision": body.baseRevision,
                "changes": body.changes,
            },
            idempotency_key=idempotency_key,
        )
    except Exception as exc:
        return _err(exc, op)
    if data.get("replayed"):
        return ok(
            data["response"],
            message="Solicitação já registrada (replay idempotente).",
            status_code=200, operation_id=op,
        )
    return ok(
        data,
        message="Solicitação registrada.",
        status_code=201, operation_id=op,
    )


# --- 02 fila ------------------------------------------------------------------


@router.get(
    "/v1/product-registration/requests",
    operation_id="prc_list_requests",
    summary="02 — Fila paginada e filtrada (escopo do ator)",
)
@require_any_permission(_READ_PERMS)
async def prc_list_requests(
    status: str | None = Query(default=None, max_length=32),
    type: str | None = Query(default=None, pattern="^(create|update)$"),
    assignee: str | None = Query(default=None, max_length=200),
    source: str | None = Query(default=None, max_length=100),
    search: str | None = Query(default=None, max_length=200),
    dateFrom: str | None = Query(default=None, max_length=40),
    dateTo: str | None = Query(default=None, max_length=40),
    page: int = Query(default=1, ge=1),
    pageSize: int = Query(default=25, ge=1, le=100),
):
    op = "prc_list_requests"
    user, denied = _user(op)
    if denied is not None:
        return denied
    try:
        data = build_prc_service().list_requests(
            actor=_actor(user),
            filters={
                "status": status, "type": type, "assignee": assignee,
                "source": source, "search": search,
                "dateFrom": dateFrom, "dateTo": dateTo,
                "page": page, "pageSize": pageSize,
            },
        )
    except Exception as exc:
        return _err(exc, op)
    return ok(data, message="Fila carregada.", operation_id=op)


# --- 03 detalhe -----------------------------------------------------------------


@router.get(
    "/v1/product-registration/requests/{request_id}",
    operation_id="prc_get_request",
    summary="03 — Detalhe do caso (draft, versão, ações permitidas)",
)
@require_any_permission(_READ_PERMS)
async def prc_get_request(request_id: str = Path(...)):
    op = "prc_get_request"
    user, denied = _user(op)
    if denied is not None:
        return denied
    rid, bad = _uuid_or_fail(request_id, op)
    if bad is not None:
        return bad
    try:
        data = build_prc_service().get_request_detail(rid, actor=_actor(user))
    except Exception as exc:
        return _err(exc, op)
    return ok(data, message="Solicitação carregada.", operation_id=op)


# --- 04 timeline -----------------------------------------------------------------


@router.get(
    "/v1/product-registration/requests/{request_id}/timeline",
    operation_id="prc_get_timeline",
    summary="04 — Histórico append-only do caso",
)
@require_any_permission(_READ_PERMS)
async def prc_get_timeline(
    request_id: str = Path(...),
    page: int = Query(default=1, ge=1),
    pageSize: int = Query(default=50, ge=1, le=200),
):
    op = "prc_get_timeline"
    user, denied = _user(op)
    if denied is not None:
        return denied
    rid, bad = _uuid_or_fail(request_id, op)
    if bad is not None:
        return bad
    try:
        data = build_prc_service().get_timeline(
            rid, actor=_actor(user), page=page, page_size=pageSize
        )
    except Exception as exc:
        return _err(exc, op)
    return ok(data, message="Timeline carregada.", operation_id=op)


# --- 05..10 ações -----------------------------------------------------------------


def _action_route(action: str, op: str, summary: str):
    @router.post(
        f"/v1/product-registration/requests/{{request_id}}/actions/{action}",
        operation_id=op, summary=summary,
    )
    @require_any_permission(_PROCESS_PERMS)
    async def handler(
        request_id: str = Path(...),
        body: ActionBody = Body(...),
        idempotency_key: str | None = Header(default=None, max_length=200),
        _action=action, _op=op,
    ):
        user, denied = _user(_op)
        if denied is not None:
            return denied
        rid, bad = _uuid_or_fail(request_id, _op)
        if bad is not None:
            return bad
        service = build_prc_service()
        fn = {
            "start": service.start_request,
            "resume": service.resume_request,
            "submit-review": service.submit_review,
        }[_action]
        try:
            data = fn(
                rid, actor=_actor(user),
                expected_version=body.expectedVersion,
                reason=body.reason, idempotency_key=idempotency_key,
            )
        except Exception as exc:
            return _err(exc, _op)
        return ok(data, message="Ação aplicada.", operation_id=_op)

    return handler


_action_route("start", "prc_action_start", "05 — Iniciar atendimento")
_action_route("resume", "prc_action_resume", "08 — Retomar caso")
_action_route(
    "submit-review", "prc_action_submit_review", "09 — Submeter à revisão"
)


@router.patch(
    "/v1/product-registration/requests/{request_id}/draft",
    operation_id="prc_update_draft",
    summary="06 — Edição campo-a-campo do draft (CAS + allowlist)",
)
@require_any_permission(_PROCESS_PERMS)
async def prc_update_draft(
    request_id: str = Path(...),
    body: DraftBody = Body(...),
    idempotency_key: str | None = Header(default=None, max_length=200),
):
    op = "prc_update_draft"
    user, denied = _user(op)
    if denied is not None:
        return denied
    rid, bad = _uuid_or_fail(request_id, op)
    if bad is not None:
        return bad
    try:
        data = build_prc_service().update_draft(
            rid, actor=_actor(user),
            expected_version=body.expectedVersion,
            changes=[c.model_dump() for c in body.changes],
            idempotency_key=idempotency_key,
        )
    except Exception as exc:
        return _err(exc, op)
    return ok(data, message="Draft atualizado.", operation_id=op)


@router.post(
    "/v1/product-registration/requests/{request_id}/actions/request-information",
    operation_id="prc_action_request_information",
    summary="07 — Solicitar informações (needs_information)",
)
@require_any_permission(_PROCESS_PERMS)
async def prc_action_request_information(
    request_id: str = Path(...),
    body: RequestInformationBody = Body(...),
    idempotency_key: str | None = Header(default=None, max_length=200),
):
    op = "prc_action_request_information"
    user, denied = _user(op)
    if denied is not None:
        return denied
    rid, bad = _uuid_or_fail(request_id, op)
    if bad is not None:
        return bad
    try:
        data = build_prc_service().request_information(
            rid, actor=_actor(user),
            expected_version=body.expectedVersion,
            reason=body.reason, pending_fields=body.pendingFields,
            idempotency_key=idempotency_key,
        )
    except Exception as exc:
        return _err(exc, op)
    return ok(data, message="Pendência registrada.", operation_id=op)


@router.post(
    "/v1/product-registration/requests/{request_id}/actions/reject",
    operation_id="prc_action_reject",
    summary="10 — Rejeitar solicitação (motivo obrigatório)",
)
@require_any_permission(_PROCESS_PERMS)
async def prc_action_reject(
    request_id: str = Path(...),
    body: RejectBody = Body(...),
    idempotency_key: str | None = Header(default=None, max_length=200),
):
    op = "prc_action_reject"
    user, denied = _user(op)
    if denied is not None:
        return denied
    rid, bad = _uuid_or_fail(request_id, op)
    if bad is not None:
        return bad
    try:
        data = build_prc_service().reject_request(
            rid, actor=_actor(user),
            expected_version=body.expectedVersion,
            reason=body.reason, idempotency_key=idempotency_key,
        )
    except Exception as exc:
        return _err(exc, op)
    return ok(data, message="Solicitação rejeitada.", operation_id=op)


@router.post(
    "/v1/product-registration/requests/{request_id}/actions/verify-and-complete",
    operation_id="prc_action_verify_and_complete",
    summary="11 — Verificar no TOTVS e concluir (revisão imutável)",
)
@require_any_permission(_PROCESS_PERMS)
async def prc_action_verify_and_complete(
    request_id: str = Path(...),
    body: VerifyBody = Body(...),
    idempotency_key: str | None = Header(default=None, max_length=200),
):
    op = "prc_action_verify_and_complete"
    user, denied = _user(op)
    if denied is not None:
        return denied
    rid, bad = _uuid_or_fail(request_id, op)
    if bad is not None:
        return bad
    access_token = str(getattr(user, "access_token", "") or "")
    if not access_token:
        return fail(
            "Token de acesso indisponível para verificação oficial.",
            401, operation_id=op,
        )
    try:
        data = await build_prc_service().verify_and_complete(
            rid, actor=_actor(user),
            expected_version=body.expectedVersion,
            official_code=body.officialCode,
            reason=body.reason,
            access_token=access_token,
            correlation_id=get_request_id(),
            idempotency_key=idempotency_key,
        )
    except Exception as exc:
        return _err(exc, op)
    return ok(data, message="Solicitação concluída com verificação "
                            "oficial.", operation_id=op)


# --- 12 verificações -------------------------------------------------------------


@router.get(
    "/v1/product-registration/requests/{request_id}/verifications",
    operation_id="prc_list_verifications",
    summary="12 — Tentativas de verificação e divergências",
)
@require_any_permission(_READ_PERMS)
async def prc_list_verifications(request_id: str = Path(...)):
    op = "prc_list_verifications"
    user, denied = _user(op)
    if denied is not None:
        return denied
    rid, bad = _uuid_or_fail(request_id, op)
    if bad is not None:
        return bad
    try:
        data = build_prc_service().list_verifications(
            rid, actor=_actor(user)
        )
    except Exception as exc:
        return _err(exc, op)
    return ok(data, message="Verificações carregadas.", operation_id=op)


# --- 13-15 technical records ------------------------------------------------------


@router.get(
    "/v1/product-registration/technical-records/{record_id}",
    operation_id="prc_get_record",
    summary="13 — Ficha técnica vigente",
)
@require_any_permission(_READ_PERMS)
async def prc_get_record(record_id: str = Path(...)):
    op = "prc_get_record"
    user, denied = _user(op)
    if denied is not None:
        return denied
    rid, bad = _uuid_or_fail(record_id, op)
    if bad is not None:
        return bad
    try:
        data = build_prc_service().get_record(rid, actor=_actor(user))
    except Exception as exc:
        return _err(exc, op)
    return ok(data, message="Ficha técnica carregada.", operation_id=op)


@router.get(
    "/v1/product-registration/technical-records/{record_id}/revisions",
    operation_id="prc_list_revisions",
    summary="14 — Índice de revisões do registro",
)
@require_any_permission(_READ_PERMS)
async def prc_list_revisions(record_id: str = Path(...)):
    op = "prc_list_revisions"
    user, denied = _user(op)
    if denied is not None:
        return denied
    rid, bad = _uuid_or_fail(record_id, op)
    if bad is not None:
        return bad
    try:
        data = build_prc_service().list_revisions(rid, actor=_actor(user))
    except Exception as exc:
        return _err(exc, op)
    return ok(data, message="Revisões carregadas.", operation_id=op)


@router.get(
    "/v1/product-registration/technical-records/{record_id}/revisions/{revision_number}",
    operation_id="prc_get_revision",
    summary="15 — Snapshot imutável de uma revisão",
)
@require_any_permission(_READ_PERMS)
async def prc_get_revision(
    record_id: str = Path(...), revision_number: int = Path(..., ge=1)
):
    op = "prc_get_revision"
    user, denied = _user(op)
    if denied is not None:
        return denied
    rid, bad = _uuid_or_fail(record_id, op)
    if bad is not None:
        return bad
    try:
        data = build_prc_service().get_revision(
            rid, revision_number, actor=_actor(user)
        )
    except Exception as exc:
        return _err(exc, op)
    return ok(data, message="Revisão carregada.", operation_id=op)


# --- 16 reference-data -------------------------------------------------------------


@router.get(
    "/v1/product-registration/reference-data",
    operation_id="prc_reference_data",
    summary="16 — Catálogo de campos, tipos e política de dados",
)
@require_any_permission(_READ_PERMS + _CREATE_PERMS)
async def prc_reference_data():
    op = "prc_reference_data"
    user, denied = _user(op)
    if denied is not None:
        return denied
    try:
        data = build_prc_service().reference_data(actor=_actor(user))
    except Exception as exc:
        return _err(exc, op)
    return ok(data, message="Dados de referência carregados.",
              operation_id=op)


# --- 17-18 outbound ------------------------------------------------------------------


@router.get(
    "/v1/product-registration/outbound/requests",
    operation_id="prc_outbound_list",
    summary="18 — Consulta outbound paginada por origem",
)
@require_any_permission(_READ_PERMS + _CREATE_PERMS)
async def prc_outbound_list(
    source: str | None = Query(default=None, max_length=100),
    page: int = Query(default=1, ge=1),
    pageSize: int = Query(default=25, ge=1, le=100),
):
    op = "prc_outbound_list"
    user, denied = _user(op)
    if denied is not None:
        return denied
    try:
        data = build_prc_service().outbound_list(
            actor=_actor(user), source=source,
            page=page, page_size=pageSize,
        )
    except Exception as exc:
        return _err(exc, op)
    return ok(data, message="Resultados carregados.", operation_id=op)


@router.get(
    "/v1/product-registration/outbound/requests/{request_id}",
    operation_id="prc_outbound_request",
    summary="17 — Contrato outbound de status/resultado do caso",
)
@require_any_permission(_READ_PERMS + _CREATE_PERMS)
async def prc_outbound_request(request_id: str = Path(...)):
    op = "prc_outbound_request"
    user, denied = _user(op)
    if denied is not None:
        return denied
    rid, bad = _uuid_or_fail(request_id, op)
    if bad is not None:
        return bad
    try:
        data = build_prc_service().outbound_request(rid, actor=_actor(user))
    except Exception as exc:
        return _err(exc, op)
    return ok(data, message="Resultado carregado.", operation_id=op)

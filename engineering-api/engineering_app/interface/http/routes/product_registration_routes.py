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
from engineering_app.infrastructure.gateways.core_identity_lookup import (
    collect_identity_subjects,
    enrich_queue_items,
    enrich_request_identity,
    enrich_timeline_events,
    lookup_display_identities,
)
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


async def _enrich_identity(user, payload, kind: str, apply_fn):
    """Resolução batch governada (Core directory lookup) para linhas
    sem snapshot de nome — best-effort: falha retorna payload intacto."""
    subjects = collect_identity_subjects(payload, kind)
    if not subjects:
        return payload
    access_token = str(getattr(user, "access_token", "") or "")
    if not access_token:
        return payload
    identities = await lookup_display_identities(
        subjects, access_token=access_token
    )
    if not identities:
        return payload
    return apply_fn(payload, identities)


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
        msg = str(exc)
        code = (
            "official_context_stale"
            if msg == "official_context_stale"
            else "stale_version"
        )
        return fail(msg, 409, data={"code": code},
                    operation_id=operation_id)
    if isinstance(exc, PrcStateConflictError):
        msg = str(exc)
        code = (
            "remove_completion_pending_owner"
            if msg == "remove_completion_pending_owner"
            else "state_conflict"
        )
        return fail(msg, 409, data={"code": code},
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
    supplierLinkChanges: list[dict] | None = None
    # D14-FIX — justificativas opcionais por campo/vínculo no create
    # (mesma família de reasons do update; aditivo e opcional).
    reasons: dict | None = None
    # D15 — fingerprint do edit-context para gate de concorrência
    # (estado oficial relevante; não usa timestamp isolado).
    baselineFingerprint: str | None = Field(default=None, max_length=128)
    editContextReadAt: str | None = Field(default=None, max_length=64)


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


class FlagCreateBody(BaseModel):
    title: str = Field(..., min_length=1, max_length=120)
    description: str = Field(..., min_length=1, max_length=1000)
    subject: str = Field(default="GENERAL", max_length=32)
    targetPath: str | None = Field(default=None, max_length=120)
    supplierKey: dict | None = None


class FlagUpdateBody(BaseModel):
    expectedVersion: int = Field(..., ge=1)
    title: str | None = Field(default=None, min_length=1, max_length=120)
    description: str | None = Field(
        default=None, min_length=1, max_length=1000
    )
    subject: str | None = Field(default=None, max_length=32)
    targetPath: str | None = Field(default=None, max_length=120)
    supplierKey: dict | None = None


class FlagActionBody(BaseModel):
    expectedVersion: int = Field(..., ge=1)
    reason: str | None = Field(default=None, max_length=1000)


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
        access_token = str(getattr(user, "access_token", "") or "")
        data = await build_prc_service().submit_request(
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
                "supplierLinkChanges": body.supplierLinkChanges,
                "reasons": body.reasons,
                "baselineFingerprint": body.baselineFingerprint,
                "editContextReadAt": body.editContextReadAt,
            },
            idempotency_key=idempotency_key,
            access_token=access_token or None,
            correlation_id=get_request_id(),
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
    sortBy: str | None = Query(
        default=None,
        pattern="^(createdAt|requestType|status|officialCode|requester|assignedTo|id)$",
    ),
    sortDir: str | None = Query(default=None, pattern="^(asc|desc)$"),
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
                "sortBy": sortBy, "sortDir": sortDir,
            },
        )
    except Exception as exc:
        return _err(exc, op)
    data = await _enrich_identity(user, data, "queue", enrich_queue_items)
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
    data = await _enrich_identity(user, data, "detail", enrich_request_identity)
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
    data = await _enrich_identity(user, data, "timeline", enrich_timeline_events)
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


# --- 16b reference-data: catálogos TOTVS e busca SA2 via api-delpi ---------

_PRC_CATALOG_KINDS = {
    "product-groups", "units", "warehouses", "accounting-accounts"
}


async def _delegated_get(user, op: str, path: str, params: dict):
    """Delega o Bearer humano à rota engineering da api-delpi."""
    from engineering_app.config import settings
    from engineering_app.infrastructure.gateways.downstream_client import (
        DownstreamClient,
    )

    access_token = str(getattr(user, "access_token", "") or "")
    if not access_token:
        return None, fail(
            "Token de acesso indisponível para consulta oficial.",
            401, operation_id=op,
        )
    client = DownstreamClient(settings.DELPI_API_URL, timeout_seconds=15.0)
    try:
        return await client.get(
            path, params=params,
            access_token=access_token, request_id=get_request_id(),
        ), None
    except Exception as exc:
        return None, fail(
            "Fonte oficial indisponível.", 503, operation_id=op,
        )


@router.get(
    "/v1/product-registration/reference-data/products/{official_code}/edit-context",
    operation_id="prc_edit_context",
    summary="16a — Contexto oficial de edição (SB1 + SA5)",
)
@require_any_permission(_READ_PERMS + _CREATE_PERMS)
async def prc_edit_context(
    official_code: str = Path(..., max_length=60),
):
    op = "prc_edit_context"
    user, denied = _user(op)
    if denied is not None:
        return denied
    access_token = str(getattr(user, "access_token", "") or "")
    if not access_token:
        return fail(
            "Token de acesso indisponível para consulta oficial.",
            401, operation_id=op,
        )
    try:
        data = await build_prc_service().edit_context(
            actor=_actor(user),
            official_code=official_code,
            access_token=access_token,
            correlation_id=get_request_id(),
        )
    except Exception as exc:
        return _err(exc, op)
    if data.get("status") != "available":
        kind = str(data.get("status") or "unavailable")
        code = {
            "not_found": 404, "forbidden": 403,
            "timeout": 503, "contract_error": 502,
        }.get(kind, 503)
        return fail(
            f"Fonte oficial indisponível ({kind}).", code,
            data={"code": kind, "officialCode": data.get("officialCode")},
            operation_id=op,
        )
    return ok(data, message="Contexto oficial carregado.", operation_id=op)


@router.get(
    "/v1/product-registration/reference-data/catalogs/{catalog}",
    operation_id="prc_catalog_items",
    summary="16b — Catálogos TOTVS read-only da ficha técnica",
)
@require_any_permission(_READ_PERMS + _CREATE_PERMS)
async def prc_catalog_items(
    catalog: str = Path(...),
    query: str | None = Query(default=None, max_length=60),
    limit: int = Query(default=200, ge=1, le=500),
):
    op = "prc_catalog_items"
    user, denied = _user(op)
    if denied is not None:
        return denied
    if catalog not in _PRC_CATALOG_KINDS:
        return fail("Catálogo não suportado.", 404, operation_id=op)
    data, denied = await _delegated_get(
        user, op,
        f"/engineering/product-registration/catalogs/{catalog}",
        {"query": query, "limit": limit},
    )
    if denied is not None:
        return denied
    return ok(data, message="Catálogo carregado.", operation_id=op)


@router.get(
    "/v1/product-registration/reference-data/suppliers/search",
    operation_id="prc_supplier_search",
    summary="16c — Busca de fornecedores SA2 (código ou nome)",
)
@require_any_permission(_READ_PERMS + _CREATE_PERMS)
async def prc_supplier_search(
    query: str = Query(..., min_length=2, max_length=80),
    page: int = Query(default=1, ge=1),
    pageSize: int = Query(default=20, ge=1, le=100),
):
    op = "prc_supplier_search"
    user, denied = _user(op)
    if denied is not None:
        return denied
    data, denied = await _delegated_get(
        user, op,
        "/engineering/product-registration/suppliers",
        {"query": query, "page": page, "page_size": pageSize},
    )
    if denied is not None:
        return denied
    return ok(data, message="Fornecedores carregados.", operation_id=op)


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


# --- D16 attendance flags ----------------------------------------------------


@router.get(
    "/v1/product-registration/requests/{request_id}/flags",
    operation_id="prc_flag_list",
    summary="D16 — Listar bandeiras de acompanhamento",
)
@require_any_permission(_PROCESS_PERMS)
async def prc_flag_list(
    request_id: str = Path(...),
    status: str | None = Query(default=None, max_length=16),
    page: int = Query(default=1, ge=1),
    pageSize: int = Query(default=25, ge=1, le=100),
):
    op = "prc_flag_list"
    user, denied = _user(op)
    if denied is not None:
        return denied
    rid, bad = _uuid_or_fail(request_id, op)
    if bad is not None:
        return bad
    try:
        data = build_prc_service().list_flags(
            rid, actor=_actor(user), status=status,
            page=page, page_size=pageSize,
        )
    except Exception as exc:
        return _err(exc, op)
    return ok(data, message="Bandeiras carregadas.", operation_id=op)


@router.get(
    "/v1/product-registration/requests/{request_id}/flags/{flag_id}",
    operation_id="prc_flag_detail",
    summary="D16 — Detalhe de bandeira",
)
@require_any_permission(_PROCESS_PERMS)
async def prc_flag_detail(
    request_id: str = Path(...), flag_id: str = Path(...),
):
    op = "prc_flag_detail"
    user, denied = _user(op)
    if denied is not None:
        return denied
    rid, bad = _uuid_or_fail(request_id, op)
    if bad is not None:
        return bad
    fid, bad = _uuid_or_fail(flag_id, op)
    if bad is not None:
        return bad
    try:
        data = build_prc_service().get_flag(rid, fid, actor=_actor(user))
    except Exception as exc:
        return _err(exc, op)
    return ok(data, message="Bandeira carregada.", operation_id=op)


@router.post(
    "/v1/product-registration/requests/{request_id}/flags",
    operation_id="prc_flag_create",
    summary="D16 — Criar bandeira de acompanhamento",
)
@require_any_permission(_PROCESS_PERMS)
async def prc_flag_create(
    request_id: str = Path(...),
    body: FlagCreateBody = Body(...),
    idempotency_key: str | None = Header(default=None, max_length=200),
):
    op = "prc_flag_create"
    user, denied = _user(op)
    if denied is not None:
        return denied
    rid, bad = _uuid_or_fail(request_id, op)
    if bad is not None:
        return bad
    try:
        data = build_prc_service().create_flag(
            rid, actor=_actor(user),
            title=body.title, description=body.description,
            subject=body.subject, target_path=body.targetPath,
            supplier_key=body.supplierKey,
            idempotency_key=idempotency_key,
        )
    except Exception as exc:
        return _err(exc, op)
    if isinstance(data, dict) and data.get("replayed"):
        return ok(
            data["response"], message="Bandeira já registrada (replay).",
            status_code=200, operation_id=op,
        )
    return ok(
        data, message="Bandeira criada.", status_code=201, operation_id=op,
    )


@router.patch(
    "/v1/product-registration/requests/{request_id}/flags/{flag_id}",
    operation_id="prc_flag_update",
    summary="D16 — Editar bandeira",
)
@require_any_permission(_PROCESS_PERMS)
async def prc_flag_update(
    request_id: str = Path(...),
    flag_id: str = Path(...),
    body: FlagUpdateBody = Body(...),
    idempotency_key: str | None = Header(default=None, max_length=200),
):
    op = "prc_flag_update"
    user, denied = _user(op)
    if denied is not None:
        return denied
    rid, bad = _uuid_or_fail(request_id, op)
    if bad is not None:
        return bad
    fid, bad = _uuid_or_fail(flag_id, op)
    if bad is not None:
        return bad
    try:
        data = build_prc_service().update_flag(
            rid, fid, actor=_actor(user),
            expected_version=body.expectedVersion,
            title=body.title, description=body.description,
            subject=body.subject, target_path=body.targetPath,
            supplier_key=body.supplierKey,
            idempotency_key=idempotency_key,
        )
    except Exception as exc:
        return _err(exc, op)
    if isinstance(data, dict) and data.get("replayed"):
        return ok(
            data["response"],
            message="Bandeira já atualizada (replay).",
            operation_id=op,
        )
    return ok(data, message="Bandeira atualizada.", operation_id=op)


@router.post(
    "/v1/product-registration/requests/{request_id}/flags/{flag_id}/actions/resolve",
    operation_id="prc_flag_resolve",
    summary="D16 — Resolver bandeira",
)
@require_any_permission(_PROCESS_PERMS)
async def prc_flag_resolve(
    request_id: str = Path(...),
    flag_id: str = Path(...),
    body: FlagActionBody = Body(...),
    idempotency_key: str | None = Header(default=None, max_length=200),
):
    op = "prc_flag_resolve"
    user, denied = _user(op)
    if denied is not None:
        return denied
    rid, bad = _uuid_or_fail(request_id, op)
    if bad is not None:
        return bad
    fid, bad = _uuid_or_fail(flag_id, op)
    if bad is not None:
        return bad
    try:
        data = build_prc_service().resolve_flag(
            rid, fid, actor=_actor(user),
            expected_version=body.expectedVersion,
            reason=body.reason, idempotency_key=idempotency_key,
        )
    except Exception as exc:
        return _err(exc, op)
    if isinstance(data, dict) and data.get("replayed"):
        return ok(
            data["response"],
            message="Bandeira já resolvida (replay).",
            operation_id=op,
        )
    return ok(data, message="Bandeira resolvida.", operation_id=op)


@router.post(
    "/v1/product-registration/requests/{request_id}/flags/{flag_id}/actions/reopen",
    operation_id="prc_flag_reopen",
    summary="D16 — Reabrir bandeira",
)
@require_any_permission(_PROCESS_PERMS)
async def prc_flag_reopen(
    request_id: str = Path(...),
    flag_id: str = Path(...),
    body: FlagActionBody = Body(...),
    idempotency_key: str | None = Header(default=None, max_length=200),
):
    op = "prc_flag_reopen"
    user, denied = _user(op)
    if denied is not None:
        return denied
    rid, bad = _uuid_or_fail(request_id, op)
    if bad is not None:
        return bad
    fid, bad = _uuid_or_fail(flag_id, op)
    if bad is not None:
        return bad
    try:
        data = build_prc_service().reopen_flag(
            rid, fid, actor=_actor(user),
            expected_version=body.expectedVersion,
            reason=body.reason, idempotency_key=idempotency_key,
        )
    except Exception as exc:
        return _err(exc, op)
    if isinstance(data, dict) and data.get("replayed"):
        return ok(
            data["response"],
            message="Bandeira já reaberta (replay).",
            operation_id=op,
        )
    return ok(data, message="Bandeira reaberta.", operation_id=op)


@router.delete(
    "/v1/product-registration/requests/{request_id}/flags/{flag_id}",
    operation_id="prc_flag_delete",
    summary="D16 — Excluir bandeira (soft-delete)",
)
@require_any_permission(_PROCESS_PERMS)
async def prc_flag_delete(
    request_id: str = Path(...),
    flag_id: str = Path(...),
    expectedVersion: int = Query(..., ge=1),
    idempotency_key: str | None = Header(default=None, max_length=200),
):
    op = "prc_flag_delete"
    user, denied = _user(op)
    if denied is not None:
        return denied
    rid, bad = _uuid_or_fail(request_id, op)
    if bad is not None:
        return bad
    fid, bad = _uuid_or_fail(flag_id, op)
    if bad is not None:
        return bad
    try:
        data = build_prc_service().delete_flag(
            rid, fid, actor=_actor(user),
            expected_version=expectedVersion,
            idempotency_key=idempotency_key,
        )
    except Exception as exc:
        return _err(exc, op)
    if isinstance(data, dict) and data.get("replayed"):
        return ok(
            data["response"],
            message="Bandeira já excluída (replay).",
            operation_id=op,
        )
    return ok(data, message="Bandeira excluída.", operation_id=op)

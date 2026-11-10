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
        if msg == "remove_completion_pending_owner":
            code = "remove_completion_pending_owner"
        elif msg == "open_flag_exists":
            code = "open_flag_exists"
        else:
            code = "state_conflict"
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


def _unwrap_replay(data):
    """Replay idempotente do service → (payload, replayed)."""
    if isinstance(data, dict) and data.get("replayed"):
        return data["response"], True
    return data, False


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


class InformationQuestionBody(BaseModel):
    """PRC-REF-019 — pergunta tipada; o alvo é validado no domínio."""

    targetType: str = Field(default="GENERAL", max_length=32)
    targetPath: str | None = Field(default=None, max_length=120)
    targetAttribute: str | None = Field(default=None, max_length=32)
    supplierKey: dict | None = None
    questionText: str = Field(..., min_length=1, max_length=1000)


class RequestInformationBody(ActionBody):
    pendingFields: list[str] = Field(default_factory=list)
    questions: list[InformationQuestionBody] = Field(default_factory=list)
    message: str | None = Field(default=None, max_length=1000)


class CorrectionTargetBody(BaseModel):
    """PRC-REF-022 — alvo tipado da devolução (FIELD | SUPPLIER_LINK)."""

    targetType: str = Field(..., min_length=1, max_length=32)
    targetPath: str | None = Field(default=None, max_length=120)
    targetAttribute: str | None = Field(default=None, max_length=32)
    supplierKey: dict | None = None
    reason: str = Field(..., min_length=3, max_length=1000)


class ReturnForCorrectionBody(ActionBody):
    targets: list[CorrectionTargetBody] = Field(..., min_length=1)


class ReturnedFieldChangeBody(BaseModel):
    path: str = Field(..., min_length=1, max_length=120)
    proposedValue: object = None
    reason: str = Field(..., min_length=3, max_length=500)
    mode: str = Field(default="changed", max_length=32)


class UpdateReturnedFieldsBody(BaseModel):
    expectedVersion: int = Field(..., ge=1)
    changes: list[ReturnedFieldChangeBody] = Field(..., min_length=1)


class DivergenceSupplierKeyBody(BaseModel):
    supplierCode: str = Field(..., min_length=1, max_length=32)
    store: str = Field(..., min_length=1, max_length=8)


class DivergenceRouteBody(ActionBody):
    """PRC-REF-021 — encaminhamento por item divergente (não altera MATCH)."""

    verificationId: str = Field(..., min_length=1, max_length=64)
    targetType: str = Field(..., min_length=1, max_length=32)
    targetPath: str | None = Field(default=None, max_length=128)
    supplierKey: DivergenceSupplierKeyBody | None = None
    targetAttribute: str | None = Field(default=None, max_length=64)
    decision: str = Field(..., min_length=1, max_length=64)
    reason: str = Field(..., min_length=3, max_length=1000)


class InformationAnswerBody(BaseModel):
    questionId: str = Field(..., min_length=1, max_length=64)
    text: str = Field(default="", max_length=4000)


class InformationDraftAnswersBody(BaseModel):
    expectedRoundVersion: int = Field(..., ge=1)
    answers: list[InformationAnswerBody] = Field(default_factory=list)


class InformationSubmitAnswersBody(BaseModel):
    expectedRoundVersion: int = Field(..., ge=1)
    answers: list[InformationAnswerBody] | None = None


class InformationAcceptBody(BaseModel):
    expectedRoundVersion: int = Field(..., ge=1)


class InformationFollowUpBody(BaseModel):
    expectedRoundVersion: int = Field(..., ge=1)
    questions: list[InformationQuestionBody] = Field(default_factory=list)
    followUpQuestionIds: list[str] = Field(default_factory=list)
    message: str | None = Field(default=None, max_length=1000)


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
    subject: str = Field(default="FIELD", max_length=32)
    targetPath: str | None = Field(default=None, max_length=120)
    targetAttribute: str | None = Field(default=None, max_length=32)
    supplierKey: dict | None = None


class FlagUpdateBody(BaseModel):
    expectedVersion: int = Field(..., ge=1)
    title: str | None = Field(default=None, min_length=1, max_length=120)
    description: str | None = Field(
        default=None, min_length=1, max_length=1000
    )
    # Campos de alvo aceitos só para rejeição explícita de retarget.
    subject: str | None = Field(default=None, max_length=32)
    targetPath: str | None = Field(default=None, max_length=120)
    targetAttribute: str | None = Field(default=None, max_length=32)
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
            "return-to-attendance": service.return_to_attendance,
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
    "submit-review",
    "prc_action_submit_review",
    "09 — Submeter à revisão (LEGADO — preferir Concluir atendimento)",
)
_action_route(
    "return-to-attendance",
    "prc_action_return_to_attendance",
    "09b — Reabrir legado under_review → in_progress (PRC-REF-020)",
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
            questions=[q.model_dump() for q in body.questions],
            message=body.message,
            idempotency_key=idempotency_key,
        )
    except Exception as exc:
        return _err(exc, op)
    data, _ = _unwrap_replay(data)
    return ok(data, message="Pendência registrada.", operation_id=op)


@router.post(
    "/v1/product-registration/requests/{request_id}/actions/return-for-correction",
    operation_id="prc_action_return_for_correction",
    summary="PRC-REF-022 — Devolver para correção (needs_correction)",
)
@require_any_permission(_PROCESS_PERMS)
async def prc_action_return_for_correction(
    request_id: str = Path(...),
    body: ReturnForCorrectionBody = Body(...),
    idempotency_key: str | None = Header(default=None, max_length=200),
):
    op = "prc_action_return_for_correction"
    user, denied = _user(op)
    if denied is not None:
        return denied
    rid, bad = _uuid_or_fail(request_id, op)
    if bad is not None:
        return bad
    try:
        data = build_prc_service().return_for_correction(
            rid,
            actor=_actor(user),
            expected_version=body.expectedVersion,
            targets=[t.model_dump() for t in body.targets],
            reason=body.reason,
            idempotency_key=idempotency_key,
        )
    except Exception as exc:
        return _err(exc, op)
    data, _ = _unwrap_replay(data)
    return ok(data, message="Devolvida para correção.", operation_id=op)


@router.patch(
    "/v1/product-registration/requests/{request_id}/returned-fields",
    operation_id="prc_update_returned_fields",
    summary="PRC-REF-022 — Solicitante corrige campos devolvidos",
)
@require_any_permission(_PROCESS_PERMS)
async def prc_update_returned_fields(
    request_id: str = Path(...),
    body: UpdateReturnedFieldsBody = Body(...),
    idempotency_key: str | None = Header(default=None, max_length=200),
):
    op = "prc_update_returned_fields"
    user, denied = _user(op)
    if denied is not None:
        return denied
    rid, bad = _uuid_or_fail(request_id, op)
    if bad is not None:
        return bad
    try:
        data = build_prc_service().update_returned_fields(
            rid,
            actor=_actor(user),
            expected_version=body.expectedVersion,
            changes=[c.model_dump() for c in body.changes],
            idempotency_key=idempotency_key,
        )
    except Exception as exc:
        return _err(exc, op)
    data, _ = _unwrap_replay(data)
    return ok(data, message="Campos devolvidos atualizados.", operation_id=op)


@router.post(
    "/v1/product-registration/requests/{request_id}/actions/resubmit-correction",
    operation_id="prc_action_resubmit_correction",
    summary="PRC-REF-022 — Reenviar correção para Engenharia",
)
@require_any_permission(_PROCESS_PERMS)
async def prc_action_resubmit_correction(
    request_id: str = Path(...),
    body: ActionBody = Body(...),
    idempotency_key: str | None = Header(default=None, max_length=200),
):
    op = "prc_action_resubmit_correction"
    user, denied = _user(op)
    if denied is not None:
        return denied
    rid, bad = _uuid_or_fail(request_id, op)
    if bad is not None:
        return bad
    try:
        data = build_prc_service().resubmit_correction(
            rid,
            actor=_actor(user),
            expected_version=body.expectedVersion,
            idempotency_key=idempotency_key,
        )
    except Exception as exc:
        return _err(exc, op)
    data, _ = _unwrap_replay(data)
    return ok(data, message="Correção reenviada à Engenharia.", operation_id=op)


@router.get(
    "/v1/product-registration/requests/{request_id}/correction-returns",
    operation_id="prc_list_correction_returns",
    summary="PRC-REF-022 — Listar ciclos de devolução",
)
@require_any_permission(_PROCESS_PERMS)
async def prc_list_correction_returns(request_id: str = Path(...)):
    op = "prc_list_correction_returns"
    user, denied = _user(op)
    if denied is not None:
        return denied
    rid, bad = _uuid_or_fail(request_id, op)
    if bad is not None:
        return bad
    try:
        data = build_prc_service().list_correction_returns(
            rid, actor=_actor(user)
        )
    except Exception as exc:
        return _err(exc, op)
    return ok(data, message="Ciclos de devolução.", operation_id=op)


@router.get(
    "/v1/product-registration/requests/{request_id}/correction-returns/{return_id}",
    operation_id="prc_get_correction_return",
    summary="PRC-REF-022 — Detalhe de um ciclo de devolução",
)
@require_any_permission(_PROCESS_PERMS)
async def prc_get_correction_return(
    request_id: str = Path(...),
    return_id: str = Path(...),
):
    op = "prc_get_correction_return"
    user, denied = _user(op)
    if denied is not None:
        return denied
    rid, bad = _uuid_or_fail(request_id, op)
    if bad is not None:
        return bad
    ret_id, bad2 = _uuid_or_fail(return_id, op)
    if bad2 is not None:
        return bad2
    try:
        data = build_prc_service().get_correction_return(
            rid, ret_id, actor=_actor(user)
        )
    except Exception as exc:
        return _err(exc, op)
    return ok(data, message="Ciclo de devolução.", operation_id=op)


@router.post(
    "/v1/product-registration/requests/{request_id}/actions/route-divergence",
    operation_id="prc_action_route_divergence",
    summary=(
        "PRC-REF-021 (legado/deprecated operacional REF-021-REF-01) — "
        "registrar encaminhamento auditável sem alterar MATCH; não é "
        "etapa compulsória do Portal"
    ),
    deprecated=True,
)
@require_any_permission(_PROCESS_PERMS)
async def prc_action_route_divergence(
    request_id: str = Path(...),
    body: DivergenceRouteBody = Body(...),
    idempotency_key: str | None = Header(default=None, max_length=200),
):
    op = "prc_action_route_divergence"
    user, denied = _user(op)
    if denied is not None:
        return denied
    rid, bad = _uuid_or_fail(request_id, op)
    if bad is not None:
        return bad
    try:
        data = build_prc_service().route_divergence(
            rid,
            actor=_actor(user),
            expected_version=body.expectedVersion,
            verification_id=body.verificationId,
            target_type=body.targetType,
            target_path=body.targetPath,
            supplier_key=(
                body.supplierKey.model_dump() if body.supplierKey else None
            ),
            target_attribute=body.targetAttribute,
            decision=body.decision,
            reason=body.reason,
            idempotency_key=idempotency_key,
        )
    except Exception as exc:
        return _err(exc, op)
    data, _ = _unwrap_replay(data)
    return ok(data, message="Encaminhamento registrado.", operation_id=op)


# --- PRC-REF-019 rodadas de esclarecimento ---------------------------------


def _answers_payload(answers) -> list[dict]:
    return [a.model_dump() for a in answers or []]


@router.get(
    "/v1/product-registration/requests/{request_id}/information-rounds",
    operation_id="prc_information_round_list",
    summary="PRC-REF-019 — Listar rodadas de esclarecimento do caso",
)
@require_any_permission(_READ_PERMS)
async def prc_information_round_list(request_id: str = Path(...)):
    op = "prc_information_round_list"
    user, denied = _user(op)
    if denied is not None:
        return denied
    rid, bad = _uuid_or_fail(request_id, op)
    if bad is not None:
        return bad
    try:
        data = build_prc_service().list_information_rounds(
            rid, actor=_actor(user)
        )
    except Exception as exc:
        return _err(exc, op)
    return ok(data, message="Rodadas carregadas.", operation_id=op)


@router.get(
    "/v1/product-registration/requests/{request_id}/information-rounds/{round_id}",
    operation_id="prc_information_round_get",
    summary="PRC-REF-019 — Detalhe de uma rodada de esclarecimento",
)
@require_any_permission(_READ_PERMS)
async def prc_information_round_get(
    request_id: str = Path(...), round_id: str = Path(...),
):
    op = "prc_information_round_get"
    user, denied = _user(op)
    if denied is not None:
        return denied
    rid, bad = _uuid_or_fail(request_id, op)
    if bad is not None:
        return bad
    rnd_id, bad = _uuid_or_fail(round_id, op)
    if bad is not None:
        return bad
    try:
        data = build_prc_service().get_information_round(
            rid, rnd_id, actor=_actor(user)
        )
    except Exception as exc:
        return _err(exc, op)
    return ok(data, message="Rodada carregada.", operation_id=op)


@router.patch(
    "/v1/product-registration/requests/{request_id}/information-rounds/{round_id}/answers",
    operation_id="prc_information_round_draft_answers",
    summary="PRC-REF-019 — Salvar rascunho de respostas (solicitante)",
)
@require_any_permission(_PROCESS_PERMS)
async def prc_information_round_draft_answers(
    request_id: str = Path(...),
    round_id: str = Path(...),
    body: InformationDraftAnswersBody = Body(...),
    idempotency_key: str | None = Header(default=None, max_length=200),
):
    op = "prc_information_round_draft_answers"
    user, denied = _user(op)
    if denied is not None:
        return denied
    rid, bad = _uuid_or_fail(request_id, op)
    if bad is not None:
        return bad
    rnd_id, bad = _uuid_or_fail(round_id, op)
    if bad is not None:
        return bad
    try:
        data = build_prc_service().draft_information_answers(
            rid, rnd_id, actor=_actor(user),
            expected_round_version=body.expectedRoundVersion,
            answers=_answers_payload(body.answers),
            idempotency_key=idempotency_key,
        )
    except Exception as exc:
        return _err(exc, op)
    data, _ = _unwrap_replay(data)
    return ok(data, message="Rascunho salvo.", operation_id=op)


@router.post(
    "/v1/product-registration/requests/{request_id}/information-rounds/{round_id}/actions/submit-answers",
    operation_id="prc_information_round_submit_answers",
    summary="PRC-REF-019 — Enviar respostas ao analista (solicitante)",
)
@require_any_permission(_PROCESS_PERMS)
async def prc_information_round_submit_answers(
    request_id: str = Path(...),
    round_id: str = Path(...),
    body: InformationSubmitAnswersBody = Body(...),
    idempotency_key: str | None = Header(default=None, max_length=200),
):
    op = "prc_information_round_submit_answers"
    user, denied = _user(op)
    if denied is not None:
        return denied
    rid, bad = _uuid_or_fail(request_id, op)
    if bad is not None:
        return bad
    rnd_id, bad = _uuid_or_fail(round_id, op)
    if bad is not None:
        return bad
    try:
        data = build_prc_service().submit_information_answers(
            rid, rnd_id, actor=_actor(user),
            expected_round_version=body.expectedRoundVersion,
            answers=(
                None if body.answers is None
                else _answers_payload(body.answers)
            ),
            idempotency_key=idempotency_key,
        )
    except Exception as exc:
        return _err(exc, op)
    data, _ = _unwrap_replay(data)
    return ok(data, message="Respostas enviadas.", operation_id=op)


@router.post(
    "/v1/product-registration/requests/{request_id}/information-rounds/{round_id}/questions/{question_id}/actions/accept",
    operation_id="prc_information_question_accept",
    summary="PRC-REF-019 — Aceitar esclarecimento de uma pergunta (analista)",
)
@require_any_permission(_PROCESS_PERMS)
async def prc_information_question_accept(
    request_id: str = Path(...),
    round_id: str = Path(...),
    question_id: str = Path(...),
    body: InformationAcceptBody = Body(...),
    idempotency_key: str | None = Header(default=None, max_length=200),
):
    op = "prc_information_question_accept"
    user, denied = _user(op)
    if denied is not None:
        return denied
    rid, bad = _uuid_or_fail(request_id, op)
    if bad is not None:
        return bad
    rnd_id, bad = _uuid_or_fail(round_id, op)
    if bad is not None:
        return bad
    qid, bad = _uuid_or_fail(question_id, op)
    if bad is not None:
        return bad
    try:
        data = build_prc_service().accept_information_question(
            rid, rnd_id, qid, actor=_actor(user),
            expected_round_version=body.expectedRoundVersion,
            idempotency_key=idempotency_key,
        )
    except Exception as exc:
        return _err(exc, op)
    data, _ = _unwrap_replay(data)
    return ok(data, message="Esclarecimento aceito.", operation_id=op)


@router.post(
    "/v1/product-registration/requests/{request_id}/information-rounds/{round_id}/actions/request-follow-up",
    operation_id="prc_information_round_request_follow_up",
    summary="PRC-REF-019 — Solicitar complemento em nova rodada (analista)",
)
@require_any_permission(_PROCESS_PERMS)
async def prc_information_round_request_follow_up(
    request_id: str = Path(...),
    round_id: str = Path(...),
    body: InformationFollowUpBody = Body(...),
    idempotency_key: str | None = Header(default=None, max_length=200),
):
    op = "prc_information_round_request_follow_up"
    user, denied = _user(op)
    if denied is not None:
        return denied
    rid, bad = _uuid_or_fail(request_id, op)
    if bad is not None:
        return bad
    rnd_id, bad = _uuid_or_fail(round_id, op)
    if bad is not None:
        return bad
    try:
        data = build_prc_service().request_information_follow_up(
            rid, rnd_id, actor=_actor(user),
            expected_parent_version=body.expectedRoundVersion,
            questions=[q.model_dump() for q in body.questions],
            follow_up_question_ids=body.followUpQuestionIds,
            message=body.message,
            idempotency_key=idempotency_key,
        )
    except Exception as exc:
        return _err(exc, op)
    data, replayed = _unwrap_replay(data)
    return ok(
        data, message="Complemento solicitado.",
        status_code=200 if replayed else 201, operation_id=op,
    )


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


async def _prc_complete_handler(
    *,
    request_id: str,
    body: VerifyBody,
    idempotency_key: str | None,
    op: str,
    use_legacy_alias: bool,
):
    """PRC-REF-020 — conclusão verificada (complete + alias verify-and-complete)."""
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
    svc = build_prc_service()
    try:
        if use_legacy_alias:
            data = await svc.verify_and_complete(
                rid, actor=_actor(user),
                expected_version=body.expectedVersion,
                official_code=body.officialCode,
                reason=body.reason,
                access_token=access_token,
                correlation_id=get_request_id(),
                idempotency_key=idempotency_key,
            )
        else:
            data = await svc.complete_attendance(
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
    return ok(
        data,
        message="Atendimento concluído com verificação oficial.",
        operation_id=op,
    )


@router.post(
    "/v1/product-registration/requests/{request_id}/actions/complete",
    operation_id="prc_action_complete",
    summary="11 — Concluir atendimento (validação + verificação TOTVS)",
)
@require_any_permission(_PROCESS_PERMS)
async def prc_action_complete(
    request_id: str = Path(...),
    body: VerifyBody = Body(...),
    idempotency_key: str | None = Header(default=None, max_length=200),
):
    return await _prc_complete_handler(
        request_id=request_id,
        body=body,
        idempotency_key=idempotency_key,
        op="prc_action_complete",
        use_legacy_alias=False,
    )


@router.post(
    "/v1/product-registration/requests/{request_id}/actions/verify-and-complete",
    operation_id="prc_action_verify_and_complete",
    summary="11b — Alias legado de Concluir atendimento (mesmo use case)",
    deprecated=True,
)
@require_any_permission(_PROCESS_PERMS)
async def prc_action_verify_and_complete(
    request_id: str = Path(...),
    body: VerifyBody = Body(...),
    idempotency_key: str | None = Header(default=None, max_length=200),
):
    return await _prc_complete_handler(
        request_id=request_id,
        body=body,
        idempotency_key=idempotency_key,
        op="prc_action_verify_and_complete",
        use_legacy_alias=True,
    )


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


# --- D16 / D16-REF-01 attendance flags ---------------------------------------


@router.get(
    "/v1/product-registration/flags",
    operation_id="prc_flag_list_cross",
    summary="D16-REF-01 — Consulta transversal de bandeiras",
)
@require_any_permission(_PROCESS_PERMS)
async def prc_flag_list_cross(
    status: str | None = Query(default=None, max_length=16),
    subject: str | None = Query(default=None, max_length=32),
    targetPath: str | None = Query(default=None, max_length=120),
    targetAttribute: str | None = Query(default=None, max_length=32),
    productCode: str | None = Query(default=None, max_length=60),
    requestId: str | None = Query(default=None),
    requestType: str | None = Query(default=None, max_length=32),
    requestStatus: str | None = Query(default=None, max_length=32),
    assignee: str | None = Query(default=None, max_length=200),
    supplierCode: str | None = Query(default=None, max_length=60),
    store: str | None = Query(default=None, max_length=16),
    createdFrom: str | None = Query(default=None, max_length=40),
    createdTo: str | None = Query(default=None, max_length=40),
    page: int = Query(default=1, ge=1),
    pageSize: int = Query(default=25, ge=1, le=100),
):
    op = "prc_flag_list_cross"
    user, denied = _user(op)
    if denied is not None:
        return denied
    rid = None
    if requestId:
        rid, bad = _uuid_or_fail(requestId, op)
        if bad is not None:
            return bad
    try:
        data = build_prc_service().list_flags_cross_case(
            actor=_actor(user),
            status=status,
            subject=subject,
            target_path=targetPath,
            target_attribute=targetAttribute,
            product_code=productCode,
            request_id=rid,
            request_type=requestType,
            request_status=requestStatus,
            assignee=assignee,
            supplier_code=supplierCode,
            store=store,
            created_from=createdFrom,
            created_to=createdTo,
            page=page,
            page_size=pageSize,
        )
    except Exception as exc:
        return _err(exc, op)
    return ok(data, message="Bandeiras transversais carregadas.",
              operation_id=op)


@router.get(
    "/v1/product-registration/flags/summary",
    operation_id="prc_flag_summary",
    summary="D16-REF-01 — Agregados de bandeiras (AuthZ no servidor)",
)
@require_any_permission(_PROCESS_PERMS)
async def prc_flag_summary(
    groupBy: str = Query(default="request", max_length=32),
    status: str | None = Query(default=None, max_length=16),
    subject: str | None = Query(default=None, max_length=32),
    targetPath: str | None = Query(default=None, max_length=120),
    targetAttribute: str | None = Query(default=None, max_length=32),
    productCode: str | None = Query(default=None, max_length=60),
    requestStatus: str | None = Query(default=None, max_length=32),
    page: int = Query(default=1, ge=1),
    pageSize: int = Query(default=50, ge=1, le=100),
):
    op = "prc_flag_summary"
    user, denied = _user(op)
    if denied is not None:
        return denied
    try:
        data = build_prc_service().summarize_flags_cross_case(
            actor=_actor(user),
            group_by=groupBy,
            status=status,
            subject=subject,
            target_path=targetPath,
            target_attribute=targetAttribute,
            product_code=productCode,
            request_status=requestStatus,
            page=page,
            page_size=pageSize,
        )
    except Exception as exc:
        return _err(exc, op)
    return ok(data, message="Resumo de bandeiras carregado.",
              operation_id=op)


@router.get(
    "/v1/product-registration/requests/{request_id}/flags",
    operation_id="prc_flag_list",
    summary="D16 — Listar bandeiras de acompanhamento",
)
@require_any_permission(_PROCESS_PERMS)
async def prc_flag_list(
    request_id: str = Path(...),
    status: str | None = Query(default=None, max_length=16),
    subject: str | None = Query(default=None, max_length=32),
    targetPath: str | None = Query(default=None, max_length=120),
    targetAttribute: str | None = Query(default=None, max_length=32),
    supplierCode: str | None = Query(default=None, max_length=60),
    store: str | None = Query(default=None, max_length=16),
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
            subject=subject, target_path=targetPath,
            target_attribute=targetAttribute,
            supplier_code=supplierCode, store=store,
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
            target_attribute=body.targetAttribute,
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
        # Só rejeita retarget quando o cliente envia os campos de alvo.
        sent = body.model_fields_set
        data = build_prc_service().update_flag(
            rid, fid, actor=_actor(user),
            expected_version=body.expectedVersion,
            title=body.title, description=body.description,
            subject=body.subject if "subject" in sent else None,
            target_path=body.targetPath if "targetPath" in sent else ...,
            supplier_key=(
                body.supplierKey if "supplierKey" in sent else ...
            ),
            target_attribute=(
                body.targetAttribute if "targetAttribute" in sent else ...
            ),
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

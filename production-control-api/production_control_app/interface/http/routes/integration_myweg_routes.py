"""Ingestão S2S MyWEG — necessidades e observações de NF Emitidas."""

from __future__ import annotations

from typing import Any

from fastapi import APIRouter, Header, Request

from delpi_auth.service_token import request_has_valid_internal_service_token
from production_control_app.composition.pc_composer import (
    build_myweg_invoice_observations_service,
    build_myweg_needs_service,
    build_myweg_sb1_resolve_service,
)
from production_control_app.core.responses import fail, ok
from production_control_app.domain.errors import (
    MyWegInvoiceObservationConflict,
    MyWegInvoiceObservationValidationFailed,
    MyWegNeedsBatchConflict,
    MyWegNeedsBatchNotFound,
    MyWegNeedsValidationFailed,
)

router = APIRouter(prefix="/integrations/myweg", tags=["MyWEG integrations"])


def _deny_unless_internal(request: Request):
    if request_has_valid_internal_service_token(request):
        return None
    return fail("Credencial de serviço interno inválida ou ausente.", 401)


@router.post("/need-batches", operation_id="ingest_myweg_need_batch")
def ingest_myweg_need_batch(
    request: Request,
    body: dict[str, Any],
    idempotency_key: str | None = Header(default=None, alias="Idempotency-Key"),
    caller_app: str | None = Header(default=None, alias="X-Delpi-Caller-App"),
):
    denied = _deny_unless_internal(request)
    if denied is not None:
        return denied
    try:
        data = build_myweg_needs_service().ingest_batch(
            body,
            idempotency_key=idempotency_key,
            caller_app=caller_app,
        )
    except MyWegNeedsValidationFailed as exc:
        return fail(str(exc), 422, data={"issues": exc.issues})
    except MyWegNeedsBatchConflict as exc:
        return fail(str(exc), 409)
    except ValueError as exc:
        return fail(str(exc), 422)
    status = 201 if data.get("created") else 200
    return ok(data, status_code=status)


@router.post(
    "/invoice-observations",
    operation_id="ingest_myweg_invoice_observation_batch",
)
def ingest_myweg_invoice_observation_batch(
    request: Request,
    body: dict[str, Any],
    idempotency_key: str | None = Header(default=None, alias="Idempotency-Key"),
    caller_app: str | None = Header(default=None, alias="X-Delpi-Caller-App"),
):
    denied = _deny_unless_internal(request)
    if denied is not None:
        return denied
    try:
        data = build_myweg_invoice_observations_service().ingest_observation(
            body,
            idempotency_key=idempotency_key,
            caller_app=caller_app,
        )
    except MyWegInvoiceObservationValidationFailed as exc:
        return fail(str(exc), 422, data={"issues": exc.issues})
    except MyWegInvoiceObservationConflict as exc:
        return fail(str(exc), 409)
    except ValueError as exc:
        return fail(str(exc), 422)
    status = 201 if data.get("created") else 200
    return ok(data, status_code=status)


@router.post(
    "/need-batches/sb1-resolve",
    operation_id="resolve_myweg_need_batch_sb1",
)
def resolve_myweg_need_batch_sb1(
    request: Request,
    body: dict[str, Any] | None = None,
    caller_app: str | None = Header(default=None, alias="X-Delpi-Caller-App"),
):
    """Resolução SB1 — S2S apenas (view JWT não dispara). dry_run default true.

    Automação do publicador: dry_run=false + skip_if_complete=true evita
    reconsulta Protheus quando a projeção V026 já cobre o lote sem unavailable.
    """
    denied = _deny_unless_internal(request)
    if denied is not None:
        return denied
    payload = body or {}
    dry_run = True if payload.get("dry_run") is None else bool(payload.get("dry_run"))
    skip_if_complete = bool(
        payload.get("skip_if_complete")
        if payload.get("skip_if_complete") is not None
        else payload.get("skipIfComplete")
    )
    try:
        data = build_myweg_sb1_resolve_service().resolve_batch(
            batch_id=(payload.get("batch_id") or payload.get("batchId") or None),
            collection_id=(
                payload.get("collection_id") or payload.get("collectionId") or None
            ),
            dry_run=dry_run,
            caller_app=caller_app,
            skip_if_complete=skip_if_complete,
        )
    except MyWegNeedsBatchNotFound as exc:
        return fail(str(exc), 404)
    except MyWegNeedsValidationFailed as exc:
        return fail(str(exc), 422, data={"issues": exc.issues})
    except ValueError as exc:
        return fail(str(exc), 422)
    return ok(data)

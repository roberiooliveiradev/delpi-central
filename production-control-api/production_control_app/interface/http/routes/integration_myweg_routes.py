"""Ingestão S2S MyWEG Necessidades — POST /integrations/myweg/need-batches."""

from __future__ import annotations

from typing import Any

from fastapi import APIRouter, Header, Request

from delpi_auth.service_token import request_has_valid_internal_service_token
from production_control_app.composition.pc_composer import build_myweg_needs_service
from production_control_app.core.responses import fail, ok
from production_control_app.domain.errors import (
    MyWegNeedsBatchConflict,
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

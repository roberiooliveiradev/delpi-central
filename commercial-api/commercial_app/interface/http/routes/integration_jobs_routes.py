"""Ops jobs for commercial integration side-effects."""

from __future__ import annotations

import logging

from fastapi import APIRouter, Request

from commercial_app.application.security.auth_dependencies import require_any_permission
from commercial_app.application.security.commercial_permissions import (
    COMMERCIAL_MANAGE_PERMISSIONS,
)
from commercial_app.composition.commercial_composer import (
    build_scan_ready_to_invoice_notifications_use_case,
)
from commercial_app.core.responses import fail, ok

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/integrations/jobs", tags=["Commercial integrations"])


@router.post(
    "/ready-to-invoice-scan",
    operation_id="scan_commercial_ready_to_invoice_notifications",
)
@require_any_permission(*COMMERCIAL_MANAGE_PERMISSIONS)
def scan_ready_to_invoice_notifications(_request: Request):
    try:
        result = build_scan_ready_to_invoice_notifications_use_case().execute()
        return ok(result, message="Varredura de pronto para faturar concluída.")
    except RuntimeError as exc:
        return fail(
            str(exc),
            502,
            operation_id="scan_commercial_ready_to_invoice_notifications",
        )
    except Exception:
        logger.exception("scan_ready_to_invoice_notifications_failed")
        return fail(
            "Erro interno na varredura de pronto para faturar.",
            500,
            operation_id="scan_commercial_ready_to_invoice_notifications",
        )

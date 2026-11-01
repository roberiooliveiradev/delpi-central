"""Governed Comex writes for SURI ``execute``.

Same ACT machinery as ``supplier_execute``: per-operation durable claim in
``supplies.suri_execute_operations`` (V005), structured audit line, closed
operation keys, caller's own identity. The writes delegate to the canonical
``ComexAnalysisService`` — the same owner used by the BFF routes — so no
business rule is duplicated here.

Outcomes: confirmed | rejected | indeterminate | replayed | in_progress.
"""

from __future__ import annotations

import logging
import uuid as _uuid
from typing import Any

from app.interfaces.mcp.supplier_execute import (
    _audit,
    _claim_or_replay,
    _complete_claim,
    _op_error,
)
from app.application.services.comex_analysis_service import (
    ComexAnalysisService,
    ComexConflictError,
    ComexForbiddenError,
    ComexNotFoundError,
    ComexValidationError,
)
from app.domain.entities import EffectiveUser

logger = logging.getLogger("supplies-api.suri_mcp.execute")

_COMEX = ComexAnalysisService()

_NCM_REQUEST_KEYS = frozenset(
    {
        "idempotency_key", "ncm_code", "description", "ncm_version",
        "family_code", "product_codes", "notes", "initial_status",
    }
)
_NCM_TRANSITION_KEYS = frozenset(
    {
        "idempotency_key", "governance_id", "to_status", "notes",
        "expected_revision",
    }
)
_VIEW_CREATE_KEYS = frozenset(
    {
        "idempotency_key", "name", "unit_scope", "selected_product_codes",
        "selected_materials", "approved_ncm_references",
        "selected_metrics", "date_range", "granularity", "view_mode",
    }
)
_VIEW_UPDATE_KEYS = _VIEW_CREATE_KEYS | frozenset({"view_id"})

COMEX_WRITE_KEYS_BY_ACTION = {
    "ncm_request": _NCM_REQUEST_KEYS,
    "ncm_transition": _NCM_TRANSITION_KEYS,
    "view_create": _VIEW_CREATE_KEYS,
    "view_update": _VIEW_UPDATE_KEYS,
}


def _exec_op(user: EffectiveUser, action: str, op: dict[str, Any]) -> dict:
    if action == "ncm_request":
        return _COMEX.request_ncm(
            user=user,
            ncm_code=op.get("ncm_code"),
            description=op.get("description"),
            ncm_version=op.get("ncm_version"),
            family_code=op.get("family_code"),
            product_codes=op.get("product_codes"),
            notes=op.get("notes"),
            initial_status=op.get("initial_status"),
        )
    if action == "ncm_transition":
        return _COMEX.transition(
            user=user,
            governance_id=op.get("governance_id"),
            to_status=op.get("to_status"),
            notes=op.get("notes"),
            expected_revision=op.get("expected_revision"),
        )
    if action == "view_create":
        body = {k: v for k, v in op.items() if k != "idempotency_key"}
        return _COMEX.create_view(user=user, body=body)
    body = {k: v for k, v in op.items() if k != "idempotency_key"}
    return _COMEX.update_view(
        op.get("view_id"), user=user, body=body
    )


def _identity_for(action: str, payload: dict[str, Any]) -> dict[str, Any]:
    if action in {"ncm_request", "ncm_transition"}:
        return {
            "governance_id": payload.get("governance_id"),
            "status": payload.get("status"),
        }
    return {
        "view_id": payload.get("view_id"),
        "name": payload.get("name"),
    }


def execute_comex_write(
    user: EffectiveUser, *, action: str, operations: list[dict[str, Any]]
) -> dict[str, Any]:
    correlation_id = str(_uuid.uuid4())
    results: list[dict[str, Any]] = []
    for index, op in enumerate(operations):
        idem_key = op.get("idempotency_key")
        entry, claim_id = _claim_or_replay(
            user, action, index, op, idem_key, correlation_id
        )
        if entry is not None:
            _audit(user, correlation_id=correlation_id, action=action, entry=entry,
            field_names=sorted(k for k in op if k != "idempotency_key"))
            results.append(entry)
            continue
        try:
            payload = _exec_op(user, action, op)
        except ComexValidationError as exc:
            entry = _op_error(
                index,
                outcome="rejected",
                code=getattr(exc, "code", "invalid_request"),
                message=str(exc),
                idempotency_key=idem_key,
                http_status=422,
            )
        except ComexNotFoundError as exc:
            entry = _op_error(
                index,
                outcome="rejected",
                code="not_found",
                message=str(exc),
                idempotency_key=idem_key,
                http_status=404,
            )
        except ComexForbiddenError as exc:
            entry = _op_error(
                index,
                outcome="rejected",
                code="forbidden",
                message=str(exc),
                idempotency_key=idem_key,
                http_status=403,
            )
        except ComexConflictError as exc:
            entry = _op_error(
                index,
                outcome="rejected",
                code=getattr(exc, "code", "conflict"),
                message=str(exc),
                idempotency_key=idem_key,
                http_status=409,
            )
        except Exception as exc:  # noqa: BLE001
            entry = _op_error(
                index,
                outcome="indeterminate",
                code="upstream_error",
                message=(
                    "Upstream did not confirm the write — verify before "
                    "retrying with the same idempotency_key."
                ),
                idempotency_key=idem_key,
                http_status=502,
            )
        else:
            entry = {
                "index": index,
                "outcome": "confirmed",
                "idempotency_key": idem_key,
                **_identity_for(action, payload),
            }
        _complete_claim(claim_id, entry)
        _audit(user, correlation_id=correlation_id, action=action, entry=entry,
            field_names=sorted(k for k in op if k != "idempotency_key"))
        results.append(entry)
    confirmed = sum(1 for r in results if r.get("outcome") == "confirmed")
    return {
        "success": all(
            r.get("outcome") in {"confirmed", "replayed"} for r in results
        ),
        "correlation_id": correlation_id,
        "entity": "comex",
        "action": action,
        "operations_total": len(results),
        "operations_confirmed": confirmed,
        "results": results,
    }

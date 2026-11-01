"""Governed session/preferences and user-profile writes for SURI ``execute``.

Same ACT machinery: durable V005 claim, structured audit, closed operation
keys, caller identity only. Delegates to the canonical ``PreferencesService``
and ``UserProfileService`` — self-only and self|admin enforcement stay
inside the services, exactly as the BFF routes.
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
from app.domain.exceptions import AuthorizationError
from app.application.services.preferences_service import PreferencesService
from app.application.services.user_profile_service import UserProfileService
from app.domain.entities import EffectiveUser

logger = logging.getLogger("supplies-api.suri_mcp.execute")

_PREFERENCES = PreferencesService()
_PROFILE = UserProfileService()

_PREFERENCES_KEYS = frozenset(
    {"idempotency_key", "defaultBranch", "tableDensity"}
)
_PROFILE_UPDATE_KEYS = frozenset(
    {"idempotency_key", "user_id", "defaultBranch", "tableDensity",
     "preferences"}
)

PERSONAL_WRITE_KEYS_BY_ACTION = {
    "preferences_update": _PREFERENCES_KEYS,
    "profile_update": _PROFILE_UPDATE_KEYS,
}

ENTITY_BY_ACTION = {
    "preferences_update": "session",
    "profile_update": "users",
}


def _exec_op(user: EffectiveUser, action: str, op: dict[str, Any]) -> dict:
    if action == "preferences_update":
        payload = {
            k: v for k, v in op.items() if k != "idempotency_key"
        }
        result = _PREFERENCES.patch(user, payload)
        return {"user_id": result.get("userId"),
                "defaultBranch": result.get("defaultBranch")}
    uid = str(op.get("user_id") or "").strip()
    payload = {k: v for k, v in op.items()
               if k not in {"idempotency_key", "user_id"}}
    result = _PROFILE.patch(user, uid, payload)
    return {"user_id": result.get("userId") or result.get("id")}


def execute_personal_write(
    user: EffectiveUser, *, entity: str, action: str,
    operations: list[dict[str, Any]],
) -> dict[str, Any]:
    correlation_id = str(_uuid.uuid4())
    results: list[dict[str, Any]] = []
    for index, op in enumerate(operations):
        idem_key = op.get("idempotency_key")
        entry, claim_id = _claim_or_replay(
            user, action, index, op, idem_key, correlation_id
        )
        if entry is not None:
            _audit(user, correlation_id=correlation_id, action=action,
                   entry=entry,
                   field_names=sorted(
                       k for k in op if k != "idempotency_key"))
            results.append(entry)
            continue
        try:
            payload = _exec_op(user, action, op)
        except AuthorizationError as exc:
            entry = _op_error(
                index, outcome="rejected",
                code="forbidden", message=str(exc) or "forbidden",
                idempotency_key=idem_key, http_status=403)
        except ValueError as exc:
            entry = _op_error(
                index, outcome="rejected",
                code="invalid_request", message=str(exc),
                idempotency_key=idem_key, http_status=422)
        except Exception as exc:
            name = type(exc).__name__.lower()
            if "denied" in name or "forbidden" in name:
                entry = _op_error(
                    index, outcome="rejected", code="forbidden",
                    message=str(exc), idempotency_key=idem_key,
                    http_status=403)
            else:
                entry = _op_error(
                    index, outcome="indeterminate",
                    code="upstream_error",
                    message=("Upstream did not confirm the write — "
                             "verify before retrying with the same "
                             "idempotency_key."),
                    idempotency_key=idem_key, http_status=502)
        else:
            entry = {
                "index": index, "outcome": "confirmed",
                "idempotency_key": idem_key, **payload,
            }
        _complete_claim(claim_id, entry)
        _audit(user, correlation_id=correlation_id, action=action,
               entry=entry,
               field_names=sorted(k for k in op if k != "idempotency_key"))
        results.append(entry)
    confirmed = sum(1 for r in results if r.get("outcome") == "confirmed")
    return {
        "success": all(
            r.get("outcome") in {"confirmed", "replayed"} for r in results
        ),
        "correlation_id": correlation_id,
        "entity": entity,
        "action": action,
        "operations_total": len(results),
        "operations_confirmed": confirmed,
        "results": results,
    }

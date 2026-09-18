"""Trusted supplies-api reads.

The Portal Suprimentos BFF already decided supplies.access and unit scope.
api-delpi must not copy that membership. A valid internal service token plus
the supplies-api caller is the service-to-service proof. Direct callers keep
the route's own permission and branch gate.
"""

from __future__ import annotations

import inspect
from functools import wraps

from delpi_auth.authorization import require_any_permission
from delpi_auth.service_token import request_has_valid_internal_service_token

from app.infrastructure.observability.request_context import get_caller_app, get_request

SUPPLIES_BFF_CALLER = "supplies-api"


def is_trusted_supplies_bff_call(*, supplies_department_only: bool = False) -> bool:
    request = get_request()
    if request is None:
        return False
    if (get_caller_app() or "").strip() != SUPPLIES_BFF_CALLER:
        return False
    if not request_has_valid_internal_service_token(request):
        return False
    if not supplies_department_only:
        return True
    return (request.query_params.get("department_id") or "").strip() == "supplies"


def require_any_permission_or_supplies_bff(
    permission_codes,
    *,
    supplies_department_only: bool = False,
):
    """User permission, or a trusted supplies-api service read. Not a write bypass."""

    def decorator(fn):
        guarded = require_any_permission(permission_codes)(fn)

        if inspect.iscoroutinefunction(fn):

            @wraps(fn)
            async def async_wrapper(*args, **kwargs):
                if is_trusted_supplies_bff_call(
                    supplies_department_only=supplies_department_only
                ):
                    return await fn(*args, **kwargs)
                return await guarded(*args, **kwargs)

            return async_wrapper

        @wraps(fn)
        def sync_wrapper(*args, **kwargs):
            if is_trusted_supplies_bff_call(
                supplies_department_only=supplies_department_only
            ):
                return fn(*args, **kwargs)
            return guarded(*args, **kwargs)

        return sync_wrapper

    return decorator

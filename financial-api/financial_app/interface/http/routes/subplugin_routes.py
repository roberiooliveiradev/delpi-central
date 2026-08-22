from __future__ import annotations

from fastapi import APIRouter, Request

from financial_app.composition.financial_composer import build_catalog_service
from financial_app.core.responses import fail, ok
from financial_app.core.security import FIN_EXPORT, can
from financial_app.interface.http.auth_http import resolve_user

router = APIRouter(tags=["Subplugins"])


@router.get("/subplugins")
def list_subplugins(request: Request):
    user = resolve_user(request)
    try:
        items = build_catalog_service().list_visible(user)
    except PermissionError as exc:
        return fail(str(exc), 403)
    return ok(
        {
            "items": [item.to_dict() for item in items],
            "capabilities": {"export": can(user, FIN_EXPORT)},
        }
    )

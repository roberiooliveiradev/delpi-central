from __future__ import annotations

from fastapi import APIRouter, Request

from travel_expenses_app.application.security import travel_expenses_permissions as perms
from travel_expenses_app.core.responses import ok

router = APIRouter(tags=["Travel Expenses Access"])


@router.get("/access")
def get_access(request: Request):
    return ok(perms.build_access_payload(request.state.user))

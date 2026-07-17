from __future__ import annotations

from fastapi import APIRouter, Request

from cipa_app.application.security import cipa_permissions as perms
from cipa_app.core.responses import ok

router = APIRouter(tags=["CIPA Access"])


@router.get("/access")
def get_access(request: Request):
    return ok(perms.build_access_payload(request.state.user))

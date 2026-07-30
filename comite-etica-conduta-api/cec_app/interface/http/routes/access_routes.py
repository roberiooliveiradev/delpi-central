from __future__ import annotations

from fastapi import APIRouter, Request

from cec_app.application.security import cec_permissions as perms
from cec_app.core.responses import ok

router = APIRouter(tags=["CEC Access"])


@router.get("/access")
def get_access(request: Request):
    return ok(perms.build_access_payload(request.state.user))

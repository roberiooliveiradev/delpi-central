from __future__ import annotations

from fastapi import APIRouter

from tv_app.application.services.presentation_payload_service import PresentationPayloadService
from tv_app.core.responses import fail, ok

router = APIRouter(prefix="/public", tags=["Public"])
_present = PresentationPayloadService()


@router.get("/present/{token}")
def public_present(token: str):
    payload = _present.build_by_token(token, track_view=True)
    if payload is None:
        return fail("Programação não encontrada ou desativada.", 404)
    return ok(payload)

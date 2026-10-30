"""VISTA consent — trusted human channel for governed confirms (D-5).

These BFF-style routes are the ONLY path that turns a PENDING consent
challenge into APPROVED. The human approves the sealed plan here with a
Keycloak token issued *after* the challenge was minted
(``iat >= challenge.created_at``) — a credential the agent transport
(MCP/GPT Actions) cannot fabricate because the refresh token lives in
the trusted human session.

The agent channel never writes consent: it receives ``consent_challenge``
at PREPARE, points the human here, and presents the resulting
``consent_artifact`` (challenge_id) at COMMIT.
"""

from __future__ import annotations

import uuid

from fastapi import APIRouter, Path, Request

from delpi_auth.jwt_validator import validate_token
from tv_app.application.gpt_actions.errors import GptActionsError
from tv_app.application.gpt_actions.vista_consent_service import (
    VistaConsentService,
)
from tv_app.application.services.playlist_access_service import (
    PlaylistAccessService,
)
from tv_app.core.responses import fail, ok
from tv_app.infrastructure.persistence.repositories.vista_consent_challenge_repository import (
    get_vista_consent_challenge_repository,
)
from tv_app.interface.http.auth_http import resolve_user

router = APIRouter(prefix="/vista/consent", tags=["VISTA Consent"])

_service = VistaConsentService(
    challenges=get_vista_consent_challenge_repository()
)
_access = PlaylistAccessService()


def _actor(request: Request) -> str:
    user = resolve_user(request)
    actor = _access.actor_id(user)
    if not actor:
        raise GptActionsError(
            "Usuário não identificado.",
            code="AUTHENTICATION_REQUIRED",
            status_code=401,
        )
    return actor


def _step_up_claims(request: Request) -> dict:
    """Revalidate the request Bearer and return verified claims.

    Same canonical authority as the auth middleware
    (``delpi_auth.jwt_validator.validate_token``) — no parallel
    validation mechanism.
    """
    header = request.headers.get("authorization") or ""
    scheme, _, token = header.partition(" ")
    if scheme.lower() != "bearer" or not token.strip():
        raise GptActionsError(
            "Bearer token ausente.",
            code="AUTHENTICATION_REQUIRED",
            status_code=401,
        )
    try:
        return validate_token(token.strip())
    except GptActionsError:
        raise
    except Exception as exc:  # noqa: BLE001
        raise GptActionsError(
            "Token inválido.",
            code="AUTHENTICATION_REQUIRED",
            status_code=401,
        ) from exc


def _fail(exc: Exception):
    if isinstance(exc, GptActionsError):
        return fail(
            exc.message,
            exc.status_code,
            data={"error": {"code": exc.code, "details": exc.details}},
        )
    if isinstance(exc, PermissionError):
        return fail(str(exc), 403, data={"error": {"code": "FORBIDDEN"}})
    raise exc


@router.get("/proposals/{proposal_id}")
def get_consent_view(request: Request, proposal_id: str = Path()):
    """Sealed-plan view for the human approval surface (actor-bound)."""
    try:
        result = _service.summary_for_consent(
            proposal_id=str(proposal_id), actor_sub=_actor(request)
        )
        return ok(result)
    except Exception as exc:  # noqa: BLE001
        return _fail(exc)


@router.post("/challenges/{challenge_id}/approve")
def approve_challenge(request: Request, challenge_id: uuid.UUID = Path()):
    """Record human approval — PENDING→APPROVED with step-up token proof."""
    try:
        result = _service.approve(
            challenge_id=str(challenge_id),
            actor_sub=_actor(request),
            token_claims=_step_up_claims(request),
        )
        return ok(result)
    except Exception as exc:  # noqa: BLE001
        return _fail(exc)

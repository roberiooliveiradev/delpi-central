"""CLARA — superfície confiável de consentimento (Portal step-up).

Estas rotas BFF são a ÚNICA forma de gravar ``consent_record`` no
Modo B. A aprovação exige o ``challenge_id`` emitido no PREPARE —
objeto de autorização vinculado a ator, alvo, plano selado e
expiração (V014) — mais token Keycloak emitido **depois** do desafio
(``iat >= challenge.created_at``). O refresh token que produz esse
JWT novo vive na sessão do Portal: nem a chamada MCP, nem um JWT
recente isolado, nem um desafio de outro alvo autorizam o plano.

O canal MCP nunca escreve consentimento; ele apenas lê o estado
(CONFIRMED) gravado aqui.
"""

from __future__ import annotations

import uuid

from fastapi import APIRouter, Path, Request

from controllership_finance_app.application.clara.step_up_consent import (
    ClaraStepUpConsent,
)
from controllership_finance_app.core.responses import fail, ok
from controllership_finance_app.domain.closing_checklist.errors import (
    ChecklistDomainError,
)
from controllership_finance_app.interface.http.authz import (
    actor_subject,
    authorized_user,
)
from delpi_auth.jwt_validator import validate_token

router = APIRouter(prefix="/clara", tags=["CLARA Consent"])


def _domain_fail(exc: ChecklistDomainError, operation_id: str):
    return fail(
        exc.message,
        exc.status,
        data={"error": {"code": exc.code}},
        operation_id=operation_id,
    )


def _actor(request: Request) -> str:
    return actor_subject(authorized_user(request))


def _step_up_claims(request: Request) -> dict:
    """Revalida o Bearer da requisição e devolve os claims (iat/jti).

    Mesma autoridade canônica do middleware (``validate_token``) —
    nenhum mecanismo de validação paralelo.
    """
    header = request.headers.get("authorization") or ""
    scheme, _, token = header.partition(" ")
    if scheme.lower() != "bearer" or not token.strip():
        raise ConsentAuthError("Bearer token ausente.")
    try:
        return validate_token(token.strip())
    except ChecklistDomainError:
        raise
    except Exception as exc:  # noqa: BLE001
        raise ConsentAuthError("Token inválido.") from exc


class ConsentAuthError(ChecklistDomainError):
    code = "consent_auth"
    status = 401


def _service() -> ClaraStepUpConsent:
    return ClaraStepUpConsent()


@router.get(
    "/batches/{batch_id}",
    operation_id="get_clara_batch_consent_view",
)
def get_clara_batch(
    request: Request,
    batch_id: uuid.UUID = Path(),
):
    try:
        actor = _actor(request)
        result = _service().batch_summary(
            batch_id=str(batch_id), actor_sub=actor
        )
    except ChecklistDomainError as exc:
        return _domain_fail(exc, "get_clara_batch_consent_view")
    return ok(result, operation_id="get_clara_batch_consent_view")


async def _challenge_id(request: Request) -> str | None:
    """`challenge_id` do corpo — a aprovação é do desafio emitido no
    PREPARE, nunca de um batch_id solto (R-CLARA-01)."""
    try:
        body = await request.json()
    except Exception:  # noqa: BLE001
        return None
    if not isinstance(body, dict):
        return None
    value = body.get("challenge_id")
    return str(value) if value else None


@router.post(
    "/batches/{batch_id}/consent",
    operation_id="record_clara_batch_consent",
)
async def record_clara_batch_consent(
    request: Request,
    batch_id: uuid.UUID = Path(),
):
    try:
        actor = _actor(request)
        claims = _step_up_claims(request)
        result = _service().record_batch_consent(
            batch_id=str(batch_id),
            actor_sub=actor,
            token_claims=claims,
            challenge_id=await _challenge_id(request),
        )
    except ChecklistDomainError as exc:
        return _domain_fail(exc, "record_clara_batch_consent")
    return ok(result, operation_id="record_clara_batch_consent")


@router.get(
    "/proposals/{proposal_id}",
    operation_id="get_clara_proposal_consent_view",
)
def get_clara_proposal(
    request: Request,
    proposal_id: uuid.UUID = Path(),
):
    try:
        actor = _actor(request)
        result = _service().proposal_summary(
            proposal_id=str(proposal_id), actor_sub=actor
        )
    except ChecklistDomainError as exc:
        return _domain_fail(exc, "get_clara_proposal_consent_view")
    return ok(result, operation_id="get_clara_proposal_consent_view")


@router.post(
    "/proposals/{proposal_id}/consent",
    operation_id="record_clara_proposal_consent",
)
async def record_clara_proposal_consent(
    request: Request,
    proposal_id: uuid.UUID = Path(),
):
    try:
        actor = _actor(request)
        claims = _step_up_claims(request)
        result = _service().record_proposal_consent(
            proposal_id=str(proposal_id),
            actor_sub=actor,
            token_claims=claims,
            challenge_id=await _challenge_id(request),
        )
    except ChecklistDomainError as exc:
        return _domain_fail(exc, "record_clara_proposal_consent")
    return ok(result, operation_id="record_clara_proposal_consent")

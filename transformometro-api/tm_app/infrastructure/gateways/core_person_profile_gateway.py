"""Read-only Core PersonProfile for the authenticated user (Bearer forward)."""

from __future__ import annotations

import logging
import os

import httpx

from tm_app.application.gpt_actions.errors import GptActionsError

logger = logging.getLogger(__name__)

CORE_API_URL = (
    os.getenv("DELPI_AUTH_CORE_API_URL") or os.getenv("CORE_API_URL") or "http://core-api:8000"
)
PROFILE_TIMEOUT_SECONDS = float(os.getenv("DELPI_AUTH_RBAC_TIMEOUT_SECONDS", "2.5"))


class CorePersonProfileGateway:
    """User-parity read of GET /me/person-profile — no S2S, no admin token."""

    def get_my_person_profile(self, authorization: str) -> dict:
        if not authorization or not str(authorization).strip():
            raise GptActionsError(
                "Usuário não autenticado.",
                401,
                {"error_kind": "authn"},
            )
        url = f"{CORE_API_URL.rstrip('/')}/me/person-profile"
        timeout = httpx.Timeout(PROFILE_TIMEOUT_SECONDS, connect=PROFILE_TIMEOUT_SECONDS)
        try:
            with httpx.Client(timeout=timeout) as client:
                response = client.get(url, headers={"Authorization": authorization})
        except httpx.RequestError as exc:
            logger.warning(
                "core_person_profile_unavailable core_api_url=%s err=%s",
                CORE_API_URL,
                exc,
            )
            raise GptActionsError(
                "Não foi possível consultar o perfil pessoal no momento.",
                503,
                {"error_kind": "persistence", "integration": "core-api"},
            ) from exc

        if response.status_code == 401:
            raise GptActionsError(
                "Sessão inválida ou expirada.",
                401,
                {"error_kind": "authn"},
            )
        if response.status_code != 200:
            logger.warning(
                "core_person_profile_failed status=%s core_api_url=%s",
                response.status_code,
                CORE_API_URL,
            )
            raise GptActionsError(
                "Não foi possível consultar o perfil pessoal no momento.",
                503,
                {"error_kind": "persistence", "integration": "core-api"},
            )

        payload = response.json()
        if not isinstance(payload, dict):
            raise GptActionsError(
                "Resposta inválida do serviço de perfil.",
                503,
                {"error_kind": "persistence", "integration": "core-api"},
            )
        return payload

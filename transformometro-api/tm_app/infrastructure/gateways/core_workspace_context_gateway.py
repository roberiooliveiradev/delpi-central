"""Read-only Core WorkspaceContext for the authenticated user (Bearer forward).

Calls ``GET /me/workspace-context?app_id=transformometro`` on core-api with the
user's own token — same user-parity posture as ``CorePersonProfileGateway``.
The response is a navigation hint only: entity refs, never domain facts,
never authorization.
"""

from __future__ import annotations

import logging
import os

import httpx

from tm_app.application.gpt_actions.errors import GptActionsError

logger = logging.getLogger(__name__)

CORE_API_URL = (
    os.getenv("DELPI_AUTH_CORE_API_URL")
    or os.getenv("CORE_API_URL")
    or os.getenv("CORE_API_BASE_URL")
    or "http://core-api:8000"
)
WORKSPACE_CONTEXT_TIMEOUT_SECONDS = float(
    os.getenv("DELPI_AUTH_RBAC_TIMEOUT_SECONDS", "2.5")
)

TRANSFORMOMETRO_APP_ID = "transformometro"


class CoreWorkspaceContextGateway:
    """User-parity read of GET /me/workspace-context — no S2S, no admin token."""

    def get_my_workspace_context(
        self, authorization: str, *, app_id: str = TRANSFORMOMETRO_APP_ID
    ) -> dict:
        if not authorization or not str(authorization).strip():
            raise GptActionsError(
                "Usuário não autenticado.",
                401,
                {"error_kind": "authn"},
            )
        url = f"{CORE_API_URL.rstrip('/')}/me/workspace-context"
        timeout = httpx.Timeout(
            WORKSPACE_CONTEXT_TIMEOUT_SECONDS,
            connect=WORKSPACE_CONTEXT_TIMEOUT_SECONDS,
        )
        try:
            with httpx.Client(timeout=timeout) as client:
                response = client.get(
                    url,
                    params={"app_id": app_id},
                    headers={"Authorization": authorization},
                )
        except httpx.RequestError as exc:
            logger.warning(
                "core_workspace_context_unavailable core_api_url=%s err=%s",
                CORE_API_URL,
                exc,
            )
            raise GptActionsError(
                "Não foi possível consultar o contexto de workspace no momento.",
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
                "core_workspace_context_failed status=%s core_api_url=%s",
                response.status_code,
                CORE_API_URL,
            )
            raise GptActionsError(
                "Não foi possível consultar o contexto de workspace no momento.",
                503,
                {"error_kind": "persistence", "integration": "core-api"},
            )

        payload = response.json()
        if not isinstance(payload, dict):
            raise GptActionsError(
                "Resposta inválida do serviço de contexto de workspace.",
                503,
                {"error_kind": "persistence", "integration": "core-api"},
            )
        return payload

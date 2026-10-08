"""Bearer-forwarded read of the Core solution catalog (/solutions).

Same user-parity posture as CoreWorkspaceContextGateway: the user's own
token is forwarded — never a service account, never impersonation.
KNOWLEDGE VISIBILITY != ACCESS AUTHORIZATION.
"""

from __future__ import annotations

import logging

import httpx

from tm_app.application.gpt_actions.errors import GptActionsError
from tm_app.infrastructure.gateways.core_workspace_context_gateway import (
    CORE_API_URL,
    WORKSPACE_CONTEXT_TIMEOUT_SECONDS,
)

logger = logging.getLogger(__name__)


class CoreSolutionCatalogGateway:
    def _request(self, path: str, authorization: str) -> httpx.Response:
        if not authorization or not str(authorization).strip():
            raise GptActionsError(
                "Usuário não autenticado.", 401, {"error_kind": "authn"}
            )
        url = f"{CORE_API_URL.rstrip('/')}{path}"
        timeout = httpx.Timeout(
            WORKSPACE_CONTEXT_TIMEOUT_SECONDS,
            connect=WORKSPACE_CONTEXT_TIMEOUT_SECONDS,
        )
        try:
            with httpx.Client(timeout=timeout) as client:
                return client.get(url, headers={"Authorization": authorization})
        except httpx.RequestError as exc:
            logger.warning(
                "core_solutions_unavailable core_api_url=%s err=%s",
                CORE_API_URL,
                exc,
            )
            raise GptActionsError(
                "Catálogo de soluções indisponível.",
                502,
                {"error_kind": "upstream_unavailable"},
            ) from exc

    def list_solutions(self, authorization: str) -> list[dict]:
        response = self._request("/solutions", authorization)
        if response.status_code != 200:
            raise GptActionsError(
                "Falha ao consultar catálogo de soluções.",
                502,
                {"error_kind": "upstream_error", "status": response.status_code},
            )
        return response.json().get("data") or []

    def get_solution(self, plugin_id: str, authorization: str) -> dict | None:
        response = self._request(f"/solutions/{plugin_id}", authorization)
        if response.status_code == 404:
            return None
        if response.status_code != 200:
            raise GptActionsError(
                "Falha ao consultar solução.",
                502,
                {"error_kind": "upstream_error", "status": response.status_code},
            )
        return response.json().get("data")

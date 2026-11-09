"""Bearer-forwarded directory user search — Core GET /me/directory/users.

Owner of identity search is core-api (SearchDirectoryUsersUseCase). This
gateway only forwards the authenticated user token — never a service
account, never impersonation. Same posture as CoreWorkspaceContextGateway.
"""

from __future__ import annotations

import logging
from typing import Any
from urllib.parse import urlencode

import httpx

from tm_app.application.gpt_actions.errors import GptActionsError
from tm_app.infrastructure.gateways.core_workspace_context_gateway import (
    CORE_API_URL,
    WORKSPACE_CONTEXT_TIMEOUT_SECONDS,
)

logger = logging.getLogger(__name__)

_MAX_LIMIT = 20
_MIN_QUERY_LEN = 2


class CoreDirectoryUsersGateway:
    """User-parity search of GET /me/directory/users."""

    def search_users(
        self,
        authorization: str,
        *,
        q: str,
        limit: int = 10,
        include_self: bool = True,
        app: str | None = None,
        permission: str | None = None,
    ) -> list[dict[str, Any]]:
        if not authorization or not str(authorization).strip():
            raise GptActionsError(
                "Usuário não autenticado.", 401, {"error_kind": "authn"}
            )
        query = str(q or "").strip()
        if len(query) < _MIN_QUERY_LEN:
            return []
        safe_limit = max(1, min(int(limit or 10), _MAX_LIMIT))
        params: dict[str, str] = {
            "q": query,
            "limit": str(safe_limit),
            "include_self": "true" if include_self else "false",
        }
        if app and str(app).strip():
            params["app"] = str(app).strip()
        if permission and str(permission).strip():
            params["permission"] = str(permission).strip()
        url = f"{CORE_API_URL.rstrip('/')}/me/directory/users?{urlencode(params)}"
        timeout = httpx.Timeout(
            WORKSPACE_CONTEXT_TIMEOUT_SECONDS,
            connect=WORKSPACE_CONTEXT_TIMEOUT_SECONDS,
        )
        try:
            with httpx.Client(timeout=timeout) as client:
                response = client.get(
                    url, headers={"Authorization": authorization}
                )
        except httpx.RequestError as exc:
            logger.warning(
                "core_directory_users_unavailable core_api_url=%s err=%s",
                CORE_API_URL,
                exc,
            )
            raise GptActionsError(
                "Diretório de usuários indisponível.",
                502,
                {"error_kind": "upstream_unavailable"},
            ) from exc
        if response.status_code in {401, 403}:
            raise GptActionsError(
                "Sem autorização para consultar o diretório.",
                response.status_code,
                {"error_kind": "authz"},
            )
        if response.status_code != 200:
            logger.warning(
                "core_directory_users_rejected status=%s",
                response.status_code,
            )
            raise GptActionsError(
                "Falha ao consultar o diretório de usuários.",
                502,
                {
                    "error_kind": "upstream_error",
                    "status": response.status_code,
                },
            )
        payload = response.json() if response.content else {}
        items = payload.get("items") if isinstance(payload, dict) else None
        if not isinstance(items, list):
            return []
        return [item for item in items if isinstance(item, dict)]

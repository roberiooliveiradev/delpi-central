"""Directory user search for TÉO/Portal parity — Core ownership, TM facade.

Projects a minimal safe surface for meeting-minute participant resolution:
user_id + display_name (+ masked email). Ambiguity is returned to the
caller as a multi-item list — never silently collapsed to one UUID.
"""

from __future__ import annotations

from typing import Any

from tm_app.application.gpt_actions.errors import GptActionsError
from tm_app.application.security.authorization_policy import (
    TransformometroAuthorizationPolicy,
)
from tm_app.infrastructure.gateways.core_directory_users_gateway import (
    CoreDirectoryUsersGateway,
)


class DirectoryUsersReadService:
    def __init__(
        self,
        *,
        gateway: CoreDirectoryUsersGateway | None = None,
        authz: TransformometroAuthorizationPolicy | None = None,
    ) -> None:
        self._gateway = gateway or CoreDirectoryUsersGateway()
        self._authz = authz or TransformometroAuthorizationPolicy()

    def search(
        self,
        user: Any,
        authorization: str,
        *,
        q: str,
        limit: int = 10,
        include_self: bool = True,
    ) -> dict[str, Any]:
        if user is None:
            raise GptActionsError(
                "Usuário não autenticado.", 401, {"error_kind": "authn"}
            )
        if not self._authz.has_access(user):
            raise GptActionsError(
                "Sem permissão transformometro.access.",
                403,
                {"error_kind": "authz"},
            )
        query = str(q or "").strip()
        if len(query) < 2:
            raise GptActionsError(
                "Informe ao menos 2 caracteres em q para buscar usuários.",
                400,
                {"error_kind": "validation", "error_code": "QUERY_TOO_SHORT"},
            )
        raw = self._gateway.search_users(
            authorization,
            q=query,
            limit=limit,
            include_self=include_self,
        )
        items = [self._project(item) for item in raw]
        items = [item for item in items if item.get("user_id")]
        return {
            "schema": "directory_user_search_v1",
            "q": query,
            "total": len(items),
            "items": items,
            "ambiguity": len(items) > 1,
            "guidance": (
                "When ambiguity is true, ask the user to disambiguate — "
                "never pick a UUID by name alone."
                if len(items) > 1
                else (
                    "No match — refine the query."
                    if not items
                    else "Unique match — use user_id as the canonical identity."
                )
            ),
        }

    @staticmethod
    def _project(item: dict[str, Any]) -> dict[str, Any]:
        user_id = str(item.get("id") or "").strip()
        name = str(item.get("name") or "").strip()
        email = str(item.get("email") or "").strip() or None
        return {
            "user_id": user_id or None,
            "display_name": name or None,
            "email_masked": email,
            "eligible": True,
        }

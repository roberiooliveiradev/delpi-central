"""Bearer-forwarded read of the Core solution catalog (/solutions).

User-parity posture (same pattern as TÉO's CoreSolutionCatalogGateway —
adapted, not imported): the caller's own Bearer token is forwarded —
never a service account, never impersonation, never cached or logged.
Core owns the safe projection and the ``accessible`` semantics:
KNOWLEDGE VISIBILITY != ACCESS AUTHORIZATION.

Bounded projection: only the fields P6 consumes (id, name, description,
category, accessible). Any other Core field is discarded here so the
manifest internals can never leak downstream.

Fail-closed: transport/auth/schema failures raise GptActionsError with
``error_kind`` markers the dispatcher maps to CONTRACT_GAP — never a
guess, never an embedded fallback copy.
"""

from __future__ import annotations

import logging
from typing import Any

import httpx

from tv_app.application.gpt_actions.errors import GptActionsError
from tv_app.config import settings

logger = logging.getLogger(__name__)

CORE_SOLUTION_TIMEOUT_SECONDS = 5.0

_PROJECTED_FIELDS = ("id", "name", "description", "category", "accessible")


def _project_solution(raw: Any) -> dict[str, Any]:
    """Bounded projection — drops routes/permissions/dependencies/internals."""
    if not isinstance(raw, dict):
        raise GptActionsError(
            "Contrato de soluções inválido.",
            code="INVALID_CONTRACT",
            status_code=502,
            details={"error_kind": "invalid_contract"},
        )
    sid = raw.get("id")
    name = raw.get("name")
    if not isinstance(sid, str) or not sid or not isinstance(name, str):
        raise GptActionsError(
            "Contrato de soluções inválido.",
            code="INVALID_CONTRACT",
            status_code=502,
            details={"error_kind": "invalid_contract"},
        )
    return {field: raw.get(field) for field in _PROJECTED_FIELDS}


class CoreSolutionCatalogGateway:
    def _request(self, path: str, authorization: str) -> httpx.Response:
        if not authorization or not str(authorization).strip():
            raise GptActionsError(
                "Usuário não autenticado.",
                code="UNAUTHENTICATED",
                status_code=401,
                details={"error_kind": "authn"},
            )
        url = f"{settings.CORE_API_BASE_URL.rstrip('/')}{path}"
        timeout = httpx.Timeout(
            CORE_SOLUTION_TIMEOUT_SECONDS,
            connect=CORE_SOLUTION_TIMEOUT_SECONDS,
        )
        try:
            with httpx.Client(timeout=timeout) as client:
                return client.get(
                    url, headers={"Authorization": authorization}
                )
        except httpx.RequestError:
            logger.warning(
                "core_solutions_unavailable core_api_url=%s",
                settings.CORE_API_BASE_URL,
            )
            raise GptActionsError(
                "Catálogo de soluções indisponível.",
                code="UPSTREAM_UNAVAILABLE",
                status_code=502,
                details={"error_kind": "upstream_unavailable"},
            ) from None

    def list_solutions(self, authorization: str) -> list[dict[str, Any]]:
        """All discoverable ACTIVE solutions with `accessible` flag.

        The catalog is KNOWLEDGE, not authorization: `accessible` reports
        the user's effective access as computed by Core; it never grants.
        """
        response = self._request("/solutions", authorization)
        if response.status_code != 200:
            raise GptActionsError(
                "Falha ao consultar catálogo de soluções.",
                code="UPSTREAM_ERROR",
                status_code=502,
                details={
                    "error_kind": "upstream_error",
                    "status": response.status_code,
                },
            )
        try:
            payload = response.json()
        except ValueError:
            raise GptActionsError(
                "Contrato de soluções inválido.",
                code="INVALID_CONTRACT",
                status_code=502,
                details={"error_kind": "invalid_contract"},
            ) from None
        items = payload.get("data") if isinstance(payload, dict) else None
        if not isinstance(items, list):
            raise GptActionsError(
                "Contrato de soluções inválido.",
                code="INVALID_CONTRACT",
                status_code=502,
                details={"error_kind": "invalid_contract"},
            )
        return [_project_solution(item) for item in items]

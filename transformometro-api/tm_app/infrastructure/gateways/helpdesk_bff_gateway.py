"""Bearer-forwarded read of the Helpdesk BFF (GLPI tickets).

Same user-parity posture as CoreSolutionCatalogGateway: the user's own
token is forwarded — never a service account, never impersonation.
GLPI remains the ticket authority; the BFF owns the Helpdesk contract,
OAuth sessions, validation and idempotency. TÉO receives knowledge,
never GLPI/OAuth credential material.
"""

from __future__ import annotations

import logging
import os
from typing import Any

import httpx

from tm_app.application.gpt_actions.errors import GptActionsError
from tm_app.application.helpdesk.helpdesk_read_port import HelpdeskReadPort
from tm_app.infrastructure.gateways.core_workspace_context_gateway import (
    WORKSPACE_CONTEXT_TIMEOUT_SECONDS,
)

logger = logging.getLogger(__name__)

HELPDESK_API_URL = (
    os.getenv("HELPDESK_API_URL")
    or os.getenv("HELPDESK_BFF_URL")
    or "http://helpdesk-api:8000"
)

CATALOG_PATHS: dict[str, str] = {
    "categories": "/ticket-categories",
    "urgencies": "/urgencies",
    "request_types": "/request-types",
    "users": "/users",
    "groups": "/groups",
    "followup_templates": "/followup-templates",
    "solution_types": "/solution-types",
    "solution_templates": "/solution-templates",
    "task_categories": "/task-categories",
    "task_templates": "/task-templates",
    "task_statuses": "/task-statuses",
    "validation_templates": "/validation-templates",
    "approval_steps": "/approval-steps",
}

# BFF domain error body is {"error": <code>} — mapped onto the canonical
# TÉO envelope without inventing codes or turning domain errors into 500.
_ERROR_KIND_BY_HTTP_STATUS = {
    400: "validation",
    401: "authn",
    403: "forbidden",
    404: "not_found",
    409: "conflict",
    422: "validation",
    502: "upstream_unavailable",
    503: "feature_disabled",
}


class HelpdeskBffGateway(HelpdeskReadPort):
    """Read-only Helpdesk BFF adapter — Bearer forward, bounded timeout."""

    def _get(
        self, path: str, authorization: str, params: dict[str, Any] | None = None
    ) -> Any:
        if not authorization or not str(authorization).strip():
            raise GptActionsError(
                "Usuário não autenticado.", 401, {"error_kind": "authn"}
            )
        url = f"{HELPDESK_API_URL.rstrip('/')}{path}"
        timeout = httpx.Timeout(
            WORKSPACE_CONTEXT_TIMEOUT_SECONDS,
            connect=WORKSPACE_CONTEXT_TIMEOUT_SECONDS,
        )
        try:
            with httpx.Client(timeout=timeout) as client:
                response = client.get(
                    url,
                    params=params,
                    headers={"Authorization": authorization},
                )
        except httpx.RequestError as exc:
            logger.warning(
                "helpdesk_bff_unavailable helpdesk_api_url=%s err=%s",
                HELPDESK_API_URL,
                exc,
            )
            raise GptActionsError(
                "Helpdesk indisponível.",
                502,
                {"error_kind": "upstream_unavailable"},
            ) from exc
        if response.status_code == 200:
            return response.json()
        try:
            body = response.json()
        except ValueError:
            body = {}
        code = str(body.get("error") or "")
        data: dict[str, Any] = {
            "error_kind": _ERROR_KIND_BY_HTTP_STATUS.get(
                response.status_code, "upstream_error"
            ),
            "error_code": code or None,
            "status": response.status_code,
        }
        # The BFF exposes the canonical GLPI link start location — public
        # route, no OAuth state/verifier/token material. Safe to surface.
        if code == "glpi_link_required" and body.get("authorize_url"):
            data["authorize_url"] = body["authorize_url"]
        raise GptActionsError(
            f"Helpdesk BFF error: {code or response.status_code}.",
            response.status_code,
            data,
        )

    def session(self, authorization: str) -> dict[str, Any]:
        return self._get("/auth/glpi/session", authorization)

    def capabilities(self, authorization: str) -> dict[str, Any]:
        return self._get("/session/capabilities", authorization)

    def tickets(
        self, authorization: str, filters: dict[str, Any]
    ) -> dict[str, Any]:
        params = {
            key: value
            for key, value in filters.items()
            if value is not None and str(value).strip() != ""
        }
        return self._get("/tickets", authorization, params=params)

    def ticket(self, authorization: str, ticket_id: int) -> dict[str, Any]:
        return self._get(f"/tickets/{int(ticket_id)}", authorization)

    def catalog(
        self,
        authorization: str,
        catalog_kind: str,
        *,
        q: str | None = None,
        purpose: str | None = None,
        limit: int | None = None,
    ) -> dict[str, Any]:
        path = CATALOG_PATHS.get(str(catalog_kind or "").strip())
        if path is None:
            raise GptActionsError(
                f"catalog_kind desconhecido: {catalog_kind!r}.",
                400,
                {
                    "error_kind": "validation",
                    "error_code": "INVALID_CATALOG_KIND",
                },
            )
        params: dict[str, Any] = {}
        if catalog_kind == "users":
            if q:
                params["q"] = q
            if purpose:
                params["purpose"] = purpose
            if limit is not None:
                params["limit"] = int(limit)
        return self._get(path, authorization, params=params)

"""Execute DELPI information — catalog-fixed GET with end-user Authorization."""

from __future__ import annotations

from typing import Any

from app.application.external_capabilities.dynamic_information.action_index import (
    get_action_by_id,
)
from app.application.external_capabilities.dynamic_information.candidate_token import (
    CandidateTokenError,
    parse_candidate_token,
)
from app.application.external_capabilities.dynamic_information.content_loader import (
    candidate_token_secret,
    load_dynamic_read_budgets,
)
from app.application.external_capabilities.dynamic_information.governed_http_executor import (
    GovernedExecutionError,
    execute_catalog_get,
)
from app.application.external_capabilities.dynamic_information.projection import (
    bound_response_payload,
)


def execute_delpi_information(
    *,
    candidate_token: str,
    arguments: dict[str, Any] | None = None,
    actor_id: str | None = None,
    authorization: str | None = None,
    http_client: Any,
) -> dict[str, Any]:
    if not candidate_token:
        raise CandidateTokenError("candidate_token is required")
    if not authorization:
        raise PermissionError("Unauthorized")
    if http_client is None:
        raise GovernedExecutionError("HTTP client is required", status_code=500)

    budgets = load_dynamic_read_budgets()
    secret = candidate_token_secret()
    payload = parse_candidate_token(
        candidate_token,
        secret=secret,
        expected_actor_id=actor_id,
    )
    action_id = str(payload["action_id"])
    action = get_action_by_id(action_id)
    if action is None or not action.executable:
        raise GovernedExecutionError("Action is not DAVI-eligible", status_code=403)

    # Re-validate allowlist membership at execution time (fail-closed).
    if not action.executable:
        raise GovernedExecutionError("Action disabled for DAVI", status_code=403)

    status, body = execute_catalog_get(
        action=action,
        arguments=arguments,
        authorization=authorization,
        client=http_client,
    )

    if status in (401, 403):
        raise PermissionError("Forbidden" if status == 403 else "Unauthorized")

    bounded = bound_response_payload(
        body,
        max_bytes=int(budgets.get("execute_max_response_bytes") or 65536),
        max_items=int(budgets.get("execute_max_items") or 50),
    )
    return {
        "action_id": action.action_id,
        "http_status": status,
        "entity": action.entity,
        "shape": action.shape,
        **bounded,
    }

"""Execute DELPI information — catalog plan + approved projection (no HTTP)."""

from __future__ import annotations

from collections.abc import Callable
from typing import Any

from app.application.external_capabilities.dynamic_information.action_index import (
    get_action_by_id,
)
from app.application.external_capabilities.dynamic_information.argument_validator import (
    ArgumentValidationError,
)
from app.application.external_capabilities.dynamic_information.candidate_token import (
    CandidateTokenError,
    parse_candidate_token,
)
from app.application.external_capabilities.dynamic_information.content_loader import (
    candidate_token_secret,
    load_dynamic_read_budgets,
)
from app.application.external_capabilities.dynamic_information.errors import (
    GovernedExecutionError,
)
from app.application.external_capabilities.dynamic_information.execution_plan import (
    ApprovedCapabilityPlan,
    CatalogActionPlan,
    build_execution_plan,
)
from app.application.external_capabilities.dynamic_information.projection import (
    apply_approved_field_projection,
    bound_response_payload,
    unwrap_api_payload,
)
from app.domain.ports.davi_catalog_action_executor_port import CatalogActionExecutorPort

SearchProductsRunner = Callable[..., dict[str, Any]]


def execute_delpi_information(
    *,
    candidate_token: str,
    arguments: dict[str, Any] | None = None,
    actor_id: str | None = None,
    catalog_action_executor: CatalogActionExecutorPort | None = None,
    search_products_runner: SearchProductsRunner | None = None,
) -> dict[str, Any]:
    """Governed execute. Application never sees HTTP, headers, or status codes."""
    if not candidate_token:
        raise CandidateTokenError("candidate_token is required")
    if not (actor_id or "").strip():
        raise CandidateTokenError("actor_id is required")

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
        raise GovernedExecutionError("Action is not DAVI-eligible")

    try:
        plan = build_execution_plan(action, arguments)
    except ArgumentValidationError as exc:
        raise GovernedExecutionError(str(exc)) from exc

    if isinstance(plan, ApprovedCapabilityPlan):
        if search_products_runner is None:
            raise GovernedExecutionError("Approved capability runner is not configured")
        args = plan.arguments
        body = search_products_runner(
            code=args.get("code"),
            description=args.get("description"),
            group_code=args.get("group_code"),
            page=args.get("page", 1),
            page_size=args.get("page_size", 50),
            enforce_authz=True,
            tool_name="execute_delpi_information",
        )
        body = apply_approved_field_projection(
            body,
            approved_fields=action.approved_response_fields
            or ("product_code", "description", "group_category"),
            list_key="items",
        )
    elif isinstance(plan, CatalogActionPlan):
        if catalog_action_executor is None:
            raise GovernedExecutionError("Catalog action executor is not configured")
        result = catalog_action_executor.execute(
            action_id=plan.action_id,
            validated_arguments=plan.validated_arguments,
        )
        if result.outcome == "unauthorized":
            raise PermissionError("Unauthorized")
        if result.outcome == "forbidden":
            raise PermissionError("Forbidden")
        if result.outcome != "ok":
            raise GovernedExecutionError(
                result.error_message or "Catalog action execution failed"
            )
        body = apply_approved_field_projection(
            unwrap_api_payload(result.payload),
            approved_fields=action.approved_response_fields,
            list_key="items",
            max_depth=int(budgets.get("projection_max_depth") or 8),
            max_array_items=int(budgets.get("execute_max_items") or 50),
        )
    else:
        raise GovernedExecutionError("Unsupported execution plan")

    bounded = bound_response_payload(
        body,
        max_bytes=int(budgets.get("execute_max_response_bytes") or 65536),
        max_items=int(budgets.get("execute_max_items") or 50),
    )
    return {
        "action_id": action.action_id,
        "status": "ok",
        "entity": action.entity,
        "shape": action.shape,
        "projection": "approved_fields"
        if action.approved_response_fields
        else "size_bound_only",
        **bounded,
    }

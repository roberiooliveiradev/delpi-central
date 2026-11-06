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
from app.application.external_capabilities.dynamic_information.content_loader import (
    
    load_dynamic_read_budgets
)
from app.application.external_capabilities.dynamic_information.errors import (
    ARGUMENT_VALIDATION_CODE,
    CAPABILITY_NOT_ALLOWED_CODE,
    OWNER_EXECUTION_ERROR_CODE,
    GovernedExecutionError,
)
from app.application.external_capabilities.dynamic_information.execution_plan import (
    ApprovedCapabilityPlan,
    CatalogActionPlan,
    build_execution_plan,
)
from app.application.external_capabilities.dynamic_information.projection import (
    RESPONSE_CONTRACT_BOUNDED_DYNAMIC_RESULTSET,
    apply_dynamic_resultset_projection,
    apply_approved_field_projection,
    bound_response_payload,
    unwrap_api_payload,
)
from app.domain.ports.davi_catalog_action_executor_port import CatalogActionExecutorPort

SearchProductsRunner = Callable[..., dict[str, Any]]


def execute_catalog_read(
    *,
    action,
    plan: CatalogActionPlan,
    catalog_action_executor: CatalogActionExecutorPort | None,
    budgets: dict[str, Any] | None = None,
) -> dict[str, Any]:
    """Shared governed catalog READ: bound plan → executor → projection → bound.

    Single owner of the catalog_action semantics for every DAVI surface that
    executes an eligible TechnicalAction (discover→execute broker and dedicated
    semantic tools alike). Caller supplies the TechnicalAction, the
    validated CatalogActionPlan and the request-bound executor port; actor
    binding/AuthZ stay in the bound executor and backend.
    """
    budgets = budgets or load_dynamic_read_budgets()
    if catalog_action_executor is None:
        raise GovernedExecutionError(
            "Catalog action executor is not configured",
            code=OWNER_EXECUTION_ERROR_CODE,
        )
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
            result.error_message or "Catalog action execution failed",
            code=OWNER_EXECUTION_ERROR_CODE,
        )
    if (
        action.response_contract
        == RESPONSE_CONTRACT_BOUNDED_DYNAMIC_RESULTSET
    ):
        body = apply_dynamic_resultset_projection(
            unwrap_api_payload(result.payload),
            max_resultsets=int(budgets.get("execute_max_resultsets") or 8),
            max_columns=int(budgets.get("execute_max_result_columns") or 64),
            max_array_items=int(budgets.get("execute_max_items") or 50),
        )
    else:
        body = apply_approved_field_projection(
            unwrap_api_payload(result.payload),
            approved_fields=action.approved_response_fields,
            list_key="items",
            max_depth=int(budgets.get("projection_max_depth") or 8),
            max_array_items=int(budgets.get("execute_max_items") or 50),
            response_bindings=action.response_bindings,
        )
    return bound_response_payload(
        body,
        max_bytes=int(budgets.get("execute_max_response_bytes") or 65536),
        max_items=int(budgets.get("execute_max_items") or 50),
    )


def execute_action_plan(
    *,
    action,
    plan,
    catalog_action_executor: CatalogActionExecutorPort | None,
    search_products_runner: SearchProductsRunner | None,
    budgets: dict[str, Any] | None = None,
    tool_name: str = "read",
) -> dict[str, Any]:
    """Dispatch a validated execution plan to its governed runner.

    Single owner of plan dispatch for every DAVI surface: approved external
    capabilities (search_products runner) and catalog actions share the same
    projection + bounds pipeline. Caller supplies the TechnicalAction and the
    already-validated plan; actor binding/AuthZ stay in the runner/executor.
    """
    budgets = budgets or load_dynamic_read_budgets()
    if isinstance(plan, ApprovedCapabilityPlan):
        if search_products_runner is None:
            raise GovernedExecutionError(
                "Approved capability runner is not configured",
                code=OWNER_EXECUTION_ERROR_CODE,
            )
        args = plan.arguments
        body = search_products_runner(
            code=args.get("code"),
            description=args.get("description"),
            group_code=args.get("group_code"),
            page=args.get("page", 1),
            page_size=args.get("page_size", 50),
            enforce_authz=True,
            tool_name=tool_name,
        )
        body = apply_approved_field_projection(
            body,
            approved_fields=action.approved_response_fields
            or ("product_code", "description", "group_category"),
            list_key="items",
        )
        return bound_response_payload(
            body,
            max_bytes=int(budgets.get("execute_max_response_bytes") or 65536),
            max_items=int(budgets.get("execute_max_items") or 50),
        )
    if isinstance(plan, CatalogActionPlan):
        return execute_catalog_read(
            action=action,
            plan=plan,
            catalog_action_executor=catalog_action_executor,
            budgets=budgets,
        )
    raise GovernedExecutionError(
        "Unsupported execution plan",
        code=OWNER_EXECUTION_ERROR_CODE,
    )


def davi_read(
    *,
    capability: str,
    arguments: dict[str, Any] | None = None,
    catalog_action_executor: CatalogActionExecutorPort | None = None,
    search_products_runner: SearchProductsRunner | None = None,
) -> dict[str, Any]:
    """Semantic read — resolve one governed capability id and execute it.

    ``capability`` is the technical action id published by the governed
    catalog (``get_context`` action=catalog/schema). It is not a free
    operationId: only ids resolving to a currently DAVI-eligible
    TechnicalAction execute; everything else fails closed. No URL, path,
    method or SQL is accepted. Backend AuthZ stays authoritative through
    the request-bound executor/runner — same boundary as the broker.
    """
    requested = (capability or "").strip()
    if not requested:
        raise GovernedExecutionError(
            "capability is required",
            code=ARGUMENT_VALIDATION_CODE,
        )
    action = get_action_by_id(requested)
    if action is None or not action.executable:
        raise GovernedExecutionError(
            "capability is not available on the governed DAVI surface",
            code=CAPABILITY_NOT_ALLOWED_CODE,
        )
    try:
        plan = build_execution_plan(action, arguments)
    except ArgumentValidationError as exc:
        raise GovernedExecutionError(
            str(exc), code=ARGUMENT_VALIDATION_CODE
        ) from exc
    bounded = execute_action_plan(
        action=action,
        plan=plan,
        catalog_action_executor=catalog_action_executor,
        search_products_runner=search_products_runner,
        tool_name="read",
    )
    return {
        "capability": requested,
        "status": "ok",
        "action_id": action.action_id,
        "entity": action.entity,
        "shape": action.shape,
        "projection": "approved_fields"
        if action.approved_response_fields
        else "size_bound_only",
        **bounded,
    }


ANALYZE_ELIGIBLE_SHAPES = frozenset(
    {"playbook_report", "composite_analysis"}
)


def davi_analyze(
    *,
    capability: str,
    arguments: dict[str, Any] | None = None,
    catalog_action_executor: CatalogActionExecutorPort | None = None,
    search_products_runner: SearchProductsRunner | None = None,
) -> dict[str, Any]:
    """Governed analysis — analytic-shape capabilities only.

    Same resolution boundary as ``read``: capability id must map to an
    executable TechnicalAction whose shape is an authoritative
    backend-computed report/aggregate (never recomputed over paged rows).
    Output separates facts, completeness and provenance; the data itself
    is the owner-approved projection — nothing is invented or extrapolated.
    """
    requested = (capability or "").strip()
    if not requested:
        raise GovernedExecutionError(
            "capability is required",
            code=ARGUMENT_VALIDATION_CODE,
        )
    action = get_action_by_id(requested)
    if (
        action is None
        or not action.executable
        or (action.shape or "") not in ANALYZE_ELIGIBLE_SHAPES
    ):
        raise GovernedExecutionError(
            "capability is not an eligible governed analysis",
            code=CAPABILITY_NOT_ALLOWED_CODE,
        )
    try:
        plan = build_execution_plan(action, arguments)
    except ArgumentValidationError as exc:
        raise GovernedExecutionError(
            str(exc), code=ARGUMENT_VALIDATION_CODE
        ) from exc
    bounded = execute_action_plan(
        action=action,
        plan=plan,
        catalog_action_executor=catalog_action_executor,
        search_products_runner=search_products_runner,
        tool_name="analyze",
    )
    limitations: list[str] = []
    if not bounded.get("is_complete", True):
        limitations.append(
            "partial coverage — the authorized window does not cover the full population"
        )
    if bounded.get("truncated"):
        limitations.append(
            "result bounded by governed limits — values reflect the returned window only"
        )
    return {
        "action": "analyze",
        "status": "ok",
        "capability": requested,
        "facts": {
            "action_id": action.action_id,
            "entity": action.entity,
            "shape": action.shape,
            "projection": "approved_fields"
            if action.approved_response_fields
            else "size_bound_only",
            "data": bounded.get("data"),
        },
        "completeness": {
            "is_complete": bounded.get("is_complete"),
            "truncated": bounded.get("truncated"),
            "response_bytes": bounded.get("response_bytes"),
        },
        "provenance": {
            "source": "api-delpi",
            "calculation_authority": "backend",
            "knowledge_kind": "ANALYTIC_READ",
            "note": (
                "facts are the owner-approved projection of an authorized "
                "backend report; no recomputation, no extrapolation, "
                "no inferred totals"
            ),
        },
        "limitations": limitations,
    }

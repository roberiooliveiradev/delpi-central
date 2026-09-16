"""Application-side execution planning (transport-neutral)."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any, Literal

from app.application.external_capabilities.dynamic_information.argument_validator import (
    ArgumentValidationError,
    validate_arguments,
)
from app.application.external_capabilities.dynamic_information.catalog_builder import (
    TechnicalAction,
)

EXECUTION_MODE_APPROVED_EXTERNAL = "approved_external_capability"
EXECUTION_MODE_CATALOG_ACTION = "catalog_action"


@dataclass(frozen=True)
class ApprovedCapabilityPlan:
    """Execute via approved Application external capability (not catalog transport)."""

    kind: Literal["approved_external_capability"]
    action_id: str
    capability: Literal["search_products"]
    arguments: dict[str, Any]


@dataclass(frozen=True)
class CatalogActionPlan:
    """Execute via bound CatalogActionExecutorPort (action_id + validated args only)."""

    kind: Literal["catalog_action"]
    action_id: str
    validated_arguments: dict[str, Any]


ExecutionPlan = ApprovedCapabilityPlan | CatalogActionPlan


def build_execution_plan(
    action: TechnicalAction,
    arguments: dict[str, Any] | None,
) -> ExecutionPlan:
    validated = validate_arguments(action, arguments)
    mode = (action.execution_mode or "").strip() or EXECUTION_MODE_CATALOG_ACTION

    if (
        action.operation_id == "search_products"
        or mode == EXECUTION_MODE_APPROVED_EXTERNAL
    ):
        if action.operation_id != "search_products":
            raise ArgumentValidationError(
                "approved_external_capability is only wired for search_products in V1"
            )
        return ApprovedCapabilityPlan(
            kind="approved_external_capability",
            action_id=action.action_id,
            capability="search_products",
            arguments=validated,
        )

    return CatalogActionPlan(
        kind="catalog_action",
        action_id=action.action_id,
        validated_arguments=validated,
    )

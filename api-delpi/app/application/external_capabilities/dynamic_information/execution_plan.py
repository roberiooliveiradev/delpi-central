"""Application-side execution planning (no HTTP transport)."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any, Literal

from app.application.external_capabilities.dynamic_information.argument_validator import (
    ArgumentValidationError,
    split_path_and_query,
    validate_arguments,
)
from app.application.external_capabilities.dynamic_information.catalog_builder import (
    TechnicalAction,
)
from app.application.external_capabilities.dynamic_information.errors import (
    GovernedExecutionError,
)
from app.domain.ports.davi_catalog_fixed_get_port import CatalogFixedGetRequest

EXECUTION_MODE_APPROVED_EXTERNAL = "approved_external_capability"
EXECUTION_MODE_CATALOG_GET = "catalog_get"


@dataclass(frozen=True)
class ApprovedCapabilityPlan:
    """Execute via approved Application external capability (not raw HTTP)."""

    kind: Literal["approved_external_capability"]
    action_id: str
    capability: Literal["search_products"]
    arguments: dict[str, Any]


@dataclass(frozen=True)
class CatalogGetPlan:
    """Execute via catalog-fixed GET port (future eligible actions)."""

    kind: Literal["catalog_get"]
    action_id: str
    request: CatalogFixedGetRequest


ExecutionPlan = ApprovedCapabilityPlan | CatalogGetPlan


def build_execution_plan(
    action: TechnicalAction,
    arguments: dict[str, Any] | None,
) -> ExecutionPlan:
    if action.method != "GET":
        raise GovernedExecutionError("Only GET actions are executable in V1")

    validated = validate_arguments(action, arguments)
    mode = (action.execution_mode or "").strip() or EXECUTION_MODE_CATALOG_GET

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

    path, query = split_path_and_query(action, validated)
    return CatalogGetPlan(
        kind="catalog_get",
        action_id=action.action_id,
        request=CatalogFixedGetRequest(
            action_id=action.action_id,
            method="GET",
            path=path,
            query=query,
        ),
    )

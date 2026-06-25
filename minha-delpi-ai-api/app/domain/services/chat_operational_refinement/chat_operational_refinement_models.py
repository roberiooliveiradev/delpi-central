"""Modelos — refinamento operacional."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any


@dataclass(frozen=True)
class RecentPaginatedAction:
    action_id: str
    path: str
    parameters: dict[str, Any]
    page: int | None = None
    page_size: int | None = None
    product_code: str | None = None
    route_segment: str | None = None


@dataclass(frozen=True)
class OperationalRefinement:
    kind: str
    product_code: str | None = None
    branch: str | None = None
    warehouse: str | None = None
    reason: str = ""
    route_segment: str | None = None
    metric_domain_prefix: str | None = None
    metric_path_token: str | None = None
    metric_kind: str | None = None
    action_id: str | None = None
    previous_parameters: dict[str, Any] | None = None
    previous_path: str | None = None
    page: int | None = None
    page_size: int | None = None
    max_depth: int | None = None
    group_by: str | None = None
    operational_route_id: str | None = None
    group_by_label: str | None = None

    @property
    def clears_branch_filter(self) -> bool:
        return self.kind in {"stock_reset", "metric_reset"}

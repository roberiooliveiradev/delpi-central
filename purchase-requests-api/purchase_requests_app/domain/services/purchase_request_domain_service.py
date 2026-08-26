from __future__ import annotations

from dataclasses import dataclass


def map_approval_status(raw: str | None) -> str:
    value = (raw or "").strip().upper()
    if value == "L":
        return "approved"
    if value == "R":
        return "rejected"
    if value == "B":
        return "blocked"
    return "unknown"


def request_open_quantity(requested: float, ordered: float) -> float:
    return max(float(requested or 0) - float(ordered or 0), 0.0)


def purchase_order_open_quantity(ordered: float, received: float) -> float:
    return max(float(ordered or 0) - float(received or 0), 0.0)


def derive_order_status(*, ordered_quantity: float, requested_quantity: float, has_orders: bool) -> str:
    if ordered_quantity <= 0 and not has_orders:
        return "not_ordered"
    if 0 < ordered_quantity < requested_quantity:
        return "partially_ordered"
    return "fully_ordered"


def derive_receipt_status(
    *,
    has_orders: bool,
    received_quantity: float,
    ordered_quantity: float,
) -> str:
    if not has_orders:
        return "not_ordered"
    if received_quantity <= 0:
        return "awaiting_receipt"
    if 0 < received_quantity < ordered_quantity:
        return "partially_received"
    return "received"


def derive_overall_stage(
    *,
    residual: bool,
    requested_quantity: float,
    ordered_quantity: float,
    has_orders: bool,
    max_received_quantity: float,
    max_order_quantity: float,
) -> str:
    if residual:
        return "residual_closed"
    if ordered_quantity >= requested_quantity and max_order_quantity > 0 and max_received_quantity >= max_order_quantity:
        return "completed"
    if max_received_quantity > 0 and max_order_quantity > 0 and max_received_quantity < max_order_quantity:
        return "partially_received"
    if ordered_quantity >= requested_quantity and max_received_quantity <= 0 and has_orders:
        return "awaiting_receipt"
    if 0 < ordered_quantity < requested_quantity:
        return "partially_ordered"
    if ordered_quantity <= 0 and not has_orders:
        return "awaiting_order"
    return "awaiting_receipt"


def derive_delivery_status(
    *,
    expected_delivery_date: str | None,
    open_quantity: float,
    received_quantity: float,
    today_iso: str,
) -> str:
    if received_quantity > 0 and open_quantity <= 0:
        return "received"
    if not expected_delivery_date or open_quantity <= 0:
        return "not_applicable"
    if expected_delivery_date < today_iso and open_quantity > 0:
        return "overdue"
    return "on_time"


@dataclass(frozen=True)
class CostCenterScope:
    branch: str
    cost_center_code: str


@dataclass(frozen=True)
class ScopeResolution:
    view_all: bool
    allowed_cost_centers: frozenset[CostCenterScope]

    def allows(self, branch: str, cost_center_code: str | None) -> bool:
        if self.view_all:
            return bool((cost_center_code or "").strip())
        code = (cost_center_code or "").strip()
        if not code:
            return False
        return CostCenterScope(branch=branch, cost_center_code=code) in self.allowed_cost_centers

    def cost_center_codes_for_branch(self, branch: str) -> list[str]:
        if self.view_all:
            return []
        return sorted(
            {
                item.cost_center_code
                for item in self.allowed_cost_centers
                if item.branch == branch
            }
        )

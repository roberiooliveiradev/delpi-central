from __future__ import annotations

from app.application.dto.supplies.get_stock_value_request import GetStockValueRequest

STOCK_METHOD_AUTO = "auto"
STOCK_METHOD_HYBRID = "hybrid"
STOCK_METHOD_ESTIMATED = "estimated"
STOCK_METHOD_OFFICIAL = "official_closure"

STOCK_METHODS = frozenset(
    {
        STOCK_METHOD_AUTO,
        STOCK_METHOD_HYBRID,
        STOCK_METHOD_ESTIMATED,
        STOCK_METHOD_OFFICIAL,
    }
)

STOCK_METHOD_RESOLVED_ESTIMATED = "estimated"
STOCK_METHOD_RESOLVED_OFFICIAL = "official_closure"
STOCK_METHOD_RESOLVED_REGISTER_SNAPSHOT = "register_snapshot"
STOCK_METHOD_RESOLVED_MIXED = "mixed"

DEFAULT_STOCK_BRANCHES = ("01", "02")

_HYBRID_LIKE = frozenset({STOCK_METHOD_AUTO, STOCK_METHOD_HYBRID})


def normalize_stock_method(value: str | None) -> str:
    normalized = (value or STOCK_METHOD_AUTO).strip().lower()
    if normalized not in STOCK_METHODS:
        raise ValueError(
            "stock_method inválido. Use auto, hybrid, estimated ou official_closure."
        )
    return normalized


def target_branches(request: GetStockValueRequest) -> tuple[str, ...]:
    branch = (request.branch or "").strip()
    if branch:
        return (branch,)
    return DEFAULT_STOCK_BRANCHES


def _resolve_branch_sets(
    method: str,
    branches: tuple[str, ...],
    breakdown_by_branch: dict[str, dict],
) -> tuple[tuple[str, ...], tuple[str, ...], tuple[str, ...]]:
    official_branches: list[str] = []
    register_snapshot_branches: list[str] = []
    estimated_branches: list[str] = []

    for branch in branches:
        row = breakdown_by_branch.get(branch) or {}
        on_period_end = bool(row.get("official_closure_on_period_end"))

        if method == STOCK_METHOD_ESTIMATED:
            estimated_branches.append(branch)
            continue

        if method == STOCK_METHOD_OFFICIAL:
            if not on_period_end:
                raise ValueError(
                    f"Filial {branch}: não há fechamento SB9010 na data final do período."
                )
            official_branches.append(branch)
            continue

        if on_period_end:
            official_branches.append(branch)
        elif method in _HYBRID_LIKE:
            register_snapshot_branches.append(branch)
        else:
            estimated_branches.append(branch)

    return (
        tuple(official_branches),
        tuple(register_snapshot_branches),
        tuple(estimated_branches),
    )


def _resolve_label(
    *,
    official_branches: tuple[str, ...],
    register_snapshot_branches: tuple[str, ...],
    estimated_branches: tuple[str, ...],
) -> str:
    labels = {
        STOCK_METHOD_RESOLVED_OFFICIAL: official_branches,
        STOCK_METHOD_RESOLVED_REGISTER_SNAPSHOT: register_snapshot_branches,
        STOCK_METHOD_RESOLVED_ESTIMATED: estimated_branches,
    }
    active = [name for name, items in labels.items() if items]
    if len(active) > 1:
        return STOCK_METHOD_RESOLVED_MIXED
    if not active:
        return STOCK_METHOD_RESOLVED_ESTIMATED
    return active[0]


def resolve_stock_method_plan(
    request: GetStockValueRequest,
    breakdown_rows: list[dict],
    *,
    period_end: str,
) -> dict:
    method = normalize_stock_method(request.stock_method)
    breakdown_by_branch = {
        str(row.get("branch") or "").strip(): row for row in breakdown_rows
    }
    branches = target_branches(request)

    official_branches, register_snapshot_branches, estimated_branches = _resolve_branch_sets(
        method,
        branches,
        breakdown_by_branch,
    )

    if method == STOCK_METHOD_OFFICIAL and not official_branches:
        raise ValueError(
            f"Não há fechamento SB9010 na data final do período ({period_end})."
        )

    resolved = _resolve_label(
        official_branches=official_branches,
        register_snapshot_branches=register_snapshot_branches,
        estimated_branches=estimated_branches,
    )

    return {
        "requested": method,
        "resolved": resolved,
        "official_branches": official_branches,
        "register_snapshot_branches": register_snapshot_branches,
        "estimated_branches": estimated_branches,
        "period_end": period_end,
    }


def branch_uses_register_snapshot(plan: dict, branch: str) -> bool:
    return branch in (plan.get("register_snapshot_branches") or ())


def branch_uses_official_closure(plan: dict, branch: str) -> bool:
    return branch in (plan.get("official_branches") or ())

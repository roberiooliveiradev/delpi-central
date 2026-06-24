from __future__ import annotations

from app.application.dto.supplies.get_stock_value_request import GetStockValueRequest

STOCK_METHOD_AUTO = "auto"
STOCK_METHOD_ESTIMATED = "estimated"
STOCK_METHOD_OFFICIAL = "official_closure"

STOCK_METHODS = frozenset(
    {
        STOCK_METHOD_AUTO,
        STOCK_METHOD_ESTIMATED,
        STOCK_METHOD_OFFICIAL,
    }
)

STOCK_METHOD_RESOLVED_ESTIMATED = "estimated"
STOCK_METHOD_RESOLVED_OFFICIAL = "official_closure"
STOCK_METHOD_RESOLVED_MIXED = "mixed"

DEFAULT_STOCK_BRANCHES = ("01", "02")


def normalize_stock_method(value: str | None) -> str:
    normalized = (value or STOCK_METHOD_AUTO).strip().lower()
    if normalized not in STOCK_METHODS:
        raise ValueError(
            "stock_method inválido. Use auto, estimated ou official_closure."
        )
    return normalized


def target_branches(request: GetStockValueRequest) -> tuple[str, ...]:
    branch = (request.branch or "").strip()
    if branch:
        return (branch,)
    return DEFAULT_STOCK_BRANCHES


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

    official_branches: list[str] = []
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
                    f"Filial {branch}: não há fechamento SB9010 na data final do período "
                    f"({period_end})."
                )
            official_branches.append(branch)
            continue
        if on_period_end:
            official_branches.append(branch)
        else:
            estimated_branches.append(branch)

    if method == STOCK_METHOD_OFFICIAL and not official_branches:
        raise ValueError(
            f"Não há fechamento SB9010 na data final do período ({period_end})."
        )

    if official_branches and estimated_branches:
        resolved = STOCK_METHOD_RESOLVED_MIXED
    elif official_branches:
        resolved = STOCK_METHOD_RESOLVED_OFFICIAL
    else:
        resolved = STOCK_METHOD_RESOLVED_ESTIMATED

    return {
        "requested": method,
        "resolved": resolved,
        "official_branches": tuple(official_branches),
        "estimated_branches": tuple(estimated_branches),
        "period_end": period_end,
    }

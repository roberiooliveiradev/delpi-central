"""SQL — SC1 approval-state polling feed (per-item rows) for SC notifications.

Read-only snapshot of the approval decision fields on ``SC1010``: the poller
in ``purchase-requests-api`` diffs these rows against its persisted snapshot
instead of relying on ``R_E_C_N_O_`` (C1_APROV mutates in place).
"""

from __future__ import annotations

from app.domain.totvs.protheus_branches import PROTHEUS_BRANCH_CODES
from app.infrastructure.persistence.totvs.supplies_repositories.purchase_request_lines_sql import (
    default_date_range,
    normalize_purchase_request_branches,
)

DEFAULT_LIMIT = 500
MAX_LIMIT = 5000


def clamp_approval_states_limit(limit: int | None) -> int:
    try:
        parsed = int(limit if limit is not None else DEFAULT_LIMIT)
    except (TypeError, ValueError):
        parsed = DEFAULT_LIMIT
    return min(MAX_LIMIT, max(1, parsed))


def build_purchase_request_approval_states_filters(
    *,
    branches: list[str] | None = None,
    date_from: str | None = None,
    date_to: str | None = None,
) -> tuple[str, list]:
    codes = (
        normalize_purchase_request_branches(branches=branches)
        if branches
        else list(PROTHEUS_BRANCH_CODES)
    )
    start_iso, end_iso = default_date_range(date_from=date_from, date_to=date_to)
    placeholders = ", ".join("?" * len(codes))
    filters = [
        "SC1.D_E_L_E_T_ = ''",
        f"RTRIM(SC1.C1_FILIAL) IN ({placeholders})",
        "RTRIM(SC1.C1_EMISSAO) >= ?",
        "RTRIM(SC1.C1_EMISSAO) <= ?",
    ]
    params: list = [
        *codes,
        start_iso.replace("-", ""),
        end_iso.replace("-", ""),
    ]
    return " AND ".join(filters), params


def build_purchase_request_approval_states_sql(
    *,
    where_clause: str,
    limit: int,
) -> str:
    # One extra row lets the caller detect truncation exactly. Newest SCs
    # first so a truncated page drops the oldest rows, never the ones where
    # approval transitions actually happen.
    fetch = clamp_approval_states_limit(limit) + 1
    return f"""
    SELECT TOP {fetch}
        RTRIM(SC1.C1_FILIAL) AS branch,
        RTRIM(SC1.C1_NUM) AS request_number,
        RTRIM(SC1.C1_ITEM) AS request_item,
        RTRIM(ISNULL(SC1.C1_USER, '')) AS requester_protheus_user_id,
        RTRIM(ISNULL(SC1.C1_APROV, '')) AS approval_raw,
        RTRIM(ISNULL(SC1.C1_NOMAPRO, '')) AS approver_name,
        RTRIM(SC1.C1_EMISSAO) AS request_issue_date
    FROM SC1010 SC1 WITH (NOLOCK)
    WHERE {where_clause}
    ORDER BY RTRIM(SC1.C1_NUM) DESC, RTRIM(SC1.C1_ITEM) DESC
    """

"""Repository — SC1 approval-state polling feed (read-only)."""

from __future__ import annotations

from typing import Any

from app.application.services.product.protheus_field_normalizer import protheus_date_to_iso
from app.domain.totvs.protheus_purchase_request import (
    map_purchase_request_approval_status,
)
from app.infrastructure.persistence.totvs.base_repository import BaseRepository
from app.infrastructure.persistence.totvs.supplies_repositories.purchase_request_approval_states_sql import (
    build_purchase_request_approval_states_filters,
    build_purchase_request_approval_states_sql,
    clamp_approval_states_limit,
)


def _normalize_approval_state_row(row: dict[str, Any]) -> dict[str, Any]:
    approval_raw = (row.get("approval_raw") or "").strip()
    return {
        "branch": (row.get("branch") or "").strip(),
        "request_number": (row.get("request_number") or "").strip(),
        "request_item": (row.get("request_item") or "").strip(),
        "requester_protheus_user_id": (
            (row.get("requester_protheus_user_id") or "").strip() or None
        ),
        "approval_raw": approval_raw,
        "approval_status": map_purchase_request_approval_status(approval_raw),
        "approver_name": (row.get("approver_name") or "").strip() or None,
        "request_issue_date": protheus_date_to_iso(row.get("request_issue_date")),
    }


class PurchaseRequestApprovalStatesRepository(BaseRepository):
    def list_approval_states(
        self,
        *,
        branches: list[str] | None = None,
        date_from: str | None = None,
        date_to: str | None = None,
        limit: int | None = None,
    ) -> dict[str, Any]:
        safe_limit = clamp_approval_states_limit(limit)
        where_clause, params = build_purchase_request_approval_states_filters(
            branches=branches,
            date_from=date_from,
            date_to=date_to,
        )
        sql = build_purchase_request_approval_states_sql(
            where_clause=where_clause,
            limit=safe_limit,
        )
        with self as repo:
            rows = repo.execute_query(sql, tuple(params))
        truncated = len(rows) > safe_limit
        items = [_normalize_approval_state_row(row) for row in rows[:safe_limit]]
        return {
            "items": items,
            "limit": safe_limit,
            "truncated": truncated,
        }

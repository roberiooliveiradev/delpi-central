"""TOTVS SQL Server read model for verified SCR010 approval lead time (HD #1004)."""

from __future__ import annotations

from math import ceil
from typing import Any

from app.infrastructure.persistence.totvs.base_repository import BaseRepository
from app.infrastructure.persistence.totvs.supplies_repositories.purchase_request_approval_lead_time_sql import (
    DEFAULT_PAGE_SIZE,
    MAX_PAGE_SIZE,
    build_lead_time_events_sql,
    build_lead_time_filter,
    build_lead_time_page_sql,
    build_lead_time_summary_sql,
    normalize_lead_time_filters,
)


class PurchaseRequestApprovalLeadTimeRepository(BaseRepository):
    def get_lead_time(
        self,
        *,
        branches: list[str] | None,
        date_from: str | None = None,
        date_to: str | None = None,
        request_number: str | None = None,
        page: int = 1,
        page_size: int = DEFAULT_PAGE_SIZE,
    ) -> dict[str, Any]:
        if not 1 <= page <= 100000:
            raise ValueError("Página inválida.")
        if not 1 <= page_size <= MAX_PAGE_SIZE:
            raise ValueError("Tamanho de página inválido.")
        codes, start, end, number = normalize_lead_time_filters(
            branches=branches,
            date_from=date_from,
            date_to=date_to,
            request_number=request_number,
        )
        where, params = build_lead_time_filter(
            branches=codes,
            date_from=start,
            date_to=end,
            request_number=number,
        )
        offset = (page - 1) * page_size
        with self as repo:
            summary_row = repo.execute_one(
                build_lead_time_summary_sql(where), tuple(params)
            ) or {}
            rows = repo.execute_query(
                build_lead_time_page_sql(where),
                tuple(params) + (offset, page_size),
            )
            keys = [
                (str(row["branch"]).strip(), str(row["request_number"]).strip())
                for row in rows
            ]
            if keys:
                events_sql, events_params = build_lead_time_events_sql(keys)
                events = repo.execute_query(events_sql, tuple(events_params))
            else:
                events = []

        events_by_sc: dict[tuple[str, str], list[dict[str, str]]] = {}
        seen_events: set[tuple[str, str, str, str, str, str]] = set()
        for event in events:
            key = (
                str(event.get("branch") or "").strip(),
                str(event.get("request_number") or "").strip(),
            )
            payload = {
                "level": str(event.get("level") or "").strip(),
                "approved_at": str(event.get("approved_at") or "").strip(),
                "action_user_code": str(event.get("action_user_code") or "").strip(),
                "approver_code": str(event.get("approver_code") or "").strip(),
            }
            identity = (*key, *payload.values())
            if identity in seen_events:
                continue
            seen_events.add(identity)
            events_by_sc.setdefault(key, []).append(payload)

        items = []
        for row in rows:
            branch = str(row.get("branch") or "").strip()
            number_value = str(row.get("request_number") or "").strip()
            items.append({
                "branch": branch,
                "request_number": number_value,
                "issue_date": row.get("issue_date"),
                "requester_name": row.get("requester_name"),
                "requester_user_id": row.get("requester_user_id"),
                "item_count": int(row.get("item_count") or 0),
                "final_approval_date": row.get("final_approval_date"),
                "approval_levels": int(row.get("approval_levels") or 0),
                "lead_days": int(row.get("lead_days") or 0),
                "events": events_by_sc.get((branch, number_value), []),
            })

        total = int(summary_row.get("total_requests") or 0)
        return {
            "source": "SCR010",
            "scope": "confirmed_history_only",
            "unit": "calendar_days",
            "filters": {
                "branches": codes,
                "date_from": start,
                "date_to": end,
                "request_number": number,
            },
            "summary": {
                "total_requests": total,
                "avg_lead_days": (
                    float(summary_row["avg_lead_days"])
                    if summary_row.get("avg_lead_days") is not None else None
                ),
                "same_day": int(summary_row.get("same_day") or 0),
                "one_to_two_days": int(summary_row.get("one_to_two_days") or 0),
                "three_to_five_days": int(summary_row.get("three_to_five_days") or 0),
                "six_to_ten_days": int(summary_row.get("six_to_ten_days") or 0),
                "over_10_days": int(summary_row.get("over_10_days") or 0),
                "multi_level": int(summary_row.get("multi_level") or 0),
            },
            "items": items,
            "total": total,
            "page": page,
            "page_size": page_size,
            "total_pages": ceil(total / page_size),
        }

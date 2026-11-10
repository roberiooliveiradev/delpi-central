"""Visão geral do Portal de TI — indicadores calculados sobre dados persistidos."""

from __future__ import annotations

from collections.abc import Callable
from datetime import date, datetime, timezone

from it_portal_app.application.ports import ItPortalRepository
from it_portal_app.domain.action_plans import is_overdue

RECENT_SERVERS_LIMIT = 5
ATTENTION_ACTIONS_LIMIT = 8


class DashboardService:
    def __init__(self, repository: ItPortalRepository, today: Callable[[], date]):
        self._repo = repository
        self._today = today

    def overview(self, *, include_action_plans: bool) -> dict:
        today = self._today()
        counts = self._repo.dashboard_counts(today)
        payload: dict = {
            "reference_date": today,
            "generated_at": datetime.now(timezone.utc),
            "servers": {
                "total": counts["servers_total"],
                "high_or_critical": counts["servers_high_or_critical"],
            },
            "recent_servers": self._repo.recent_servers(RECENT_SERVERS_LIMIT),
            "action_plans": None,
            "attention_action_plans": None,
        }
        if include_action_plans:
            payload["action_plans"] = {
                "open": counts["actions_open"],
                "overdue": counts["actions_overdue"],
            }
            payload["attention_action_plans"] = [
                {**plan, "is_overdue": is_overdue(plan["status"], plan["due_date"], today)}
                for plan in self._repo.attention_action_plans(today, ATTENTION_ACTIONS_LIMIT)
            ]
        return payload

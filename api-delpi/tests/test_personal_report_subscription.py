"""Unit — assinatura pessoal de relatório (S2S)."""

from __future__ import annotations

from datetime import datetime, timezone
from typing import Any

from app.application.use_cases.reports.personal_report_subscription_use_cases import (
    GetPersonalReportSubscriptionUseCase,
    UpsertPersonalReportSubscriptionUseCase,
)
from app.domain.services.reports.stock_balances_pa_rules import PROVIDER_KEY


class _FakeRepo:
    def __init__(self) -> None:
        self.definitions: dict[str, dict[str, Any]] = {}
        self.schedules: dict[str, dict[str, Any]] = {}
        self.recipients: dict[str, list[dict[str, str]]] = {}
        self._seq = 0

    def find_personal_definition(
        self,
        *,
        provider_key: str,
        created_by_user_id: str,
        branch: str,
    ) -> dict[str, Any] | None:
        for item in self.definitions.values():
            if (
                item["providerKey"] == provider_key
                and item["createdByUserId"] == created_by_user_id
                and item["params"].get("branch") == branch
            ):
                return dict(item)
        return None

    def create_definition(self, **kwargs: Any) -> dict[str, Any]:
        self._seq += 1
        definition_id = f"def-{self._seq}"
        payload = {
            "id": definition_id,
            "name": kwargs["name"],
            "providerKey": kwargs["provider_key"],
            "params": dict(kwargs["params"]),
            "active": bool(kwargs["active"]),
            "createdByUserId": kwargs["created_by_user_id"],
        }
        self.definitions[definition_id] = payload
        return dict(payload)

    def update_definition(self, **kwargs: Any) -> dict[str, Any] | None:
        definition_id = kwargs["definition_id"]
        current = self.definitions.get(definition_id)
        if current is None:
            return None
        if kwargs.get("name") is not None:
            current["name"] = kwargs["name"]
        if kwargs.get("params") is not None:
            current["params"] = dict(kwargs["params"])
        if kwargs.get("active") is not None:
            current["active"] = bool(kwargs["active"])
        return dict(current)

    def replace_recipients(
        self, *, definition_id: str, items: list[dict[str, str]]
    ) -> list[dict[str, Any]]:
        self.recipients[definition_id] = list(items)
        return list(items)

    def get_schedule_for_definition(self, definition_id: str) -> dict[str, Any] | None:
        item = self.schedules.get(definition_id)
        return dict(item) if item else None

    def upsert_schedule_for_definition(self, **kwargs: Any) -> dict[str, Any]:
        definition_id = kwargs["definition_id"]
        payload = {
            "definitionId": definition_id,
            "scheduleKind": kwargs["schedule_kind"],
            "cronExpression": kwargs["cron_expression"],
            "timezone": kwargs["timezone"],
            "nextRunAt": kwargs["next_run_at"].isoformat()
            if isinstance(kwargs["next_run_at"], datetime)
            else str(kwargs["next_run_at"]),
            "enabled": bool(kwargs["enabled"]),
        }
        self.schedules[definition_id] = payload
        return dict(payload)


def test_upsert_personal_subscription_creates_weekdays_schedule() -> None:
    repo = _FakeRepo()
    use_case = UpsertPersonalReportSubscriptionUseCase(repo)
    result = use_case.execute(
        provider_key=PROVIDER_KEY,
        user_id="user-1",
        email="user@delpi.com.br",
        branch="01",
        hour=7,
        minute=30,
        enabled=True,
    )
    assert result["configured"] is True
    assert result["definition"]["providerKey"] == PROVIDER_KEY
    assert result["definition"]["params"]["branch"] == "01"
    assert result["schedule"]["scheduleKind"] == "weekdays"
    assert result["schedule"]["enabled"] is True
    assert repo.recipients[result["definition"]["id"]][0]["email"] == "user@delpi.com.br"


def test_get_personal_subscription_none_when_missing() -> None:
    repo = _FakeRepo()
    use_case = GetPersonalReportSubscriptionUseCase(repo)
    assert (
        use_case.execute(provider_key=PROVIDER_KEY, user_id="u1", branch="01") is None
    )


def test_upsert_rejects_unknown_provider() -> None:
    repo = _FakeRepo()
    use_case = UpsertPersonalReportSubscriptionUseCase(repo)
    try:
        use_case.execute(
            provider_key="other",
            user_id="u1",
            email="a@b.com",
            branch="01",
            hour=8,
            minute=0,
        )
        raise AssertionError("expected ValueError")
    except ValueError as exc:
        assert "não permitido" in str(exc)

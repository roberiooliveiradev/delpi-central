"""Assinatura pessoal de relatório (S2S) — Portal PCP agenda, Reports monitora."""

from __future__ import annotations

from typing import Any, Protocol

from app.domain.services.reports.report_schedule_next_run_service import (
    DEFAULT_TIMEZONE,
    build_cron_expression,
    compute_next_run_at,
)
from app.domain.services.reports.stock_balances_pa_rules import (
    PROVIDER_KEY as STOCK_BALANCES_PA_KEY,
    normalize_branch,
)

_ALLOWLISTED_PERSONAL_PROVIDERS = frozenset({STOCK_BALANCES_PA_KEY})


class _ReportsRepo(Protocol):
    def find_personal_definition(
        self,
        *,
        provider_key: str,
        created_by_user_id: str,
        branch: str,
    ) -> dict[str, Any] | None: ...

    def create_definition(self, **kwargs: Any) -> dict[str, Any]: ...

    def update_definition(self, **kwargs: Any) -> dict[str, Any] | None: ...

    def replace_recipients(
        self, *, definition_id: str, items: list[dict[str, str]]
    ) -> list[dict[str, Any]]: ...

    def get_schedule_for_definition(
        self, definition_id: str
    ) -> dict[str, Any] | None: ...

    def upsert_schedule_for_definition(self, **kwargs: Any) -> dict[str, Any]: ...


def _definition_name(*, branch: str, email: str) -> str:
    return f"Saldos PA — filial {branch} — {email.strip().lower()}"


class GetPersonalReportSubscriptionUseCase:
    def __init__(self, repository: _ReportsRepo) -> None:
        self._repository = repository

    def execute(
        self,
        *,
        provider_key: str,
        user_id: str,
        branch: str,
    ) -> dict[str, Any] | None:
        key = str(provider_key or "").strip()
        if key not in _ALLOWLISTED_PERSONAL_PROVIDERS:
            raise ValueError("providerKey não permitido para assinatura pessoal.")
        uid = str(user_id or "").strip()
        if not uid:
            raise ValueError("userId é obrigatório.")
        resolved_branch = normalize_branch(branch)
        definition = self._repository.find_personal_definition(
            provider_key=key,
            created_by_user_id=uid,
            branch=resolved_branch,
        )
        if definition is None:
            return None
        schedule = self._repository.get_schedule_for_definition(definition["id"])
        return {
            "definition": definition,
            "schedule": schedule,
            "configured": schedule is not None,
        }


class UpsertPersonalReportSubscriptionUseCase:
    def __init__(self, repository: _ReportsRepo) -> None:
        self._repository = repository

    def execute(
        self,
        *,
        provider_key: str,
        user_id: str,
        email: str,
        branch: str,
        hour: int,
        minute: int,
        enabled: bool = True,
        timezone_name: str = DEFAULT_TIMEZONE,
    ) -> dict[str, Any]:
        key = str(provider_key or "").strip()
        if key not in _ALLOWLISTED_PERSONAL_PROVIDERS:
            raise ValueError("providerKey não permitido para assinatura pessoal.")
        uid = str(user_id or "").strip()
        mail = str(email or "").strip().lower()
        if not uid:
            raise ValueError("userId é obrigatório.")
        if not mail or "@" not in mail or "***" in mail.split("@", 1)[0]:
            raise ValueError("email válido é obrigatório.")
        resolved_branch = normalize_branch(branch)
        hour_i = int(hour)
        minute_i = int(minute)
        if hour_i < 0 or hour_i > 23:
            raise ValueError("hour deve estar entre 0 e 23.")
        if minute_i < 0 or minute_i > 59:
            raise ValueError("minute deve estar entre 0 e 59.")

        definition = self._repository.find_personal_definition(
            provider_key=key,
            created_by_user_id=uid,
            branch=resolved_branch,
        )
        name = _definition_name(branch=resolved_branch, email=mail)
        params = {"branch": resolved_branch}
        if definition is None:
            definition = self._repository.create_definition(
                name=name,
                provider_key=key,
                params=params,
                active=True,
                created_by_user_id=uid,
            )
        else:
            updated = self._repository.update_definition(
                definition_id=definition["id"],
                name=name,
                params=params,
                active=True,
            )
            if updated is not None:
                definition = updated

        self._repository.replace_recipients(
            definition_id=definition["id"],
            items=[{"userId": uid, "email": mail}],
        )

        cron = build_cron_expression(
            schedule_kind="weekdays",
            hour=hour_i,
            minute=minute_i,
        )
        next_run = compute_next_run_at(
            schedule_kind="weekdays",
            hour=hour_i,
            minute=minute_i,
            timezone_name=timezone_name or DEFAULT_TIMEZONE,
        )
        schedule = self._repository.upsert_schedule_for_definition(
            definition_id=definition["id"],
            schedule_kind="weekdays",
            cron_expression=cron,
            timezone=timezone_name or DEFAULT_TIMEZONE,
            next_run_at=next_run,
            enabled=bool(enabled),
        )
        return {
            "definition": definition,
            "schedule": schedule,
            "configured": True,
        }

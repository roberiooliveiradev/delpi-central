"""CRUD auxiliar — recipients / schedule / get run (Delpi Reports Fase 3)."""

from __future__ import annotations

from typing import Any, Protocol

from app.domain.services.reports.report_schedule_next_run_service import (
    DEFAULT_TIMEZONE,
    build_cron_expression,
    compute_next_run_at,
)


class _ReportsRepo(Protocol):
    def get_definition(self, definition_id: str) -> dict[str, Any] | None: ...
    def list_recipients(self, definition_id: str) -> list[dict[str, Any]]: ...
    def replace_recipients(
        self, *, definition_id: str, items: list[dict[str, str]]
    ) -> list[dict[str, Any]]: ...
    def get_schedule_for_definition(
        self, definition_id: str
    ) -> dict[str, Any] | None: ...
    def upsert_schedule_for_definition(self, **kwargs: Any) -> dict[str, Any]: ...
    def delete_schedule_for_definition(self, definition_id: str) -> bool: ...
    def get_run(self, run_id: str) -> dict[str, Any] | None: ...
    def list_deliveries_for_run(self, run_id: str) -> list[dict[str, Any]]: ...


class ListReportRecipientsUseCase:
    def __init__(self, repository: _ReportsRepo) -> None:
        self._repository = repository

    def execute(self, definition_id: str) -> dict[str, Any]:
        if self._repository.get_definition(definition_id) is None:
            raise LookupError("Definição de relatório não encontrada.")
        items = self._repository.list_recipients(definition_id)
        return {"items": items, "total": len(items)}


class ReplaceReportRecipientsUseCase:
    def __init__(self, repository: _ReportsRepo) -> None:
        self._repository = repository

    def execute(
        self,
        *,
        definition_id: str,
        items: list[dict[str, str]],
    ) -> dict[str, Any]:
        if self._repository.get_definition(definition_id) is None:
            raise LookupError("Definição de relatório não encontrada.")
        normalized: list[dict[str, str]] = []
        seen: set[str] = set()
        for raw in items:
            user_id = str(raw.get("userId") or raw.get("user_id") or "").strip()
            email = str(raw.get("email") or "").strip()
            if not user_id or not email or "@" not in email:
                continue
            local = email.split("@", 1)[0]
            if "***" in local:
                raise ValueError(
                    "E-mail mascarado do diretório não pode ser usado no envio. "
                    "Atualize o plugin Reports e selecione o destinatário de novo."
                )
            if user_id in seen:
                continue
            seen.add(user_id)
            normalized.append({"userId": user_id, "email": email})
        if not normalized and items:
            raise ValueError(
                "Nenhum destinatário com e-mail válido. "
                "Selecione novamente no diretório (e-mail completo)."
            )
        saved = self._repository.replace_recipients(
            definition_id=definition_id,
            items=normalized,
        )
        return {"items": saved, "total": len(saved)}


class GetReportScheduleUseCase:
    def __init__(self, repository: _ReportsRepo) -> None:
        self._repository = repository

    def execute(self, definition_id: str) -> dict[str, Any] | None:
        if self._repository.get_definition(definition_id) is None:
            raise LookupError("Definição de relatório não encontrada.")
        return self._repository.get_schedule_for_definition(definition_id)


class UpsertReportScheduleUseCase:
    def __init__(self, repository: _ReportsRepo) -> None:
        self._repository = repository

    def execute(
        self,
        *,
        definition_id: str,
        schedule_kind: str,
        hour: int,
        minute: int,
        weekday: int | None = None,
        enabled: bool = True,
        timezone_name: str = DEFAULT_TIMEZONE,
    ) -> dict[str, Any]:
        if self._repository.get_definition(definition_id) is None:
            raise LookupError("Definição de relatório não encontrada.")
        cron = build_cron_expression(
            schedule_kind=schedule_kind,
            hour=hour,
            minute=minute,
            weekday=weekday,
        )
        next_run = compute_next_run_at(
            schedule_kind=schedule_kind,
            hour=hour,
            minute=minute,
            weekday=weekday,
            timezone_name=timezone_name,
        )
        return self._repository.upsert_schedule_for_definition(
            definition_id=definition_id,
            schedule_kind=str(schedule_kind).strip().lower(),
            cron_expression=cron,
            timezone=timezone_name or DEFAULT_TIMEZONE,
            next_run_at=next_run,
            enabled=bool(enabled),
        )


class DeleteReportScheduleUseCase:
    def __init__(self, repository: _ReportsRepo) -> None:
        self._repository = repository

    def execute(self, definition_id: str) -> bool:
        if self._repository.get_definition(definition_id) is None:
            raise LookupError("Definição de relatório não encontrada.")
        return self._repository.delete_schedule_for_definition(definition_id)


class GetReportRunUseCase:
    def __init__(self, repository: _ReportsRepo) -> None:
        self._repository = repository

    def execute(self, run_id: str) -> dict[str, Any] | None:
        run = self._repository.get_run(run_id)
        if run is None:
            return None
        payload = dict(run)
        payload["deliveries"] = self._repository.list_deliveries_for_run(run_id)
        return payload

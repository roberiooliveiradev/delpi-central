"""Orquestração de notificações PAC — ações a vencer e planos parados."""

from __future__ import annotations

from dataclasses import dataclass
from datetime import date, datetime, timezone
from typing import Any, Protocol

from app.application.services.pac_quality_portal_notification_service import (
    build_action_due_notification,
    build_plan_stalled_notification,
    pac_portal_notifications_enabled,
    send_pac_portal_notification,
)
from app.config import settings


class PacQualityNotificationRepository(Protocol):
    def list_actions_due_within_days(self, *, days_ahead: int) -> list[dict[str, Any]]: ...

    def list_stalled_critical_plans(self, *, stall_days: int) -> list[dict[str, Any]]: ...

    def notification_already_sent(self, notification_key: str) -> bool: ...

    def record_notification_dispatch(
        self,
        *,
        notification_key: str,
        event_type: str,
        recipient_user_id: str | None,
        entity_type: str | None,
        entity_id: str | None,
    ) -> None: ...


@dataclass(frozen=True)
class DispatchPacQualityNotificationsResult:
    enabled: bool
    dry_run: bool
    candidates: int
    sent: int
    skipped_duplicate: int
    skipped_no_recipient: int
    failed: int


def _parse_coordinator_user_ids() -> list[str]:
    raw = (settings.PAC_QUALITY_COORDINATOR_USER_IDS or "").strip()
    if not raw:
        return []
    return [item.strip() for item in raw.split(",") if item.strip()]


def _today_key() -> str:
    return datetime.now(timezone.utc).strftime("%Y-%m-%d")


class DispatchPacQualityNotificationsUseCase:
    def __init__(self, repository: PacQualityNotificationRepository) -> None:
        self._repository = repository

    def execute(self, *, dry_run: bool = False) -> DispatchPacQualityNotificationsResult:
        if not pac_portal_notifications_enabled():
            return DispatchPacQualityNotificationsResult(
                enabled=False,
                dry_run=dry_run,
                candidates=0,
                sent=0,
                skipped_duplicate=0,
                skipped_no_recipient=0,
                failed=0,
            )

        days_ahead = max(1, int(settings.PAC_QUALITY_ACTION_DUE_DAYS_AHEAD or 2))
        stall_days = max(1, int(settings.PAC_QUALITY_STALL_DAYS or 7))
        coordinators = _parse_coordinator_user_ids()

        candidates: list[dict[str, Any]] = []

        for row in self._repository.list_actions_due_within_days(days_ahead=days_ahead):
            recipient = str(row.get("responsible_user_id") or "").strip()
            if not recipient:
                continue
            due_date = row.get("due_date")
            due_label = (
                due_date.isoformat()
                if isinstance(due_date, (date, datetime))
                else str(due_date or "")
            )
            action_id = str(row.get("action_id") or row.get("id") or "")
            plan_id = str(row.get("plan_id") or "")
            dedupe_key = f"pac:action_due:{action_id}:{due_label}"
            candidates.append(
                build_action_due_notification(
                    action_id=action_id,
                    plan_id=plan_id,
                    plan_code=row.get("plan_code"),
                    action_description=row.get("description"),
                    due_date=due_label,
                    recipient_user_id=recipient,
                    dedupe_key=dedupe_key,
                )
            )

        for row in self._repository.list_stalled_critical_plans(stall_days=stall_days):
            plan_id = str(row.get("id") or "")
            day_key = _today_key()
            recipients: list[str] = []
            owner = str(row.get("owner_user_id") or "").strip()
            if owner:
                recipients.append(owner)
            recipients.extend(coordinators)
            seen: set[str] = set()
            for recipient in recipients:
                if recipient in seen:
                    continue
                seen.add(recipient)
                dedupe_key = f"pac:plan_stalled:{plan_id}:{recipient}:{day_key}"
                candidates.append(
                    build_plan_stalled_notification(
                        plan_id=plan_id,
                        plan_code=row.get("code"),
                        plan_title=row.get("title"),
                        days_without_update=int(row.get("days_without_update") or 0),
                        recipient_user_id=recipient,
                        dedupe_key=dedupe_key,
                    )
                )

        sent = 0
        skipped_duplicate = 0
        skipped_no_recipient = 0
        failed = 0

        for item in candidates:
            recipient = str(item.get("recipient_user_id") or "").strip()
            dedupe_key = str(item.get("dedupe_key") or "")
            if not recipient:
                skipped_no_recipient += 1
                continue
            if self._repository.notification_already_sent(dedupe_key):
                skipped_duplicate += 1
                continue
            if dry_run:
                sent += 1
                continue

            ok = send_pac_portal_notification(
                recipient_user_id=recipient,
                title=str(item.get("title") or "PAC Qualidade"),
                message=str(item.get("message") or ""),
                notification_type=str(item.get("notification_type") or "info"),
                action_label=str(item.get("action_label") or "Abrir"),
                action_target=str(item.get("action_target") or ""),
                dedupe_key=dedupe_key,
                event_type=str(item.get("event_type") or "pac_notification"),
                metadata=item.get("metadata") if isinstance(item.get("metadata"), dict) else None,
            )
            if ok:
                metadata = item.get("metadata") if isinstance(item.get("metadata"), dict) else {}
                entity_type = "quality_action" if item.get("event_type") == "pac_action_due_soon" else "quality_action_plan"
                entity_id = metadata.get("actionId") or metadata.get("planId")
                self._repository.record_notification_dispatch(
                    notification_key=dedupe_key,
                    event_type=str(item.get("event_type") or "pac_notification"),
                    recipient_user_id=recipient,
                    entity_type=entity_type,
                    entity_id=str(entity_id) if entity_id else None,
                )
                sent += 1
            else:
                failed += 1

        return DispatchPacQualityNotificationsResult(
            enabled=True,
            dry_run=dry_run,
            candidates=len(candidates),
            sent=sent,
            skipped_duplicate=skipped_duplicate,
            skipped_no_recipient=skipped_no_recipient,
            failed=failed,
        )

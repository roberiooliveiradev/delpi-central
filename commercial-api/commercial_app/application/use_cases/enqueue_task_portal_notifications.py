"""Enqueue + publish commercial task portal notifications via outbox."""

from __future__ import annotations

import logging
from dataclasses import dataclass
from datetime import datetime, timedelta, timezone
from typing import Any, Sequence

from commercial_app.application.services.task_portal_notification_delivery_policy import (
    TaskPortalNotificationDeliveryPolicy,
)
from commercial_app.domain.entities.task import CommercialTask
from commercial_app.domain.ports.commercial_group_repository_port import (
    CommercialGroupRepositoryPort,
)
from commercial_app.domain.ports.integration_outbox_repository_port import (
    IntegrationCheckpointRepositoryPort,
    IntegrationOutboxRepositoryPort,
)
from commercial_app.domain.ports.task_repository_port import TaskRepositoryPort
from commercial_app.domain.services.task_portal_notification_content_service import (
    EVENT_ASSIGNED,
    EVENT_COMPLETED,
    EVENT_DUE_SOON,
    EVENT_GROUP_ASSIGNED,
    EVENT_OVERDUE,
    TaskPortalNotificationContentService,
)
from commercial_app.domain.services.task_portal_notification_recipient_resolver_service import (
    TaskPortalNotificationRecipientResolverService,
)

logger = logging.getLogger("commercial.task_portal_notifications")


def _due_iso(task: CommercialTask) -> str | None:
    if task.due_at is None:
        return None
    due = task.due_at
    if due.tzinfo is None:
        due = due.replace(tzinfo=timezone.utc)
    return due.isoformat()


@dataclass(frozen=True, slots=True)
class EnqueueTaskPortalResult:
    enqueued: int


@dataclass(frozen=True, slots=True)
class DetectTaskDueResult:
    due_soon_count: int
    overdue_count: int
    enqueued: int


class EnqueueTaskPortalNotificationsService:
    """Application service: enqueue task portal notifications and flush outbox."""

    def __init__(
        self,
        *,
        outbox: IntegrationOutboxRepositoryPort,
        groups: CommercialGroupRepositoryPort,
        publish: "PublishIntegrationOutboxUseCase | None" = None,
        content: type[TaskPortalNotificationContentService] | None = None,
        delivery_policy: TaskPortalNotificationDeliveryPolicy | None = None,
    ) -> None:
        self._outbox = outbox
        self._recipients = TaskPortalNotificationRecipientResolverService(groups=groups)
        self._publish = publish
        self._content = content or TaskPortalNotificationContentService
        self._delivery = delivery_policy or TaskPortalNotificationDeliveryPolicy()

    def _enqueue_event(
        self,
        *,
        event_type: str,
        task: CommercialTask,
        user_ids: Sequence[str],
        dedupe_key: str,
    ) -> bool:
        recipients = self._delivery.filter_portal_recipients(event_type, user_ids)
        if not recipients:
            return False
        due_iso = _due_iso(task)
        bucket = self._content.bucket_for(event_type)
        action_target = self._content.build_deep_link_path(
            bucket=bucket,
            search=task.title,
        )
        payload: dict[str, Any] = {
            "taskId": str(task.id),
            "title": task.title,
            "dueAt": due_iso,
            "userIds": recipients,
            "actionTarget": action_target,
            "dedupeKey": dedupe_key,
            "bucket": bucket,
        }
        self._outbox.enqueue(
            event_type=event_type,
            aggregate_type=self._content.aggregate_type(),
            aggregate_id=str(task.id),
            payload=payload,
        )
        return True

    def _flush(self) -> None:
        if self._publish is None:
            return
        try:
            self._publish.execute(limit=50)
        except Exception:
            logger.exception("task_portal_notification_publish_failed")

    def on_task_created(self, *, task: CommercialTask, actor_user_id: str) -> int:
        enqueued = 0
        assignees = [
            uid
            for uid in task.resolved_assignee_user_ids()
            if uid and uid != actor_user_id
        ]
        if assignees:
            recipients = self._recipients.resolve_interested_user_ids(
                task,
                actor_user_id=actor_user_id,
                include_creator=False,
                only_user_ids=assignees,
            )
            for user_id in recipients:
                if self._enqueue_event(
                    event_type=EVENT_ASSIGNED,
                    task=task,
                    user_ids=[user_id],
                    dedupe_key=f"commercial:task:assigned:{task.id}:{user_id}",
                ):
                    enqueued += 1

        for group_id in task.resolved_assignee_group_ids():
            recipients = self._recipients.resolve_interested_user_ids(
                task,
                actor_user_id=actor_user_id,
                include_creator=False,
                only_group_ids=[group_id],
            )
            for user_id in recipients:
                if self._enqueue_event(
                    event_type=EVENT_GROUP_ASSIGNED,
                    task=task,
                    user_ids=[user_id],
                    dedupe_key=f"commercial:task:group:{task.id}:{group_id}:{user_id}",
                ):
                    enqueued += 1
        if enqueued:
            self._flush()
        return enqueued

    def on_task_assignees_changed(
        self,
        *,
        task: CommercialTask,
        actor_user_id: str,
        previous_user_ids: Sequence[str],
        previous_group_ids: Sequence[str],
    ) -> int:
        prev_users = {str(uid).strip() for uid in previous_user_ids if str(uid).strip()}
        prev_groups = {str(gid).strip() for gid in previous_group_ids if str(gid).strip()}
        new_users = [
            uid
            for uid in task.resolved_assignee_user_ids()
            if uid and uid not in prev_users and uid != actor_user_id
        ]
        new_groups = [
            gid
            for gid in task.resolved_assignee_group_ids()
            if gid and gid not in prev_groups
        ]
        enqueued = 0
        if new_users:
            recipients = self._recipients.resolve_interested_user_ids(
                task,
                actor_user_id=actor_user_id,
                include_creator=False,
                only_user_ids=new_users,
            )
            for user_id in recipients:
                if self._enqueue_event(
                    event_type=EVENT_ASSIGNED,
                    task=task,
                    user_ids=[user_id],
                    dedupe_key=f"commercial:task:assigned:{task.id}:{user_id}",
                ):
                    enqueued += 1
        for group_id in new_groups:
            recipients = self._recipients.resolve_interested_user_ids(
                task,
                actor_user_id=actor_user_id,
                include_creator=False,
                only_group_ids=[group_id],
            )
            for user_id in recipients:
                if self._enqueue_event(
                    event_type=EVENT_GROUP_ASSIGNED,
                    task=task,
                    user_ids=[user_id],
                    dedupe_key=f"commercial:task:group:{task.id}:{group_id}:{user_id}",
                ):
                    enqueued += 1
        if enqueued:
            self._flush()
        return enqueued

    def on_task_completed(self, *, task: CommercialTask, actor_user_id: str) -> int:
        recipients = self._recipients.resolve_interested_user_ids(
            task,
            actor_user_id=actor_user_id,
            include_creator=True,
        )
        if not recipients:
            return 0
        ok = self._enqueue_event(
            event_type=EVENT_COMPLETED,
            task=task,
            user_ids=sorted(recipients),
            dedupe_key=f"commercial:task:completed:{task.id}",
        )
        if ok:
            self._flush()
        return 1 if ok else 0


class DetectTaskDueNotificationsUseCase:
    """Detect open tasks that are due soon / overdue and enqueue portal notifications."""

    def __init__(
        self,
        *,
        tasks: TaskRepositoryPort,
        outbox: IntegrationOutboxRepositoryPort,
        checkpoints: IntegrationCheckpointRepositoryPort,
        groups: CommercialGroupRepositoryPort,
        content: type[TaskPortalNotificationContentService] | None = None,
    ) -> None:
        self._tasks = tasks
        self._outbox = outbox
        self._checkpoints = checkpoints
        self._recipients = TaskPortalNotificationRecipientResolverService(groups=groups)
        self._content = content or TaskPortalNotificationContentService

    def execute(self, *, persist_checkpoint: bool = True) -> DetectTaskDueResult:
        now = datetime.now(timezone.utc)
        soon_limit = now + timedelta(hours=self._content.due_soon_hours())
        day_key = now.date().isoformat()

        checkpoint = self._checkpoints.get_by_source_key(
            self._content.due_checkpoint_source_key()
        )
        previous: set[str] = set()
        if checkpoint and isinstance(checkpoint.metadata, dict):
            raw = checkpoint.metadata.get("keys")
            if isinstance(raw, list):
                previous = {str(item) for item in raw if str(item).strip()}

        open_tasks = list(self._tasks.list_by_status(status="open", limit=2000))
        due_soon = 0
        overdue = 0
        enqueued = 0
        next_keys: set[str] = set()

        for task in open_tasks:
            if task.due_at is None:
                continue
            due = task.due_at
            if due.tzinfo is None:
                due = due.replace(tzinfo=timezone.utc)

            if due < now:
                event_type = EVENT_OVERDUE
                key = f"overdue:{task.id}:{day_key}"
                overdue += 1
            elif due <= soon_limit:
                event_type = EVENT_DUE_SOON
                key = f"due_soon:{task.id}:{day_key}"
                due_soon += 1
            else:
                continue

            next_keys.add(key)
            if key in previous:
                continue

            recipients = self._recipients.resolve_interested_user_ids(
                task,
                actor_user_id=None,
                include_creator=True,
            )
            if not recipients:
                continue
            due_iso = due.isoformat()
            action_target = self._content.build_deep_link_path(
                bucket=self._content.bucket_for(event_type),
                search=task.title,
            )
            self._outbox.enqueue(
                event_type=event_type,
                aggregate_type=self._content.aggregate_type(),
                aggregate_id=str(task.id),
                payload={
                    "taskId": str(task.id),
                    "title": task.title,
                    "dueAt": due_iso,
                    "userIds": sorted(recipients),
                    "actionTarget": action_target,
                    "dedupeKey": f"commercial:task:{key}",
                    "bucket": self._content.bucket_for(event_type),
                },
            )
            enqueued += 1

        if persist_checkpoint:
            self._checkpoints.upsert_metadata(
                source_key=self._content.due_checkpoint_source_key(),
                metadata={
                    "keys": sorted(next_keys),
                    "keyCount": len(next_keys),
                    "day": day_key,
                },
                cursor_value=day_key,
                last_success_at=now,
            )

        return DetectTaskDueResult(
            due_soon_count=due_soon,
            overdue_count=overdue,
            enqueued=enqueued,
        )


# Late import type for publish — defined in enqueue_ready_to_invoice module historically.
from commercial_app.application.use_cases.enqueue_ready_to_invoice_notifications import (  # noqa: E402
    PublishIntegrationOutboxUseCase,
)


@dataclass(frozen=True, slots=True)
class ScanTaskDueNotificationsResult:
    detection: DetectTaskDueResult
    published: int
    failed: int
    processed: int


class ScanTaskDueNotificationsUseCase:
    def __init__(
        self,
        *,
        detect: DetectTaskDueNotificationsUseCase,
        publish: PublishIntegrationOutboxUseCase,
    ) -> None:
        self._detect = detect
        self._publish = publish

    def execute(self) -> dict[str, Any]:
        detection = self._detect.execute(persist_checkpoint=True)
        published = self._publish.execute(limit=100)
        return {
            "dueSoonCount": detection.due_soon_count,
            "overdueCount": detection.overdue_count,
            "enqueued": detection.enqueued,
            "processed": published.processed,
            "published": published.published,
            "failed": published.failed,
        }

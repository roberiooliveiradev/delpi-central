"""Portal notifications for commercial tasks (outbox + recipients + publish)."""

from __future__ import annotations

from datetime import datetime, timedelta, timezone
from uuid import uuid4

from commercial_app.application.services.commercial_portal_notification_service import (
    CommercialPortalNotificationService,
)
from commercial_app.application.use_cases.enqueue_ready_to_invoice_notifications import (
    PublishIntegrationOutboxUseCase,
)
from commercial_app.application.use_cases.enqueue_task_portal_notifications import (
    DetectTaskDueNotificationsUseCase,
    EnqueueTaskPortalNotificationsService,
)
from commercial_app.domain.entities.task import CommercialTask
from commercial_app.domain.ports.integration_outbox_repository_port import (
    IntegrationCheckpoint,
    IntegrationOutboxRow,
)
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


class _OutboxMemory:
    def __init__(self) -> None:
        self.rows: list[IntegrationOutboxRow] = []
        self.published: list[str] = []
        self.failed: list[tuple[str, str]] = []

    def enqueue(self, *, event_type, aggregate_type, aggregate_id, payload):
        row = IntegrationOutboxRow(
            id=f"ob-{len(self.rows)+1}",
            event_type=event_type,
            aggregate_type=aggregate_type,
            aggregate_id=aggregate_id,
            payload=payload,
            created_at=None,
            available_at=None,
            published_at=None,
            attempts=0,
            last_error=None,
        )
        self.rows.append(row)
        return row

    def list_pending(self, *, limit: int = 50):
        return [row for row in self.rows if row.id not in self.published][:limit]

    def mark_published(self, outbox_id: str) -> None:
        self.published.append(outbox_id)

    def mark_failed(
        self, outbox_id: str, *, error: str, delay_seconds: int | None = None
    ) -> None:
        self.failed.append((outbox_id, error))

    def defer(self, outbox_id: str, *, delay_seconds: int) -> None:
        return None


class _GroupsMemory:
    def __init__(self, members: dict[str, list[str]] | None = None) -> None:
        self._members = members or {}

    def list_member_user_ids_by_group_id(self, group_id: str) -> list[str]:
        return list(self._members.get(group_id, []))


class _CheckpointMemory:
    def __init__(self) -> None:
        self.by_key: dict[str, IntegrationCheckpoint] = {}

    def get_by_source_key(self, source_key: str) -> IntegrationCheckpoint | None:
        return self.by_key.get(source_key)

    def upsert_metadata(
        self,
        *,
        source_key: str,
        metadata: dict,
        cursor_value: str | None = None,
        last_success_at: datetime | None = None,
    ) -> IntegrationCheckpoint:
        row = IntegrationCheckpoint(
            id=f"cp-{source_key}",
            source_key=source_key,
            cursor_value=cursor_value,
            last_success_at=last_success_at,
            metadata=metadata,
            updated_at=last_success_at,
        )
        self.by_key[source_key] = row
        return row


class _TasksMemory:
    def __init__(self, tasks: list[CommercialTask]) -> None:
        self._tasks = tasks

    def list_by_status(self, *, status: str, limit: int = 2000):
        return [t for t in self._tasks if t.status == status][:limit]


def _task(
    *,
    title: str = "Follow-up ACME",
    assignee_user_ids: tuple[str, ...] = ("assignee-1",),
    assignee_group_ids: tuple[str, ...] = (),
    created_by: str = "creator-1",
    due_at: datetime | None = None,
    status: str = "open",
) -> CommercialTask:
    now = datetime.now(timezone.utc)
    primary = assignee_user_ids[0] if assignee_user_ids else ""
    return CommercialTask(
        id=uuid4(),
        title=title,
        description=None,
        task_type="follow_up",
        status=status,
        priority="normal",
        due_at=due_at,
        completed_at=None,
        assignee_user_id=primary,
        created_by_user_id=created_by,
        customer_code=None,
        customer_store=None,
        created_at=now,
        updated_at=now,
        assignee_user_ids=assignee_user_ids,
        assignee_group_ids=assignee_group_ids,
    )


def test_content_templates_and_deep_link() -> None:
    assert TaskPortalNotificationContentService.category() == "commercial_tasks"
    assert TaskPortalNotificationContentService.title_for(EVENT_ASSIGNED)
    msg = TaskPortalNotificationContentService.format_message(
        EVENT_ASSIGNED, title="X", due_at_iso="2026-08-20T12:00:00+00:00"
    )
    assert "X" in msg
    assert "2026-08-20" in msg
    path = TaskPortalNotificationContentService.build_deep_link_path(
        bucket="overdue", search="WEG"
    )
    assert path.startswith("/apps/commercial/my-tasks")
    assert "bucket=overdue" in path
    assert "q=WEG" in path
    assert "view=" not in path


def test_recipients_exclude_actor_and_expand_groups() -> None:
    groups = _GroupsMemory({"g1": ["m1", "m2", "actor"]})
    resolver = TaskPortalNotificationRecipientResolverService(groups=groups)  # type: ignore[arg-type]
    task = _task(
        assignee_user_ids=("assignee-1", "actor"),
        assignee_group_ids=("g1",),
        created_by="creator-1",
    )
    recipients = resolver.resolve_interested_user_ids(task, actor_user_id="actor")
    assert "actor" not in recipients
    assert "assignee-1" in recipients
    assert "m1" in recipients
    assert "m2" in recipients
    assert "creator-1" in recipients


def test_on_create_notifies_new_assignees_not_actor() -> None:
    outbox = _OutboxMemory()
    svc = EnqueueTaskPortalNotificationsService(
        outbox=outbox,
        groups=_GroupsMemory(),  # type: ignore[arg-type]
        publish=None,
    )
    task = _task(assignee_user_ids=("actor", "peer"))
    enqueued = svc.on_task_created(task=task, actor_user_id="actor")
    assert enqueued == 1
    assert outbox.rows[0].event_type == EVENT_ASSIGNED
    assert outbox.rows[0].payload["userIds"] == ["peer"]
    assert "view=" not in outbox.rows[0].payload["actionTarget"]


def test_on_create_group_assigned_dedupe_per_group() -> None:
    outbox = _OutboxMemory()
    svc = EnqueueTaskPortalNotificationsService(
        outbox=outbox,
        groups=_GroupsMemory({"g1": ["m1"], "g2": ["m2"]}),  # type: ignore[arg-type]
        publish=None,
    )
    task = _task(assignee_user_ids=(), assignee_group_ids=("g1", "g2"))
    enqueued = svc.on_task_created(task=task, actor_user_id="actor")
    assert enqueued == 2
    keys = {row.payload["dedupeKey"] for row in outbox.rows}
    assert f"commercial:task:group:{task.id}:g1:m1" in keys
    assert f"commercial:task:group:{task.id}:g2:m2" in keys
    assert all(row.event_type == EVENT_GROUP_ASSIGNED for row in outbox.rows)


def test_on_complete_notifies_interested_except_actor() -> None:
    outbox = _OutboxMemory()
    svc = EnqueueTaskPortalNotificationsService(
        outbox=outbox,
        groups=_GroupsMemory({"g1": ["m1"]}),  # type: ignore[arg-type]
        publish=None,
    )
    task = _task(
        assignee_user_ids=("assignee-1",),
        assignee_group_ids=("g1",),
        created_by="creator-1",
    )
    enqueued = svc.on_task_completed(task=task, actor_user_id="assignee-1")
    assert enqueued == 1
    assert outbox.rows[0].event_type == EVENT_COMPLETED
    users = set(outbox.rows[0].payload["userIds"])
    assert "assignee-1" not in users
    assert "creator-1" in users
    assert "m1" in users


def test_publish_registry_handles_task_and_ready_events() -> None:
    outbox = _OutboxMemory()
    outbox.enqueue(
        event_type=EVENT_ASSIGNED,
        aggregate_type="commercial_task",
        aggregate_id="t1",
        payload={
            "taskId": "t1",
            "title": "T",
            "userIds": ["u1"],
            "actionTarget": "/apps/commercial/my-tasks?bucket=today",
            "dedupeKey": "commercial:task:assigned:t1:u1",
            "bucket": "today",
        },
    )
    outbox.enqueue(
        event_type="commercial.order.ready_to_invoice",
        aggregate_type="open_order_line",
        aggregate_id="01|10|01",
        payload={
            "lineKey": "01|10|01",
            "userIds": ["u1"],
            "permissionCodes": [],
            "actionTarget": "/apps/commercial/open-orders?stage=ready_to_invoice",
            "pedido": "10",
            "linha": "01",
            "cliente": "ACME",
            "filial": "01",
        },
    )
    task_calls: list[dict] = []
    ready_calls: list[dict] = []

    class _Notifier(CommercialPortalNotificationService):
        def __init__(self) -> None:
            super().__init__(enabled=True, service_token="tok")

        def notify_task_event(self, **kwargs):  # type: ignore[override]
            task_calls.append(kwargs)
            return True

        def notify_ready_to_invoice(self, **kwargs):  # type: ignore[override]
            ready_calls.append(kwargs)
            return True

    result = PublishIntegrationOutboxUseCase(
        outbox=outbox,
        notifier=_Notifier(),
    ).execute()
    assert result.published == 2
    assert len(task_calls) == 1
    assert len(ready_calls) == 1
    assert task_calls[0]["event_type"] == EVENT_ASSIGNED


def test_notify_task_event_payload_category(monkeypatch) -> None:
    captured: dict = {}

    class _Resp:
        status_code = 200
        text = "ok"

    def _post(url, *, headers, json, timeout):
        captured["json"] = json
        return _Resp()

    monkeypatch.setattr(
        "commercial_app.application.services.commercial_portal_notification_service.httpx.post",
        _post,
    )
    svc = CommercialPortalNotificationService(
        core_api_url="http://core-api:8000",
        service_token="secret",
        enabled=True,
    )
    assert svc.notify_task_event(
        event_type=EVENT_ASSIGNED,
        user_ids=["u1"],
        task_id="tid",
        title="Tarefa X",
        due_at="2026-08-20T00:00:00+00:00",
    )
    body = captured["json"]
    assert body["category"] == "commercial_tasks"
    assert body["sourceApp"] == "commercial"
    assert body["userIds"] == ["u1"]
    assert "permissionCodes" not in body
    assert body["action"]["label"] == "Abrir tarefas"
    assert "view=" not in body["action"]["target"]
    assert "/apps/commercial/my-tasks" in body["action"]["target"]


def test_due_scan_enqueues_once_per_day() -> None:
    now = datetime.now(timezone.utc)
    soon = _task(due_at=now + timedelta(hours=2), assignee_user_ids=("u1",))
    overdue = _task(due_at=now - timedelta(hours=1), assignee_user_ids=("u2",))
    far = _task(due_at=now + timedelta(days=5), assignee_user_ids=("u3",))
    outbox = _OutboxMemory()
    checkpoints = _CheckpointMemory()
    detect = DetectTaskDueNotificationsUseCase(
        tasks=_TasksMemory([soon, overdue, far]),  # type: ignore[arg-type]
        outbox=outbox,
        checkpoints=checkpoints,
        groups=_GroupsMemory(),  # type: ignore[arg-type]
    )
    first = detect.execute()
    assert first.due_soon_count == 1
    assert first.overdue_count == 1
    assert first.enqueued == 2
    types = {row.event_type for row in outbox.rows}
    assert EVENT_DUE_SOON in types
    assert EVENT_OVERDUE in types

    second = detect.execute()
    assert second.enqueued == 0
    assert len(outbox.rows) == 2


def test_skip_portal_when_recipient_online_for_assign() -> None:
    from commercial_app.application.services.task_portal_notification_delivery_policy import (
        TaskPortalNotificationDeliveryPolicy,
    )

    class _Hub:
        def is_user_online(self, user_id: str | None) -> bool:
            return str(user_id or "") == "online-user"

    outbox = _OutboxMemory()
    svc = EnqueueTaskPortalNotificationsService(
        outbox=outbox,
        groups=_GroupsMemory(),  # type: ignore[arg-type]
        publish=None,
        delivery_policy=TaskPortalNotificationDeliveryPolicy(hub=_Hub()),  # type: ignore[arg-type]
    )
    task = _task(assignee_user_ids=("online-user", "offline-user"))
    enqueued = svc.on_task_created(task=task, actor_user_id="actor")
    assert enqueued == 1
    assert outbox.rows[0].payload["userIds"] == ["offline-user"]


def test_delivery_policy_suppresses_all_task_events_when_online() -> None:
    from commercial_app.application.services.task_portal_notification_delivery_policy import (
        TaskPortalNotificationDeliveryPolicy,
    )
    from commercial_app.domain.services.ready_to_invoice_notification_content_service import (
        ReadyToInvoiceNotificationContentService,
    )

    class _Hub:
        def is_user_online(self, user_id: str | None) -> bool:
            return str(user_id or "") == "online-user"

    policy = TaskPortalNotificationDeliveryPolicy(hub=_Hub())  # type: ignore[arg-type]
    assert policy.filter_portal_recipients(EVENT_DUE_SOON, ["online-user", "offline"]) == [
        "offline"
    ]
    assert policy.filter_portal_recipients(EVENT_OVERDUE, ["online-user"]) == []
    assert policy.filter_portal_recipients(EVENT_ASSIGNED, ["online-user"]) == []
    r2i = ReadyToInvoiceNotificationContentService.event_type()
    assert policy.filter_portal_recipients(r2i, ["online-user", "offline"]) == ["offline"]
    online, offline = policy.split_online_offline(r2i, ["online-user", "offline"])
    assert online == ["online-user"]
    assert offline == ["offline"]

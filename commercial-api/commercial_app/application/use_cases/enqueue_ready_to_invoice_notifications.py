"""Enqueue + publish ready_to_invoice portal notifications via outbox."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any

from commercial_app.application.services.commercial_portal_notification_service import (
    CommercialPortalNotificationService,
)
from commercial_app.application.use_cases.detect_ready_to_invoice_entries import (
    DetectReadyToInvoiceEntriesUseCase,
    DetectReadyToInvoiceResult,
)
from commercial_app.domain.ports.integration_outbox_repository_port import (
    IntegrationOutboxRepositoryPort,
)
from commercial_app.domain.services.ready_to_invoice_notification_content_service import (
    ReadyToInvoiceNotificationContentService,
)


@dataclass(frozen=True, slots=True)
class EnqueueReadyToInvoiceResult:
    detection: DetectReadyToInvoiceResult
    enqueued: int


@dataclass(frozen=True, slots=True)
class PublishOutboxResult:
    processed: int
    published: int
    failed: int


class EnqueueReadyToInvoiceNotificationsUseCase:
    """Detect delta, persist snapshot, write one outbox row per entered line."""

    def __init__(
        self,
        *,
        detect: DetectReadyToInvoiceEntriesUseCase,
        outbox: IntegrationOutboxRepositoryPort,
        content: type[ReadyToInvoiceNotificationContentService] | None = None,
    ) -> None:
        self._detect = detect
        self._outbox = outbox
        self._content = content or ReadyToInvoiceNotificationContentService

    def execute(self) -> EnqueueReadyToInvoiceResult:
        detection = self._detect.execute(persist_snapshot=True)
        # Cold start: persist snapshot only — do not flood portal/toast with every
        # line already ready before the scheduler existed.
        if detection.previous_key_count == 0:
            return EnqueueReadyToInvoiceResult(detection=detection, enqueued=0)
        event_type = self._content.event_type()
        aggregate_type = self._content.aggregate_type()
        enqueued = 0
        for entry in detection.entered:
            item = entry.item
            payload: dict[str, Any] = {
                "lineKey": entry.line_key,
                "userIds": sorted(entry.recipients.all_user_ids),
                "permissionCodes": list(entry.recipients.billing_permission_codes),
                "actionTarget": self._content.build_deep_link_path(
                    pedido=str(item.get("pedido") or "").strip(),
                    linha=str(item.get("linha") or "").strip(),
                    filial=str(item.get("filial") or "").strip(),
                ),
                "pedido": str(item.get("pedido") or "").strip(),
                "linha": str(item.get("linha") or "").strip(),
                "cliente": str(item.get("nome_cliente") or "").strip(),
                "filial": str(item.get("filial") or "").strip(),
            }
            if not payload["userIds"] and not payload["permissionCodes"]:
                continue
            self._outbox.enqueue(
                event_type=event_type,
                aggregate_type=aggregate_type,
                aggregate_id=entry.line_key,
                payload=payload,
            )
            enqueued += 1
        return EnqueueReadyToInvoiceResult(detection=detection, enqueued=enqueued)


class PublishIntegrationOutboxUseCase:
    """Flush pending outbox rows to Minha Delpi notifications (multi-event)."""

    def __init__(
        self,
        *,
        outbox: IntegrationOutboxRepositoryPort,
        notifier: CommercialPortalNotificationService | None = None,
        content: type[ReadyToInvoiceNotificationContentService] | None = None,
    ) -> None:
        self._outbox = outbox
        self._notifier = notifier or CommercialPortalNotificationService()
        self._content = content or ReadyToInvoiceNotificationContentService

    def _publish_row(self, row) -> bool:
        from commercial_app.application.services.commercial_realtime_notify import (
            notify_ready_to_invoice_changed,
            notify_worklist_changed,
            portal_task_event_to_worklist_reason,
        )
        from commercial_app.application.services.task_portal_notification_delivery_policy import (
            TaskPortalNotificationDeliveryPolicy,
        )
        from commercial_app.domain.services.task_portal_notification_content_service import (
            TASK_PORTAL_EVENT_TYPES,
            TaskPortalNotificationContentService,
        )

        payload = row.payload if isinstance(row.payload, dict) else {}
        if not self._notifier.enabled:
            return True

        delivery = TaskPortalNotificationDeliveryPolicy()
        ready_event = self._content.event_type()
        if row.event_type == ready_event:
            all_user_ids = list(payload.get("userIds") or [])
            permission_codes = list(payload.get("permissionCodes") or [])
            online, offline = delivery.split_online_offline(ready_event, all_user_ids)
            # Toast: online sellers + always TEAM_ROOM (managers). Empty online with
            # only billing permission codes still fans out to team room.
            if online or permission_codes or all_user_ids:
                notify_ready_to_invoice_changed(
                    user_ids=online,
                    line_key=str(payload.get("lineKey") or row.aggregate_id),
                    pedido=str(payload.get("pedido") or ""),
                    linha=str(payload.get("linha") or ""),
                    cliente=str(payload.get("cliente") or ""),
                    filial=str(payload.get("filial") or ""),
                    action_target=str(payload.get("actionTarget") or "") or None,
                )
            if not offline and not permission_codes:
                return True
            return self._notifier.notify_ready_to_invoice(
                user_ids=offline,
                permission_codes=permission_codes,
                line_key=str(payload.get("lineKey") or row.aggregate_id),
                pedido=str(payload.get("pedido") or ""),
                linha=str(payload.get("linha") or ""),
                cliente=str(payload.get("cliente") or ""),
                filial=str(payload.get("filial") or ""),
                action_target=str(payload.get("actionTarget") or "") or None,
            )

        if row.event_type in TASK_PORTAL_EVENT_TYPES:
            all_user_ids = list(payload.get("userIds") or [])
            online, offline = delivery.split_online_offline(
                row.event_type, all_user_ids
            )
            ws_reason = portal_task_event_to_worklist_reason(row.event_type)
            if online and ws_reason is not None:
                title = str(payload.get("title") or "Tarefa")
                due_at = str(payload.get("dueAt") or "") or None
                message = TaskPortalNotificationContentService.format_message(
                    row.event_type, title=title, due_at_iso=due_at
                )
                notif_type = TaskPortalNotificationContentService.notification_type_for(
                    row.event_type
                )
                variant = (
                    notif_type
                    if notif_type in {"info", "success", "warning", "error"}
                    else "info"
                )
                notify_worklist_changed(
                    reason=ws_reason,
                    task_id=str(payload.get("taskId") or row.aggregate_id),
                    assignee_user_ids=online,
                    task_title=title,
                    notification_override={
                        "title": TaskPortalNotificationContentService.title_for(
                            row.event_type
                        ),
                        "message": message,
                        "variant": variant,
                    },
                )
            if not offline:
                return True
            return self._notifier.notify_task_event(
                event_type=row.event_type,
                user_ids=offline,
                task_id=str(payload.get("taskId") or row.aggregate_id),
                title=str(payload.get("title") or "Tarefa"),
                due_at=str(payload.get("dueAt") or "") or None,
                action_target=str(payload.get("actionTarget") or "") or None,
                dedupe_key=str(payload.get("dedupeKey") or "") or None,
                bucket=str(payload.get("bucket") or "") or None,
            )

        return False

    def execute(self, *, limit: int = 50) -> PublishOutboxResult:
        from commercial_app.domain.services.task_portal_notification_content_service import (
            TASK_PORTAL_EVENT_TYPES,
        )

        ready_event = self._content.event_type()
        supported = {ready_event, *TASK_PORTAL_EVENT_TYPES}
        pending = self._outbox.list_pending(limit=limit)
        processed = 0
        published = 0
        failed = 0
        for row in pending:
            processed += 1
            if row.event_type not in supported:
                self._outbox.mark_failed(
                    row.id, error=f"unsupported_event_type:{row.event_type}"
                )
                failed += 1
                continue
            ok = self._publish_row(row)
            if ok:
                self._outbox.mark_published(row.id)
                published += 1
            else:
                self._outbox.mark_failed(row.id, error="portal_notification_failed")
                failed += 1
        return PublishOutboxResult(
            processed=processed, published=published, failed=failed
        )


class ScanReadyToInvoiceNotificationsUseCase:
    """Ops job: detect → enqueue → publish."""

    def __init__(
        self,
        *,
        enqueue: EnqueueReadyToInvoiceNotificationsUseCase,
        publish: PublishIntegrationOutboxUseCase,
    ) -> None:
        self._enqueue = enqueue
        self._publish = publish

    def execute(self) -> dict[str, Any]:
        enqueued = self._enqueue.execute()
        published = self._publish.execute()
        return {
            "previousKeyCount": enqueued.detection.previous_key_count,
            "currentKeyCount": enqueued.detection.current_key_count,
            "enteredCount": len(enqueued.detection.entered),
            "enqueued": enqueued.enqueued,
            "outboxProcessed": published.processed,
            "outboxPublished": published.published,
            "outboxFailed": published.failed,
            "boardDeepLinkPath": enqueued.detection.board_deep_link_path,
        }

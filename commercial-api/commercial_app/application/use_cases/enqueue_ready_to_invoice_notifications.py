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
    """Flush pending outbox rows to Minha Delpi notifications."""

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

    def execute(self, *, limit: int = 50) -> PublishOutboxResult:
        ready_event = self._content.event_type()
        pending = self._outbox.list_pending(limit=limit)
        processed = 0
        published = 0
        failed = 0
        for row in pending:
            processed += 1
            if row.event_type != ready_event:
                self._outbox.mark_failed(
                    row.id, error=f"unsupported_event_type:{row.event_type}"
                )
                failed += 1
                continue
            payload = row.payload if isinstance(row.payload, dict) else {}
            if not self._notifier.enabled:
                self._outbox.mark_published(row.id)
                published += 1
                continue
            ok = self._notifier.notify_ready_to_invoice(
                user_ids=list(payload.get("userIds") or []),
                permission_codes=list(payload.get("permissionCodes") or []),
                line_key=str(payload.get("lineKey") or row.aggregate_id),
                pedido=str(payload.get("pedido") or ""),
                linha=str(payload.get("linha") or ""),
                cliente=str(payload.get("cliente") or ""),
                filial=str(payload.get("filial") or ""),
                action_target=str(payload.get("actionTarget") or "") or None,
            )
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

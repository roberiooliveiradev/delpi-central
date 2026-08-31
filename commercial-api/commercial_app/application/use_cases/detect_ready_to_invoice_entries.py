"""Detect newly ready-to-invoice open-order lines and persist snapshot keys."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any, Protocol

from commercial_app.domain.ports.integration_outbox_repository_port import (
    IntegrationCheckpointRepositoryPort,
)
from commercial_app.domain.services.ready_to_invoice_notification_content_service import (
    ReadyToInvoiceNotificationContentService,
)
from commercial_app.domain.services.ready_to_invoice_recipient_resolver_service import (
    ReadyToInvoiceRecipientResolverService,
    ReadyToInvoiceRecipients,
)
from commercial_app.domain.services.ready_to_invoice_snapshot_delta_service import (
    ReadyToInvoiceSnapshotDeltaService,
    open_order_line_key,
)


class _OpenOrdersGateway(Protocol):
    def list_open_orders(self, *, params: dict[str, Any] | None = None) -> dict[str, Any]:
        ...


@dataclass(frozen=True, slots=True)
class ReadyToInvoiceEntry:
    line_key: str
    item: dict[str, Any]
    recipients: ReadyToInvoiceRecipients


@dataclass(frozen=True, slots=True)
class DetectReadyToInvoiceResult:
    previous_key_count: int
    current_key_count: int
    entered: tuple[ReadyToInvoiceEntry, ...]
    board_deep_link_path: str


class DetectReadyToInvoiceEntriesUseCase:
    """Load open orders, diff ready_to_invoice snapshot, resolve recipients."""

    def __init__(
        self,
        *,
        gateway: _OpenOrdersGateway,
        checkpoints: IntegrationCheckpointRepositoryPort,
        delta_service: ReadyToInvoiceSnapshotDeltaService | None = None,
        recipient_resolver: ReadyToInvoiceRecipientResolverService | None = None,
        content: type[ReadyToInvoiceNotificationContentService] | None = None,
    ) -> None:
        self._gateway = gateway
        self._checkpoints = checkpoints
        self._delta = delta_service or ReadyToInvoiceSnapshotDeltaService()
        self._recipients = recipient_resolver or ReadyToInvoiceRecipientResolverService()
        self._content = content or ReadyToInvoiceNotificationContentService

    def execute(self, *, persist_snapshot: bool = True) -> DetectReadyToInvoiceResult:
        source_key = self._content.checkpoint_source_key()
        checkpoint = self._checkpoints.get_by_source_key(source_key)
        previous_keys = []
        if checkpoint and isinstance(checkpoint.metadata, dict):
            raw_keys = checkpoint.metadata.get("keys")
            if isinstance(raw_keys, list):
                previous_keys = [str(key) for key in raw_keys]

        payload = self._gateway.list_open_orders()
        data = payload.get("data", payload) if isinstance(payload, dict) else {}
        items_raw = data.get("items") if isinstance(data, dict) else None
        items = (
            [item for item in items_raw if isinstance(item, dict)]
            if isinstance(items_raw, list)
            else []
        )

        delta = self._delta.compute_delta(items=items, previous_keys=previous_keys)

        entered: list[ReadyToInvoiceEntry] = []
        for item in delta.entered_items:
            key = str(item.get("_lineKey") or open_order_line_key(item))
            recipients = self._recipients.resolve_for_item(item)
            clean = {k: v for k, v in item.items() if k != "_lineKey"}
            entered.append(
                ReadyToInvoiceEntry(
                    line_key=key,
                    item=clean,
                    recipients=recipients,
                )
            )

        if persist_snapshot:
            self._checkpoints.upsert_metadata(
                source_key=source_key,
                metadata={
                    "keys": sorted(delta.current_keys),
                    "keyCount": len(delta.current_keys),
                },
                cursor_value=str(len(delta.current_keys)),
            )

        return DetectReadyToInvoiceResult(
            previous_key_count=len(delta.previous_keys),
            current_key_count=len(delta.current_keys),
            entered=tuple(entered),
            board_deep_link_path=self._content.board_deep_link_path(),
        )

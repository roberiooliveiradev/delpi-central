"""Resolve notification recipients for ready_to_invoice entries.

Audience is **permission-only**: `commercial.billing.notify` (declarative JSON).
Portfolio owners/members are **not** notified by membership alone.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any, Mapping, Sequence

from commercial_app.domain.services.ready_to_invoice_notification_content_service import (
    ReadyToInvoiceNotificationContentService,
)


@dataclass(frozen=True, slots=True)
class ReadyToInvoiceRecipients:
    """Destinatários do evento pronto para faturar.

    `seller_user_ids` / `billing_user_ids` ficam vazios — a audiência canônica
    é `billing_permission_codes` (expansão no Core / preferências).
    """

    seller_user_ids: frozenset[str]
    billing_user_ids: frozenset[str]
    billing_permission_codes: tuple[str, ...]

    @property
    def all_user_ids(self) -> frozenset[str]:
        return self.seller_user_ids | self.billing_user_ids


class ReadyToInvoiceRecipientResolverService:
    """Resolve recipients from declarative billing permission codes only."""

    def __init__(
        self,
        *,
        billing_permission_codes: Sequence[str] | None = None,
    ) -> None:
        content = ReadyToInvoiceNotificationContentService
        self._billing_permission_codes = tuple(
            str(code).strip()
            for code in (
                billing_permission_codes
                if billing_permission_codes is not None
                else content.billing_permission_codes()
            )
            if str(code).strip()
        )

    def resolve_for_item(
        self,
        item: Mapping[str, Any] | None = None,
    ) -> ReadyToInvoiceRecipients:
        _ = item  # linha disponível para regras futuras; audiência atual = só RBAC
        return ReadyToInvoiceRecipients(
            seller_user_ids=frozenset(),
            billing_user_ids=frozenset(),
            billing_permission_codes=self._billing_permission_codes,
        )

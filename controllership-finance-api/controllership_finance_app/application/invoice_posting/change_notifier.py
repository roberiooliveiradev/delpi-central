"""Port de aviso do LNF. O domain não importa este módulo.

O use case chama o port depois que o repositório retornou (o commit já
aconteceu). O adapter é quem engole falha de emissão.
"""

from __future__ import annotations

import logging
import os
import re
import sys
from typing import Protocol

logger = logging.getLogger(__name__)

REQUEST_CHANGED = "lnf.request.changed"
QUEUE_RECONCILED = "lnf.queue.reconciled"
UNMAPPED_CHANGED = "lnf.unmapped-products.changed"

REQUEST_REASONS = frozenset(
    {
        "created",
        "updated",
        "status_changed",
        "cancelled",
        "manual_posted",
        "purchase_order_linked",
        "comment_added",
        "reconciled",
    }
)
ACTOR_ORIGINS = frozenset({"user", "system"})


class InvoicePostingChangeNotifier(Protocol):
    def request_changed(
        self,
        *,
        branch: str,
        request_id: str,
        reason: str,
        actor_origin: str,
    ) -> None: ...

    def queue_reconciled(self, *, branch: str, updated_count: int) -> None: ...

    def unmapped_products_changed(self) -> None: ...


class NoOpInvoicePostingChangeNotifier:
    def request_changed(
        self,
        *,
        branch: str,
        request_id: str,
        reason: str,
        actor_origin: str,
    ) -> None:
        return None

    def queue_reconciled(self, *, branch: str, updated_count: int) -> None:
        return None

    def unmapped_products_changed(self) -> None:
        return None


class SafeInvoicePostingChangeNotifier:
    """Falha de emissão não muda o HTTP. O log não leva token, nome nem valor."""

    def __init__(self, inner: InvoicePostingChangeNotifier) -> None:
        self._inner = inner

    def request_changed(
        self,
        *,
        branch: str,
        request_id: str,
        reason: str,
        actor_origin: str,
    ) -> None:
        self._call(
            self._inner.request_changed,
            branch=branch,
            request_id=request_id,
            reason=reason,
            actor_origin=actor_origin,
        )

    def queue_reconciled(self, *, branch: str, updated_count: int) -> None:
        self._call(
            self._inner.queue_reconciled,
            branch=branch,
            updated_count=updated_count,
        )

    def unmapped_products_changed(self) -> None:
        self._call(self._inner.unmapped_products_changed)

    def _call(self, fn, **kwargs) -> None:
        try:
            fn(**kwargs)
        except Exception as exc:  # noqa: BLE001
            logger.warning(
                "lnf_realtime_notify_failed error_type=%s",
                type(exc).__name__,
            )


_notifier: InvoicePostingChangeNotifier = SafeInvoicePostingChangeNotifier(
    NoOpInvoicePostingChangeNotifier()
)


def get_invoice_posting_change_notifier() -> InvoicePostingChangeNotifier:
    return _notifier


def set_invoice_posting_change_notifier(
    notifier: InvoicePostingChangeNotifier,
) -> None:
    global _notifier
    _notifier = notifier


def reset_invoice_posting_change_notifier() -> None:
    set_invoice_posting_change_notifier(
        SafeInvoicePostingChangeNotifier(NoOpInvoicePostingChangeNotifier())
    )


def realtime_process_is_single() -> bool:
    """True quando não há sinal confiável de workers > 1.

    Réplicas de orquestrador fora do processo não aparecem aqui. Esse caso
    fica documentado: a flag tem de estar off até existir broker.
    """
    for key in ("WEB_CONCURRENCY", "UVICORN_WORKERS"):
        raw = (os.environ.get(key) or "").strip()
        if raw.isdigit() and int(raw) > 1:
            return False
    match = re.search(r"--workers(?:=|\s+)(\d+)", " ".join(sys.argv))
    if match and int(match.group(1)) > 1:
        return False
    return True


def lnf_realtime_should_mount(*, hosted: bool, realtime: bool) -> bool:
    return bool(hosted and realtime and realtime_process_is_single())


def configure_invoice_posting_realtime(*, enabled: bool) -> bool:
    """Liga o hub só com a flag e um processo. Devolve se o hub ficou ativo."""
    if not enabled:
        reset_invoice_posting_change_notifier()
        return False
    if not realtime_process_is_single():
        logger.error(
            "lnf_realtime_disabled_multiple_workers "
            "hub em memória exige 1 processo; broker ainda não existe"
        )
        reset_invoice_posting_change_notifier()
        return False
    from controllership_finance_app.infrastructure.invoice_posting.realtime_hub import (
        InMemoryInvoicePostingRealtimeHub,
        set_invoice_posting_realtime_hub,
    )

    hub = InMemoryInvoicePostingRealtimeHub()
    set_invoice_posting_realtime_hub(hub)
    set_invoice_posting_change_notifier(SafeInvoicePostingChangeNotifier(hub))
    return True


def emit_request_changed(row: dict | None, *, reason: str, actor_origin: str) -> None:
    if reason not in REQUEST_REASONS or actor_origin not in ACTOR_ORIGINS:
        return
    branch = str((row or {}).get("branch_code") or "").strip()
    request_id = str((row or {}).get("id") or "").strip()
    if not branch or not request_id:
        return
    get_invoice_posting_change_notifier().request_changed(
        branch=branch,
        request_id=request_id,
        reason=reason,
        actor_origin=actor_origin,
    )

"""Content loader for ready-to-invoice notification settings."""

from __future__ import annotations

import json
from functools import lru_cache
from pathlib import Path
from typing import Any
from urllib.parse import parse_qsl, urlencode, urlsplit, urlunsplit


_CONTENT_PATH = (
    Path(__file__).resolve().parents[2]
    / "content"
    / "pt-BR"
    / "ready_to_invoice_notification.json"
)

_DEFAULT_DEEP_LINK = "/apps/commercial/open-orders?stage=ready_to_invoice"


@lru_cache(maxsize=1)
def _load() -> dict[str, Any]:
    with _CONTENT_PATH.open(encoding="utf-8") as handle:
        payload = json.load(handle)
    return payload if isinstance(payload, dict) else {}


def _merge_query(path: str, **params: str) -> str:
    """Merge query params into a path; does not force view= (respeita layout do usuário)."""
    split = urlsplit(path)
    query = dict(parse_qsl(split.query, keep_blank_values=True))
    # Never force layout — MFE usa persistência local do usuário.
    query.pop("view", None)
    for key, value in params.items():
        cleaned = str(value or "").strip()
        if cleaned:
            query[key] = cleaned
        else:
            query.pop(key, None)
    return urlunsplit(
        (split.scheme, split.netloc, split.path, urlencode(query), split.fragment)
    )


class ReadyToInvoiceNotificationContentService:
    """Declarative settings for ready-to-invoice detection / notify."""

    @classmethod
    def raw(cls) -> dict[str, Any]:
        return dict(_load())

    @classmethod
    def checkpoint_source_key(cls) -> str:
        value = str(_load().get("checkpointSourceKey") or "").strip()
        return value or "commercial.open_orders.ready_to_invoice"

    @classmethod
    def deep_link_path(cls) -> str:
        """Base deep link sem forçar view=board (layout = preferência do usuário)."""
        raw = _load()
        value = str(
            raw.get("deepLinkPath") or raw.get("boardDeepLinkPath") or ""
        ).strip()
        if not value:
            return _DEFAULT_DEEP_LINK
        return _merge_query(value)

    @classmethod
    def board_deep_link_path(cls) -> str:
        """Alias legado — mesmo que deep_link_path (sem forçar board)."""
        return cls.deep_link_path()

    @classmethod
    def build_deep_link_path(
        cls,
        *,
        pedido: str = "",
        linha: str = "",
        filial: str = "",
    ) -> str:
        """Deep link com filtros de pedido/filial; stage pronto para faturar; sem view."""
        extras: dict[str, str] = {"stage": "ready_to_invoice"}
        pedido_s = str(pedido or "").strip()
        filial_s = str(filial or "").strip()
        if pedido_s:
            extras["q"] = pedido_s
        if filial_s:
            extras["branch"] = filial_s
        # linha fica no metadata / mensagem; busca por pedido já filtra a lista
        _ = linha
        return _merge_query(cls.deep_link_path(), **extras)

    @classmethod
    def without_forced_view(cls, path: str) -> str:
        """Remove view= da URL para respeitar o layout persistido no MFE."""
        return _merge_query(path or _DEFAULT_DEEP_LINK)

    @classmethod
    def event_type(cls) -> str:
        value = str(_load().get("eventType") or "").strip()
        return value or "commercial.order.ready_to_invoice"

    @classmethod
    def aggregate_type(cls) -> str:
        value = str(_load().get("aggregateType") or "").strip()
        return value or "open_order_line"

    @classmethod
    def billing_user_ids(cls) -> tuple[str, ...]:
        raw = _load().get("billingUserIds")
        if not isinstance(raw, list):
            return ()
        return tuple(str(item).strip() for item in raw if str(item).strip())

    @classmethod
    def billing_permission_codes(cls) -> tuple[str, ...]:
        raw = _load().get("billingPermissionCodes")
        if not isinstance(raw, list):
            return ()
        return tuple(str(item).strip() for item in raw if str(item).strip())

    @classmethod
    def notification_block(cls) -> dict[str, Any]:
        block = _load().get("notification")
        return dict(block) if isinstance(block, dict) else {}

    @classmethod
    def outbox_default_backoff_seconds(cls) -> int:
        return cls._outbox_int("defaultBackoffSeconds", 60)

    @classmethod
    def outbox_rate_limit_backoff_seconds(cls) -> int:
        return cls._outbox_int("rateLimitBackoffSeconds", 120)

    @classmethod
    def _outbox_int(cls, key: str, default: int) -> int:
        block = _load().get("outbox")
        if not isinstance(block, dict):
            return default
        raw = block.get(key)
        try:
            value = int(raw)
        except (TypeError, ValueError):
            return default
        return max(1, value)

    @classmethod
    def format_message(cls, *, pedido: str, linha: str, cliente: str) -> str:
        block = cls.notification_block()
        template = str(block.get("messageTemplate") or "").strip()
        if not template:
            template = (
                "A linha {pedido}/{linha} do cliente {cliente} "
                "entrou em Pronto para faturar."
            )
        return template.format(pedido=pedido, linha=linha, cliente=cliente)

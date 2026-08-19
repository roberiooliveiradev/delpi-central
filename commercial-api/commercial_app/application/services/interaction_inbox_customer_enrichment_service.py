"""Batch customer fields for interaction inbox cards."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any, Protocol


class OpenOrdersGateway(Protocol):
    def list_open_orders(self, *, params: dict[str, Any] | None = None) -> dict[str, Any]:
        ...


@dataclass(frozen=True)
class InboxCustomerFields:
    customer_code: str | None = None
    customer_store: str | None = None
    customer_name: str | None = None


def parse_entity_key(entity_key: str | None) -> tuple[str, str] | None:
    raw = (entity_key or "").strip()
    if "|" not in raw:
        return None
    left, right = raw.split("|", 1)
    left, right = left.strip(), right.strip()
    if not left or not right:
        return None
    return left, right


def _order_index(payload: dict[str, Any]) -> dict[tuple[str, str], InboxCustomerFields]:
    data = payload.get("data") if isinstance(payload.get("data"), dict) else payload
    items = data.get("items") if isinstance(data, dict) else None
    if not isinstance(items, list):
        return {}
    index: dict[tuple[str, str], InboxCustomerFields] = {}
    for item in items:
        if not isinstance(item, dict):
            continue
        branch = str(item.get("filial") or item.get("branch") or "").strip()
        order = str(item.get("pedido") or item.get("order") or "").strip()
        if not branch or not order:
            continue
        code = str(
            item.get("customer_code") or item.get("codigo_cliente") or ""
        ).strip() or None
        store = str(
            item.get("customer_store") or item.get("loja") or item.get("loja_cliente") or ""
        ).strip() or None
        name = str(
            item.get("nome_cliente")
            or item.get("customer_name")
            or item.get("cliente_nome")
            or ""
        ).strip() or None
        index[(branch, order)] = InboxCustomerFields(
            customer_code=code,
            customer_store=store,
            customer_name=name,
        )
    return index


class InteractionInboxCustomerEnrichmentService:
    """Maps entity rooms to customer identity without N+1 in the MFE."""

    def __init__(self, gateway: OpenOrdersGateway | None = None) -> None:
        self._gateway = gateway

    def enrich(
        self,
        *,
        entity_type: str | None,
        entity_key: str | None,
        order_index: dict[tuple[str, str], InboxCustomerFields] | None = None,
    ) -> InboxCustomerFields:
        kind = (entity_type or "").strip().lower()
        parsed = parse_entity_key(entity_key)
        if kind == "customer" and parsed:
            return InboxCustomerFields(
                customer_code=parsed[0],
                customer_store=parsed[1],
                customer_name=None,
            )
        if kind == "order" and parsed and order_index is not None:
            return order_index.get(parsed, InboxCustomerFields())
        return InboxCustomerFields()

    def load_order_index(self) -> dict[tuple[str, str], InboxCustomerFields]:
        if self._gateway is None:
            return {}
        try:
            payload = self._gateway.list_open_orders()
        except Exception:
            return {}
        if not isinstance(payload, dict):
            return {}
        try:
            return _order_index(payload)
        except Exception:
            return {}

"""Prévia/unfurl de menção — fail-closed (card opaco sem membership)."""

from __future__ import annotations

from typing import Any, Protocol, Sequence

from commercial_app.application.services.filter_open_orders_by_scope_service import (
    FilterOpenOrdersByScopeService,
)
from commercial_app.application.services.resolve_commercial_customer_scope_service import (
    CommercialCustomerScope,
    ResolveCommercialCustomerScopeService,
)
from commercial_app.application.use_cases.suggest_interaction_mentions import (
    CrmMentionSearchPort,
    _unwrap_items,
)
from commercial_app.domain.ports.seller_portfolio_repository_port import (
    SellerPortfolioRepositoryPort,
)
from commercial_app.domain.services.interaction_mention_kinds_content_service import (
    InteractionMentionKindsContentService,
)
from commercial_app.domain.services.interaction_room_content_service import (
    InteractionRoomContentService,
)


class DirectoryUserLookupPort(Protocol):
    def lookup_directory_users(
        self,
        user_ids: Sequence[str],
    ) -> dict[str, dict[str, str]]:
        ...


def _ref_str(ref: dict[str, Any], *keys: str) -> str:
    for key in keys:
        value = str(ref.get(key) or "").strip()
        if value:
            return value
    return ""


class PreviewInteractionEntityUseCase:
    """Card de unfurl: accessible=false sem vazar valor quando faltar RBAC."""

    def __init__(
        self,
        directory: DirectoryUserLookupPort,
        *,
        portfolios: SellerPortfolioRepositoryPort | None = None,
        scope: ResolveCommercialCustomerScopeService | None = None,
        gateway: CrmMentionSearchPort | None = None,
    ) -> None:
        self._directory = directory
        self._portfolios = portfolios
        self._scope = scope
        self._gateway = gateway
        self._order_filter = FilterOpenOrdersByScopeService()

    def preview(
        self,
        *,
        kind: str,
        ref: dict[str, Any] | None,
        actor_user_id: str | None = None,
        unrestricted: bool = False,
    ) -> dict[str, Any]:
        kind_id = str(kind or "").strip()
        meta = InteractionMentionKindsContentService.get(kind_id)
        if meta is None:
            raise ValueError(InteractionRoomContentService.error("kindUnknown"))
        href_strategy = str(meta.get("hrefStrategy") or "")
        clean_ref = {
            str(key): value
            for key, value in (ref or {}).items()
            if str(key).strip()
        }
        if kind_id not in InteractionMentionKindsContentService.preview_enabled_ids():
            return self._opaque(kind=kind_id, href_strategy=href_strategy, ref=clean_ref)
        scope = self._customer_scope(
            actor_user_id=actor_user_id,
            unrestricted=unrestricted,
        )
        handlers = {
            "user": self._preview_user,
            "customer": self._preview_customer,
            "portfolio": self._preview_portfolio,
            "order": self._preview_order,
            "product": self._preview_product,
            "production_order": self._preview_production_order,
            "opportunity": self._preview_opportunity,
            "otd_line": self._preview_otd_line,
            "invoice": self._preview_invoice,
        }
        handler = handlers.get(kind_id)
        if handler is None:
            return self._opaque(kind=kind_id, href_strategy=href_strategy, ref=clean_ref)
        try:
            card = handler(
                ref=clean_ref,
                href_strategy=href_strategy,
                actor_user_id=actor_user_id,
                unrestricted=unrestricted,
                scope=scope,
            )
        except Exception:
            return self._opaque(kind=kind_id, href_strategy=href_strategy, ref=clean_ref)
        if not isinstance(card, dict) or not card.get("accessible"):
            return self._opaque(kind=kind_id, href_strategy=href_strategy, ref=clean_ref)
        return card

    def _opaque(
        self,
        *,
        kind: str,
        href_strategy: str,
        ref: dict[str, Any],
    ) -> dict[str, Any]:
        return {
            "kind": kind,
            "accessible": False,
            "label": InteractionRoomContentService.message("previewDenied"),
            "subtitle": "",
            "hrefStrategy": href_strategy,
            "ref": ref,
            "fields": {},
        }

    def _ok(
        self,
        *,
        kind: str,
        href_strategy: str,
        ref: dict[str, Any],
        label: str,
        subtitle: str = "",
        fields: dict[str, Any] | None = None,
    ) -> dict[str, Any]:
        return {
            "kind": kind,
            "accessible": True,
            "label": label,
            "subtitle": subtitle,
            "hrefStrategy": href_strategy,
            "ref": ref,
            "fields": fields or {},
        }

    def _customer_scope(
        self,
        *,
        actor_user_id: str | None,
        unrestricted: bool,
    ) -> CommercialCustomerScope | None:
        if self._scope is None:
            return None
        try:
            return self._scope.execute(
                user_id=(actor_user_id or "").strip(),
                unrestricted=unrestricted,
            )
        except Exception:
            return None

    def _preview_user(
        self,
        *,
        ref: dict[str, Any],
        href_strategy: str,
        actor_user_id: str | None,
        unrestricted: bool,
        scope: CommercialCustomerScope | None,
    ) -> dict[str, Any] | None:
        user_id = _ref_str(ref, "user_id")
        if not user_id:
            return None
        try:
            found = self._directory.lookup_directory_users([user_id])
        except Exception:
            return None
        user = found.get(user_id)
        if not user:
            return None
        name = str(user.get("name") or user_id).strip()
        email = str(user.get("email") or "").strip()
        return self._ok(
            kind="user",
            href_strategy=href_strategy,
            ref={"user_id": user_id},
            label=name,
            subtitle=email,
        )

    def _preview_customer(
        self,
        *,
        ref: dict[str, Any],
        href_strategy: str,
        actor_user_id: str | None,
        unrestricted: bool,
        scope: CommercialCustomerScope | None,
    ) -> dict[str, Any] | None:
        code = _ref_str(ref, "customer_code", "code")
        store = _ref_str(ref, "customer_store", "store")
        if not code or not store or scope is None or not scope.allows(code, store):
            return None
        name = _ref_str(ref, "customer_name", "name")
        if not name and self._gateway is not None:
            try:
                payload = self._gateway.search_active_customers(
                    params={"q": code, "page": 1, "page_size": 20}
                )
                for item in _unwrap_items(payload):
                    item_code = str(item.get("code") or item.get("customer_code") or "").strip()
                    item_store = str(item.get("store") or item.get("customer_store") or "").strip()
                    if item_code == code and item_store == store:
                        name = str(item.get("name") or item.get("customer_name") or "").strip()
                        break
            except Exception:
                name = ""
        return self._ok(
            kind="customer",
            href_strategy=href_strategy,
            ref={"customer_code": code, "customer_store": store},
            label=name or code,
            subtitle=f"{code}/{store}",
        )

    def _preview_portfolio(
        self,
        *,
        ref: dict[str, Any],
        href_strategy: str,
        actor_user_id: str | None,
        unrestricted: bool,
        scope: CommercialCustomerScope | None,
    ) -> dict[str, Any] | None:
        portfolio_id = _ref_str(ref, "portfolio_id")
        if not portfolio_id or self._portfolios is None:
            return None
        portfolio = self._portfolios.get_by_id(portfolio_id)
        if portfolio is None or not portfolio.active:
            return None
        actor = (actor_user_id or "").strip()
        if not unrestricted:
            members = {portfolio.user_id} | {m.user_id for m in portfolio.members}
            if actor not in members:
                return None
        label = (portfolio.display_name or "").strip() or portfolio.id
        return self._ok(
            kind="portfolio",
            href_strategy=href_strategy,
            ref={"portfolio_id": portfolio.id},
            label=label,
        )

    def _preview_order(
        self,
        *,
        ref: dict[str, Any],
        href_strategy: str,
        actor_user_id: str | None,
        unrestricted: bool,
        scope: CommercialCustomerScope | None,
    ) -> dict[str, Any] | None:
        branch = _ref_str(ref, "branch", "filial")
        order = _ref_str(ref, "order", "pedido")
        if not branch or not order or self._gateway is None or scope is None:
            return None
        try:
            payload = self._gateway.list_open_orders()
            data = payload.get("data") if isinstance(payload.get("data"), dict) else payload
            filtered = self._order_filter.apply(
                data if isinstance(data, dict) else {},
                scope.for_open_orders(),
            )
        except Exception:
            return None
        items = filtered.get("items") if isinstance(filtered, dict) else None
        if not isinstance(items, list):
            return None
        for item in items:
            if not isinstance(item, dict):
                continue
            item_branch = str(item.get("filial") or item.get("branch") or "").strip()
            item_order = str(item.get("pedido") or item.get("order") or "").strip()
            if item_branch != branch or item_order != order:
                continue
            name = str(
                item.get("nome_cliente")
                or item.get("cliente")
                or item.get("customer_name")
                or ""
            ).strip()
            return self._ok(
                kind="order",
                href_strategy=href_strategy,
                ref={"branch": branch, "order": order},
                label=order,
                subtitle=f"{branch} · {name}".strip(" ·"),
            )
        return None

    def _preview_product(
        self,
        *,
        ref: dict[str, Any],
        href_strategy: str,
        actor_user_id: str | None,
        unrestricted: bool,
        scope: CommercialCustomerScope | None,
    ) -> dict[str, Any] | None:
        code = _ref_str(ref, "product_code", "code")
        if not code or self._gateway is None:
            return None
        try:
            detail = self._gateway.get_product(f"/{code}/factory-status")
        except Exception:
            return None
        data = detail.get("data") if isinstance(detail.get("data"), dict) else detail
        if not isinstance(data, dict):
            return None
        product_code = str(
            data.get("product_code") or data.get("code") or data.get("productCode") or code
        ).strip()
        name = str(
            data.get("description")
            or data.get("name")
            or data.get("product_description")
            or ""
        ).strip()
        return self._ok(
            kind="product",
            href_strategy=href_strategy,
            ref={"product_code": product_code},
            label=name or product_code,
            subtitle=product_code,
            fields={
                key: data[key]
                for key in ("um", "unit", "status", "structure_status")
                if key in data
            },
        )

    def _preview_production_order(
        self,
        *,
        ref: dict[str, Any],
        href_strategy: str,
        actor_user_id: str | None,
        unrestricted: bool,
        scope: CommercialCustomerScope | None,
    ) -> dict[str, Any] | None:
        op = _ref_str(ref, "production_order", "op")
        if not op or self._gateway is None:
            return None
        try:
            payload = self._gateway.get_production(f"/orders/by-op/{op}")
        except Exception:
            return None
        data = payload.get("data") if isinstance(payload.get("data"), dict) else payload
        if not isinstance(data, dict):
            return None
        production_order = str(
            data.get("op")
            or data.get("production_order")
            or data.get("productionOrder")
            or op
        ).strip()
        branch = str(data.get("branch") or data.get("filial") or _ref_str(ref, "branch") or "").strip()
        return self._ok(
            kind="production_order",
            href_strategy=href_strategy,
            ref={"production_order": production_order, "branch": branch or None},
            label=production_order,
            subtitle=branch,
        )

    def _preview_opportunity(
        self,
        *,
        ref: dict[str, Any],
        href_strategy: str,
        actor_user_id: str | None,
        unrestricted: bool,
        scope: CommercialCustomerScope | None,
    ) -> dict[str, Any] | None:
        number = _ref_str(ref, "proposal_number", "opportunity", "numero")
        if not number or self._gateway is None:
            return None
        try:
            payload = self._gateway.get_commercial_analytics(
                "/proposals",
                params={"search": number, "page": 1, "page_size": 20},
            )
        except Exception:
            return None
        for item in _unwrap_items(payload):
            item_number = str(
                item.get("proposal_number")
                or item.get("proposalNumber")
                or item.get("numero")
                or item.get("id")
                or ""
            ).strip()
            if item_number != number:
                continue
            if not self._in_customer_scope(item, scope):
                return None
            name = str(item.get("customer_name") or item.get("cliente") or "").strip()
            return self._ok(
                kind="opportunity",
                href_strategy=href_strategy,
                ref={"proposal_number": number},
                label=number,
                subtitle=name,
            )
        return None

    def _preview_otd_line(
        self,
        *,
        ref: dict[str, Any],
        href_strategy: str,
        actor_user_id: str | None,
        unrestricted: bool,
        scope: CommercialCustomerScope | None,
    ) -> dict[str, Any] | None:
        branch = _ref_str(ref, "branch", "filial")
        order = _ref_str(ref, "order", "pedido", "order_number")
        line = _ref_str(ref, "line", "linha", "line_item")
        if not branch or not order or not line or self._gateway is None:
            return None
        try:
            payload = self._gateway.get_commercial_analytics(
                "/sales-order-otd/panel",
                params={"search": order, "page": 1, "page_size": 50},
            )
        except Exception:
            return None
        for item in _unwrap_items(payload):
            item_branch = str(item.get("branch") or item.get("filial") or "").strip()
            item_order = str(
                item.get("order_number") or item.get("pedido") or item.get("order") or ""
            ).strip()
            item_line = str(
                item.get("line_item") or item.get("linha") or item.get("line") or ""
            ).strip()
            if item_branch != branch or item_order != order or item_line != line:
                continue
            if not self._in_customer_scope(item, scope):
                return None
            return self._ok(
                kind="otd_line",
                href_strategy=href_strategy,
                ref={"branch": branch, "order": order, "line": line},
                label=f"{order}/{line}",
                subtitle=branch,
            )
        return None

    def _preview_invoice(
        self,
        *,
        ref: dict[str, Any],
        href_strategy: str,
        actor_user_id: str | None,
        unrestricted: bool,
        scope: CommercialCustomerScope | None,
    ) -> dict[str, Any] | None:
        branch = _ref_str(ref, "branch", "filial")
        invoice = _ref_str(ref, "invoice", "invoice_number", "nota")
        series = _ref_str(ref, "series", "serie")
        if not branch or not invoice or not series or self._gateway is None:
            return None
        try:
            payload = self._gateway.get_outbound_invoice(
                branch=branch,
                invoice_number=invoice,
                invoice_series=series,
            )
        except Exception:
            return None
        data = payload.get("data") if isinstance(payload.get("data"), dict) else payload
        if not isinstance(data, dict):
            return None
        if not self._in_customer_scope(data, scope):
            # Sem cliente no payload: só libera se irrestrito
            if scope is None:
                return None
            if not (scope.unrestricted or scope.allowed_customers is None):
                return None
        return self._ok(
            kind="invoice",
            href_strategy=href_strategy,
            ref={"branch": branch, "invoice": invoice, "series": series},
            label=invoice,
            subtitle=f"{branch} {series}".strip(),
        )

    def _in_customer_scope(
        self,
        item: dict[str, Any],
        scope: CommercialCustomerScope | None,
    ) -> bool:
        if scope is None:
            return False
        if scope.unrestricted or scope.allowed_customers is None:
            return True
        code = str(
            item.get("customer_code")
            or item.get("codigo_cadastro")
            or item.get("codigo")
            or ""
        ).strip()
        store = str(
            item.get("customer_store")
            or item.get("loja_cadastro")
            or item.get("loja")
            or ""
        ).strip()
        if not code or not store:
            return False
        return scope.allows(code, store)

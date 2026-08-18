from __future__ import annotations

from typing import Any, Protocol, Sequence

from commercial_app.application.services.filter_open_orders_by_scope_service import (
    FilterOpenOrdersByScopeService,
)
from commercial_app.application.services.resolve_commercial_customer_scope_service import (
    CommercialCustomerScope,
    ResolveCommercialCustomerScopeService,
)
from commercial_app.domain.ports.seller_portfolio_repository_port import (
    SellerPortfolioRepositoryPort,
)
from commercial_app.domain.services.interaction_mention_kinds_content_service import (
    InteractionMentionKindsContentService,
)


class DirectoryUserSearchPort(Protocol):
    def search_directory_users(
        self,
        *,
        query: str | None = None,
        limit: int = 20,
        browse: bool = False,
    ) -> list[dict[str, str]]:
        ...


class CrmMentionSearchPort(Protocol):
    def search_active_customers(self, *, params: dict[str, Any] | None = None) -> dict[str, Any]:
        ...

    def list_open_orders(self, *, params: dict[str, Any] | None = None) -> dict[str, Any]:
        ...

    def get_product(self, path: str, *, params: dict[str, Any] | None = None) -> dict[str, Any]:
        ...

    def get_production(self, path: str, *, params: dict[str, Any] | None = None) -> dict[str, Any]:
        ...

    def get_commercial_analytics(
        self,
        path: str,
        *,
        params: dict[str, Any] | None = None,
    ) -> dict[str, Any]:
        ...

    def list_customer_outbound_invoices(
        self,
        *,
        customer_code: str,
        customer_store: str,
        params: dict[str, Any] | None = None,
    ) -> dict[str, Any]:
        ...

    def get_outbound_invoice(
        self,
        *,
        branch: str,
        invoice_number: str,
        invoice_series: str,
    ) -> dict[str, Any]:
        ...


def _needle(query: str) -> str:
    return (query or "").strip().lower()


def _matches(query: str, *parts: str) -> bool:
    needle = _needle(query)
    if not needle:
        return True
    haystack = " ".join(part for part in parts if part).lower()
    return needle in haystack


def _unwrap_items(payload: dict[str, Any] | None) -> list[dict[str, Any]]:
    if not isinstance(payload, dict):
        return []
    data = payload.get("data") if isinstance(payload.get("data"), dict) else payload
    if not isinstance(data, dict):
        return []
    items = data.get("items")
    if not isinstance(items, list):
        return []
    return [item for item in items if isinstance(item, dict)]


class SuggestInteractionMentionsUseCase:
    """Sugestões de @ — kinds só do catálogo; CRM com membership; fail-closed."""

    def __init__(
        self,
        directory: DirectoryUserSearchPort,
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

    def suggest(
        self,
        *,
        query: str,
        kinds: Sequence[str] | None = None,
        limit: int = 20,
        actor_user_id: str | None = None,
        unrestricted: bool = False,
    ) -> list[dict[str, Any]]:
        requested = [
            str(item).strip()
            for item in (kinds or ("user",))
            if str(item).strip()
        ]
        if not requested:
            requested = ["user"]
        known = InteractionMentionKindsContentService.kind_ids()
        enabled = InteractionMentionKindsContentService.suggest_enabled_ids()
        wanted = [kind for kind in requested if kind in known and kind in enabled]
        cap = max(1, min(int(limit or 20), 20))
        items: list[dict[str, Any]] = []
        if "user" in wanted:
            items.extend(self._suggest_users(query=query, limit=cap))
        remaining = cap - len(items)
        crm_kinds = [kind for kind in ("customer", "portfolio", "order") if kind in wanted]
        if remaining > 0 and crm_kinds:
            items.extend(
                self._suggest_crm(
                    query=query,
                    kinds=crm_kinds,
                    limit=remaining,
                    actor_user_id=actor_user_id,
                    unrestricted=unrestricted,
                )
            )
        remaining = cap - len(items)
        ops_kinds = [
            kind
            for kind in (
                "product",
                "production_order",
                "opportunity",
                "otd_line",
                "invoice",
            )
            if kind in wanted
        ]
        if remaining > 0 and ops_kinds:
            items.extend(
                self._suggest_ops(
                    query=query,
                    kinds=ops_kinds,
                    limit=remaining,
                    actor_user_id=actor_user_id,
                    unrestricted=unrestricted,
                )
            )
        return items[:cap]

    def _suggest_users(self, *, query: str, limit: int) -> list[dict[str, Any]]:
        try:
            users = self._directory.search_directory_users(
                query=query,
                limit=limit,
                browse=not bool((query or "").strip()),
            )
        except Exception:
            return []
        out: list[dict[str, Any]] = []
        for user in users:
            user_id = str(user.get("id") or "").strip()
            if not user_id:
                continue
            name = str(user.get("name") or user_id).strip()
            email = str(user.get("email") or "").strip()
            out.append(
                {
                    "kind": "user",
                    "label": name,
                    "subtitle": email,
                    "ref": {"user_id": user_id},
                }
            )
        return out

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

    def _suggest_crm(
        self,
        *,
        query: str,
        kinds: Sequence[str],
        limit: int,
        actor_user_id: str | None,
        unrestricted: bool,
    ) -> list[dict[str, Any]]:
        scope = self._customer_scope(
            actor_user_id=actor_user_id,
            unrestricted=unrestricted,
        )
        out: list[dict[str, Any]] = []
        if "customer" in kinds:
            out.extend(self._suggest_customers(query=query, limit=limit, scope=scope))
        if "portfolio" in kinds:
            out.extend(
                self._suggest_portfolios(
                    query=query,
                    limit=limit,
                    actor_user_id=actor_user_id,
                    unrestricted=unrestricted,
                )
            )
        if "order" in kinds:
            out.extend(self._suggest_orders(query=query, limit=limit, scope=scope))
        return out

    def _suggest_customers(
        self,
        *,
        query: str,
        limit: int,
        scope: CommercialCustomerScope | None,
    ) -> list[dict[str, Any]]:
        if self._gateway is None or scope is None:
            return []
        if scope.empty_portfolio and not scope.unrestricted:
            return []
        try:
            payload = self._gateway.search_active_customers(
                params={"q": query, "page": 1, "page_size": limit},
            )
        except Exception:
            return []
        out: list[dict[str, Any]] = []
        seen: set[tuple[str, str]] = set()
        for item in _unwrap_items(payload):
            code = str(
                item.get("code")
                or item.get("customer_code")
                or item.get("codigo")
                or ""
            ).strip()
            store = str(
                item.get("store")
                or item.get("customer_store")
                or item.get("loja")
                or ""
            ).strip()
            name = str(item.get("name") or item.get("nome") or "").strip()
            if not code or not store or (code, store) in seen:
                continue
            if not scope.allows(code, store):
                continue
            if not _matches(query, name, code, store):
                continue
            seen.add((code, store))
            out.append(
                {
                    "kind": "customer",
                    "label": name or f"{code}/{store}",
                    "subtitle": f"{code}/{store}",
                    "ref": {
                        "customer_code": code,
                        "customer_store": store,
                    },
                }
            )
            if len(out) >= limit:
                break
        return out

    def _suggest_portfolios(
        self,
        *,
        query: str,
        limit: int,
        actor_user_id: str | None,
        unrestricted: bool,
    ) -> list[dict[str, Any]]:
        if self._portfolios is None:
            return []
        try:
            if unrestricted:
                portfolios = self._portfolios.list_portfolios(active_only=True)
            else:
                uid = (actor_user_id or "").strip()
                if not uid:
                    return []
                portfolios = self._portfolios.list_by_user_id(uid, active_only=True)
        except Exception:
            return []
        out: list[dict[str, Any]] = []
        for portfolio in portfolios:
            label = (portfolio.display_name or "").strip() or portfolio.id
            if not _matches(query, label, portfolio.id):
                continue
            out.append(
                {
                    "kind": "portfolio",
                    "label": label,
                    "subtitle": "",
                    "ref": {"portfolio_id": portfolio.id},
                }
            )
            if len(out) >= limit:
                break
        return out

    def _suggest_orders(
        self,
        *,
        query: str,
        limit: int,
        scope: CommercialCustomerScope | None,
    ) -> list[dict[str, Any]]:
        if self._gateway is None or scope is None:
            return []
        try:
            payload = self._gateway.list_open_orders()
            data = payload.get("data") if isinstance(payload.get("data"), dict) else payload
            filtered = self._order_filter.apply(
                data if isinstance(data, dict) else {},
                scope.for_open_orders(),
            )
        except Exception:
            return []
        items = filtered.get("items") if isinstance(filtered, dict) else None
        if not isinstance(items, list):
            return []
        out: list[dict[str, Any]] = []
        seen: set[tuple[str, str]] = set()
        for item in items:
            if not isinstance(item, dict):
                continue
            branch = str(item.get("filial") or item.get("branch") or "").strip()
            order = str(item.get("pedido") or item.get("order") or "").strip()
            if not branch or not order or (branch, order) in seen:
                continue
            name = str(
                item.get("nome_cliente")
                or item.get("cliente")
                or item.get("customer_name")
                or ""
            ).strip()
            if not _matches(query, order, branch, name):
                continue
            seen.add((branch, order))
            out.append(
                {
                    "kind": "order",
                    "label": order,
                    "subtitle": f"{branch} · {name}".strip(" ·"),
                    "ref": {"branch": branch, "order": order},
                }
            )
            if len(out) >= limit:
                break
        return out

    def _suggest_ops(
        self,
        *,
        query: str,
        kinds: Sequence[str],
        limit: int,
        actor_user_id: str | None,
        unrestricted: bool,
    ) -> list[dict[str, Any]]:
        if self._gateway is None:
            return []
        scope = self._customer_scope(
            actor_user_id=actor_user_id,
            unrestricted=unrestricted,
        )
        out: list[dict[str, Any]] = []
        if "product" in kinds:
            out.extend(self._suggest_products(query=query, limit=limit))
        if "production_order" in kinds:
            out.extend(self._suggest_production_orders(query=query, limit=limit))
        if "opportunity" in kinds:
            out.extend(self._suggest_opportunities(query=query, limit=limit, scope=scope))
        if "otd_line" in kinds:
            out.extend(self._suggest_otd_lines(query=query, limit=limit, scope=scope))
        if "invoice" in kinds:
            out.extend(self._suggest_invoices(query=query, limit=limit, scope=scope))
        return out[:limit]

    def _suggest_products(self, *, query: str, limit: int) -> list[dict[str, Any]]:
        term = (query or "").strip()
        if not term or self._gateway is None:
            return []
        try:
            payload = self._gateway.get_product(
                "/search",
                params={"code": term, "page": 1, "page_size": limit},
            )
        except Exception:
            payload = None
        items = _unwrap_items(payload) if payload else []
        if not items:
            try:
                detail = self._gateway.get_product(f"/{term}/factory-status")
                data = detail.get("data") if isinstance(detail.get("data"), dict) else detail
                if isinstance(data, dict):
                    items = [data]
            except Exception:
                return []
        out: list[dict[str, Any]] = []
        for item in items:
            code = str(
                item.get("code")
                or item.get("product_code")
                or item.get("productCode")
                or term
            ).strip()
            if not code:
                continue
            name = str(
                item.get("description")
                or item.get("name")
                or item.get("product_description")
                or ""
            ).strip()
            out.append(
                {
                    "kind": "product",
                    "label": name or code,
                    "subtitle": code,
                    "ref": {"product_code": code},
                }
            )
            if len(out) >= limit:
                break
        return out

    def _suggest_production_orders(self, *, query: str, limit: int) -> list[dict[str, Any]]:
        term = (query or "").strip()
        if not term or self._gateway is None:
            return []
        try:
            payload = self._gateway.get_production(f"/orders/by-op/{term}")
        except Exception:
            return []
        data = payload.get("data") if isinstance(payload.get("data"), dict) else payload
        if not isinstance(data, dict):
            return []
        op = str(
            data.get("op")
            or data.get("production_order")
            or data.get("productionOrder")
            or term
        ).strip()
        branch = str(data.get("branch") or data.get("filial") or "").strip()
        if not op:
            return []
        return [
            {
                "kind": "production_order",
                "label": op,
                "subtitle": branch,
                "ref": {"production_order": op, "branch": branch or None},
            }
        ][:limit]

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

    def _suggest_opportunities(
        self,
        *,
        query: str,
        limit: int,
        scope: CommercialCustomerScope | None,
    ) -> list[dict[str, Any]]:
        if self._gateway is None:
            return []
        try:
            payload = self._gateway.get_commercial_analytics(
                "/proposals",
                params={"search": query, "page": 1, "page_size": limit},
            )
        except Exception:
            return []
        out: list[dict[str, Any]] = []
        for item in _unwrap_items(payload):
            if not self._in_customer_scope(item, scope):
                continue
            number = str(
                item.get("proposal_number")
                or item.get("proposalNumber")
                or item.get("numero")
                or item.get("id")
                or ""
            ).strip()
            if not number:
                continue
            name = str(item.get("customer_name") or item.get("cliente") or "").strip()
            if not _matches(query, number, name):
                continue
            out.append(
                {
                    "kind": "opportunity",
                    "label": number,
                    "subtitle": name,
                    "ref": {"proposal_number": number},
                }
            )
            if len(out) >= limit:
                break
        return out

    def _suggest_otd_lines(
        self,
        *,
        query: str,
        limit: int,
        scope: CommercialCustomerScope | None,
    ) -> list[dict[str, Any]]:
        if self._gateway is None:
            return []
        try:
            payload = self._gateway.get_commercial_analytics(
                "/sales-order-otd/panel",
                params={"search": query, "page": 1, "page_size": limit},
            )
        except Exception:
            return []
        out: list[dict[str, Any]] = []
        seen: set[tuple[str, str, str]] = set()
        for item in _unwrap_items(payload):
            if not self._in_customer_scope(item, scope):
                continue
            branch = str(item.get("branch") or item.get("filial") or "").strip()
            order = str(
                item.get("order_number") or item.get("pedido") or item.get("order") or ""
            ).strip()
            line = str(
                item.get("line_item") or item.get("linha") or item.get("line") or ""
            ).strip()
            key = (branch, order, line)
            if not branch or not order or not line or key in seen:
                continue
            if not _matches(query, order, line, branch):
                continue
            seen.add(key)
            out.append(
                {
                    "kind": "otd_line",
                    "label": f"{order}/{line}",
                    "subtitle": branch,
                    "ref": {
                        "branch": branch,
                        "order": order,
                        "line": line,
                    },
                }
            )
            if len(out) >= limit:
                break
        return out

    def _suggest_invoices(
        self,
        *,
        query: str,
        limit: int,
        scope: CommercialCustomerScope | None,
    ) -> list[dict[str, Any]]:
        if self._gateway is None or scope is None or not scope.allowed_customers:
            return []
        out: list[dict[str, Any]] = []
        seen: set[tuple[str, str, str]] = set()
        for code, store in list(scope.allowed_customers)[:8]:
            try:
                payload = self._gateway.list_customer_outbound_invoices(
                    customer_code=code,
                    customer_store=store,
                )
            except Exception:
                continue
            for item in _unwrap_items(payload):
                number = str(
                    item.get("invoice_number")
                    or item.get("nota")
                    or item.get("nf")
                    or item.get("number")
                    or ""
                ).strip()
                series = str(item.get("series") or item.get("serie") or "").strip()
                branch = str(item.get("branch") or item.get("filial") or "").strip()
                key = (branch, number, series)
                if not number or key in seen:
                    continue
                if not _matches(query, number, series, branch):
                    continue
                seen.add(key)
                out.append(
                    {
                        "kind": "invoice",
                        "label": number,
                        "subtitle": f"{branch} {series}".strip(),
                        "ref": {
                            "branch": branch,
                            "invoice": number,
                            "series": series,
                        },
                    }
                )
                if len(out) >= limit:
                    return out
        return out

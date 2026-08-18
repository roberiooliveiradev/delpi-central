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
        crm_kinds = [kind for kind in ("customer", "portfolio", "order") if kind in wanted]
        if crm_kinds:
            items.extend(
                self._suggest_crm(
                    query=query,
                    kinds=crm_kinds,
                    limit=cap,
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

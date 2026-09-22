"""Owner-local NL discovery over the TV data route allowlist.

Ranks routes from ``tv_data_routes.json`` without Chat AI as authority.
"""

from __future__ import annotations

import re
import unicodedata
from typing import Any

from tv_app.application.services.tv_data_route_catalog_service import TvDataRouteCatalogService

_TOKEN_RE = re.compile(r"[a-z0-9]+", re.IGNORECASE)

_CATEGORY_ALIASES: dict[str, frozenset[str]] = {
    "commercial": frozenset(
        {"comercial", "commercial", "venda", "vendas", "pedido", "pedidos", "sales"}
    ),
    "supplies": frozenset(
        {"suprimento", "suprimentos", "supplies", "compra", "compras", "purchase"}
    ),
    "production": frozenset(
        {"producao", "produção", "production", "fabril", "oee", "pcp"}
    ),
}


def _fold(text: str) -> str:
    raw = unicodedata.normalize("NFKD", str(text or ""))
    return "".join(ch for ch in raw if not unicodedata.combining(ch)).lower()


def _tokens(text: str) -> list[str]:
    return [m.group(0).lower() for m in _TOKEN_RE.finditer(_fold(text)) if m.group(0)]


class TvDataRouteDiscoveryService:
    """Deterministic catalog discovery for TV GPT Actions and MFE suggest."""

    def __init__(self, catalog: TvDataRouteCatalogService | None = None) -> None:
        self._catalog = catalog or TvDataRouteCatalogService()

    def discover(
        self,
        *,
        query: str,
        limit: int = 8,
        category: str | None = None,
    ) -> dict[str, Any]:
        message = str(query or "").strip()
        if not message:
            return {
                "query": "",
                "suggestions": [],
                "total": 0,
                "degraded": False,
                "searchMissDoesNotProveAbsence": True,
            }

        cap = max(1, min(int(limit or 8), 20))
        category_filter = str(category or "").strip().lower() or None
        q_tokens = _tokens(message)
        intent_categories = self._intent_categories(q_tokens)
        wants_otd = "otd" in q_tokens

        scored: list[tuple[float, dict[str, Any], str]] = []
        for route in self._catalog.list_routes():
            if not isinstance(route, dict):
                continue
            operation_id = str(route.get("operationId") or "").strip()
            if not operation_id:
                continue
            route_category = str(route.get("category") or "").strip().lower()
            if category_filter and route_category != category_filter:
                continue

            score, reason = self._score_route(
                route,
                query_folded=_fold(message),
                q_tokens=q_tokens,
                intent_categories=intent_categories,
                wants_otd=wants_otd,
            )
            if score <= 0:
                continue
            scored.append((score, route, reason))

        scored.sort(key=lambda item: (-item[0], str(item[1].get("operationId") or "")))
        suggestions: list[dict[str, Any]] = []
        for score, route, reason in scored[:cap]:
            suggestions.append(
                {
                    **route,
                    "reason": reason,
                    "score": round(score, 4),
                    "suggestionDomain": str(route.get("category") or "").strip() or None,
                }
            )

        return {
            "query": message,
            "suggestions": suggestions,
            "total": len(suggestions),
            "degraded": False,
            "searchMissDoesNotProveAbsence": True,
        }

    @classmethod
    def _intent_categories(cls, q_tokens: list[str]) -> set[str]:
        token_set = set(q_tokens)
        found: set[str] = set()
        for category, aliases in _CATEGORY_ALIASES.items():
            if token_set & aliases:
                found.add(category)
        return found

    @classmethod
    def _score_route(
        cls,
        route: dict[str, Any],
        *,
        query_folded: str,
        q_tokens: list[str],
        intent_categories: set[str],
        wants_otd: bool,
    ) -> tuple[float, str]:
        operation_id = str(route.get("operationId") or "")
        path = str(route.get("path") or "")
        label = str(route.get("label") or "")
        description = str(route.get("description") or "")
        when_to_use = str(route.get("whenToUse") or "")
        category = str(route.get("category") or "").strip().lower()

        hay_parts = {
            "operationId": _fold(operation_id),
            "path": _fold(path),
            "label": _fold(label),
            "description": _fold(description),
            "whenToUse": _fold(when_to_use),
            "category": _fold(category),
        }
        blob = " ".join(hay_parts.values())
        weights = {
            "operationId": 6.0,
            "path": 5.0,
            "label": 4.0,
            "category": 3.5,
            "whenToUse": 2.5,
            "description": 2.0,
        }

        score = 0.0
        hits: list[str] = []
        for token in q_tokens:
            if len(token) < 2 and token != "01" and token != "02":
                continue
            best_field = None
            best_w = 0.0
            for field, text in hay_parts.items():
                if token in text or token.replace("_", "") in text.replace("_", "").replace("-", ""):
                    w = weights[field]
                    if w > best_w:
                        best_w = w
                        best_field = field
            if best_field:
                score += best_w
                hits.append(token)

        # Phrase / substring boost
        if len(query_folded) >= 4 and query_folded in blob:
            score += 3.0

        # Domain intent boost / penalty
        if intent_categories:
            if category in intent_categories:
                score += 8.0
                hits.append(f"category:{category}")
            elif category:
                score -= 6.0

        if wants_otd:
            oid = hay_parts["operationId"]
            pth = hay_parts["path"]
            if "otd" in oid or "otd" in pth:
                score += 5.0
            if "commercial" in intent_categories or "comercial" in q_tokens:
                if "sales-order-otd" in pth or "sales_order_otd" in oid:
                    score += 12.0
                    hits.append("family:sales-order-otd")
                if "supplies" in pth or "purchase-order-otd" in pth:
                    score -= 10.0
            if "supplies" in intent_categories or "suprimentos" in q_tokens:
                if "supplies" in pth or "purchase-order-otd" in pth:
                    score += 12.0
                    hits.append("family:supplies-otd")
                if "sales-order-otd" in pth:
                    score -= 10.0

        if score <= 0:
            return 0.0, ""

        unique_hits = list(dict.fromkeys(hits))[:5]
        reason = (
            "coincide com " + ", ".join(unique_hits) if unique_hits else "correspondência lexical"
        )
        return score, reason

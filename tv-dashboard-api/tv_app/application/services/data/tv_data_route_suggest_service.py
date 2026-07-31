"""BFF: NL → sugestões de fontes do catálogo TV (intersect allowlist)."""

from __future__ import annotations

import logging
from typing import Any

import httpx

from tv_app.application.services.tv_data_route_catalog_service import TvDataRouteCatalogService
from tv_app.infrastructure.gateways.minha_delpi_ai_client import MinhaDelpiAiClient

logger = logging.getLogger(__name__)


class TvDataRouteSuggestService:
    def __init__(
        self,
        catalog: TvDataRouteCatalogService,
        *,
        ai_client: MinhaDelpiAiClient | None = None,
    ) -> None:
        self._catalog = catalog
        self._ai = ai_client or MinhaDelpiAiClient()

    def suggest(
        self,
        *,
        query: str,
        limit: int = 5,
    ) -> dict[str, Any]:
        message = str(query or "").strip()
        if not message:
            return {"query": "", "suggestions": [], "total": 0, "degraded": False}

        cap = max(1, min(int(limit or 5), 20))
        try:
            raw = self._ai.suggest_operational_routes(query=message, limit=max(cap * 3, 12))
        except httpx.HTTPError as exc:
            logger.warning("suggest routes AI unavailable: %s", exc)
            return {
                "query": message,
                "suggestions": [],
                "total": 0,
                "degraded": True,
                "error": "ai_unavailable",
            }
        except Exception as exc:  # noqa: BLE001
            logger.exception("suggest routes unexpected error: %s", exc)
            return {
                "query": message,
                "suggestions": [],
                "total": 0,
                "degraded": True,
                "error": "ai_error",
            }

        candidates = raw.get("suggestions") if isinstance(raw, dict) else None
        if not isinstance(candidates, list):
            candidates = []

        out: list[dict[str, Any]] = []
        seen: set[str] = set()
        for row in candidates:
            if not isinstance(row, dict):
                continue
            operation_id = str(row.get("operationId") or "").strip()
            if not operation_id or operation_id in seen:
                continue
            route = self._catalog.get_route(operation_id)
            if not route:
                continue
            seen.add(operation_id)
            out.append(
                {
                    **route,
                    "reason": str(row.get("reason") or "").strip(),
                    "score": row.get("score"),
                    "suggestionDomain": row.get("domain"),
                }
            )
            if len(out) >= cap:
                break

        return {
            "query": message,
            "suggestions": out,
            "total": len(out),
            "degraded": False,
        }

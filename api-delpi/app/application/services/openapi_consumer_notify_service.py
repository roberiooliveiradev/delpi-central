"""Notifica chat e TV para reimportar o OpenAPI da api-delpi (S2S)."""

from __future__ import annotations

import logging
import os
from typing import Any

import httpx
from delpi_auth.service_token import (
    apply_internal_service_headers,
    get_internal_service_token,
)

logger = logging.getLogger(__name__)

DEFAULT_CHAT_URL = (
    "http://delpi-minha-delpi-ai-api:8000/chat/internal/openapi/sync-api-delpi"
)
DEFAULT_TV_URL = "http://delpi-tv-dashboard-api:8000/data/openapi/sync"


def _env_bool(name: str, default: bool = False) -> bool:
    raw = os.getenv(name)
    if raw is None or str(raw).strip() == "":
        return default
    return str(raw).strip().lower() in {"1", "true", "yes", "on"}


def _env_float(name: str, default: float) -> float:
    try:
        return float(os.getenv(name, str(default)) or default)
    except (TypeError, ValueError):
        return default


class OpenApiConsumerNotifyService:
    """POST autenticado com API_DELPI_INTERNAL_SERVICE_TOKEN nos consumidores.

    Por padrão **atualiza os schemas OpenAPI** no chat (reimport de actions) e o
    catálogo TV. Embeddings do chat também rodam por padrão
    (`OPENAPI_CONSUMER_CHAT_SKIP_EMBEDDINGS=false`).
    """

    def has_service_token(self) -> bool:
        return bool(get_internal_service_token())

    def is_enabled(self) -> bool:
        return _env_bool("OPENAPI_CONSUMER_NOTIFY_ENABLED", default=True)

    def chat_skip_embeddings(self) -> bool:
        # Default false → atualiza schemas + embeddings no reimport.
        return _env_bool("OPENAPI_CONSUMER_CHAT_SKIP_EMBEDDINGS", default=False)

    def chat_sync_url(self) -> str:
        base = (
            os.getenv("OPENAPI_CONSUMER_CHAT_SYNC_URL") or DEFAULT_CHAT_URL
        ).strip()
        if not base:
            return ""
        # Garante query de atualização de schema; embeddings conforme flag.
        from urllib.parse import parse_qsl, urlencode, urlsplit, urlunsplit

        parts = urlsplit(base)
        query = dict(parse_qsl(parts.query, keep_blank_values=True))
        query.setdefault("updateSchema", "1")
        if "skipEmbeddings" not in query:
            query["skipEmbeddings"] = "1" if self.chat_skip_embeddings() else "0"
        return urlunsplit(
            (parts.scheme, parts.netloc, parts.path, urlencode(query), parts.fragment)
        )

    def tv_sync_url(self) -> str:
        return (os.getenv("OPENAPI_CONSUMER_TV_SYNC_URL") or DEFAULT_TV_URL).strip()

    def timeout_seconds(self) -> float:
        return _env_float("OPENAPI_CONSUMER_NOTIFY_TIMEOUT_SECONDS", 120.0)

    def list_targets(
        self,
        *,
        skip_chat: bool = False,
        skip_tv: bool = False,
    ) -> list[dict[str, str]]:
        targets: list[dict[str, str]] = []
        if not skip_chat and self.chat_sync_url():
            targets.append({"name": "chat", "url": self.chat_sync_url()})
        if not skip_tv and self.tv_sync_url():
            targets.append({"name": "tv", "url": self.tv_sync_url()})
        return targets

    def _post(self, *, name: str, url: str) -> dict[str, Any]:
        headers: dict[str, str] = {"Accept": "application/json"}
        apply_internal_service_headers(headers)
        if "X-Delpi-Service-Token" not in headers:
            return {
                "name": name,
                "url": url,
                "ok": False,
                "error": "API_DELPI_INTERNAL_SERVICE_TOKEN ausente",
            }
        try:
            with httpx.Client(timeout=self.timeout_seconds()) as client:
                response = client.post(url, headers=headers)
            body: Any
            try:
                body = response.json()
            except Exception:  # noqa: BLE001
                body = (response.text or "")[:500]
            ok = 200 <= response.status_code < 300
            return {
                "name": name,
                "url": url,
                "ok": ok,
                "statusCode": response.status_code,
                "body": body,
            }
        except Exception as exc:  # noqa: BLE001
            return {
                "name": name,
                "url": url,
                "ok": False,
                "error": str(exc),
            }

    def notify_all(
        self,
        *,
        skip_chat: bool = False,
        skip_tv: bool = False,
    ) -> dict[str, Any]:
        if not self.is_enabled():
            return {
                "ok": True,
                "skipped": True,
                "reason": "OPENAPI_CONSUMER_NOTIFY_ENABLED=false",
                "results": [],
            }
        if not self.has_service_token():
            logger.warning(
                "OpenAPI consumer notify: token S2S ausente — pulando chat/TV"
            )
            return {
                "ok": False,
                "skipped": True,
                "reason": "API_DELPI_INTERNAL_SERVICE_TOKEN ausente",
                "results": [],
            }

        results = [
            self._post(name=item["name"], url=item["url"])
            for item in self.list_targets(skip_chat=skip_chat, skip_tv=skip_tv)
        ]
        ok = bool(results) and all(bool(item.get("ok")) for item in results)
        report = {"ok": ok, "results": results}
        if ok:
            logger.info("OpenAPI consumers notificados: %s", [r["name"] for r in results])
        else:
            logger.warning("OpenAPI consumer notify incompleto: %s", report)
        return report

    def notify_safe(self) -> dict[str, Any]:
        try:
            return self.notify_all()
        except Exception as exc:  # noqa: BLE001 — startup resiliente
            logger.warning("OpenAPI consumer notify falhou: %s", exc)
            return {"ok": False, "error": str(exc), "results": []}

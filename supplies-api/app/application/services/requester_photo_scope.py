"""Photo scope guard — a requester photo may only be served when the
Protheus user id belongs to the caller's *authorized* SC universe.

The BFF ``requester.photo_url`` is an enumerable path
(``/purchase-requests/requesters/<C1_USER>/photo``): without this guard,
any ``supplies.access`` caller could iterate Protheus ids and harvest
photos of employees who never issued a purchase request in their scope.

Guard chain (fail-closed):
  1. route decorators — ``supplies.access`` + ``require_units("branch")``;
  2. this check — the id must appear in the owner's ``/requesters`` facet
     for the **same** branch+period query, which already applies the
     caller's cost-center visibility scopes server-side;
  3. the id must still resolve a ``mapped`` Core identity before Core is
     asked for bytes (``RequesterIdentityService.get_requester_photo``).

Facet sets are cached briefly per (caller, facet query) so one page of
avatars costs a single facet call instead of N.
"""

from __future__ import annotations

import logging
import time
from typing import Any

from app.infrastructure.gateways.purchase_requests_gateway import (
    PurchaseRequestsGateway,
)

logger = logging.getLogger("supplies-api.requester_photo_scope")

_FACET_TTL_SECONDS = 120.0
_CACHE_MAX_KEYS = 512


class RequesterPhotoScopeGuard:
    def __init__(self, gateway: PurchaseRequestsGateway | None = None) -> None:
        self._gateway = gateway or PurchaseRequestsGateway()
        self._cache: dict[tuple[str, str], tuple[float, frozenset[str]]] = {}

    def is_allowed(
        self,
        *,
        protheus_user_id: str,
        access_token: str,
        facet_query: str,
    ) -> bool:
        pid = (protheus_user_id or "").strip()
        if not pid or not access_token:
            return False
        return pid in self._authorized_requester_ids(access_token, facet_query)

    def _authorized_requester_ids(
        self, access_token: str, facet_query: str
    ) -> frozenset[str]:
        key = (access_token, facet_query)
        now = time.monotonic()
        cached = self._cache.get(key)
        if cached and cached[0] > now:
            return cached[1]

        ids: frozenset[str] = frozenset()
        try:
            payload: Any = self._gateway.list_requesters(
                access_token=access_token,
                query_string=facet_query or None,
            )
            data = payload.get("data", payload) if isinstance(payload, dict) else {}
            items = data.get("items") if isinstance(data, dict) else None
            if isinstance(items, list):
                ids = frozenset(
                    str(item.get("protheus_user_id") or "").strip()
                    for item in items
                    if isinstance(item, dict)
                )
                ids = frozenset(pid for pid in ids if pid)
        except Exception:
            logger.exception("requester_photo_scope_lookup_failed")

        if len(self._cache) >= _CACHE_MAX_KEYS:
            self._cache.clear()
        self._cache[key] = (now + _FACET_TTL_SECONDS, ids)
        return ids

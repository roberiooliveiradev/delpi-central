"""Requester identity resolution — Minha DELPI display name via Core link.

Deterministic join: Protheus ``requester.protheus_user_id`` (SC1.C1_USER)
→ Core ``/integrations/protheus-identities/lookup`` (``mapping_status ==
"mapped"`` rows only) → Core ``/me/directory/users/lookup`` official name.

No name similarity, no fuzzy matching, no inference from the caller. When
the link is absent, ambiguous or any source fails, the requester keeps its
source ``name`` untouched — fallback is honest, never fabricated.
"""

from __future__ import annotations

import logging
from typing import Any, Iterable

from app.infrastructure.gateways.core_api_http_gateway import CoreApiHttpGateway

logger = logging.getLogger("supplies-api.requester_identity")


def _requester_refs(payload: Any) -> Iterable[dict]:
    """Yield every requester dict inside list/detail payloads, in place."""
    if not isinstance(payload, dict):
        return
    items = payload.get("items")
    if isinstance(items, list):
        for item in items:
            if isinstance(item, dict) and isinstance(item.get("requester"), dict):
                yield item["requester"]
    header = payload.get("requester")
    if isinstance(header, dict):
        yield header
    lines = payload.get("lines")
    if isinstance(lines, list):
        for line in lines:
            if isinstance(line, dict) and isinstance(line.get("requester"), dict):
                yield line["requester"]


class RequesterIdentityService:
    def __init__(self, core_gateway: CoreApiHttpGateway | None = None) -> None:
        self._core = core_gateway or CoreApiHttpGateway()

    def enrich_payload(self, payload: Any, *, access_token: str) -> Any:
        refs = list(_requester_refs(payload))
        if not refs:
            return payload

        protheus_ids = {
            str(ref.get("protheus_user_id") or "").strip()
            for ref in refs
        }
        protheus_ids.discard("")
        if not protheus_ids:
            return payload

        try:
            mappings = self._core.lookup_protheus_identities(
                protheus_user_ids=sorted(protheus_ids)
            )
        except Exception:
            logger.exception("requester_identity_lookup_failed")
            return payload
        if not mappings:
            return payload

        user_ids = {
            str(mapping.get("user_id") or "").strip()
            for mapping in mappings.values()
        }
        user_ids.discard("")
        directory: dict[str, dict[str, str]] = {}
        if user_ids and access_token:
            try:
                directory = self._core.lookup_directory_users(
                    access_token=access_token,
                    user_ids=sorted(user_ids),
                )
            except Exception:
                logger.exception("requester_directory_lookup_failed")

        for ref in refs:
            pid = str(ref.get("protheus_user_id") or "").strip()
            mapping = mappings.get(pid)
            if not mapping:
                continue
            core_name = str(
                (directory.get(str(mapping.get("user_id") or "")) or {}).get("name")
                or ""
            ).strip()
            if core_name:
                ref["display_name"] = core_name

        return payload

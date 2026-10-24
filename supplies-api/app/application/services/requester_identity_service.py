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
    """Yield every requester dict inside list/detail/facet payloads, in place."""
    if not isinstance(payload, dict):
        return
    items = payload.get("items")
    if isinstance(items, list):
        for item in items:
            if not isinstance(item, dict):
                continue
            if isinstance(item.get("requester"), dict):
                yield item["requester"]
            elif item.get("protheus_user_id"):
                # Facet shape: the item itself is the requester ref.
                yield item
    header = payload.get("requester")
    if isinstance(header, dict):
        yield header
    detail_header = payload.get("header")
    if isinstance(detail_header, dict) and isinstance(
        detail_header.get("requester"), dict
    ):
        yield detail_header["requester"]
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

        profiles: dict[str, dict] = {}
        if user_ids:
            try:
                profiles = self._core.lookup_person_profiles(
                    user_ids=sorted(user_ids)
                )
            except Exception:
                logger.exception("requester_profiles_lookup_failed")

        for ref in refs:
            pid = str(ref.get("protheus_user_id") or "").strip()
            mapping = mappings.get(pid)
            if not mapping:
                continue
            uid = str(mapping.get("user_id") or "").strip()
            if uid:
                # Canonical opaque identifier — enables the client to link the
                # avatar/name to `/users/:userId` (AuthZ stays backend-side).
                ref["user_id"] = uid
            core_name = str(
                (directory.get(uid) or {}).get("name") or ""
            ).strip()
            if core_name:
                ref["display_name"] = core_name
            profile = profiles.get(uid) or {}
            if profile.get("has_photo"):
                # BFF proxy path — the Core user id never leaves the server.
                ref["photo_url"] = (
                    f"/purchase-requests/requesters/{pid}/photo"
                )

        return payload

    def resolve_mapped_user_id(self, protheus_user_id: str) -> str | None:
        """Exact Protheus id → Core user id when `mapping_status == mapped`."""
        pid = (protheus_user_id or "").strip()
        if not pid:
            return None
        try:
            mappings = self._core.lookup_protheus_identities(
                protheus_user_ids=[pid]
            )
        except Exception:
            logger.exception("requester_identity_resolve_failed")
            return None
        if not mappings:
            return None
        mapping = mappings.get(pid) or {}
        uid = str(mapping.get("user_id") or "").strip()
        return uid or None

    def get_requester_photo(
        self, protheus_user_id: str
    ) -> tuple[bytes, str, str] | None:
        """Photo bytes for a mapped requester; None when unmapped/absent."""
        uid = self.resolve_mapped_user_id(protheus_user_id)
        if not uid:
            return None
        try:
            return self._core.get_person_profile_photo(uid)
        except Exception:
            logger.exception("requester_photo_fetch_failed")
            return None

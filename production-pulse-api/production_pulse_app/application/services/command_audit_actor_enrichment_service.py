from __future__ import annotations

from typing import Any
from uuid import UUID

from production_pulse_app.infrastructure.gateways.core_api_user_lookup import (
    lookup_directory_users_by_ids,
)


def _is_uuid(value: str) -> bool:
    try:
        UUID(str(value).strip())
    except (TypeError, ValueError):
        return False
    return True


def enrich_command_audit_actors(
    items: list[dict[str, Any]],
    *,
    authorization: str | None,
) -> list[dict[str, Any]]:
    """Preenche issuedByName/issuedByEmail consultando o diretório do core-api."""
    actor_ids = {
        str(item["issuedBy"]).strip()
        for item in items
        if item.get("issuedBy") and _is_uuid(str(item["issuedBy"]))
    }
    if not actor_ids or not authorization:
        return items

    profiles = lookup_directory_users_by_ids(sorted(actor_ids), authorization)
    if not profiles:
        return items

    for item in items:
        actor_id = item.get("issuedBy")
        if not actor_id:
            continue
        profile = profiles.get(str(actor_id))
        if not profile:
            continue
        if profile.get("name"):
            item["issuedByName"] = profile["name"]
        if profile.get("email"):
            item["issuedByEmail"] = profile["email"]
    return items

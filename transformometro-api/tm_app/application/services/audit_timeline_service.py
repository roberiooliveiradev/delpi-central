from __future__ import annotations

from tm_app.infrastructure.gateways.core_api_user_lookup import lookup_user_names_by_ids


def enrich_timeline_actor_names(
    items: list[dict],
    *,
    authorization: str | None,
) -> list[dict]:
    """Preenche user_name ausente consultando o diretório (registros legados)."""
    missing_ids = {
        str(row["user_id"])
        for row in items
        if row.get("user_id") and not (row.get("user_name") or "").strip()
    }
    if not missing_ids:
        return items

    names_by_id = lookup_user_names_by_ids(sorted(missing_ids), authorization)
    if not names_by_id:
        return items

    for row in items:
        user_id = row.get("user_id")
        if not user_id or (row.get("user_name") or "").strip():
            continue
        resolved = names_by_id.get(str(user_id))
        if resolved:
            row["user_name"] = resolved
    return items

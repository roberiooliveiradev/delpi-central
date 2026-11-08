"""Resolução batch de identidade via Core — /me/directory/users/lookup.

Padrão governado (mesmo contrato usado pela supplies-api): POST com o
Bearer humano delegado, ids deduped, `reveal_email` para projeção
autorizada. Falhas nunca bloqueiam a leitura — retorna mapa parcial.
"""

from __future__ import annotations

from typing import Any

import httpx

from engineering_app.config import settings


async def lookup_display_identities(
    user_ids: list[str],
    *,
    access_token: str,
    timeout_seconds: float = 8.0,
) -> dict[str, dict[str, str]]:
    """Retorna ``{user_id: {"name": ..., "email": ...}}`` para os ids
    resolvidos; vazio em indisponibilidade (fallback honesto no caller)."""
    ordered: list[str] = []
    seen: set[str] = set()
    for raw in user_ids:
        uid = str(raw or "").strip()
        if uid and uid not in seen:
            seen.add(uid)
            ordered.append(uid)
    if not ordered or not access_token:
        return {}

    url = f"{settings.CORE_API_URL.rstrip('/')}/me/directory/users/lookup"
    try:
        async with httpx.AsyncClient(timeout=timeout_seconds) as client:
            resp = await client.post(
                url,
                headers={
                    "Authorization": f"Bearer {access_token}",
                    "Accept": "application/json",
                    "Content-Type": "application/json",
                },
                json={
                    "ids": ordered,
                    "app": "engineering",
                    "reveal_email": True,
                },
            )
    except httpx.HTTPError:
        return {}

    if resp.status_code >= 400:
        return {}

    try:
        items = resp.json().get("items")
    except ValueError:
        return {}
    if not isinstance(items, list):
        return {}

    out: dict[str, dict[str, str]] = {}
    for item in items:
        if not isinstance(item, dict):
            continue
        uid = str(item.get("id") or "").strip()
        if not uid:
            continue
        name = str(
            item.get("name") or item.get("display_name") or ""
        ).strip()
        email = str(item.get("email") or "").strip()
        out[uid] = {"name": name, "email": email}
    return out


def enrich_queue_items(
    payload: dict[str, Any],
    identities: dict[str, dict[str, str]],
) -> dict[str, Any]:
    """Preenche `requester.displayName` e `assignedToDisplayName` dos
    itens da fila quando ausentes — somente com identidade resolvida."""
    for item in payload.get("items") or []:
        req = item.get("requester")
        if isinstance(req, dict) and not (req.get("displayName") or "").strip():
            resolved = identities.get(str(req.get("subject") or ""))
            if resolved and resolved.get("name"):
                req["displayName"] = resolved["name"]
        if item.get("assignedTo") and not (
            item.get("assignedToDisplayName") or ""
        ).strip():
            resolved = identities.get(str(item.get("assignedTo") or ""))
            if resolved and resolved.get("name"):
                item["assignedToDisplayName"] = resolved["name"]
    return payload


def enrich_request_identity(
    detail: dict[str, Any],
    identities: dict[str, dict[str, str]],
) -> dict[str, Any]:
    """Mesma projeção para o detalhe (hero)."""
    req = detail.get("requester")
    if isinstance(req, dict) and not (req.get("displayName") or "").strip():
        resolved = identities.get(str(req.get("subject") or ""))
        if resolved and resolved.get("name"):
            req["displayName"] = resolved["name"]
    if detail.get("assignedTo") and not (
        detail.get("assignedToDisplayName") or ""
    ).strip():
        resolved = identities.get(str(detail.get("assignedTo") or ""))
        if resolved and resolved.get("name"):
            detail["assignedToDisplayName"] = resolved["name"]
    return detail


def enrich_timeline_events(
    payload: dict[str, Any],
    identities: dict[str, dict[str, str]],
) -> dict[str, Any]:
    """Preenche `actor_display_name`/`actor_email` em eventos legados
    sem snapshot V013 — nunca inventa identidade."""
    for ev in payload.get("items") or []:
        if (ev.get("actor_display_name") or "").strip():
            continue
        resolved = identities.get(str(ev.get("actor_subject") or ""))
        if not resolved:
            continue
        if resolved.get("name"):
            ev["actor_display_name"] = resolved["name"]
        if resolved.get("email"):
            ev["actor_email"] = resolved["email"]
    return payload


def collect_identity_subjects(payload: dict[str, Any], kind: str) -> list[str]:
    """Subjects ainda sem nome de apresentação, por tipo de payload."""
    subjects: list[str] = []
    if kind == "timeline":
        for ev in payload.get("items") or []:
            if not (ev.get("actor_display_name") or "").strip():
                subjects.append(str(ev.get("actor_subject") or ""))
    elif kind == "queue":
        for item in payload.get("items") or []:
            req = item.get("requester") or {}
            if not (req.get("displayName") or "").strip():
                subjects.append(str(req.get("subject") or ""))
            if item.get("assignedTo") and not (
                item.get("assignedToDisplayName") or ""
            ).strip():
                subjects.append(str(item.get("assignedTo") or ""))
    else:  # detail
        req = payload.get("requester") or {}
        if not (req.get("displayName") or "").strip():
            subjects.append(str(req.get("subject") or ""))
        if payload.get("assignedTo") and not (
            payload.get("assignedToDisplayName") or ""
        ).strip():
            subjects.append(str(payload.get("assignedTo") or ""))
    return [s for s in subjects if s]

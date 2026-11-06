"""Ator PRC a partir do principal autenticado — fonte única REST/MCP."""

from __future__ import annotations

from engineering_app.domain.product_registration.models import PrcActor


def prc_actor_from_principal(principal, *, channel: str = "portal") -> PrcActor:
    """Projeta o ``PrcActor`` do principal (user Core/delpi_auth)."""
    user_id = getattr(principal, "id", None)
    email_raw = getattr(principal, "email", None)
    name_raw = None
    for attr in ("name", "full_name", "username"):
        value = getattr(principal, attr, None)
        if isinstance(value, str) and value.strip():
            name_raw = value.strip()
            break
    email = (
        email_raw.strip()
        if isinstance(email_raw, str) and email_raw.strip()
        else None
    )
    name = name_raw[:300] if name_raw else None
    label = name or email or (str(user_id) if user_id else None) or None
    if label:
        label = label[:120]
    permissions = frozenset(
        str(p) for p in (getattr(principal, "permissions", None) or [])
    )
    return PrcActor(
        user_id=str(user_id) if user_id else "unknown",
        email=email[:255] if email else None,
        name=name,
        label=label,
        permissions=permissions,
        is_superadmin=bool(getattr(principal, "is_superadmin", False)),
        channel=channel,
    )

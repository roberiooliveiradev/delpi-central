"""Ator NC a partir do principal autenticado — fonte única REST/MCP.

A mesma projeção é usada pelas rotas HTTP e pelas tools EVA: o ator de
auditoria é sempre o humano autenticado, nunca um principal de serviço.
"""

from __future__ import annotations

from engineering_app.domain.nonconformity.models import NcActor


def nc_actor_from_principal(principal) -> NcActor:
    """Projeta o ``NcActor`` do principal autenticado (user Core/delpi_auth)."""
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
    return NcActor(
        user_id=str(user_id) if user_id else "unknown",
        email=email[:255] if email else None,
        name=name,
        label=label,
    )

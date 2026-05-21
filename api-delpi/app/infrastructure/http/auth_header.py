from __future__ import annotations

import os

from delpi_auth.request_context import get_current_user


def bearer_authorization_from_context() -> str | None:
    """Repassa JWT do usuário (ou token de serviço) para transformometro-api."""
    user = get_current_user()
    if user is not None:
        token = getattr(user, "access_token", None)
        if token:
            return f"Bearer {token}"

    service = (os.getenv("TRANSFORMOMETRO_SERVICE_BEARER") or "").strip()
    if service:
        return service if service.startswith("Bearer ") else f"Bearer {service}"
    return None

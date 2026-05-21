from __future__ import annotations


def has_transformometro_auth_error(errors: list[dict] | None) -> bool:
    """Detecta erros 401 persistidos que devem forçar nova leitura do Transformômetro."""
    if not errors:
        return False

    for item in errors:
        message = str(item.get("message") or "").lower()
        if "transformometro-api http 401" in message:
            return True
        if "transformometro" in message and "unauthorized" in message:
            return True
    return False

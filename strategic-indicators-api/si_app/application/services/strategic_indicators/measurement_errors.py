from __future__ import annotations


def has_transformometro_fetch_error(errors: list[dict] | None) -> bool:
    """Erros de chamada ao transformometro-api que devem forçar nova leitura (não usar cache)."""
    if not errors:
        return False

    for item in errors:
        message = str(item.get("message") or "").lower()
        if "transformometro-api http 401" in message:
            return True
        if "transformometro-api http 404" in message:
            return True
        if "transformometro" in message and "unauthorized" in message:
            return True
        if "transformometro" in message and "not found" in message:
            return True
    return False


# Alias usado pelo snapshot service
has_transformometro_auth_error = has_transformometro_fetch_error

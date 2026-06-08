from __future__ import annotations


def _is_auth_or_not_found(message: str) -> bool:
    if "http 401" in message or message.startswith("[401]"):
        return True
    if "http 404" in message or message.startswith("[404]"):
        return True
    if "unauthorized" in message:
        return True
    if "not found" in message:
        return True
    return False


def _is_transient_upstream_failure(message: str) -> bool:
    normalized = message.lower()
    return (
        "connection refused" in normalized
        or "errno 111" in normalized
        or "failed to connect" in normalized
        or "falha ao conectar" in normalized
        or "connect error" in normalized
        or "name or service not known" in normalized
    )


def has_transformometro_fetch_error(errors: list[dict] | None) -> bool:
    """Erros upstream de engenharia que devem forçar nova leitura (não usar cache)."""
    if not errors:
        return False

    for item in errors:
        message = str(item.get("message") or "").lower()
        department_id = str(item.get("department_id") or "").lower()
        source = str(item.get("source") or "").lower()

        if department_id == "engineering" or "engineering" in source:
            if _is_auth_or_not_found(message):
                return True

        if "transformometro-api http 401" in message:
            return True
        if "transformometro-api http 404" in message:
            return True
        if "transformometro" in message and "unauthorized" in message:
            return True
        if "transformometro" in message and "not found" in message:
            return True
    return False


def has_stale_period_snapshot_errors(errors: list[dict] | None) -> bool:
    """Snapshot materializado que não deve ser reutilizado (rede/auth/indisponibilidade)."""
    if has_transformometro_fetch_error(errors):
        return True
    if not errors:
        return False

    for item in errors:
        message = str(item.get("message") or "")
        if _is_transient_upstream_failure(message):
            return True
    return False


# Alias legado usado pelo snapshot service
has_transformometro_auth_error = has_stale_period_snapshot_errors

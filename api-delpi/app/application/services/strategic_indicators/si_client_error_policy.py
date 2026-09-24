from __future__ import annotations


def is_si_not_found_error(exc: BaseException) -> bool:
    """True when SI reported a real missing indicator (not timeout/5xx)."""
    message = str(exc)
    lower = message.lower()
    if "retornou 404" in lower or " http 404" in lower or "[404]" in message:
        return True
    if "não encontrado" in lower or "nao encontrado" in lower:
        return True
    if "not found" in lower:
        return True
    return False

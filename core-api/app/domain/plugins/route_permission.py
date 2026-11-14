"""Normalização de ``routes[].permission``: string canônica ou any-of (lista)."""

from __future__ import annotations

from typing import Any, Sequence


def normalize_route_permission_codes(
    permission: Any,
) -> tuple[str, ...]:
    """
    Aceita:
      - ``\"app.code\"`` → (\"app.code\",)
      - ``[\"a.b\", \"a.c\"]`` → any-of ordenado, sem vazios/duplicatas

    Lista vazia / valor ausente → ().
    """
    if permission is None:
        return ()
    if isinstance(permission, str):
        code = permission.strip()
        return (code,) if code else ()
    if isinstance(permission, (list, tuple)):
        seen: set[str] = set()
        ordered: list[str] = []
        for item in permission:
            code = str(item or "").strip()
            if not code or code in seen:
                continue
            seen.add(code)
            ordered.append(code)
        return tuple(ordered)
    code = str(permission).strip()
    return (code,) if code else ()


def primary_route_permission(permission: Any) -> str | None:
    codes = normalize_route_permission_codes(permission)
    return codes[0] if codes else None


def route_allows_any(
    *,
    permission_code: str | None,
    any_of_permission_codes: Sequence[str] | None,
    user_permissions: Sequence[str],
) -> bool:
    """True se a rota é pública ou o usuário possui qualquer código exigido."""
    codes = tuple(any_of_permission_codes or ())
    if not codes:
        if not permission_code:
            return True
        codes = (permission_code,)
    perm_set = set(user_permissions)
    return any(code in perm_set for code in codes)

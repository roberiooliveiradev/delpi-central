# shared/delpi_auth/context_resolver.py

from .core_client import fetch_user_context


def normalize_context(data: dict) -> dict:

    return {
        "id": str(data.get("id")),
        "email": data.get("email"),
        "name": data.get("name"),
        "roles": list(data.get("roles") or []),
        "groups": list(data.get("groups") or []),
        "permissions": list(data.get("permissions") or []),
        "is_superadmin": bool(data.get("is_superadmin")),
    }


def resolve_user_context(token: str, claims: dict | None = None):

    context = fetch_user_context(token)

    return normalize_context(context)
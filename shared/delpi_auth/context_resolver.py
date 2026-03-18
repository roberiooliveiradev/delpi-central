# delpi_auth/context_resolver.py

from .request_context import get_current_user


def resolve_user_context():
    # Flask
    try:
        from flask import g

        user = getattr(g, "current_user", None) or getattr(g, "user", None)

        if user:
            return user

    except Exception:
        pass

    # FastAPI / ASGI
    user = get_current_user()

    if user:
        return user

    return None
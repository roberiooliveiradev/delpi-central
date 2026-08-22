from fastapi import Request


def resolve_user(request: Request):
    return getattr(request.state, "user", None)
